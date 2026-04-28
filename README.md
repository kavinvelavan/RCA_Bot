# RCA Bot Service - 3-Service Architecture

A comprehensive Root Cause Analysis (RCA) service that integrates with an Orchestrator using a 3-service architecture to analyze service dependencies and error logs using AI models.

## Architecture Overview

The RCA Bot service consists of three main components:

1. **Document Extraction Service** - Extracts service dependencies and past incidents from documentation
2. **Log Fetching Service** - Fetches logs from monitoring tools and filters error logs
3. **Training & Analysis Service** - Trains model with combined data and generates RCA summaries

## Integration Flow

```
Orchestrator → Document Service → Log Service → Training Service → Dashboard
     ↓               ↓              ↓                ↓                    ↓
Service Info → Dependencies/Incidents → Error Logs → RCA Summary → Dashboard
```

---

## Setup

### Prerequisites
- Python 3.10+
- Ollama installed and running with `phi3` model (CPU-friendly)
- FAISS vector index created (run `src/ingest.py` first)

### Local Development Installation

```bash
pip install -r src/requirements.txt
```

### Start Ollama
```bash
# Option 1: In the same terminal (recommended for development)
ollama pull phi3
ollama serve

# Option 2: In a new terminal (recommended for production)
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Run other commands
ollama pull phi3  # if not already downloaded

# Verify Ollama is running (optional)
curl http://localhost:11434/api/tags
```

### Create Vector Index
```bash
# First, ensure document exists in data folder
ls src/data/

# Create FAISS vector index from the text document
cd src
python ingest.py

# You should see: "✅ FAISS index created successfully!"
```

### Start Ollama (if not already running)
```bash
# Pull the model if not already downloaded
ollama pull phi3

# Start the Ollama server
ollama serve

# Verify Ollama is running (optional)
curl http://localhost:11434/api/tags
```

### Start the Service (Local Development)
```bash
# Navigate to the src directory
cd src

# Start the FastAPI server with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# The service will be available at http://localhost:8000
# API documentation will be at http://localhost:8000/docs
```

### Test the Service
```bash
# Test health check
curl http://localhost:8000/health

# Test document extraction service
curl -X POST "http://localhost:8000/extract-document" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "payment-service"}'

# Test log fetching service
curl -X POST "http://localhost:8000/fetch-logs" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "payment-service", "start_time": "2026-04-28T21:15:00Z", "end_time": "2026-04-28T21:20:00Z"}'

# Test complete flow (all services together)
curl -X POST "http://localhost:8000/complete-flow" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "payment-service", "start_time": "2026-04-28T21:15:00Z", "end_time": "2026-04-28T21:20:00Z"}'
```

---

## AWS Lambda Deployment

### Build Lambda Layer
```bash
python build_layer.py
```

### Deploy with SAM
```bash
sam deploy --guided
```

### Lambda Configuration
- **Memory**: 1024 MB (for CPU operations)
- **Timeout**: 300 seconds (5 minutes)
- **Runtime**: Python 3.10
- **Architecture**: x86_64

---

## API Endpoints

### 1. Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "RCA Bot",
  "architecture": "3-Service Architecture",
  "services": [
    "Document Extraction Service",
    "Log Fetching Service",
    "Training & Analysis Service"
  ]
}
```

### 2. Service 1 - Document Extraction
```http
POST /extract-document
```

Request Body:
```json
{
  "service_name": "payment-service"
}
```

Response:
```json
{
  "service_name": "payment-service",
  "dependencies": {
    "upstream_services": ["order-service", "user-service"],
    "downstream_services": ["notification-service", "transaction-service"],
    "related_services": ["auth-service", "account-service"]
  },
  "past_incidents": [
    {
      "incident_id": "INC-001",
      "service_name": "payment-service",
      "error_type": "Database connection timeout",
      "root_cause": "Database connection pool exhaustion",
      "resolution": "Increased connection pool size and added connection retry logic",
      "timestamp": "2026-04-25T14:30:00Z",
      "impact": "Service unavailable for 15 minutes"
    }
  ],
  "analysis_timestamp": "2026-04-28T21:40:00Z"
}
```

### 3. Service 2 - Log Fetching
```http
POST /fetch-logs
```

Request Body:
```json
{
  "service_name": "payment-service",
  "start_time": "2026-04-28T21:15:00Z",
  "end_time": "2026-04-28T21:20:00Z"
}
```

Response:
```json
{
  "service_name": "payment-service",
  "primary_service_logs": [
    {
      "log_id": "LOG-PAYMENT-SERVICE-001",
      "service": "payment-service",
      "timestamp": "2026-04-28T21:15:00Z",
      "status_code": 500,
      "error": "Database connection timeout",
      "url": "/api/payments/endpoint1",
      "level": "ERROR",
      "message": "payment-service encountered Database connection timeout",
      "duration_ms": 100,
      "request_id": "REQ-0000-000"
    }
  ],
  "related_service_logs": [...],
  "total_error_logs": 5,
  "total_related_logs": 20,
  "fetch_timestamp": "2026-04-28T21:40:00Z"
}
```

### 4. Service 3 - Training & Analysis
```http
POST /train-analyze
```

Request Body:
```json
{
  "service_name": "payment-service",
  "document_data": {...},
  "log_data": {...}
}
```

Response:
```json
{
  "service_name": "payment-service",
  "rca_summary": {
    "error_start_time": "2026-04-28T21:15:00Z",
    "error_code": 500,
    "impacted_dependencies": ["notification-service", "transaction-service"],
    "endpoints": ["/api/payments/endpoint1"],
    "cause_of_error": "Database connection pool exhaustion similar to past incident INC-001",
    "action_taken": [
      "Increase database connection pool size",
      "Implement connection retry logic",
      "Check database server health"
    ],
    "severity": "High",
    "error_pattern": "Intermittent service failures detected",
    "business_impact": "Service degradation affecting user experience"
  },
  "ongoing_errors": [
    {
      "service": "payment-service",
      "timestamp": "2026-04-28T21:38:00Z",
      "error": "Database connection timeout",
      "status_code": 500,
      "url": "/api/payments/endpoint1",
      "severity": "High"
    }
  ],
  "analysis_timestamp": "2026-04-28T21:40:00Z"
}
```

### 5. Complete Flow (All Services)
```http
POST /complete-flow
```

Request Body:
```json
{
  "service_name": "payment-service",
  "start_time": "2026-04-28T21:15:00Z",
  "end_time": "2026-04-28T21:20:00Z"
}
```

Response: Combined results from all three services

---

## Project Structure

```
RCA_Bot/
├── src/
│   ├── app.py                    ← FastAPI application with endpoints
│   ├── lambda_handler.py         ← AWS Lambda handler
│   ├── rag_engine.py             ← RAG engine for document queries
│   ├── services/
│   │   ├── document_service.py   ← Service 1: Document extraction
│   │   ├── log_service.py        ← Service 2: Log fetching
│   │   └── training_service.py   ← Service 3: Training & analysis
│   ├── ingest.py                 ← Create FAISS vector index
│   └── requirements.txt          ← Python dependencies
├── src/data/
│   └── Banking_App_Workflow_Documentation.docx
├── faiss_index/                  ← FAISS vector store
├── template.yaml                 ← AWS SAM template
├── build_layer.py               ← Lambda layer build script
└── README.md
```

---

## Service Components

### Service 1: Document Extraction (`document_service.py`)
- Extracts upstream/downstream service dependencies from documentation
- Identifies related services from banking app workflow
- Retrieves past incidents and resolutions
- Uses RAG + LLM for structured extraction
- CPU-friendly with fallback methods

### Service 2: Log Fetching (`log_service.py`)
- Simulates monitoring tool API calls with dummy JSON data
- Filters error logs based on status codes (>= 400)
- Supports time-based filtering
- Fetches logs from related services
- Generates comprehensive log datasets

### Service 3: Training & Analysis (`training_service.py`)
- Combines document data and error logs for training
- Generates comprehensive RCA summaries
- Detects ongoing errors based on recent timestamps
- Provides actionable recommendations based on past incidents
- Estimates business impact and severity

---

## Integration with Orchestrator

### Step-by-Step Flow:

1. **Initial Call**: Orchestrator calls `/complete-flow` with service name and time window
2. **Document Analysis**: Service 1 extracts dependencies and past incidents from `Banking_App_Workflow_Documentation.docx`
3. **Log Collection**: Service 2 fetches and filters error logs from dummy JSON data
4. **Model Training**: Service 3 trains model with combined data and generates RCA summary
5. **Dashboard Update**: Orchestrator receives comprehensive analysis and updates dashboard

### Alternative Individual Service Calls:
- Call `/extract-document` for dependencies only
- Call `/fetch-logs` for error logs only  
- Call `/train-analyze` for RCA analysis with pre-collected data

---

## Configuration

### Environment Variables
- `OLLAMA_MODEL`: Model name (default: "phi3")
- `FAISS_INDEX_PATH`: Path to FAISS index (default: "faiss_index")

### CPU-Friendly Model Configuration
- Uses `phi3` model for optimal CPU performance
- Implements fallback methods for reliability
- Optimized prompts for faster inference
- Memory-efficient processing

---

## Dependencies

### Core Dependencies
- **FastAPI**: Web framework for local development
- **LangChain**: LLM orchestration and prompts
- **FAISS**: Vector similarity search
- **Ollama**: Local LLM inference (CPU-friendly)
- **Sentence Transformers**: Text embeddings

### AWS Lambda Dependencies
- **boto3**: AWS SDK
- **aws-lambda-powertools**: Lambda utilities
- **requests**: HTTP client for external APIs

---

## Development

### Local Testing
```bash
# Test individual services
curl -X POST "http://localhost:8000/extract-document" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "payment-service"}'

# Test complete flow
curl -X POST "http://localhost:8000/complete-flow" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "payment-service", "start_time": "2026-04-28T21:15:00Z", "end_time": "2026-04-28T21:20:00Z"}'
```

### Adding New Services
1. Update documentation in `src/data/`
2. Re-run `ingest.py` to update vector index
3. Add dummy log data in `log_service.py` if needed

### Extending Services
1. Modify prompts in respective service files
2. Add new analysis methods
3. Update response schemas in `app.py`

---

## Production Deployment

### AWS Lambda Deployment
1. Build Lambda layer: `python build_layer.py`
2. Deploy with SAM: `sam deploy --guided`
3. Configure API Gateway endpoints
4. Set up monitoring and CloudWatch alerts

### Monitoring Integration
- Replace dummy log data with real monitoring tool API calls
- Configure proper authentication for external services
- Set up real-time log streaming
- Implement alerting for ongoing errors

### Scaling Considerations
- Increase Lambda memory for larger datasets
- Implement async processing for long-running analyses
- Add caching for frequently accessed document data
- Consider batch processing for multiple services
