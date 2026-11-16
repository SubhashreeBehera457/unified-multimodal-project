import os
import torch
import pandas as pd
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def train_misinformation_model():
    print("Loading Real Kaggle Dataset: Disaster Tweets...")
    
    # Load dataset
    df = pd.read_csv("data/tweets/tweets.csv")
    df = df[['text', 'target']].dropna()
    df.rename(columns={'target': 'label'}, inplace=True)
    
    # Sample down to 2000 for faster training for prototype, otherwise it takes too long
    # In a real cluster we'd train on the whole thing.
    df = df.sample(n=2000, random_state=42)
    
    # Train-test split
    train_df, eval_df = train_test_split(df, test_size=0.2, random_state=42)
    
    train_dataset = Dataset.from_pandas(train_df)
    eval_dataset = Dataset.from_pandas(eval_df)

    tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

    print("Tokenizing data...")
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_eval = eval_dataset.map(tokenize_function, batched=True)

    model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=2)

    training_args = TrainingArguments(
        output_dir='./results_misinfo',
        num_train_epochs=2,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=100,
        weight_decay=0.01,
        logging_steps=10,
        eval_strategy="epoch",  # Fix for new transformers version
        save_strategy="epoch",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        compute_metrics=compute_metrics,
    )

    print("Starting Model Training for Misinformation Filter...")
    trainer.train()
    
    print("Evaluating Model...")
    eval_results = trainer.evaluate()
    print(f"Evaluation Results: {eval_results}")
    
    # Save the model
    os.makedirs("models/misinformation_filter", exist_ok=True)
    model.save_pretrained("models/misinformation_filter")
    tokenizer.save_pretrained("models/misinformation_filter")
    print("Model saved to models/misinformation_filter")

if __name__ == "__main__":
    train_misinformation_model()
