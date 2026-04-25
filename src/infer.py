"""
infer.py
--------
Load the fine-tuned RCA model and run root cause analysis
on a new raw log entry.

Usage:
    python infer.py --log sample_log.json --flow data/flow.json
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


# ── config ───────────────────────────────────────────────────────────────────

# Resolve absolute path — newer huggingface_hub rejects relative paths like ./rca_model
MODEL_DIR      = str(Path(__file__).resolve().parent / "rca_model")
MAX_INPUT_LEN  = 512
MAX_NEW_TOKENS = 150


# ── helpers (same logic as prepare_dataset.py) ───────────────────────────────

def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def is_ongoing(failure_end_time) -> str:
    if failure_end_time is None:
        return "ONGOING (no end time recorded)"
    try:
        end = datetime.fromisoformat(failure_end_time)
        if end > datetime.utcnow():
            return "ONGOING"
        return f"RESOLVED at {failure_end_time}"
    except ValueError:
        return "UNKNOWN"


def build_prompt(log: dict, flow: dict) -> str:
    """
    Accepts either a raw log dict (with 'input' key like the dataset)
    or a flat log dict (direct fields).
    """
    inp = log.get("input", log)   # support both wrapped and flat formats

    flow_summary = (
        f"Application: {flow['application']}. "
        f"Flow: {flow['start_point']} -> {flow['gateway']} -> "
        + " -> ".join(
            step["to"]
            for step in flow["sequence"]
            if step["type"] == "service"
        )
        + f". {flow['failure_condition']}."
    )

    log_summary = (
        f"Log entry for correlation_id={inp.get('correlation_id', 'N/A')}: "
        f"path={inp.get('path', 'N/A')}, method={inp.get('method', 'N/A')}, "
        f"start_time={inp.get('start_time', 'N/A')}, end_time={inp.get('end_time', 'N/A')}, "
        f"duration_ms={inp.get('duration_request', 'N/A')}, "
        f"bin_outcome={inp.get('bin_outcome', 'N/A')}, "
        f"status_code={inp.get('status_code', 'N/A')}, "
        f"gateway_response_code={inp.get('gateway_response_code', 'N/A')}, "
        f"tdh_response_code={inp.get('tdh_response_code', 'N/A')}, "
        f"sel_response_code={inp.get('sel_response_code', 'N/A')}, "
        f"st_response_code={inp.get('st_response_code', 'N/A')}, "
        f"event=\"{inp.get('event', 'N/A')}\"."
    )

    return f"{flow_summary} {log_summary} Perform root cause analysis."


# ── inference ────────────────────────────────────────────────────────────────

def run_rca(prompt: str, tokenizer, model, device: str) -> str:
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=MAX_INPUT_LEN,
        truncation=True,
        padding=True,
    ).to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            num_beams=4,
            early_stopping=True,
        )

    return tokenizer.decode(output_ids[0], skip_special_tokens=True)


def parse_rca_output(rca_text: str) -> dict:
    """
    Parse the model's output text into a structured dict.
    The model was trained to output fields in a consistent format.
    """
    def extract(label: str, text: str) -> str:
        for part in text.split(". "):
            if part.strip().startswith(label):
                return part.strip()[len(label):].strip()
        return "N/A"

    return {
        "failed_dependency":   extract("Failed dependency:", rca_text),
        "error":               extract("Error:", rca_text),
        "failure_window":      extract("Failure window:", rca_text),
        "status":              extract("Status:", rca_text),
        "impacted_downstream": extract("Impacted downstream:", rca_text),
        "root_cause":          extract("Reason:", rca_text),
        "raw_output":          rca_text,
    }


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run RCA inference on a log entry.")
    parser.add_argument("--log",       required=True, help="Path to log JSON file")
    parser.add_argument("--flow",      required=True, help="Path to flow.json")
    parser.add_argument("--model_dir", default=None,  help="Override model directory path")
    args = parser.parse_args()

    # allow --model_dir override, otherwise use resolved default
    model_path = str(Path(args.model_dir).resolve()) if args.model_dir else MODEL_DIR

    if not os.path.isdir(model_path):
        print(f"ERROR: Model directory not found: {model_path}")
        print("Make sure you have run train.py first and the rca_model folder exists.")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device : {device}")
    print(f"Model path   : {model_path}")

    # load model
    print("Loading model ...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path, local_files_only=True).to(device)
    model.eval()

    # build prompt
    log  = load_json(args.log)
    flow = load_json(args.flow)
    prompt = build_prompt(log, flow)

    print("\n--- Prompt -----------------------------------------------------")
    print(prompt)

    # run model
    raw_output = run_rca(prompt, tokenizer, model, device)

    # parse + display
    rca = parse_rca_output(raw_output)

    print("\n--- Root Cause Analysis ----------------------------------------")
    print(f"  Failed Dependency  : {rca['failed_dependency']}")
    print(f"  Error              : {rca['error']}")
    print(f"  Failure Window     : {rca['failure_window']}")
    print(f"  Status             : {rca['status']}")
    print(f"  Impacted Downstream: {rca['impacted_downstream']}")
    print(f"  Root Cause         : {rca['root_cause']}")
    print("----------------------------------------------------------------")

    # save result
    output_path = "rca_result.json"
    with open(output_path, "w") as f:
        json.dump(rca, f, indent=2)
    print(f"\nResult saved to {output_path}")


if __name__ == "__main__":
    main()