from fastapi import FastAPI, UploadFile, File
import base64
import requests

app = FastAPI()
@app.post("/test")
async def test():
    return {"status": "ok"}

GEMINI_API_KEY = "TU_API_KEY"

def encode(file):
    return base64.b64encode(file.file.read()).decode("utf-8")

@app.post("/analyze")
async def analyze(
    invoice: UploadFile = File(...),
    packing: UploadFile = File(...),
    po: UploadFile = File(...)
):
    invoice_b64 = encode(invoice)
    packing_b64 = encode(packing)
    po_b64 = encode(po)

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Analiza estos documentos y genera comparación + email."},
                    {"inline_data": {"mime_type": "application/pdf", "data": invoice_b64}},
                    {"inline_data": {"mime_type": "application/pdf", "data": packing_b64}},
                    {"inline_data": {"mime_type": "application/pdf", "data": po_b64}},
                ]
            }
        ]
    }

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
        json=payload
    )

    return response.json()
