#!/usr/bin/env python3
"""Script to redact Hugging Face token from files."""
import os
import sys

TOKEN_TO_REPLACE = "YOUR_TOKEN_HERE"
REPLACEMENT = 'os.getenv("HUGGINGFACE_API_TOKEN", "YOUR_TOKEN_HERE")'

files_to_check = [
    "scripts/test_hf_api_simple.py",
    "scripts/test_inference_client.py"
]

for filepath in files_to_check:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if TOKEN_TO_REPLACE in content:
            # Replace the token line
            if 'API_TOKEN = "' in content:
                content = content.replace(
                    f'API_TOKEN = "{TOKEN_TO_REPLACE}"',
                    f'API_TOKEN = {REPLACEMENT}'
                )
            elif "API_TOKEN = '" in content:
                content = content.replace(
                    f"API_TOKEN = '{TOKEN_TO_REPLACE}'",
                    f'API_TOKEN = {REPLACEMENT}'
                )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

