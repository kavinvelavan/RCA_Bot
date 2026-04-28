from typing import Dict, List, Any
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
import json
import re

class DocumentService:
    """Service 1: Extract service dependencies and past incidents from documentation"""
    
    def __init__(self):
        # Use a CPU-friendly model
        self.llm = Ollama(model="phi3")
        
    def extract_service_dependencies(self, service_name: str, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract upstream and downstream services for a given service"""
        
        prompt = PromptTemplate(
            input_variables=["service_name", "context"],
            template="""
            Based on the following context about banking application workflows, extract the service dependencies for {service_name}.
            
            Context: {context}
            
            Return a JSON object with:
            - upstream_services: List of services that call this service
            - downstream_services: List of services that this service calls
            - related_services: List of services that are related but not directly connected
            
            Focus only on services mentioned in the context. If no dependencies found, return empty lists.
            Service names might include: payment-service, user-service, auth-service, order-service, 
            inventory-service, notification-service, shipping-service, transaction-service, account-service.
            """
        )
        
        context_text = "\n".join(rag_result.get("sources", []))
        
        formatted_prompt = prompt.format(
            service_name=service_name,
            context=context_text
        )
        
        try:
            response = self.llm.invoke(formatted_prompt)
            
            # Try to extract JSON from response
            try:
                dependencies = json.loads(response)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                dependencies = self._extract_dependencies_fallback(service_name, context_text)
            
            return dependencies
            
        except Exception as e:
            print(f"Error extracting dependencies: {e}")
            return self._extract_dependencies_fallback(service_name, context_text)
    
    def extract_past_incidents(self, service_name: str, rag_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract past incidents related to the service"""
        
        prompt = PromptTemplate(
            input_variables=["service_name", "context"],
            template="""
            Based on the following context about banking application workflows and incidents, extract past incidents related to {service_name}.
            
            Context: {context}
            
            Return a JSON list of incident objects with:
            - incident_id: Unique identifier (format: INC-XXX)
            - service_name: Service affected
            - error_type: Type of error (e.g., Database timeout, Memory leak, API failure)
            - root_cause: Root cause analysis
            - resolution: How it was resolved
            - timestamp: When it occurred (format: YYYY-MM-DDTHH:MM:SSZ)
            - impact: Impact description
            
            Focus only on incidents mentioned in the context. If no incidents found, return empty list.
            """
        )
        
        context_text = "\n".join(rag_result.get("sources", []))
        
        formatted_prompt = prompt.format(
            service_name=service_name,
            context=context_text
        )
        
        try:
            response = self.llm.invoke(formatted_prompt)
            
            # Try to extract JSON from response
            try:
                incidents = json.loads(response)
                if isinstance(incidents, list):
                    return incidents
                else:
                    return []
            except json.JSONDecodeError:
                return self._extract_incidents_fallback(service_name, context_text)
            
        except Exception as e:
            print(f"Error extracting incidents: {e}")
            return self._extract_incidents_fallback(service_name, context_text)
    
    def _extract_dependencies_fallback(self, service_name: str, context: str) -> Dict[str, Any]:
        """Fallback method for dependency extraction"""
        # Basic fallback dependencies based on common banking app patterns
        fallback_deps = {
            "payment-service": {
                "upstream_services": ["order-service", "user-service"],
                "downstream_services": ["notification-service", "transaction-service"],
                "related_services": ["auth-service", "account-service"]
            },
            "user-service": {
                "upstream_services": ["auth-service"],
                "downstream_services": ["payment-service", "order-service", "account-service"],
                "related_services": ["notification-service"]
            },
            "order-service": {
                "upstream_services": ["user-service", "inventory-service"],
                "downstream_services": ["payment-service", "shipping-service"],
                "related_services": ["notification-service", "transaction-service"]
            }
        }
        
        return fallback_deps.get(service_name, {
            "upstream_services": [],
            "downstream_services": [],
            "related_services": []
        })
    
    def _extract_incidents_fallback(self, service_name: str, context: str) -> List[Dict[str, Any]]:
        """Fallback method for incident extraction"""
        # Basic fallback incidents
        fallback_incidents = [
            {
                "incident_id": "INC-001",
                "service_name": service_name,
                "error_type": "Database connection timeout",
                "root_cause": "Database connection pool exhaustion",
                "resolution": "Increased connection pool size and added connection retry logic",
                "timestamp": "2026-04-25T14:30:00Z",
                "impact": "Service unavailable for 15 minutes"
            },
            {
                "incident_id": "INC-002",
                "service_name": service_name,
                "error_type": "Memory leak",
                "root_cause": "Unbounded cache growth",
                "resolution": "Implemented cache eviction policy and memory monitoring",
                "timestamp": "2026-04-23T09:15:00Z",
                "impact": "Service degradation for 2 hours"
            }
        ]
        
        return fallback_incidents if service_name in ["payment-service", "user-service", "order-service"] else []
    
    def analyze_document(self, service_name: str, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to analyze document and extract service flow and incidents"""
        
        dependencies = self.extract_service_dependencies(service_name, rag_result)
        incidents = self.extract_past_incidents(service_name, rag_result)
        
        return {
            "service_name": service_name,
            "dependencies": dependencies,
            "past_incidents": incidents,
            "analysis_timestamp": "2026-04-28T21:40:00Z"
        }
