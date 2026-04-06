#!/usr/bin/env python3
"""
Example: Local fine-tuning with Hugging Face transformers.
Use this as a template for custom fine-tuning implementations.
"""

import json
import torch
from typing import Dict, List, Optional
from pathlib import Path

# Note: Install required packages with:
# pip install transformers datasets torch peft bitsandbytes


class LocalFineTurningExample:
    """Example of fine-tuning locally with transformers library."""
    
    @staticmethod
    def load_training_data(filepath: str) -> List[Dict]:
        """Load training data from JSONL file."""
        examples = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))
        return examples
    
    @staticmethod
    def format_for_training(examples: List[Dict]) -> List[Dict]:
        """Format examples for training."""
        formatted = []
        for example in examples:
            text = f"Email Triage Task\n\n{example['prompt']}\n\nResponse: {example['completion']}"
            formatted.append({
                "text": text,
                "difficulty": example.get("difficulty", "medium"),
                "reward": example.get("reward", 0.0)
            })
        return formatted
    
    @staticmethod
    def finetune_with_lora(
        model_name: str = "meta-llama/Llama-2-7b",
        training_data_path: str = "data/training_supervised.jsonl",
        output_dir: str = "models/finetuned",
        num_epochs: int = 3,
        batch_size: int = 8
    ):
        """Fine-tune model using LoRA (Parameter-Efficient Fine-Tuning)."""
        
        try:
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                TrainingArguments,
                Trainer,
            )
            from peft import LoraConfig, get_peft_model
            from datasets import Dataset
        except ImportError:
            print("Install required packages: pip install transformers datasets peft")
            return
        
        print(f"Loading model: {model_name}")
        
        # Load model and tokenizer
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load training data
        print(f"Loading training data: {training_data_path}")
        examples = LocalFineTurningExample.load_training_data(training_data_path)
        formatted = LocalFineTurningExample.format_for_training(examples)
        
        # Create dataset
        dataset = Dataset.from_dict({
            "text": [ex["text"] for ex in formatted],
            "difficulty": [ex["difficulty"] for ex in formatted],
        })
        
        # Apply LoRA
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            save_steps=10,
            save_total_limit=3,
            logging_steps=5,
            learning_rate=2e-4,
            warmup_steps=100,
            weight_decay=0.01,
        )
        
        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
        )
        
        # Fine-tune
        print("Starting fine-tuning...")
        trainer.train()
        
        # Save
        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        print(f"✓ Fine-tuned model saved to {output_dir}")
        return model


class LocalFineTuningWithVLLM:
    """Example using vLLM for distributed training."""
    
    @staticmethod
    def prepare_for_vllm(training_data_path: str, output_path: str):
        """Prepare data for vLLM training."""
        
        examples = []
        with open(training_data_path, 'r') as f:
            for line in f:
                if line.strip():
                    ex = json.loads(line)
                    # Format: [INST] prompt [/INST] completion
                    text = f"[INST] {ex['prompt']} [/INST] {ex['completion']}"
                    examples.append(text)
        
        # Save formatted data
        with open(output_path, 'w') as f:
            for text in examples:
                f.write(text + '\n')
        
        print(f"✓ Prepared {len(examples)} examples for vLLM")
        print(f"Saved to: {output_path}")
        
        # Usage instructions
        print("\nTo train with vLLM:")
        print(f"python -m vllm.entrypoints.fastapi --model meta-llama/Llama-2-7b-hf --tensor-parallel-size 2")
        print(f"# Then submit training job via API")


class CloudFineTuningExample:
    """Example of using cloud-based fine-tuning services."""
    
    @staticmethod
    def prepare_for_openai(training_data_path: str):
        """Prepare data for OpenAI fine-tuning API."""
        
        examples = []
        with open(training_data_path, 'r') as f:
            for line in f:
                if line.strip():
                    example = json.loads(line)
                    messages = [
                        {"role": "system", "content": "You are an expert email triage assistant."},
                        {"role": "user", "content": example["prompt"]},
                        {"role": "assistant", "content": example["completion"]}
                    ]
                    examples.append({"messages": messages})
        
        # Save in OpenAI format
        output = training_data_path.replace(".jsonl", "_openai.jsonl")
        with open(output, 'w') as f:
            for ex in examples:
                f.write(json.dumps(ex) + '\n')
        
        print(f"✓ Prepared {len(examples)} examples for OpenAI")
        print(f"Saved to: {output}")
        
        # Usage
        print("\nTo fine-tune with OpenAI:")
        print(f"openai api fine_tunes.create -t {output} -m gpt-3.5-turbo")
    
    @staticmethod
    def prepare_for_huggingface(training_data_path: str):
        """Prepare dataset for HuggingFace Hub."""
        
        examples = []
        with open(training_data_path, 'r') as f:
            for line in f:
                if line.strip():
                    example = json.loads(line)
                    examples.append({
                        "prompt": example["prompt"],
                        "completion": example["completion"],
                        "difficulty": example.get("difficulty", "medium")
                    })
        
        # Save as JSON
        output = training_data_path.replace(".jsonl", "_hf.json")
        with open(output, 'w') as f:
            json.dump(examples, f, indent=2)
        
        print(f"✓ Prepared {len(examples)} examples for HuggingFace")
        print(f"Saved to: {output}")
        
        print("\nTo push to HuggingFace Hub:")
        print(f"from datasets import load_dataset")
        print(f"dataset = load_dataset('json', data_files='{output}')")
        print(f"dataset.push_to_hub('username/email-triage-finetuned')")


def main():
    """Run examples based on command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local fine-tuning examples")
    parser.add_argument("--backend", choices=["lora", "vllm", "openai", "huggingface"],
                       default="lora", help="Fine-tuning backend")
    parser.add_argument("--model", default="meta-llama/Llama-2-7b",
                       help="Model to fine-tune")
    parser.add_argument("--training-data", default="data/training_supervised.jsonl",
                       help="Training data path")
    parser.add_argument("--output", default="models/finetuned",
                       help="Output directory")
    
    args = parser.parse_args()
    
    print("="*60)
    print("LOCAL FINE-TUNING EXAMPLE")
    print("="*60)
    
    if args.backend == "lora":
        print("\nFine-tuning with LoRA (Parameter-Efficient)...")
        print("Install: pip install peft bitsandbytes")
        # LocalFineTurningExample.finetune_with_lora(
        #     model_name=args.model,
        #     training_data_path=args.training_data,
        #     output_dir=args.output
        # )
        print("(Uncomment line above to run)")
    
    elif args.backend == "vllm":
        print("\nPreparing for vLLM distributed training...")
        LocalFineTuningWithVLLM.prepare_for_vllm(
            args.training_data,
            args.training_data.replace(".jsonl", "_vllm.txt")
        )
    
    elif args.backend == "openai":
        print("\nPreparing for OpenAI fine-tuning...")
        CloudFineTuningExample.prepare_for_openai(args.training_data)
    
    elif args.backend == "huggingface":
        print("\nPreparing for HuggingFace Hub...")
        CloudFineTuningExample.prepare_for_huggingface(args.training_data)


if __name__ == "__main__":
    main()
