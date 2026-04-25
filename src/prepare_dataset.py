"""
prepare_dataset.py
------------------
Converts the 10 dataset JSON files + flow.json into
(input_text, target_text) training pairs for flan-t5 fine-tuning.

Output: training_data.jsonl
"""

import json
import os
import glob
from datetime import datetime


# ── helpers ──────────────────────────────────────────────────────────────────

def load_flow(flow_path: str) -> dict:
    with open(flow_path) as f:
        return json.load(f)


def load_dataset_files(data_dir: str) -> list[dict]:
    """Load all fileN.json files and return a flat list of records."""
    records = []
    for path in sorted(glob.glob(os.path.join(data_dir, "file*.json"))):
        with open(path) as f:
            records.extend(json.load(f))
    print(f"Loaded {len(records)} records from {data_dir}")
    return records


def is_ongoing(failure_end_time: str | None) -> bool:
    """
    Heuristic: if failure_end_time is None or in the future, treat as ongoing.
    In real usage you'd compare against the log ingestion timestamp.
    """
    if failure_end_time is None:
        return True
    try:
        end = datetime.fromisoformat(failure_end_time)
        return end > datetime.utcnow()
    except ValueError:
        return False


def build_input_text(record: dict, flow: dict) -> str:
    """
    Serialise one log record + the application flow into a single
    natural-language prompt that the model will learn to map → RCA output.
    """
    inp = record["input"]
    flow_summary = (
        f"Application: {flow['application']}. "
        f"Flow: {flow['start_point']} → {flow['gateway']} → "
        + " → ".join(
            step["to"]
            for step in flow["sequence"]
            if step["type"] == "service"
        )
        + f". {flow['failure_condition']}."
    )

    log_summary = (
        f"Log entry for correlation_id={inp['correlation_id']}: "
        f"path={inp['path']}, method={inp['method']}, "
        f"start_time={inp['start_time']}, end_time={inp['end_time']}, "
        f"duration_ms={inp['duration_request']}, "
        f"bin_outcome={inp['bin_outcome']}, "
        f"status_code={inp['status_code']}, "
        f"gateway_response_code={inp['gateway_response_code']}, "
        f"tdh_response_code={inp['tdh_response_code']}, "
        f"sel_response_code={inp['sel_response_code']}, "
        f"st_response_code={inp['st_response_code']}, "
        f"event=\"{inp['event']}\"."
    )

    return f"{flow_summary} {log_summary} Perform root cause analysis."


def build_target_text(record: dict) -> str:
    """
    Build a concise, structured RCA string the model learns to generate.
    """
    inp = record["input"]
    out = record["output"]

    ongoing = is_ongoing(out.get("failure_end_time"))
    status = "ONGOING" if ongoing else "RESOLVED"

    impacted = ", ".join(out["impacted_dependencies"]) if out["impacted_dependencies"] else "none"

    return (
        f"Failed dependency: {out['failed_dependency']}. "
        f"Error: {out['error_code']} - {out['error_message']}. "
        f"Failure window: {out['failure_start_time']} to {out['failure_end_time']}. "
        f"Status: {status}. "
        f"Impacted downstream: {impacted}. "
        f"Reason: {out['reason']}."
    )


def build_training_pairs(records: list[dict], flow: dict) -> list[dict]:
    pairs = []
    for record in records:
        pairs.append({
            "input_text": build_input_text(record, flow),
            "target_text": build_target_text(record),
        })
    return pairs


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    # ── paths (adjust if your files are elsewhere) ───────────────────────────
    DATA_DIR = "./data"          # folder containing file2.json … file11.json
    FLOW_PATH = "./data/flow.json"
    OUTPUT_PATH = "./training_data.jsonl"

    flow = load_flow(FLOW_PATH)
    records = load_dataset_files(DATA_DIR)
    pairs = build_training_pairs(records, flow)

    with open(OUTPUT_PATH, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"Saved {len(pairs)} training pairs → {OUTPUT_PATH}")

    # preview first pair
    print("\n─── Sample input ───────────────────────────────────────────────")
    print(pairs[0]["input_text"])
    print("\n─── Sample target ──────────────────────────────────────────────")
    print(pairs[0]["target_text"])


if __name__ == "__main__":
    main()