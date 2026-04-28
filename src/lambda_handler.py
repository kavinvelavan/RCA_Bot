import json
import os
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.rag_engine import query_rag
from src.services.document_service import DocumentService
from src.services.log_service import LogService
from src.services.training_service import TrainingService

# Initialize AWS Lambda utilities
logger = Logger()
tracer = Tracer()

# Initialize services
document_service = DocumentService()
log_service = LogService()
training_service = TrainingService()

class ServiceEndpoints:
    """API endpoints for the 3-service architecture"""
    
    @staticmethod
    def extract_document_data(event: Dict[str, Any]) -> Dict[str, Any]:
        """Service 1: Extract dependencies and incidents from document"""
        
        try:
            body = json.loads(event.get("body", "{}"))
            service_name = body.get("service_name")
            
            if not service_name:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "service_name is required"})
                }
            
            # Query RAG for service information
            rag_result = query_rag(f"Tell me about {service_name} service dependencies and past incidents")
            
            # Extract structured information
            analysis = document_service.analyze_document(service_name, rag_result)
            
            return {
                "statusCode": 200,
                "body": json.dumps(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in document extraction: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
    
    @staticmethod
    def fetch_logs(event: Dict[str, Any]) -> Dict[str, Any]:
        """Service 2: Fetch logs and filter error logs"""
        
        try:
            body = json.loads(event.get("body", "{}"))
            service_name = body.get("service_name")
            start_time = body.get("start_time")
            end_time = body.get("end_time")
            
            if not service_name:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "service_name is required"})
                }
            
            # Get logs for the service
            log_data = log_service.get_logs_for_service(service_name, start_time, end_time)
            
            return {
                "statusCode": 200,
                "body": json.dumps(log_data)
            }
            
        except Exception as e:
            logger.error(f"Error in log fetching: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
    
    @staticmethod
    def train_and_analyze(event: Dict[str, Any]) -> Dict[str, Any]:
        """Service 3: Train model and generate RCA summary"""
        
        try:
            body = json.loads(event.get("body", "{}"))
            service_name = body.get("service_name")
            document_data = body.get("document_data")
            log_data = body.get("log_data")
            
            if not all([service_name, document_data, log_data]):
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "service_name, document_data, and log_data are required"})
                }
            
            # Train model and generate RCA summary
            analysis = training_service.train_and_analyze(service_name, document_data, log_data)
            
            return {
                "statusCode": 200,
                "body": json.dumps(analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in training and analysis: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }
    
    @staticmethod
    def complete_flow(event: Dict[str, Any]) -> Dict[str, Any]:
        """Complete flow: Document -> Logs -> Training -> Summary"""
        
        try:
            body = json.loads(event.get("body", "{}"))
            service_name = body.get("service_name")
            start_time = body.get("start_time")
            end_time = body.get("end_time")
            
            if not service_name:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "service_name is required"})
                }
            
            # Step 1: Extract document data
            rag_result = query_rag(f"Tell me about {service_name} service dependencies and past incidents")
            document_data = document_service.analyze_document(service_name, rag_result)
            
            # Step 2: Fetch logs
            log_data = log_service.get_logs_for_service(service_name, start_time, end_time)
            
            # Step 3: Train and analyze
            final_analysis = training_service.train_and_analyze(service_name, document_data, log_data)
            
            # Combine all results
            complete_result = {
                "service_name": service_name,
                "document_analysis": document_data,
                "log_analysis": log_data,
                "rca_summary": final_analysis,
                "flow_timestamp": final_analysis["analysis_timestamp"]
            }
            
            return {
                "statusCode": 200,
                "body": json.dumps(complete_result)
            }
            
        except Exception as e:
            logger.error(f"Error in complete flow: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Main Lambda handler for routing requests"""
    
    # Extract path from the event
    path = event.get("path", "")
    http_method = event.get("httpMethod", "GET")
    
    logger.info(f"Request: {http_method} {path}")
    
    # Route to appropriate service
    if path == "/extract-document" and http_method == "POST":
        return ServiceEndpoints.extract_document_data(event)
    elif path == "/fetch-logs" and http_method == "POST":
        return ServiceEndpoints.fetch_logs(event)
    elif path == "/train-analyze" and http_method == "POST":
        return ServiceEndpoints.train_and_analyze(event)
    elif path == "/complete-flow" and http_method == "POST":
        return ServiceEndpoints.complete_flow(event)
    elif path == "/health" and http_method == "GET":
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "healthy",
                "service": "RCA Bot Lambda",
                "version": "1.0.0"
            })
        }
    else:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Endpoint not found",
                "available_endpoints": [
                    "POST /extract-document",
                    "POST /fetch-logs", 
                    "POST /train-analyze",
                    "POST /complete-flow",
                    "GET /health"
                ]
            })
        }

# For local testing
def local_test():
    """Test function for local development"""
    
    test_event = {
        "path": "/complete-flow",
        "httpMethod": "POST",
        "body": json.dumps({
            "service_name": "payment-service",
            "start_time": "2026-04-28T21:30:00Z",
            "end_time": "2026-04-28T21:50:00Z"
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(json.loads(result["body"]), indent=2))

if __name__ == "__main__":
    local_test()
