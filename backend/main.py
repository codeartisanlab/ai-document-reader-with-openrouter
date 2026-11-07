from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

from scanner_service import process_document_with_ai

app = FastAPI(title="AI Document Scanner API")

# Allow requests from the Next.js frontend (running on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas for data validation
class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = 1.0
    unit_price: Optional[float] = 0.0
    total: Optional[float] = 0.0

class InvoiceData(BaseModel):
    vendor_name: Optional[str] = "Unknown"
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    items: List[LineItem] = []
    subtotal: Optional[float] = 0.0
    tax: Optional[float] = 0.0
    total_amount: Optional[float] = 0.0

@app.post("/api/scan-document", response_model=InvoiceData)
async def scan_document(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        result = process_document_with_ai(file_bytes, file.content_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="The AI failed to format output as valid JSON. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")