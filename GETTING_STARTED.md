# Getting Started - HR Vacation Application

## Prerequisites

- Python 3.10+ installed
- A terminal or command prompt

---

## 1. Clone / Open the Project

```powershell
cd path\to\local-llm-test
```

---

## 2. Install Dependencies

Create a virtual environment and install required packages:

```powershell
# Create virtual environment
python -m venv venv

# Activate it (PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

---

## 3. Seed the Database

This creates the test users, roles, and vacation balances:

```powershell
cd backend
python seed_data.py
cd ..
```

### Test Users Created

| Username    | Role(s)         | Vacation Balance | Manager   |
|-------------|-----------------|------------------|-----------|
| `admin`     | ADMIN, MANAGER  | None             | —         |
| `jdoe`      | MANAGER         | None             | —         |
| `janedoe`   | EMPLOYEE        | 80 hours         | jdoe      |
| `bobsmith`  | EMPLOYEE        | 60 hours         | jdoe      |

---

## 4. Run the Server

```powershell
cd backend
python flask_main.py
```

The server starts on **http://localhost:5000** with debug mode enabled.

---

## 5. Sample Flow: Create & Approve a Vacation Request

### Step A — Employee Creates a Request

1. Open http://localhost:5000 in your browser
2. Enter username **janedoe** and click **Login**
3. Click the **"New Request"** tab
4. Fill in the form:
   - **Start Date**: e.g., `2026-09-15`
   - **End Date**: e.g., `2026-09-17`
   - **Request Type**: Full Day(s)
   - **Reason** (optional): "Team offsite"
5. The hours field auto-calculates (3 days = 24 hours)
6. Click **Submit Request**
7. Navigate to **"My Requests"** tab — you'll see your request with status `PENDING`
8. Navigate to **"My Balance"** tab — you'll see your available hours

### Step B — Manager Approves the Request

1. Click **Logout**
2. Log in as **jdoe** (the manager)
3. You'll see a new **"Pending Approvals"** tab (visible only to managers)
4. Click **"Pending Approvals"** — you'll see janedoe's request
5. Click **Approve** on the request card
6. A toast notification confirms "Request approved successfully!"

### Step C — Employee Verifies Approval

1. Click **Logout**
2. Log in as **janedoe** again
3. Go to **"My Requests"** tab
4. The request status is now `APPROVED`
5. Check **"My Balance"** — your used hours have increased

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "User not found" on login | Database wasn't seeded. Run `python backend/seed_data.py` again |
| Server won't start | Port 5000 is in use. Check for other Flask processes or set a new port in `.env` |
| Balance shows 0 or missing | Re-seed the database with `cd backend && python seed_data.py` |
