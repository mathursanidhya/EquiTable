# app.py

import streamlit as st
from pantry_logic import (
    update_item_status,
    check_item_status,
    start_donation,
    confirm_donation,
    ask_policy,
)

# ----------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="EquiTable",
    page_icon="🥫",
)

# --------------------------------------------------------------------
# Pantry item catalog: categories & items as used at your real pantry
# --------------------------------------------------------------------

ITEM_OPTIONS = [
    # Canned Vegetables
    "Green Beans",
    "Corn",
    "Green Peas",
    "Canned Tomatoes",
    "Carrots (Canned)",
    "Mixed Vegetables",
    "Spinach (Canned)",
    "Potatoes (Canned)",
    "Beets",
    "Pumpkin Puree",

    # Canned Fruit
    "Peaches",
    "Pears",
    "Pineapple",
    "Fruit Cocktail",
    "Mandarin Oranges",
    "Applesauce",
    "Apricots",
    "Mango",

    # Grain
    "Rice",
    "Pasta",
    "Oats",
    "Cereal",
    "Quinoa",
    "Flour",
    "Cornmeal",
    "Barley",
    "Couscous",
    "Crackers",

    # Protein
    "Tuna",
    "Salmon",
    "Canned Chicken",
    "Beans",
    "Lentils",
    "Chickpeas",
    "Eggs",
    "Ground Meat",
    "Fish Fillets",
    "Tofu",

    # Dairy
    "Milk",
    "UHT Milk",
    "Yogurt",
    "Cheese",
    "Sliced Cheese",
    "Butter",
    "Almond Milk",
    "Oat Milk",

    # Fresh Produce
    "Leafy Greens",
    "Tomatoes",
    "Onions",
    "Potatoes",
    "Carrots",
    "Apples",
    "Bananas",
    "Oranges",
    "Bell Peppers",
    "Cucumbers",
    "Broccoli",
    "Cauliflower",

    # Manual entry
    "Other (type manually)",
]

ITEM_TO_GROUP = {
    # Canned Vegetables
    "Green Beans": "Canned Vegetable",
    "Corn": "Canned Vegetable",
    "Green Peas": "Canned Vegetable",
    "Canned Tomatoes": "Canned Vegetable",
    "Carrots (Canned)": "Canned Vegetable",
    "Mixed Vegetables": "Canned Vegetable",
    "Spinach (Canned)": "Canned Vegetable",
    "Potatoes (Canned)": "Canned Vegetable",
    "Beets": "Canned Vegetable",
    "Pumpkin Puree": "Canned Vegetable",

    # Canned Fruit
    "Peaches": "Canned Fruit",
    "Pears": "Canned Fruit",
    "Pineapple": "Canned Fruit",
    "Fruit Cocktail": "Canned Fruit",
    "Mandarin Oranges": "Canned Fruit",
    "Applesauce": "Canned Fruit",
    "Apricots": "Canned Fruit",
    "Mango": "Canned Fruit",

    # Grain
    "Rice": "Grain",
    "Pasta": "Grain",
    "Oats": "Grain",
    "Cereal": "Grain",
    "Quinoa": "Grain",
    "Flour": "Grain",
    "Cornmeal": "Grain",
    "Barley": "Grain",
    "Couscous": "Grain",
    "Crackers": "Grain",

    # Protein
    "Tuna": "Protein",
    "Salmon": "Protein",
    "Canned Chicken": "Protein",
    "Beans": "Protein",
    "Lentils": "Protein",
    "Chickpeas": "Protein",
    "Eggs": "Protein",
    "Ground Meat": "Protein",
    "Fish Fillets": "Protein",
    "Tofu": "Protein",

    # Dairy
    "Milk": "Dairy",
    "UHT Milk": "Dairy",
    "Yogurt": "Dairy",
    "Cheese": "Dairy",
    "Sliced Cheese": "Dairy",
    "Butter": "Dairy",
    "Almond Milk": "Dairy",
    "Oat Milk": "Dairy",

    # Fresh Produce
    "Leafy Greens": "Fresh Produce",
    "Tomatoes": "Fresh Produce",
    "Onions": "Fresh Produce",
    "Potatoes": "Fresh Produce",
    "Carrots": "Fresh Produce",
    "Apples": "Fresh Produce",
    "Bananas": "Fresh Produce",
    "Oranges": "Fresh Produce",
    "Bell Peppers": "Fresh Produce",
    "Cucumbers": "Fresh Produce",
    "Broccoli": "Fresh Produce",
    "Cauliflower": "Fresh Produce",

    "Other (type manually)": None,
}

STATUS_LABELS = {
    "✅ In Stock": "In Stock",
    "⚠️ Low": "Low",
    "❌ Out of Stock": "Out of Stock",
}

STATUS_LABELS_REVERSE = {v: k for k, v in STATUS_LABELS.items()}

# --------------------------------------------------------------------
# Streamlit layout
# --------------------------------------------------------------------

st.title("🥫 EquiTable")
st.markdown(
    "A real-time inventory brain for volunteers who need to make fast, fair, "
    "and kind decisions. Let the system handle the logistics while you serve "
    "with compassion."
)

tab_inventory, tab_table, tab_donations = st.tabs(
    ["📦 Inventory", "🤝 Volunteer Service Desk", "🚚 Surplus Donation Routing"]
)

# Store pending donation tokens & last donation item between reruns
if "donation_token" not in st.session_state:
    st.session_state["donation_token"] = None
if "last_donation_item" not in st.session_state:
    st.session_state["last_donation_item"] = ""
if "donation_reject_reason" not in st.session_state:
    st.session_state["donation_reject_reason"] = ""


# ====================================================================
# TAB 1: INVENTORY
# ====================================================================
with tab_inventory:
    st.subheader("📦 Inventory tools")

    # ---------- QUICK SINGLE-ITEM UPDATE ----------
    with st.expander("🔹 Quick single-item update", expanded=True):
        st.caption(
            "Use this when you just need to flip **one item** quickly "
            "during a shift (for example, when a case of beans just arrived)."
        )

        col1, col2 = st.columns([3, 1])

        with col1:
            item_choice_single = st.selectbox(
                "Item to update",
                ITEM_OPTIONS,
                key="item_single_choice",
            )

            custom_item_single = ""
            if item_choice_single == "Other (type manually)":
                custom_item_single = st.text_input(
                    "Custom item name",
                    key="item_single_custom",
                )

        with col2:
            status_label_single = st.selectbox(
                "Status",
                list(STATUS_LABELS.keys()),
                key="status_single",
            )

        if st.button("Update this item"):
            # Resolve name & status
            if item_choice_single == "Other (type manually)":
                item_name_single = custom_item_single.strip()
            else:
                item_name_single = item_choice_single

            if not item_name_single:
                st.warning("Please select or enter an item name.")
            else:
                status_plain = STATUS_LABELS[status_label_single]
                try:
                    _ = update_item_status(item_name_single, status_plain)
                    # Only one succinct success line (no duplicate)
                    st.success(
                        f"{item_name_single} is now **{status_plain}**."
                    )
                except Exception as e:
                    st.error(f"Error updating inventory: {e}")

    st.markdown("---")

    # ---------- MULTI-ITEM UPDATE ----------
    with st.expander("☑️ Update multiple items at once", expanded=True):
        st.caption(
            "Pick several items that share the same status and save them in **one click**. "
            "Helpful when a whole case arrives or a whole shelf runs out."
        )

        items_multi = st.multiselect(
            "Items to update",
            ITEM_OPTIONS,
            key="items_multi_select",
        )

        status_label_multi = st.selectbox(
            "Status for all selected items",
            list(STATUS_LABELS.keys()),
            key="status_multi",
        )

        if st.button("Update selected items"):
            if not items_multi:
                st.warning("Please select at least one item to update.")
            else:
                status_plain = STATUS_LABELS[status_label_multi]
                updated = []
                errors = []

                for item in items_multi:
                    if item == "Other (type manually)":
                        continue
                    try:
                        update_item_status(item, status_plain)
                        updated.append(item)
                    except Exception as e:
                        errors.append(f"{item}: {e}")

                if updated:
                    st.success(
                        f"Updated {len(updated)} item(s) to **{status_plain}**: "
                        + ", ".join(updated)
                    )
                if errors:
                    st.error(
                        "Some items could not be updated:\n\n"
                        + "\n".join(f"- {e}" for e in errors)
                    )


# ====================================================================
# TAB 2: VOLUNTEER SERVICE DESK
# ====================================================================
with tab_table:
    st.subheader("🤝 Volunteer Service Desk")

    # ---------- CHECK ITEM STATUS ----------
    st.markdown("### 🛒 Check item availability")

    item_choice_check = st.selectbox(
        "Item to check",
        ITEM_OPTIONS,
        key="item_check_choice",
    )

    custom_item_check = ""
    if item_choice_check == "Other (type manually)":
        custom_item_check = st.text_input(
            "Custom item name",
            key="item_check_custom",
        )

    if st.button("Check status"):
        if item_choice_check == "Other (type manually)":
            item_name_check = custom_item_check.strip()
        else:
            item_name_check = item_choice_check

        if not item_name_check:
            st.warning("Please select or enter an item name.")
        else:
            try:
                result = check_item_status(item_name_check)
                st.info(result)
            except Exception as e:
                st.error(f"Error: {e}")

    # ---------- SUBSTITUTION HELPER ----------
    st.markdown("---")
    st.markdown("### 🔄 Policy-Guide Wiz")
    st.caption(
        "Policy note: The coordinator uses **family size, dietary needs, inventory, "
        "and fairness rules** to evaluate tricky trades."
    )

    family_size = st.number_input(
        "Family size",
        min_value=1,
        step=1,
        value=4,
        key="sub_family_size",
    )

    col_sub1, col_sub2 = st.columns(2)

    with col_sub1:
        from_item = st.selectbox(
            "Item to substitute (e.g., allergy, preference)",
            ITEM_OPTIONS,
            key="sub_from_item",
        )

    with col_sub2:
        to_item = st.selectbox(
            "Requested substitution item",
            ITEM_OPTIONS,
            key="sub_to_item",
        )

    extra_notes = st.text_area(
        "📋 Coordinator notes / dietary needs (e.g., lactose intolerant, vegetarian, allergies)",
        key="sub_notes",
        placeholder="Family is vegetarian, one child is lactose intolerant...",
        height=80,
    )

    if st.button("Balance the basket"):
        if (
            from_item == "Other (type manually)"
            and to_item == "Other (type manually)"
            and not extra_notes.strip()
        ):
            st.warning(
                "Please choose at least one specific item or add notes before asking."
            )
        else:
            context_lines = [f"Family size: {int(family_size)}."]

            from_group = ITEM_TO_GROUP.get(from_item)
            to_group = ITEM_TO_GROUP.get(to_item)

            if from_item != "Other (type manually)":
                if from_group:
                    context_lines.append(
                        f"The family is giving up '{from_item}', which is in the '{from_group}' food group."
                    )
                else:
                    context_lines.append(
                        f"The family is giving up '{from_item}'."
                    )

            if to_item != "Other (type manually)":
                if to_group:
                    context_lines.append(
                        f"They are asking for more of '{to_item}', which is in the '{to_group}' food group."
                    )
                else:
                    context_lines.append(
                        f"They are asking for more of '{to_item}'."
                    )

            if extra_notes.strip():
                context_lines.append(f"Notes: {extra_notes.strip()}")

            context_lines.append(
                "Volunteer wants to know if this substitution is fair and allowed. "
                "Give a clear yes/no recommendation and a brief allocation summary "
                "based on their card, inventory tools, and your trade rules."
            )

            full_query = "\n".join(context_lines)

            with st.spinner("Checking policy and inventory..."):
                try:
                    answer = ask_policy(full_query)
                except Exception as e:
                    st.error(f"Error: {e}")
                else:
                    st.markdown("### Coordinator decision & rationale")

                    lower = answer.lower()
                    if any(x in lower for x in ["yes", "approve", "allowed"]) and not any(
                        x in lower for x in ["cannot", "not approve", "deny"]
                    ):
                        st.success(answer)
                    elif any(
                        x in lower
                        for x in ["cannot", "not approve", "decline", "deny"]
                    ):
                        st.error(answer)
                    else:
                        st.info(answer)


# ====================================================================
# TAB 3: DONATIONS
# ====================================================================

# ---------- TAB 3: DONATIONS ----------
with tab_donations:
    st.subheader("🚚 Surplus Donation Routing")

    # make sure flag exists
    if "show_reject_form" not in st.session_state:
        st.session_state["show_reject_form"] = False

    item_type = st.text_input(
        "What surplus food do we need to route?",
        placeholder="e.g. sandwiches, milk, chicken, canned goods",
    )

    if st.button("Find donation partner"):
        if not item_type.strip():
            st.warning("Please describe the surplus food.")
        else:
            with st.spinner("Looking for a partner shelter..."):
                try:
                    st.session_state["last_donation_item"] = item_type.strip()
                    st.session_state["show_reject_form"] = False  # reset form
                    message, pending, token = start_donation(item_type.strip())
                    st.info(message)
                    if pending and token:
                        st.session_state["donation_token"] = token
                    else:
                        st.session_state["donation_token"] = None
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state["donation_token"] = None
                    st.session_state["show_reject_form"] = False

    # If we have a pending donation request, show HITL UI
    if st.session_state.get("donation_token"):
        st.markdown("---")
        st.markdown("### Human-in-the-Loop Approval")
        st.caption(
            "The agent has found a partner shelter but is paused until a human "
            "supervisor approves or rejects this route."
        )

        col_a, col_b = st.columns(2)

        # APPROVE BUTTON
        with col_a:
            if st.button("✅ Approve donation"):
                with st.spinner("Completing donation..."):
                    try:
                        msg = confirm_donation(
                            st.session_state["donation_token"], approve=True
                        )
                        st.success(msg)
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        st.session_state["donation_token"] = None
                        st.session_state["show_reject_form"] = False
                        st.session_state["donation_reject_reason"] = ""

        # REJECT BUTTON (shows the form, doesn’t reject yet)
        with col_b:
            if st.button("❌ Reject donation"):
                st.session_state["show_reject_form"] = True

        # REJECTION FORM + FINAL “REJECT WITH FEEDBACK” BUTTON
        if st.session_state.get("show_reject_form", False):
            st.markdown("#### Tell us why this route doesn’t work ↪")
            st.caption("Why can't this partner accept the donation right now?")

            reason = st.text_area(
                "",
                key="donation_reject_reason",
                placeholder="e.g., They refused the item last time, or their fridge is not working.",
                height=90,
            )

            if st.button("Submit feedback and reject route"):
                if not reason.strip():
                    st.warning("Please add a short reason before rejecting this route.")
                else:
                    with st.spinner("Recording feedback and updating route..."):
                        try:
                            msg = confirm_donation(
                                st.session_state["donation_token"], approve=False
                            )
                            st.error("❌ Donation route declined.")
                            st.markdown(
                                f"- **Item(s):** `{st.session_state.get('last_donation_item', '').strip() or 'N/A'}`\n"
                                f"- **Reason:** {reason.strip()}\n"
                                "- **Next step:** Keep the food on site for now and use this tool again later "
                                "to explore a better partner shelter when conditions improve."
                            )
                            st.info(msg)
                        except Exception as e:
                            st.error(f"Error: {e}")
                        finally:
                            st.session_state["donation_token"] = None
                            st.session_state["show_reject_form"] = False
                            # keep reason in state only for this run; widget key persists automatically


