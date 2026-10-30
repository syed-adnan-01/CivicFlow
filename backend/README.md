# QueueLess 2.3 Backend

FastAPI backend providing citizen appointment lifecycle, persisted slot capacity, and QR reference management.

## 1. Quick Start

### Step 1: Navigate to backend folder
```powershell
cd backend
```

### Step 2: Activate the Virtual Environment
- **PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Command Prompt (CMD)**:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- **Git Bash / Bash**:
  ```bash
  source .venv/Scripts/activate
  ```

### Step 3: Run Database Migrations (PostgreSQL)
Ensure your PostgreSQL database is running and `DATABASE_URL` in `.env` is configured:
```powershell
alembic upgrade head
```

### Step 4: Seed Demo Data
```powershell
python scripts/seed_demo_data.py
```

### Step 5: Start the Development Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Or directly without activating:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 2. Interactive Documentation & Endpoints

Once the server is running, open in your browser:
- **Swagger Interactive API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 3. Running Tests

Run the full automated test suite:
```powershell
pytest
```
Or with verbose output:
```powershell
.\.venv\Scripts\pytest.exe -v
```
