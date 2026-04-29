# RCA Bot Sample Outputs

This directory contains sample outputs from the RCA Bot system for reference and documentation purposes.

## Files

### `rca_sample_output.json`
Sample JSON output from a complete RCA analysis of the payment-service. This demonstrates:

- **Service Dependencies**: Upstream, downstream, and related services
- **Error Summary**: Total errors, severity, and timing information
- **Root Cause Analysis**: Cause, patterns, business impact, and affected components
- **Recommended Actions**: Actionable steps to resolve the issue
- **Past Incidents**: Historical incident data for context
- **Ongoing Errors**: Real-time error detection results

## Output Structure

The RCA Bot generates structured JSON output with the following main sections:

```json
{
  "service_name": "string",
  "analysis_timestamp": "ISO 8601 timestamp",
  "service_dependencies": {
    "upstream_services": ["array"],
    "downstream_services": ["array"],
    "related_services": ["array"]
  },
  "error_summary": {
    "total_errors": "number",
    "error_code": "number",
    "severity": "string",
    "error_start_time": "ISO 8601 timestamp"
  },
  "root_cause_analysis": {
    "cause": "string",
    "pattern": "string",
    "business_impact": "string",
    "impacted_dependencies": ["array"],
    "affected_endpoints": ["array"]
  },
  "recommended_actions": ["array"],
  "ongoing_errors": ["array"],
  "past_incidents": ["array"]
}
```

## Usage

This sample output can be used for:
- API documentation examples
- Integration testing
- System validation
- Reference for expected data structures

## Integration with Orchestrator

The output format is designed to be compatible with the orchestrator system, providing:
- Standardized error information
- Service hierarchy data
- Actionable RCA insights
- Historical context for pattern recognition
