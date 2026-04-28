from typing import Dict, List, Any
from datetime import datetime, timedelta
import json

class LogService:
    """Service 2: Fetch logs from monitoring tool and filter error logs"""
    
    def __init__(self):
        # Initialize with dummy log data
        self.dummy_logs = self._generate_dummy_logs()
    
    def _generate_dummy_logs(self) -> List[Dict[str, Any]]:
        """Generate comprehensive dummy log data for testing"""
        
        base_time = datetime.now() - timedelta(hours=2)
        services = ["payment-service", "user-service", "order-service", "auth-service", 
                   "inventory-service", "notification-service", "shipping-service", "transaction-service"]
        
        logs = []
        
        # Generate error logs
        for i, service in enumerate(services):
            for j in range(5):  # 5 error logs per service
                timestamp = base_time + timedelta(minutes=i*10 + j*2)
                
                error_types = [
                    "Database connection timeout",
                    "Service unavailable", 
                    "Authentication failed",
                    "Invalid request data",
                    "External API failure",
                    "Memory allocation error",
                    "Network timeout",
                    "Resource exhaustion"
                ]
                
                status_codes = [500, 503, 502, 504, 400, 401, 404, 409]
                
                log_entry = {
                    "log_id": f"LOG-{service.upper()}-{j+1:03d}",
                    "service": service,
                    "timestamp": timestamp.isoformat() + "Z",
                    "status_code": status_codes[j % len(status_codes)],
                    "error": error_types[j % len(error_types)],
                    "url": f"/api/{service.replace('-', '/')}/endpoint{j+1}",
                    "level": "ERROR",
                    "message": f"{service} encountered {error_types[j % len(error_types)]} at {timestamp.isoformat()}",
                    "duration_ms": (j + 1) * 100,
                    "request_id": f"REQ-{i:04d}-{j:03d}",
                    "user_id": f"USER-{(i*5 + j) % 1000:05d}",
                    "ip_address": f"192.168.{i%255}.{(j*10)%255}",
                    "user_agent": "Mozilla/5.0 (compatible; RCA-Bot/1.0)"
                }
                logs.append(log_entry)
            
            # Add some success logs for context
            for j in range(3):
                timestamp = base_time + timedelta(minutes=i*10 + j*2 + 1)
                log_entry = {
                    "log_id": f"LOG-{service.upper()}-SUCCESS-{j+1:03d}",
                    "service": service,
                    "timestamp": timestamp.isoformat() + "Z",
                    "status_code": 200,
                    "error": None,
                    "url": f"/api/{service.replace('-', '/')}/health",
                    "level": "INFO",
                    "message": f"{service} health check successful",
                    "duration_ms": 50,
                    "request_id": f"REQ-{i:04d}-HEALTH-{j:03d}",
                    "user_id": None,
                    "ip_address": "127.0.0.1",
                    "user_agent": "HealthChecker/1.0"
                }
                logs.append(log_entry)
        
        return logs
    
    def fetch_logs(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch logs based on filters (simulating monitoring tool API)"""
        
        service_name = filters.get("service_name")
        start_time = filters.get("start_time")
        end_time = filters.get("end_time")
        status_codes = filters.get("status_codes", [])
        log_level = filters.get("log_level", "ERROR")
        
        filtered_logs = []
        
        for log in self.dummy_logs:
            # Filter by service name
            if service_name and log["service"] != service_name:
                continue
            
            # Filter by time range
            if start_time and log["timestamp"] < start_time:
                continue
            
            if end_time and log["timestamp"] > end_time:
                continue
            
            # Filter by status codes
            if status_codes and log["status_code"] not in status_codes:
                continue
            
            # Filter by log level
            if log["level"] != log_level:
                continue
            
            filtered_logs.append(log)
        
        return filtered_logs
    
    def filter_error_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out only error logs from the fetched logs"""
        
        error_logs = []
        
        for log in logs:
            # Consider only error status codes
            if log["status_code"] >= 400:
                error_logs.append(log)
        
        return error_logs
    
    def get_logs_for_service(self, service_name: str, start_time: str = None, end_time: str = None) -> Dict[str, Any]:
        """Main method to get logs for a specific service"""
        
        filters = {
            "service_name": service_name,
            "start_time": start_time,
            "end_time": end_time,
            "log_level": "ERROR"
        }
        
        # Fetch all logs matching filters
        all_logs = self.fetch_logs(filters)
        
        # Filter only error logs
        error_logs = self.filter_error_logs(all_logs)
        
        # Get logs for related services (upstream/downstream)
        related_service_logs = self._get_related_service_logs(service_name, start_time, end_time)
        
        return {
            "service_name": service_name,
            "primary_service_logs": error_logs,
            "related_service_logs": related_service_logs,
            "total_error_logs": len(error_logs),
            "total_related_logs": len(related_service_logs),
            "fetch_timestamp": datetime.now().isoformat() + "Z"
        }
    
    def _get_related_service_logs(self, service_name: str, start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
        """Get error logs for related services (simplified for demo)"""
        
        # For demo, assume all other services are potentially related
        related_logs = []
        
        for log in self.dummy_logs:
            if log["service"] != service_name and log["status_code"] >= 400:
                # Apply time filters if provided
                if start_time and log["timestamp"] < start_time:
                    continue
                if end_time and log["timestamp"] > end_time:
                    continue
                
                related_logs.append(log)
        
        return related_logs[:20]  # Limit to 20 related logs for demo
    
    def get_recent_errors(self, service_name: str, minutes_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent error logs for ongoing error detection"""
        
        cutoff_time = (datetime.now() - timedelta(minutes=minutes_back)).isoformat() + "Z"
        
        recent_errors = []
        for log in self.dummy_logs:
            if (log["service"] == service_name and 
                log["timestamp"] >= cutoff_time and 
                log["status_code"] >= 400):
                recent_errors.append(log)
        
        return recent_errors
