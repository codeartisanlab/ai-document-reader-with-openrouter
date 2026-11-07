import os
import json
import base64
import requests
from dotenv import load_dotenv

# Load key from .env
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """
You are an expert OCR and document data extractor. Analyze the uploaded document, invoice, or receipt image.
Extract the relevant details and return ONLY a valid, raw JSON object matching this schema:
{
  "vendor_name": "string",
  "invoice_number": "string or null",
  "date": "YYYY-MM-DD or string",
  "items": [
    {
      "description": "string",
      "quantity": float,
      "unit_price": float,
      "total": float
    }
  ],
  "subtotal": float,
  "tax": float,
  "total_amount": float
}
Do NOT wrap output in markdown code blocks like ```json ... ```.
Do NOT include any text before or after the JSON.
Return raw JSON only.
"""

def process_document_with_ai(file_bytes: bytes, content_type: str) -> dict:
    """Encodes image bytes to base64, queries OpenRouter Vision, and parses JSON output."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is missing from .env file.")

    # Convert binary image bytes to a base64 string
    base64_image = base64.b64encode(file_bytes).decode("utf-8")
    mime_type = content_type or "image/jpeg"

    payload = {
        "model": "openrouter/auto",
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all structured information from this invoice accurately."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "AI Document Scanner"
    }

    # Call OpenRouter
    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    raw_text = response.json()["choices"][0]["message"]["content"].strip()

    # Clean markdown formatting if returned
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0]

    return json.loads(raw_text)