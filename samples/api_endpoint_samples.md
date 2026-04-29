# RCA Bot API Endpoint Samples

This document contains sample requests and responses for the RCA Bot API endpoints.

## 1. Complete Flow Endpoint

### Request
```bash
POST /complete-flow
Content-Type: application/json

{
  "service_name": "payment-service",
  "start_time": "2026-04-29T13:00:00Z",
  "end_time": "2026-04-29T15:00:00Z"
}
```

### Response
```json
{
  "service_name": "payment-service",
  "document_analysis": {
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
  },
  "log_analysis": {
    "service_name": "payment-service",
    "primary_service_logs": [
      {
        "log_id": "LOG-PAYMENT-SERVICE-001",
        "service": "payment-service",
        "timestamp": "2026-04-29T13:06:56.470922Z",
        "status_code": 500,
        "error": "Database connection timeout",
        "url": "/api/payment/service/endpoint1",
        "level": "ERROR",
        "message": "payment-service encountered Database connection timeout at 2026-04-29T13:06:56.470922Z",
        "duration_ms": 100,
        "request_id": "REQ-0000-000",
        "user_id": "USER-00000",
        "ip_address": "192.168.0.0",
        "user_agent": "Mozilla/5.0 (compatible; RCA-Bot/1.0)"
      }
    ],
    "related_service_logs": [
      {
        "log_id": "LOG-USER-SERVICE-001",
        "service": "user-service",
        "timestamp": "2026-04-29T13:10:56.470922Z",
        "status_code": 500,
        "error": "Database connection timeout",
        "url": "/api/user/service/endpoint1",
        "level": "ERROR",
        "message": "user-service encountered Database connection timeout at 2026-04-29T13:10:56.470922Z",
        "duration_ms": 150,
        "request_id": "REQ-0002-000",
        "user_id": "USER-00002",
        "ip_address": "192.168.2.0",
        "user_agent": "Mozilla/5.0 (compatible; RCA-Bot/1.0)"
      }
    ],
    "total_error_logs": 5,
    "total_related_logs": 20,
    "fetch_timestamp": "2026-04-29T15:06:56.480758Z"
  },
  "rca_summary": {
    "service_name": "payment-service",
    "rca_summary": {
      "error_start_time": "2026-04-28T21:40:00Z",
      "error_code": 500,
      "impacted_dependencies": ["order-service", "user-service"],
      "endpoints": ["/api/payment/service/endpoint1"],
      "cause_of_error": "Database connection timeout affecting multiple services",
      "action_taken": [
        "Restart database connection pool",
        "Check database server health",
        "Implement connection retry logic",
        "Monitor service recovery"
      ],
      "severity": "High",
      "error_pattern": "Database connectivity issues causing cascade failures",
      "business_impact": "Payment processing unavailable, affecting user transactions"
    },
    "ongoing_errors": [
      {
        "service": "payment-service",
        "timestamp": "2026-04-29T13:06:56.470922Z",
        "error": "Database connection timeout",
        "status_code": 500,
        "url": "/api/payment/service/endpoint1",
        "severity": "High"
      }
    ],
    "analysis_timestamp": "2026-04-29T15:06:56.482374Z"
  },
  "flow_timestamp": "2026-04-29T15:06:56.482374Z"
}
```

## 2. Individual Service Endpoints

### Document Analysis
```bash
POST /extract-document
Content-Type: application/json

{
  "service_name": "payment-service"
}
```

### Log Fetching
```bash
POST /fetch-logs
Content-Type: application/json

{
  "service_name": "payment-service",
  "start_time": "2026-04-29T13:00:00Z",
  "end_time": "2026-04-29T15:00:00Z"
}
```

### Training & Analysis
```bash
POST /train-analyze
Content-Type: application/json

{
  "service_name": "payment-service",
  "document_data": {...},
  "log_data": {...}
}
```

## 3. Health Check

### Request
```bash
GET /health
```

### Response
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

## 4. Lambda Handler Format

### Event Structure
```json
{
  "path": "/complete-flow",
  "httpMethod": "POST",
  "body": "{\"service_name\": \"payment-service\", \"start_time\": \"2026-04-29T13:00:00Z\", \"end_time\": \"2026-04-29T15:00:00Z\"}"
}
```

### Lambda Response
```json
{
  "statusCode": 200,
  "body": "{\"service_name\": \"payment-service\", ...}"
}
```

## 5. Error Responses

### Validation Error
```json
{
  "statusCode": 400,
  "body": "{\"error\": \"service_name is required\"}"
}
```

### Service Error
```json
{
  "statusCode": 500,
  "body": "{\"error\": \"Failed to process request\"}"
}
```

### Not Found
```json
{
  "statusCode": 404,
  "body": "{\"error\": \"Endpoint not found\", \"available_endpoints\": [...]}"
}
```
