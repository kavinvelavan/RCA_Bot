# CAT Application - RCA Model Training Pipeline

Fine-tunes `google/flan-t5-base` on your structured failure logs
to automatically perform **Root Cause Analysis** on new log inputs.

---

## Folder Structure

```
project/
├── data/
│   ├── flow.json          ← application flow definition
│   ├── file1.json
│   ├── file2.json
│   │   ... (file1 to file10)
│   └── file10.json
│
├── prepare_dataset.py     ← step 1: build training pairs
├── train.py               ← step 2: fine-tune flan-t5
├── infer.py               ← step 3: run RCA on new logs
├── requirements.txt
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
```

Requires Python 3.10+. GPU recommended but CPU works for this model size.

---

## Step 1 — Prepare the Dataset

Converts your 10 JSON files + flow.json into (input, target) training pairs.

```bash
python prepare_dataset.py
```

Output: `training_data.jsonl`

Each line is:
```json
{
  "input_text": "Application: CAT. Flow: CAT → GATEWAY → TDH → SEL → ST ... Perform root cause analysis.",
  "target_text": "Failed dependency: GATEWAY. Error: 401 - Unauthorized. Failure window: ... Status: RESOLVED. ..."
}
```

---

## Step 2 — Fine-Tune the Model

```bash
python train.py
```

- Base model: `google/flan-t5-small` (~250M params, runs on CPU/GPU)
- Training: 20 epochs, early stopping patience of 3
- Output saved to: `./rca_model/`

Training time estimates:
| Hardware | Approximate Time |
|----------|-----------------|
| CPU only | 10–20 minutes   |
| GPU (T4) | 2–4 minutes     |

---

## Step 3 — Run RCA on a New Log

Create a new log JSON file (same format as your dataset's `input` block):

```json
{
  "start_time": "2026-04-25T20:00:00.00",
  "path": "/cat2/kd/account/9999/bin",
  "method": "POST",
  "correlation_id": "REQ-9999",
  "content_type": "service/json;charset=UTF-8",
  "accept": "service/json;v=2",
  "bin_outcome": "FAILURE",
  "tdh_response_code": 200,
  "sel_response_code": 503,
  "st_response_code": null,
  "gateway_response_code": 200,
  "duration_request": 540,
  "status_code": "503",
  "end_time": "2026-04-25T20:00:05.40",
  "event": "SEL service temporarily unavailable"
}
```

Then run:

```bash
python infer.py --log yourinputfile.json --flow data/flow.json
```

Output:
```
─── Root Cause Analysis ──────────────────────────────────
  Failed Dependency  : SEL
  Error              : 503 - Service Unavailable
  Failure Window     : 2026-04-25T20:00:02.00 to 2026-04-25T20:00:05.40
  Status             : RESOLVED
  Impacted Downstream: ST
  Root Cause         : SEL outage prevents ST from being invoked
──────────────────────────────────────────────────────────
```

Result also saved to `rca_result.json`.

---

## What the Model Learns

| Input Signal              | What the Model Identifies          |
|---------------------------|------------------------------------|
| `gateway_response_code` 4xx | Gateway is the failed dependency |
| `tdh_response_code` 5xx   | TDH is failing, SEL+ST impacted    |
| `sel_response_code` 5xx   | SEL is failing, ST impacted        |
| `st_response_code` 5xx    | ST is failing, no further impact   |
| `failure_start_time`      | When the failure started           |
| `failure_end_time`        | Whether issue is ongoing/resolved  |

---

## Scaling Up

| Scenario                        | Recommendation                              |
|---------------------------------|---------------------------------------------|
| More data (100+ records)        | Switch to `flan-t5-large` or `flan-t5-xl`  |
| Production / real-time logs     | Add RAG with flow.json as a retrieval doc   |
| Multi-application support       | Fine-tune `Mistral-7B` with LoRA adapters   |
| Streaming logs                  | Wrap `infer.py` in a FastAPI service        |

---

## Key Design Decisions

- **Why flan-t5?** It is a seq2seq model — well suited for structured input → structured output tasks. It is small enough to fine-tune on CPU with your current dataset.
- **Why not GPT/Claude API?** Fine-tuning gives you a local, offline, low-latency model that does not send production log data to a third party.
- **Why 20 epochs?** With only ~40 training records, more passes are needed for the model to generalise. Early stopping prevents overfitting.

## Training model :
![alt text](train_model.png)

## Outputs

Output 1:
![alt text](output1.png)

Output 2:
![alt text](output2.png)

Output 3:
![alt text](output3.png)
