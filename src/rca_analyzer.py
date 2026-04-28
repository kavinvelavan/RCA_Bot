#rca script that parses newRelic logs, analyze failures in the last 10 mins,
# exctract key fields * FunctionName,start_time,end_time,path,status_code,message(from logs)
# classifies them into common or unique
#generate json output - > input for RCA bot


import json
from datetime import datetime,timedelta
from collections import Counter

INPUT_FILE=""
OUTPUT_FILE=""

def load_logs():
    with open(INPUT_FILE) as f:
        return json.load(f)

def parse_message(log):
    try:
        msg = json.loads(log["message"])
        return {
            "function_name": log["function_name"],
            "start_time": msg.get("start_time"),
            "end_time": msg.get("end_time"),
            "url": msg.get("path"),
            "status_code": msg.get("status_code"),
            "message": log["message"],
        }
    except:
        return None

def filter_last_10_min(parsed_logs):
    now=datetime.strptime(parsed_logs[0]["start_time"], "%Y-%m-%d %H:%M:%S")
    last_10_min = now - timedelta(minutes=10)
    result = []
    for log in parsed_logs:
        if not log:
            continue
        log_time = datetime.strptime(log["start_time"], "%Y-%m-%d %H:%M:%S")
        if log_time > last_10_min:
            result.append(log)
        return result

def analyze_failures(logs):
    failures = []
    status_counter = Counter()
    for log in logs:
        if log["status_code"] != 200:
            failures.append(log)
            status_counter[log["status_code"]] += 1
    return failures, status_counter

def classify_failures(failures, status_counter):
    output=[]
    for log in failures:
        failure_type = "uniqure_failure"

        if status_counter[log["status_code"]] > 1:
            failure_type = "common_failure"
        output.append({
           "function_name": log["function_name"],
           "start_time": log["start_time"],
           "end_time": log["end_time"],
           "url": log["url"],
           "status_code": log["status_code"],
           "message": log["message"],
           "failure_type": failure_type,
        })
    return output

def main():
    raw_logs = load_logs()

    parsed_logs = [parse_message(log) for log in raw_logs]

    logs_10_min = filter_last_10_min(parsed_logs)

    failures, status_counter = analyze_failures(logs_10_min)

    final_output = classify_failures(failures, status_counter)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_output, f, indent=2)
    print("RCA JSON:",OUTPUT_FILE)

if __name__ == "__main__":
    main()
