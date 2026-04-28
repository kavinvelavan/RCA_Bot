from typing import Dict, List, Any
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
import json

class KnowledgeBot:
    def __init__(self):
        self.llm = Ollama(model="phi3")
        
    def extract_service_dependencies(self, service_name: str, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract upstream and downstream services for a given service"""
        
        prompt = PromptTemplate(
            input_variables=["service_name", "context"],
            template="""
            Based on the following context about service workflows, extract the service dependencies for {service_name}.
            
            Context: {context}
            
            Return a JSON object with:
            - upstream_services: List of services that call this service
            - downstream_services: List of services that this service calls
            - related_services: List of services that are related but not directly connected
            
            Focus only on services mentioned in the context. If no dependencies found, return empty lists.
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
                dependencies = {
                    "upstream_services": [],
                    "downstream_services": [],
                    "related_services": []
                }
            
            return dependencies
            
        except Exception as e:
            print(f"Error extracting dependencies: {e}")
            return {
                "upstream_services": [],
                "downstream_services": [],
                "related_services": []
            }
    
    def extract_past_incidents(self, service_name: str, rag_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract past incidents related to the service"""
        
        prompt = PromptTemplate(
            input_variables=["service_name", "context"],
            template="""
            Based on the following context about service workflows and incidents, extract past incidents related to {service_name}.
            
            Context: {context}
            
            Return a JSON list of incident objects with:
            - incident_id: Unique identifier
            - service_name: Service affected
            - error_type: Type of error
            - root_cause: Root cause analysis
            - resolution: How it was resolved
            - timestamp: When it occurred (if available)
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
                return []
            
        except Exception as e:
            print(f"Error extracting incidents: {e}")
            return []
    
    def analyze_service_flow(self, service_name: str, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to analyze service flow and incidents"""
        
        dependencies = self.extract_service_dependencies(service_name, rag_result)
        incidents = self.extract_past_incidents(service_name, rag_result)
        
        return {
            "service_name": service_name,
            "dependencies": dependencies,
            "past_incidents": incidents,
            "analysis_timestamp": "2026-04-28T21:19:00Z"
        }
