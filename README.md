# 🥫 EquiTable

### **Empowering food pantry volunteers to make fast, fair, and kind decisions using a Multi-Agent AI System.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sani-equitable.streamlit.app/)
*Built for the Google X Kaggle AI Agents Capstone (Agents for Good Track)*

---

## 📖 The Problem
Food pantries are high-stress environments. Volunteers often face the **"Chaos of Compassion"**: trying to mentally juggle complex point systems, track real-time shortages, and enforce substitution rules while maintaining a dignified connection with families.

**EquiTable** acts as a "Shift Lead" AI. It abstracts the logistics, allowing volunteers to focus on people, not paperwork.

## 🏗️ Architecture
EquiTable utilizes a **Hub-and-Spoke Multi-Agent Architecture** orchestrated by the Google Agent Development Kit (ADK). This ensures that logic (rules) and arithmetic (math) are handled by specialists, preventing AI hallucinations.

![Architecture Diagram](image_922526.jpg)

### **The Agent Squad**
1.  **Pantry Coordinator (Root Agent):** The interface. Understands natural language and routes tasks.
2.  **Policy Adjudicator:** The logic engine. Enforces the pantry's "Constitution" (e.g., "No dairy for lactose intolerance").
3.  **Point Calculator:** A math specialist using `BuiltInCodeExecutor` to run Python code for 100% accurate math.
4.  **Inventory Clerk:** Manages the persistent SQLite database to track stock levels.
5.  **Donation Logistics:** Handles surplus routing using a **Human-in-the-Loop** workflow.

---

## 🚀 Features & Course Concepts
This project implements 5 key concepts from the AI Agents curriculum:
* **Multi-Agent Orchestration:** Specialized agents for distinct tasks.
* **Long-Running Operations:** The Donation agent pauses execution to wait for human approval before routing food.
* **Custom Tools:** Specialized Python functions for database interaction.
* **Persistent State:** Uses `DatabaseSessionService` (SQLite) so inventory is remembered across shifts.
* **Production Deployment:** Hosted on Streamlit Cloud with secure secret management.

---

## ⚙️ Setup & Installation

**Prerequisites:** Python 3.10+

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/EquiTable.git](https://github.com/YOUR_USERNAME/EquiTable.git)
   cd EquiTable
