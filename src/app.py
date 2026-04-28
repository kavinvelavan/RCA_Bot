from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
from src.rag_engine import query_rag
from src.services.document_service import DocumentService
from src.services.log_service import LogService
from src.services.training_service import TrainingService

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RCA Bot Service", description="3-Service Architecture for Root Cause Analysis")

# ✅ Add this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all (for local dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_service = DocumentService()
log_service = LogService()
training_service = TrainingService()

class QueryRequest(BaseModel):
    question: str

class DocumentExtractionRequest(BaseModel):
    service_name: str

class LogFetchRequest(BaseModel):
    service_name: str
    start_time: str = None
    end_time: str = None

class TrainingRequest(BaseModel):
    service_name: str
    document_data: Dict[str, Any]
    log_data: Dict[str, Any]

class CompleteFlowRequest(BaseModel):
    service_name: str
    start_time: str = None
    end_time: str = None

@app.post("/ask")
def ask_question(req: QueryRequest):
    """General RAG query endpoint"""
    return query_rag(req.question)

@app.post("/extract-document")
def extract_document_data(req: DocumentExtractionRequest):
    """Service 1: Extract dependencies and incidents from document"""
    
    # Query RAG for service information
    rag_result = query_rag(f"Tell me about {req.service_name} service dependencies and past incidents")
    
    # Extract structured information
    analysis = document_service.analyze_document(req.service_name, rag_result)
    
    return analysis

@app.post("/fetch-logs")
def fetch_error_logs(req: LogFetchRequest):
    """Service 2: Fetch logs and filter error logs"""
    
    # Get logs for the service
    log_data = log_service.get_logs_for_service(req.service_name, req.start_time, req.end_time)
    
    return log_data

@app.post("/train-analyze")
def train_and_analyze(req: TrainingRequest):
    """Service 3: Train model and generate RCA summary"""
    
    # Train model and generate RCA summary
    analysis = training_service.train_and_analyze(req.service_name, req.document_data, req.log_data)
    
    return analysis

@app.post("/complete-flow")
def complete_rca_flow(req: CompleteFlowRequest):
    """Complete flow: Document -> Logs -> Training -> Summary"""
    
    # Step 1: Extract document data
    rag_result = query_rag(f"Tell me about {req.service_name} service dependencies and past incidents")
    document_data = document_service.analyze_document(req.service_name, rag_result)
    
    # Step 2: Fetch logs
    log_data = log_service.get_logs_for_service(req.service_name, req.start_time, req.end_time)
    
    # Step 3: Train and analyze
    final_analysis = training_service.train_and_analyze(req.service_name, document_data, log_data)
    
    # Combine all results
    complete_result = {
        "service_name": req.service_name,
        "document_analysis": document_data,
        "log_analysis": log_data,
        "rca_summary": final_analysis,
        "flow_timestamp": final_analysis["analysis_timestamp"]
    }
    
    return complete_result

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "RCA Bot",
        "architecture": "3-Service Architecture",
        "services": [
            "Document Extraction Service",
            "Log Fetching Service", 
            "Training & Analysis Service"
        ]
    }

# Legacy endpoints for backward compatibility
@app.post("/analyze-service")
def analyze_service_legacy(req: DocumentExtractionRequest):
    """Legacy endpoint - redirects to new document extraction"""
    return extract_document_data(req)

@app.post("/analyze-logs")
def analyze_logs_legacy(req: LogFetchRequest):
    """Legacy endpoint - redirects to complete flow"""
    return complete_rca_flow(CompleteFlowRequest(
        service_name=req.service_name,
        start_time=req.start_time,
        end_time=req.end_time
    ))