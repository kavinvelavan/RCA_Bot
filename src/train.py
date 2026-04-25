"""
train.py
--------
Fine-tunes google/flan-t5-base on the RCA training pairs
produced by prepare_dataset.py.

Requirements:
    pip install transformers datasets accelerate torch

Run:
    python train.py
"""

import json
import os
from pathlib import Path
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)
import torch
import transformers as _tv


# ── config ───────────────────────────────────────────────────────────────────

MODEL_NAME       = "google/flan-t5-small"
TRAINING_FILE    = str(Path(__file__).resolve().parent / "training_data.jsonl")
OUTPUT_DIR       = str(Path(__file__).resolve().parent / "rca_model")
MAX_INPUT_LEN    = 256    # reduced from 512 — speeds up CPU training significantly
MAX_TARGET_LEN   = 128
EPOCHS           = 10     # more epochs to compensate for tiny dataset
BATCH_SIZE       = 1      # small batch — works on CPU with limited RAM
LEARNING_RATE    = 5e-4   # slightly higher LR for faster convergence on small data
WARMUP_STEPS     = 5
SAVE_TOTAL_LIMIT = 2

# With only 40 records, using an eval split wastes too much training data
# and causes early stopping to fire prematurely.
# We train on ALL data and save every N steps instead.
USE_EVAL_SPLIT   = False
EVAL_SPLIT       = 0.10   # only used if USE_EVAL_SPLIT = True


# ── version check ─────────────────────────────────────────────────────────────

_new_transformers = tuple(int(x) for x in _tv.__version__.split(".")[:2]) >= (4, 41)
print(f"transformers version : {_tv.__version__}")
print(f"torch version        : {torch.__version__}")
print(f"Device               : {'CUDA (GPU)' if torch.cuda.is_available() else 'CPU'}")
if not torch.cuda.is_available():
    print("  → Running on CPU. Training will take ~10-20 min. This is normal for your dataset size.")


# ── load data ─────────────────────────────────────────────────────────────────

def load_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"training_data.jsonl not found at: {path}\n"
            "Run prepare_dataset.py first."
        )
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def build_hf_dataset(pairs: list[dict], use_eval_split: bool, eval_split: float):
    ds = Dataset.from_list(pairs)
    if use_eval_split and len(pairs) >= 20:
        split = ds.train_test_split(test_size=eval_split, seed=42)
        return split["train"], split["test"]
    # too few records — train on everything, no eval split
    print(f"  Dataset too small for eval split ({len(pairs)} records). Training on full dataset.")
    return ds, None


# ── tokenise ──────────────────────────────────────────────────────────────────

def make_tokenise_fn(tokenizer):
    def tokenise(batch):
        model_inputs = tokenizer(
            batch["input_text"],
            max_length=MAX_INPUT_LEN,
            padding="max_length",
            truncation=True,
        )
        labels = tokenizer(
            text_target=batch["target_text"],
            max_length=MAX_TARGET_LEN,
            padding="max_length",
            truncation=True,
        )
        # mask padding so loss ignores it
        labels["input_ids"] = [
            [(t if t != tokenizer.pad_token_id else -100) for t in label]
            for label in labels["input_ids"]
        ]
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs
    return tokenise


# ── training args ─────────────────────────────────────────────────────────────

def build_training_args(has_eval: bool) -> Seq2SeqTrainingArguments:
    eval_key = "eval_strategy" if _new_transformers else "evaluation_strategy"

    if has_eval:
        return Seq2SeqTrainingArguments(
            output_dir=OUTPUT_DIR,
            num_train_epochs=EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            per_device_eval_batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            warmup_steps=WARMUP_STEPS,
            predict_with_generate=True,
            **{eval_key: "epoch"},
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            save_total_limit=SAVE_TOTAL_LIMIT,
            logging_dir="./logs",
            logging_steps=2,
            fp16=torch.cuda.is_available(),
            dataloader_pin_memory=False,   # FIX: suppress pin_memory warning on CPU
            report_to="none",
        )
    else:
        # no eval dataset — save on steps instead
        return Seq2SeqTrainingArguments(
            output_dir=OUTPUT_DIR,
            num_train_epochs=EPOCHS,
            per_device_train_batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            warmup_steps=WARMUP_STEPS,
            predict_with_generate=True,
            **{eval_key: "no"},
            save_strategy="steps",
            save_steps=50,
            save_total_limit=SAVE_TOTAL_LIMIT,
            logging_dir="./logs",
            logging_steps=2,
            fp16=torch.cuda.is_available(),
            dataloader_pin_memory=False,   # FIX: suppress pin_memory warning on CPU
            report_to="none",
        )


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\nTraining file : {TRAINING_FILE}")
    print(f"Output dir    : {OUTPUT_DIR}\n")

    # load tokenizer & model
    print("Downloading/loading base model (flan-t5-base) ...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model     = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # load data
    pairs = load_jsonl(TRAINING_FILE)
    print(f"\nTotal records     : {len(pairs)}")

    train_ds, eval_ds = build_hf_dataset(pairs, USE_EVAL_SPLIT, EVAL_SPLIT)
    has_eval = eval_ds is not None
    print(f"Training samples  : {len(train_ds)}")
    print(f"Eval samples      : {len(eval_ds) if has_eval else 'none (training on full dataset)'}")

    # tokenise
    print("\nTokenising dataset ...")
    tokenise_fn = make_tokenise_fn(tokenizer)
    train_ds = train_ds.map(tokenise_fn, batched=True, remove_columns=train_ds.column_names)
    if has_eval:
        eval_ds = eval_ds.map(tokenise_fn, batched=True, remove_columns=eval_ds.column_names)

    # trainer
    training_args = build_training_args(has_eval)
    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds if has_eval else None,
        processing_class=tokenizer,    # FIX: replaces deprecated 'tokenizer' argument
        data_collator=data_collator,
        # NO EarlyStoppingCallback — fires too soon on tiny datasets
    )

    # train
    print(f"\nStarting fine-tuning for {EPOCHS} epochs ...")
    print("You will see loss values logged every 2 steps. Loss should decrease over time.\n")
    trainer.train()

    # force save at end regardless of strategy
    print("\nSaving model ...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved to: {OUTPUT_DIR}")
    print("\nDone! You can now run: python infer.py --log your_log.json --flow data/flow.json")


if __name__ == "__main__":
    main()