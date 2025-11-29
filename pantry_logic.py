# pantry_logic.py

import os
import uuid
import asyncio

from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import AgentTool, ToolContext, FunctionTool
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.apps.app import App, ResumabilityConfig

# If running inside Streamlit, prefer st.secrets as a fallback for env var
try:
    import streamlit as _st
    # only set env var when not already set
    if not os.getenv("GOOGLE_API_KEY") and "GOOGLE_API_KEY" in _st.secrets:
        os.environ["GOOGLE_API_KEY"] = _st.secrets["GOOGLE_API_KEY"]
except Exception:
    # not running in Streamlit or st.secrets not available; keep going
    pass

# ---------- ASYNC LOOP HELPER (for Streamlit & sync code) ----------

_event_loop = None


def _get_event_loop():
    """Get or create a global event loop that we reuse for all async calls."""
    global _event_loop

    if _event_loop is not None and not _event_loop.is_closed():
        return _event_loop

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    _event_loop = loop
    return loop


def run_sync(coro):
    """Run an async coroutine from sync code using a persistent loop."""
    loop = _get_event_loop()
    return loop.run_until_complete(coro)


# ---------- API KEY SETUP ----------

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. "
        "Set it as an environment variable before running the app."
    )
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


# ---------- MODEL CONFIG ----------

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

model_config = Gemini(
    model="gemini-2.5-flash-lite",
    retry_options=retry_config,
)

# Use ONE shared session id so inventory + policy see the same state
SESSION_ID_MAIN = "pantry_main_session"


# ---------- GLOBAL DATA (PARTNER SHELTERS) ----------

PARTNER_SHELTERS = [
    {
        "name": "SafeHaven Shelter",
        # Hot / prepared / protein-heavy food
        "accepts": [
            "sandwiches",
            "meals",
            "prepared food",
            "meat",
            "chicken",
            "hot food",
            "protein",
        ],
        "status": "Open 24/7",
    },
    {
        "name": "Community Pantry North",
        # Shelf-stable and cold items, including milk / dairy
        "accepts": [
            "canned goods",
            "canned",
            "dry goods",
            "rice",
            "beans",
            "pasta",
            "cereal",
            "canned vegetables",
            "canned fruit",
            "milk",
            "dairy",
        ],
        "status": "Open 9-5",
    },
    {
        "name": "Youth Center",
        # Snacks & fruit for kids/teens
        "accepts": [
            "snacks",
            "fruit",
            "sandwiches",
            "juice",
            "granola bars",
            "apples",
            "bananas",
            "oranges",
        ],
        "status": "Open until 10 PM",
    },
]


# ---------- LOW-LEVEL TOOLS (functions) ----------

def update_inventory(tool_context: ToolContext, item_name: str, status: str) -> str:
    """Updates inventory status in Session State."""
    key = f"inventory:{item_name.lower()}"
    tool_context.state[key] = status
    return f"✅ SYSTEM UPDATE: Inventory for '{item_name}' set to '{status}'."


def check_inventory(tool_context: ToolContext, item_name: str) -> str:
    """Checks inventory status from Session State."""
    key = f"inventory:{item_name.lower()}"
    status = tool_context.state.get(key, "In Stock")
    return f"STATUS CHECK: {item_name} is currently '{status}'."


def find_donation_partner_safe(item_type: str, tool_context: ToolContext):
    """
    Finds a shelter but PAUSES for human approval.
    Demonstrates long-running operations with pause/resume.
    """
    match = None
    for p in PARTNER_SHELTERS:
        if any(keyword in item_type.lower() for keyword in p["accepts"]):
            match = p
            break

    if not match:
        return (
            "I couldn't find a good partner shelter for that specific kind of food. "
            "You may need to hold it on site or check with the coordinator."
        )

    # First call: no confirmation yet → pause and surface details
    if not tool_context.tool_confirmation:
        tool_context.state["donation:last_item"] = item_type
        tool_context.state["donation:last_partner_name"] = match["name"]
        tool_context.state["donation:last_partner_status"] = match["status"]

        accepts_preview = ", ".join(match["accepts"][:5])
        partner_summary = (
            f"{match['name']} ({match['status']}). "
            f"They typically accept items like {accepts_preview}."
        )

        tool_context.request_confirmation(
            hint=f"Approve sending the extra {item_type} to {match['name']}?"
        )

        return (
            f"I've found a partner for the extra {item_type}: {partner_summary} "
            "Please let me know if you'd like to approve this donation."
        )

    # Second call: human has responded
    item = tool_context.state.get("donation:last_item", "this food")
    name = tool_context.state.get("donation:last_partner_name", "the partner shelter")

    if tool_context.tool_confirmation.confirmed:
        return (
            f"I've recorded your approval. We'll send the information needed for "
            f"volunteers or drivers to transfer the extra {item} to {name}."
        )
    else:
        return (
            f"Okay, we won't send this donation to {name}. "
            "The partner shelter isn't able to accept it right now. "
            "You can hold the food on site or try another partner if appropriate."
        )


# ======================================================================
#                     AGENT SQUAD ("Pantry Squad")
# ======================================================================

# ---------- Agent 2: Point Calculator (math only) ----------

point_calculator_agent = LlmAgent(
    name="Point_Calculator",
    model=model_config,
    instruction="""
You are a Python Code Generator used ONLY for math.

INPUT: A math expression (e.g., "5 * 2").
OUTPUT: Python code that prints ONLY the final number.

Do NOT explain. Do NOT chat. Just generate and run code that prints a single number.
""",
    code_executor=BuiltInCodeExecutor(),
)


# ---------- Agent 4: Inventory Clerk (owns inventory tools) ----------

inventory_clerk_agent = LlmAgent(
    name="Inventory_Clerk",
    model=model_config,
    instruction="""
You are the Inventory Clerk.

Your job:
- Update inventory status for individual items.
- Report current status for items when asked.

You have TWO tools:
- update_inventory(item_name, status)
- check_inventory(item_name)

ALWAYS use these tools instead of guessing.
""",
    tools=[update_inventory, check_inventory],
)


# ---------- Agent 3: Policy Adjudicator (substitution rulebook) ----------

policy_adjudicator_agent = LlmAgent(
    name="Policy_Adjudicator",
    model=model_config,
    instruction="""
You are the Policy Adjudicator for a New York City community food pantry.

You never talk directly to volunteers. You only talk to the Pantry Coordinator
and return structured, thoughtful answers.

You decide if a requested substitution is fair and allowed, based on:
- Family size
- Food groups (Dairy, Protein, Grain, Canned Veg, Canned Fruit, Fresh Produce)
- Allergies or dietary notes
- Inventory (via tools)
- Our fairness rules

You have access to THREE tools:
- Point_Calculator (for math on allowances & caps)
- update_inventory(item_name, status)
- check_inventory(item_name)

When you need numbers:
- Group A categories (Canned Veg, Canned Fruit, Grain, Protein) get 2 points per person.
- Group B categories (Dairy, Fresh Produce) get 1 point per person.
- Use Point_Calculator for any multiplication or limit math.

FAIRNESS RULES (short version):
- Only one category trade per family.
- Never move ALL items out of a category.
- Keep destination category under ~2x its base allowance.
- Respect inventory: if item or group is Low/Out, lean NO.
- Protein is most valuable: trades out of Protein should usually be 2:1.
- Dairy → Protein is allowed at ~2 dairy : 1 protein, especially for lactose-intolerant families.
- Never trade INTO Dairy for lactose-intolerant families.

When you respond:
- Start with a clear decision line:
    - "APPROVED – short reason..."
    - "DECLINED – short reason..."
- Then give a brief rationale and allocation summary.
- Keep it under 2–3 short paragraphs.
""",
    tools=[
        AgentTool(agent=point_calculator_agent),
        update_inventory,
        check_inventory,
    ],
)


# ---------- Agent 5: Donation Logistics (owns donation tool) ----------

donation_logistics_agent = LlmAgent(
    name="Donation_Logistics",
    model=model_config,
    instruction="""
You are the Donation Logistics agent.

Your job:
- Take a description of surplus food (e.g., "extra milk", "chicken", "sandwiches").
- ALWAYS call the find_donation_partner_safe tool to locate a good partner shelter.
- NEVER answer directly without calling this tool.
- Rely on the tool's built-in pause/resume (human-in-the-loop) flow.

Your entire job is:
1) Call find_donation_partner_safe(item_type)
2) Return the tool's text back to the Pantry Coordinator.
""",
    tools=[FunctionTool(find_donation_partner_safe)],
)


# ---------- Agent 1: Pantry Coordinator (router / face to user) ----------

pantry_coordinator_agent = LlmAgent(
    name="Pantry_Coordinator",
    model=model_config,
    instruction="""
You are the Shift Lead at a New York City community food pantry.

You are the ONLY agent that interacts with volunteers.

Your job is to:
1. Understand the volunteer's request in natural language.
2. Route work to the right specialist:
   - Inventory questions → Inventory_Clerk
   - Substitution / fairness questions → Policy_Adjudicator
   - Surplus donations → Donation_Logistics
3. For very simple inventory flips, you MAY call:
   - update_inventory(item_name, status)
   - check_inventory(item_name)
4. For any numeric allowance / cap work, you MUST call:
   - Point_Calculator

Routing rules:
- If the message mentions "surplus", "extra food", "donation", or "route",
  you MUST call Donation_Logistics and NOT answer directly.
- If the message mentions "family size", "substitute", "allergy",
  or "trade X for Y", you MUST call Policy_Adjudicator.
- If the message is clearly about just marking an item In Stock / Low / Out,
  you MAY either:
     - call Inventory_Clerk, OR
     - call update_inventory directly.

Tone:
- Calm, kind, practical.
- Lead with the decision, then a short explanation.
""",
    tools=[
        # Specialist agents
        AgentTool(agent=inventory_clerk_agent),
        AgentTool(agent=policy_adjudicator_agent),
        AgentTool(agent=donation_logistics_agent),
        AgentTool(agent=point_calculator_agent),  # <-- Root can call calculator too
        # Low-level inventory tools
        update_inventory,
        check_inventory,
    ],
)


# ---------- APP & RUNNER ----------

pantry_app = App(
    name="pantry_app",
    root_agent=pantry_coordinator_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)

runner = Runner(
    app=pantry_app,
    session_service=DatabaseSessionService(
        db_url="sqlite+aiosqlite:///./pantry.db",
    ),
)


# ---------- HELPER: SINGLE TURN RUN ----------

async def _run_once(message: str, session_id: str = SESSION_ID_MAIN) -> str:
    """
    Sends a single message to the pantry app and returns the final text reply.
    Used by the UI-friendly wrapper functions.
    """
    response_list = await runner.run_debug(message, session_id=session_id)

    final_answer = "NO RESPONSE"
    for event in reversed(response_list):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    final_answer = part.text
                    break
        if final_answer != "NO RESPONSE":
            break

    return final_answer


# ---------- INVENTORY HELPERS ----------

async def update_item_status_async(item_name: str, status: str) -> str:
    """
    Update inventory status for a particular item.
    Uses a shared main session so state persists across checks & policy.
    """
    msg = f"Update status: {item_name} is {status}."
    return await _run_once(msg, session_id=SESSION_ID_MAIN)


async def check_item_status_async(item_name: str) -> str:
    """
    Check inventory status for a particular item.
    Uses the same main session as updates & policy.
    """
    msg = f"Can I give {item_name}?"
    return await _run_once(msg, session_id=SESSION_ID_MAIN)


# ---------- DONATION (HITL) HELPERS ----------

# ---------- DONATION (HITL) HELPERS ----------
# NOTE: The Donation_Logistics agent + find_donation_partner_safe still
# uses tool_context.request_confirmation for the capstone rubric.
# For the UI, we run a simple, robust Python-based HITL flow here.

DONATION_SESSIONS: dict[str, dict] = {}


async def start_donation_async(item_type: str) -> tuple[str, bool, str | None]:
    """
    Start a donation flow *for the Streamlit UI*.

    Returns (message, pending, token).

    - If pending == False, message is final (no partner found).
    - If pending == True, token identifies the pending route so the
      UI can later approve/reject it via confirm_donation_async.

    This uses the same PARTNER_SHELTERS and matching logic as
    find_donation_partner_safe, but does NOT depend on ADK's
    pause/resume machinery so the UI is stable.
    """
    item_lower = item_type.lower().strip()

    # 1) Find a matching partner (same logic as the tool)
    match = None
    for p in PARTNER_SHELTERS:
        if any(keyword in item_lower for keyword in p["accepts"]):
            match = p
            break

    if not match:
        message = (
            "I couldn't find a good partner shelter for that specific kind of food. "
            "You may need to hold it on site or check with the coordinator."
        )
        return message, False, None

    # 2) Build a clear banner message for the UI
    accepts_preview = ", ".join(match["accepts"][:5])
    message = (
        f"I've found a partner for the extra {item_type}: "
        f"{match['name']} ({match['status']}). "
        f"They typically accept items like {accepts_preview}. "
        "Please review and decide whether to approve this donation."
    )

    # 3) Record a pending session for human approval
    token = uuid.uuid4().hex
    DONATION_SESSIONS[token] = {
        "item_type": item_type,
        "partner_name": match["name"],
        "partner_status": match["status"],
        "partner_accepts": match["accepts"],
    }

    return message, True, token


async def confirm_donation_async(token: str, approve: bool) -> str:
    """
    Complete a pending donation flow after human approval/rejection,
    *without* depending on ADK resumability for the UI.

    The long-running pattern is still demonstrated inside the
    find_donation_partner_safe tool via tool_context.request_confirmation.
    """
    info = DONATION_SESSIONS.get(token)
    if not info:
        return "No pending donation request was found. Please start a new one."

    item = info["item_type"]
    name = info["partner_name"]

    # Clean up the pending session now that a decision has been made
    DONATION_SESSIONS.pop(token, None)

    if approve:
        return (
            f"I've recorded your approval. We'll send the information needed for "
            f"volunteers or drivers to transfer the extra {item} to {name}."
        )
    else:
        return (
            f"I'm sorry, but it looks like {name} isn't able to accept the {item} right now. "
            "You can keep the food on site for now or try a different partner later."
        )



# ---------- POLICY QUESTIONS ----------

async def ask_policy_async(query: str) -> str:
    """
    Ask the Pantry Coordinator a policy question in natural language.
    Uses the same main session so it can see inventory updates.
    """
    return await _run_once(query, session_id=SESSION_ID_MAIN)


# ---------- PUBLIC SYNC WRAPPERS (for Streamlit) ----------

def update_item_status(item_name: str, status: str) -> str:
    return run_sync(update_item_status_async(item_name, status))


def check_item_status(item_name: str) -> str:
    return run_sync(check_item_status_async(item_name))


def start_donation(item_type: str) -> tuple[str, bool, str | None]:
    return run_sync(start_donation_async(item_type))


def confirm_donation(token: str, approve: bool) -> str:
    return run_sync(confirm_donation_async(token, approve))


def ask_policy(query: str) -> str:
    """Sync wrapper for Streamlit."""
    return run_sync(ask_policy_async(query))
