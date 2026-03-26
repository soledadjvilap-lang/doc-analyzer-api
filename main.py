from fastapi import FastAPI, UploadFile, File
import base64
import requests
import os

app = FastAPI()

# Endpoint de prueba
@app.get("/test")
async def test():
    return {"status": "ok"}

# 🔐 API Key desde Render
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validación
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
                        "text": """
Analiza los documentos (Factura, OC y Packing List) y entrega una revisión directa. 

====================
REGLAS CRÍTICAS
====================
1. NÚMEROS DE FACTURA: Considera que los números coinciden aunque varíen en ceros iniciales (ej: "004355" es igual a "4355"). NO lo marques como error.
2. UNIDADES VS BULTOS: Es CORRECTO que la cantidad en Factura (unidades) sea distinta a la del PL (bultos/crates), siempre que la relación sea lógica.
3. ESTILO: No te presentes como auditor ni des introducciones sobre tu rol. Usa el saludo: "Hola Soledad. He realizado el análisis de esta carpeta de documentos..."

====================
FORMATO DE RESPUESTA (ESTRICTO)
====================

Hola Soledad. He realizado el análisis de esta carpeta de documentos. Aquí tienes el detalle de la revisión:

1. REVISIÓN DEL PACKING LIST (PL) Y COHERENCIA DOCUMENTAL:
- Orden de Compra (OC): [Número]. [Estado: Correcto/Error] + breve nota.
- Número de SO (Sales Order): [Número]. [Estado: Correcto/Error] + breve nota.
- Item: Descripción del item y Número de Parte.
- Certificado de Origen (COO): Indica si aplica o no según el "Country of Origin" del PL y justifica brevemente.
- Número de Factura en PL: [Número]. Confirma si coincide con la factura (ignora ceros a la izquierda).

2. VALIDACIÓN CONTRA EL ASUNTO:
Compara la información de los documentos y genera el asunto EXACTAMENTE en este formato:
[INCOTERM] || OP DROPSHIP || [CLIENTE] || OC [N°] || FLS SO [N°] || PO [N°] (SO [N°]) || PSlip [N°] || [DESCRIPCIÓN]

3. OBSERVACIONES:
(Solo si hay discrepancias críticas o datos faltantes).

ASUNTO EMAIL:
[Generar el asunto en una sola línea siguiendo el formato solicitado anteriormente]
"""
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
