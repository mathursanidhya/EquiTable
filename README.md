# 🥫 EquiTable

### **Empowering food pantry volunteers to make fast, fair, and kind decisions using a Multi-Agent AI System.**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sani-equitable.streamlit.app/)
*Built for the Google X Kaggle AI Agents Capstone (Agents for Good Track)* 

---

## 📖 The Problem
Food pantries are high-stress environments. Volunteers often face the **"Chaos of Compassion"**: trying to mentally juggle complex point systems, track real-time shortages, and enforce substitution rules while maintaining a dignified connection with families.

**EquiTable** acts as a "Shift Lead" AI. It abstracts the logistics, allowing volunteers to focus on people,not paperwork.

## 🏗️ Architecture 
EquiTable utilizes a **Hub-and-Spoke Multi-Agent Architecture** orchestrated by the Google Agent Development Kit (ADK). This ensures that logic (rules) and arithmetic (math) are handled by specialists, preventing AI hallucinations.

<img width="2816" height="1536" alt="The Fairness Logic" src="https://github.com/user-attachments/assets/03f2c03a-9821-495b-8498-6494a8975361" />

<img width="2816" height="1536" alt="The Donation Flow" src="https://github.com/user-attachments/assets/c7fa198b-7eb7-4167-a95d-2153e06d4b11" />

<img width="2816" height="1536" alt="The Inventory Flow" src="https://github.com/user-attachments/assets/f4d6a6df-c013-4a01-892a-366981df859c" />

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
   git clone https://github.com/mathursanidhya/EquiTable.git
   cd EquiTable

2. **Install Dependancies:**
   ```bash
   pip install -r requirements.txt

3. **Set up credentials:**

   Create a .env file in the root directory.
   
   Add your API key: GOOGLE_API_KEY=your_actual_api_key_here

   (Note: In production, this is handled via Streamlit Secrets).

5. **Run the application:**
   ```bash
   streamlit run app.py


## 💻 Usage Guide

### **1. Inventory Management**
Use the **"Inventory"** tab to instantly update stock levels. The system writes these to a persistent database, ensuring the Policy Agent always has up-to-date data.

### **2. The Volunteer Desk**
Type complex requests like: *"Family of 5 wants to swap Milk for Chicken, due to Milk Allergy."*
The agent will:
* Calculate the points allowance.
* Check the database for Bean availability.
* Check fairness rules (e.g., allergy exceptions).
* Return an **"Approved"** or **"Declined"** verdict.

### **3. Surplus Donations**
Input surplus items (e.g., *"50 trays of canned chicken"*). The agent scans for open partner shelters and **pauses** for your approval before confirming the route.

*Created by Sanidhya Mathur*
