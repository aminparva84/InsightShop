#!/bin/sh
# Filter script to redact Hugging Face token

if [ -f scripts/test_hf_api_simple.py ]; then
    sed -i "s/YOUR_TOKEN_HERE/YOUR_TOKEN_HERE/g" scripts/test_hf_api_simple.py
    sed -i 's/API_TOKEN = "YOUR_TOKEN_HERE"/API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "YOUR_TOKEN_HERE")/g' scripts/test_hf_api_simple.py
fi

if [ -f scripts/test_inference_client.py ]; then
    sed -i "s/YOUR_TOKEN_HERE/YOUR_TOKEN_HERE/g" scripts/test_inference_client.py
    sed -i 's/API_TOKEN = "YOUR_TOKEN_HERE"/API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "YOUR_TOKEN_HERE")/g' scripts/test_inference_client.py
fi

