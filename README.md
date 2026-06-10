# Reimbursement Management Backend

A production-ready FastAPI backend for the Reimbursement Management System with Supabase and Zoho Books integration.

## Features
- **FastAPI**: High-performance asynchronous API framework.
- **Supabase Integration**: Auth, Postgres, Storage, and RLS.
- **Zoho Books**: Automated syncing of approved expenses.
- **Audit Logging**: Comprehensive tracking of all actions.
- **Role-Based Access**: Employee and Admin roles properly isolated.
- **Repository/Service Pattern**: Clean architecture separating data access from business logic.

## Setup Instructions

### 1. Environment Setup

Copy the example environment file and fill in your credentials:
```bash
cp .env.example .env
```

Ensure `tokens.json` exists in the backend directory with valid Zoho API credentials.

### 2. Install Dependencies

Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Database Migration

The Supabase schema can be found in `migration.sql` (if you want to apply it manually). Ensure your tables, storage buckets, and RLS policies are created correctly.

### 4. Running the Application

Run the server with Uvicorn:
```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
You can view the interactive documentation at `http://127.0.0.1:8000/docs`.

### 5. Running Tests

Execute the test suite using pytest:
```bash
pytest
```
