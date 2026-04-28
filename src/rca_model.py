from typing import Dict, List, Any
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
import json
from datetime import datetime

class RCAModel:
    def __init__(self):
        self.llm = Ollama(model="phi3")
        
    def analyze_error_logs(self, error_logs: List[Dict[str, Any]], service_flow: Dict[str, Any], past_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error logs and generate RCA summary"""
        
        # Prepare context for analysis
        error_context = self._prepare_error_context(error_logs)
        service_context = self._prepare_service_context(service_flow)
        incident_context = self._prepare_incident_context(past_incidents)
        
        prompt = PromptTemplate(
            input_variables=["error_context", "service_context", "incident_context"],
            template="""
            Analyze the following error logs and provide a comprehensive Root Cause Analysis summary.
            
            ERROR LOGS:
            {error_context}
            
            SERVICE FLOW/DEPENDENCIES:
            {service_context}
            
            PAST INCIDENTS:
            {incident_context}
            
            Based on this information, provide a JSON response with:
            - error_start_time: When the error started
            - error_url: URL/endpoint where error occurred
            - status_code: HTTP status code
            - error_message: Primary error message
            - impacted_dependencies: List of affected services
            - root_cause: Likely root cause
            - recommended_actions: List of actions to take based on past incidents
            - severity: Critical/High/Medium/Low
            - estimated_impact: Business impact description
            
            Be specific and actionable in your analysis.
            """
        )
        
        formatted_prompt = prompt.format(
            error_context=error_context,
            service_context=service_context,
            incident_context=incident_context
        )
        
        try:
            response = self.llm.invoke(formatted_prompt)
            
            # Try to extract JSON from response
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = self._generate_fallback_analysis(error_logs, service_flow, past_incidents)
            
            # Add metadata
            analysis["analysis_timestamp"] = datetime.now().isoformat()
            analysis["total_logs_analyzed"] = len(error_logs)
            
            return analysis
            
        except Exception as e:
            print(f"Error in RCA analysis: {e}")
            return self._generate_fallback_analysis(error_logs, service_flow, past_incidents)
    
    def _prepare_error_context(self, error_logs: List[Dict[str, Any]]) -> str:
        """Prepare error logs context"""
        if not error_logs:
            return "No error logs provided."
        
        context = "Error Logs:\n"
        for i, log in enumerate(error_logs[:10], 1):  # Limit to 10 logs
            context += f"{i}. Service: {log.get('service', 'Unknown')}\n"
            context += f"   Timestamp: {log.get('timestamp', 'Unknown')}\n"
            context += f"   Status: {log.get('status_code', 'Unknown')}\n"
            context += f"   Error: {log.get('error', 'Unknown')}\n"
            context += f"   URL: {log.get('url', 'Unknown')}\n\n"
        
        return context
    
    def _prepare_service_context(self, service_flow: Dict[str, Any]) -> str:
        """Prepare service flow context"""
        context = "Service Dependencies:\n"
        
        deps = service_flow.get("dependencies", {})
        context += f"Upstream Services: {deps.get('upstream_services', [])}\n"
        context += f"Downstream Services: {deps.get('downstream_services', [])}\n"
        context += f"Related Services: {deps.get('related_services', [])}\n\n"
        
        return context
    
    def _prepare_incident_context(self, past_incidents: List[Dict[str, Any]]) -> str:
        """Prepare past incidents context"""
        if not past_incidents:
            return "No past incidents available."
        
        context = "Past Incidents:\n"
        for i, incident in enumerate(past_incidents[:5], 1):  # Limit to 5 incidents
            context += f"{i}. Incident ID: {incident.get('incident_id', 'Unknown')}\n"
            context += f"   Error Type: {incident.get('error_type', 'Unknown')}\n"
            context += f"   Root Cause: {incident.get('root_cause', 'Unknown')}\n"
            context += f"   Resolution: {incident.get('resolution', 'Unknown')}\n\n"
        
        return context
    
    def _generate_fallback_analysis(self, error_logs: List[Dict[str, Any]], service_flow: Dict[str, Any], past_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback analysis if LLM fails"""
        if not error_logs:
            return {
                "error_start_time": "Unknown",
                "error_url": "Unknown",
                "status_code": "Unknown",
                "error_message": "No error logs available",
                "impacted_dependencies": [],
                "root_cause": "Unable to determine - no error data",
                "recommended_actions": ["Check service logs", "Verify service health"],
                "severity": "Medium",
                "estimated_impact": "Unknown"
            }
        
        # Extract basic info from first error log
        first_log = error_logs[0]
        
        return {
            "error_start_time": first_log.get('timestamp', 'Unknown'),
            "error_url": first_log.get('url', 'Unknown'),
            "status_code": first_log.get('status_code', 'Unknown'),
            "error_message": first_log.get('error', 'Unknown'),
            "impacted_dependencies": service_flow.get("dependencies", {}).get("downstream_services", []),
            "root_cause": "Service failure detected - requires investigation",
            "recommended_actions": ["Restart affected service", "Check upstream dependencies", "Review recent deployments"],
            "severity": "High",
            "estimated_impact": "Service degradation detected"
        }
