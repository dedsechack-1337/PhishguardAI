"""
Fine-tune DistilBERT for phishing email text classification.

Trains a binary classifier (legit=0, phishing=1) on email body text
and saves the model + tokenizer for use by the inference service.

Replace data/emails_dataset.csv with a real corpus (e.g. Nazario phishing
corpus + Enron ham emails) for production training. The script only
requires a CSV with 'text' and 'label' columns.
"""

import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "emails_dataset.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "email_bert")
MODEL_NAME = "distilbert-base-uncased"
MAX_LEN = 128


class EmailDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=MAX_LEN):
        self.encodings = tokenizer(
            list(texts), truncation=True, padding=True, max_length=max_len
        )
        self.labels = list(labels)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = torch.softmax(torch.tensor(logits), dim=1)[:, 1].numpy()
    preds = np.argmax(logits, axis=1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "auc": roc_auc_score(labels, probs),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} email samples")
    print(df["label"].value_counts())

    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label"]
    )

    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

    train_dataset = EmailDataset(train_df["text"], train_df["label"], tokenizer)
    test_dataset = EmailDataset(test_df["text"], test_df["label"], tokenizer)

    training_args = TrainingArguments(
        output_dir=os.path.join(OUTPUT_DIR, "checkpoints"),
        num_train_epochs=4,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        learning_rate=2e-5,
        eval_strategy="epoch",
        save_strategy="no",
        logging_steps=20,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    print("\n=== Final Evaluation ===")
    metrics = trainer.evaluate()
    print(metrics)

    # Detailed classification report
    preds_output = trainer.predict(test_dataset)
    preds = np.argmax(preds_output.predictions, axis=1)
    print(classification_report(test_df["label"], preds, target_names=["legit", "phishing"]))

    # Save model + tokenizer for inference
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nModel + tokenizer saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
