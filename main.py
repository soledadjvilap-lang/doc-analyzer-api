from fastapi import FastAPI, UploadFile, File
import base64
import requests
import os

app = FastAPI()

# Endpoint de prueba
@app.get("/test")
async def test():
    return {"status": "ok"}

# 🔐 API Key desde Render (variable de entorno)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validación (muy importante)
if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY no está configurada en Render")

# Función para convertir archivos a base64
def encode(file):
    return base64.b64encode(file.file.read()).decode("utf-8")

# Endpoint principal
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
                    {
                        "text": "Analiza estos documentos (invoice, packing list y purchase order). Detecta diferencias, errores y genera un resumen claro + sugerencia de email profesional."
                    },
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": invoice_b64
                        }
                    },
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": packing_b64
                        }
                    },
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": po_b64
                        }
                    },
                ]
            }
        ]
    }

    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
        json=payload
    )

    data = response.json()

    # Manejo seguro de respuesta
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        text = str(data)

    return {
        "analysis": text
    }
