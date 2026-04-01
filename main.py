from fastapi import FastAPI, UploadFile, File
import base64
import requests
import os
import re

app = FastAPI()

# Endpoint de prueba
@app.get("/test")
async def test():
    return {"status": "ok"}

# 🔐 API Key desde Render
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY no está configurada en Render")

# Convertir archivos a base64
def encode(file):
    return base64.b64encode(file.file.read()).decode("utf-8")

# Función para parsear respuesta
def parse_response(text):
    try:
        revision = re.search(r"1\..*?COHERENCIA DOCUMENTAL:(.*?)(?=2\.)", text, re.S)
        referencias = re.search(r"2\..*?ASUNTO:(.*?)(?=3\.)", text, re.S)
        observaciones = re.search(r"3\..*?OBSERVACIONES:(.*?)(?=ASUNTO EMAIL:)", text, re.S)
        asunto = re.search(r"ASUNTO EMAIL:(.*)", text, re.S)

        return {
            "revision": revision.group(1).strip() if revision else "",
            "referencias": referencias.group(1).strip() if referencias else "",
            "observaciones": observaciones.group(1).strip() if observaciones else "",
            "asunto": asunto.group(1).strip() if asunto else ""
        }
    except:
        return {
            "revision": text,
            "referencias": "",
            "observaciones": "",
            "asunto": ""
        }

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
Analiza la Factura, OC y Packing List adjuntos.

Entrega el análisis EXACTAMENTE una sola vez, siguiendo estrictamente el formato indicado.

====================
REGLAS DE VALIDACIÓN
====================

1. FACTURAS CON CEROS:
Considera coincidente el número aunque tenga ceros iniciales distintos.

2. UNIDADES VS BULTOS:
Factura = unidades
Packing List = bultos
Esto NO es error si es lógico.

3. CONSISTENCIA:
Validar coherencia entre OC, SO, Invoice y PL.

====================
FORMATO OBLIGATORIO
====================

1. REVISIÓN DEL PACKING LIST (PL) Y COHERENCIA DOCUMENTAL:
- Orden de Compra (OC):
- Número de SO (Sales Order):
- Item:
- Certificado de Origen (COO):
- Número de Factura en PL:

2. ESTADO DE REFERENCIAS PARA ASUNTO:
- Incoterm:
- Cliente:
- OC:
- SO:
- PO:
- PSlip:

3. OBSERVACIONES:
(Notas relevantes. Si no hay, escribir: "Sin observaciones")

FORMATO DE OBSERVACIONES (OBLIGATORIO):
- Usa viñetas con símbolo "•"
- Una idea por línea
- Máximo 5 puntos
- No usar párrafos largos
- No repetir información
- Frases cortas y claras

ASUNTO EMAIL:
[texto]

====================
REGLAS
====================

- RESPUESTA SOLO UNA VEZ
- NO repetir contenido
- TERMINAR en ASUNTO EMAIL
"""
                    },
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

    data = response.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return {"error": data}

    parsed = parse_response(text)

    return parsed
