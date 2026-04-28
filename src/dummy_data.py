from typing import List, Dict, Any
import random
from datetime import datetime, timedelta

# Dummy error log data for testing
DUMMY_ERROR_LOGS = [
    {
        "service": "payment-service",
        "timestamp": "2026-04-28T21:15:00Z",
        "status_code": 500,
        "error": "Database connection timeout",
        "url": "/api/payments/process",
        "level": "ERROR",
        "message": "Failed to connect to payment database after 30 seconds"
    },
    {
        "service": "payment-service",
        "timestamp": "2026-04-28T21:15:30Z",
        "status_code": 503,
        "error": "Service unavailable",
        "url": "/api/payments/validate",
        "level": "ERROR",
        "message": "Payment validation service temporarily unavailable"
    },
    {
        "service": "user-service",
        "timestamp": "2026-04-28T21:16:00Z",
        "status_code": 404,
        "error": "User not found",
        "url": "/api/users/12345",
        "level": "ERROR",
        "message": "User ID 12345 not found in database"
    },
    {
        "service": "order-service",
        "timestamp": "2026-04-28T21:16:30Z",
        "status_code": 400,
        "error": "Invalid order data",
        "url": "/api/orders/create",
        "level": "ERROR",
        "message": "Order validation failed: missing required fields"
    },
    {
        "service": "notification-service",
        "timestamp": "2026-04-28T21:17:00Z",
        "status_code": 502,
        "error": "Gateway timeout",
        "url": "/api/notifications/send",
        "level": "ERROR",
        "message": "External email service timeout"
    },
    {
        "service": "auth-service",
        "timestamp": "2026-04-28T21:17:30Z",
        "status_code": 401,
        "error": "Authentication failed",
        "url": "/api/auth/validate",
        "level": "ERROR",
        "message": "Invalid token provided"
    },
    {
        "service": "inventory-service",
        "timestamp": "2026-04-28T21:18:00Z",
        "status_code": 409,
        "error": "Conflict",
        "url": "/api/inventory/update",
        "level": "ERROR",
        "message": "Inventory update conflict: concurrent modification"
    },
    {
        "service": "shipping-service",
        "timestamp": "2026-04-28T21:18:30Z",
        "status_code": 500,
        "error": "External API failure",
        "url": "/api/shipping/calculate",
        "level": "ERROR",
        "message": "Third-party shipping API returned error"
    }
]

# Dummy service dependency data
DUMMY_SERVICE_DEPENDENCIES = {
    "payment-service": {
        "upstream_services": ["order-service", "user-service"],
        "downstream_services": ["notification-service", "inventory-service"],
        "related_services": ["auth-service"]
    },
    "user-service": {
        "upstream_services": ["auth-service"],
        "downstream_services": ["payment-service", "order-service"],
        "related_services": ["notification-service"]
    },
    "order-service": {
        "upstream_services": ["user-service", "inventory-service"],
        "downstream_services": ["payment-service", "shipping-service"],
        "related_services": ["notification-service"]
    }
}

# Dummy past incidents
DUMMY_PAST_INCIDENTS = [
    {
        "incident_id": "INC-001",
        "service_name": "payment-service",
        "error_type": "Database connection timeout",
        "root_cause": "Database connection pool exhaustion",
        "resolution": "Increased connection pool size and added connection retry logic",
        "timestamp": "2026-04-25T14:30:00Z",
        "impact": "Payment processing unavailable for 15 minutes"
    },
    {
        "incident_id": "INC-002", 
        "service_name": "user-service",
        "error_type": "Memory leak",
        "root_cause": "Unbounded cache growth",
        "resolution": "Implemented cache eviction policy and memory monitoring",
        "timestamp": "2026-04-23T09:15:00Z",
        "impact": "User authentication delays for 2 hours"
    },
    {
        "incident_id": "INC-003",
        "service_name": "order-service",
        "error_type": "Third-party API failure",
        "root_cause": "Rate limiting on inventory service",
        "resolution": "Implemented circuit breaker and retry with exponential backoff",
        "timestamp": "2026-04-20T16:45:00Z",
        "impact": "Order creation failures for 45 minutes"
    }
]

def get_error_logs_for_service(service_name: str, start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
    """Get error logs for a specific service"""
    logs = [log for log in DUMMY_ERROR_LOGS if log["service"] == service_name]
    
    # Filter by time if provided (simplified for demo)
    if start_time or end_time:
        return logs  # In real implementation, would filter by timestamp
    
    return logs

def get_related_service_logs(service_name: str, dependencies: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Get logs for related services (upstream and downstream)"""
    related_services = set()
    related_services.update(dependencies.get("upstream_services", []))
    related_services.update(dependencies.get("downstream_services", []))
    
    logs = []
    for service in related_services:
        service_logs = get_error_logs_for_service(service)
        logs.extend(service_logs)
    
    return logs
