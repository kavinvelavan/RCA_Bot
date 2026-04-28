# Scope of this script is to
# pull data from NewRelic using NRQL
# Focus on logs correlation ID, status code, message
# Each request (one correlation ID) , combines all logs to trace the flow
# Detect common vs unique issues

# Analyze last 10 mins logs -> detect failures-> group by correlation ID -> RCA -> result