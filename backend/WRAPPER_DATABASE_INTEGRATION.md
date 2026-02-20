# Wrapper & Database Integration Guide

## Overview
The `wrapper.py` and `database.py` modules have been successfully integrated into the FastAPI backend to provide:
1. **Wrapper Functions** - Gemini and LLaMA API calls for semantic analysis
2. **Database Storage** - SQLite-based storage for analysis history and search

## What Was Added

### 1. Imports (Lines 11-17)
```python
# Wrapper and Database
try:
    from wrapper import gemini_analyze_code, llama_extract_json, extract_json
    from env11.database import init_db, save_analysis, get_analysis_by_id, search_by_keyword
    WRAPPER_DB_AVAILABLE = True
except Exception as e:
    WRAPPER_DB_AVAILABLE = False
```

### 2. Database Initialization (Lines 56-63)
Added startup event to initialize SQLite database on application start:
```python
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    if WRAPPER_DB_AVAILABLE:
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
```

### 3. Analysis Auto-Save (Lines 271-285)
Every analysis result is automatically saved to the database:
```python
# Save analysis to database (if available)
if WRAPPER_DB_AVAILABLE:
    try:
        analysis_kind = request.analysis_type if request.analysis_type != "all" else "comprehensive"
        save_analysis(
            language=request.file_type,
            kind=analysis_kind,
            code=request.code,
            result=json.dumps(result_data),
            summary=f"Analysis of {request.file_type} code with {analysis_kind} mode"
        )
        logger.info("Analysis saved to database")
    except Exception as e:
        logger.warning(f"Failed to save analysis to database: {str(e)}")
```

### 4. New Endpoints

#### `GET /api/analysis/{analysis_id}` (Lines 531-547)
Retrieve a previous analysis by ID:
```bash
curl http://localhost:8000/api/analysis/1
```
Response:
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "language": "python",
    "kind": "comprehensive",
    "code": "def hello(): pass",
    "result": { /* full analysis result */ },
    "summary": "Analysis of python code with comprehensive mode",
    "created_at": "2025-11-17 10:30:45"
  }
}
```

#### `GET /api/search` (Lines 550-570)
Search analysis history by keyword:
```bash
curl "http://localhost:8000/api/search?keyword=function"
```
Response:
```json
{
  "status": "success",
  "count": 5,
  "data": [
    { /* matching analysis records */ }
  ]
}
```

## Database Schema

SQLite table `analysis_results`:
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| language | TEXT | Programming language (e.g., "python", "javascript") |
| kind | TEXT | Analysis type ("parser", "semantic", "comprehensive") |
| code | TEXT | Source code analyzed |
| result | TEXT | Raw JSON result from analysis |
| summary | TEXT | Human-readable summary |
| created_at | TIMESTAMP | Creation timestamp |

Database file: `analysis.db` (created automatically on startup)

## Usage Examples

### 1. Automatic Analysis Saving
Every call to `/api/analyze` automatically saves to database:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a, b): return a + b",
    "file_type": "python",
    "analysis_type": "all"
  }'
```

### 2. Retrieve Analysis by ID
```bash
curl http://localhost:8000/api/analysis/1
```

### 3. Search Analysis History
```bash
curl "http://localhost:8000/api/search?keyword=function"
curl "http://localhost:8000/api/search?keyword=error"
curl "http://localhost:8000/api/search?keyword=class"
```

## Wrapper Functions Available

The `wrapper.py` module provides:

### `gemini_analyze_code(language: str, code: str) -> dict`
Analyze code using Google Gemini API
```python
result = gemini_analyze_code("python", "def hello(): pass")
```

### `llama_extract_json(prompt: str) -> dict`
Extract JSON from LLaMA API response
```python
result = llama_extract_json("Analyze this code: def hello(): pass")
```

### `extract_json(text: str) -> Optional[dict]`
Extract JSON from any text string
```python
json_obj = extract_json("Some text with JSON {\"key\": \"value\"}")
```

## Configuration

Ensure `.env` has the required API keys:
```
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
```

## Error Handling

- If wrapper/database modules fail to import, `WRAPPER_DB_AVAILABLE` is set to False
- Analysis continues normally without database saving if imports fail
- New endpoints return 503 status if database is unavailable
- All database operations have try-catch error handling

## Running the Backend

```bash
# Activate virtual environment
D:\auto ai project\env11\Scripts\Activate.ps1

# Run backend (database initializes automatically)
python backend.py
```

The backend runs on `http://localhost:8000` with auto-reload enabled.

## API Documentation

Full API documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

The new History endpoints are tagged as `["History"]` for easy filtering in the docs.
