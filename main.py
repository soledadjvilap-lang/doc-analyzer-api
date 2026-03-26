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
Analiza la Factura, OC y Packing List adjuntos.

Entrega el análisis EXACTAMENTE una sola vez, siguiendo estrictamente el formato indicado.

====================
REGLAS DE VALIDACIÓN
====================

1. FACTURAS CON CEROS:
Considera coincidente el número de factura aunque varíen los ceros iniciales (ej: 004355 = 4355).

2. UNIDADES VS BULTOS:
Es correcto que la Factura indique unidades y el Packing List indique bultos (crates/pallets), siempre que la relación sea lógica.
NO marcar error por esta diferencia.
Si falta información (ej: unidades por bulto), indicar como observación.

3. CONSISTENCIA GENERAL:
Valida coherencia entre OC, SO, Invoice y PL.

4. ESTILO:
Respuesta técnica, directa, sin explicaciones innecesarias.

====================
FORMATO DE RESPUESTA (ESTRICTO)
====================

1. REVISIÓN DEL PACKING LIST (PL) Y COHERENCIA DOCUMENTAL:
- Orden de Compra (OC): [Número]. [Correcto/Error] + breve nota.
- Número de SO (Sales Order): [Número]. [Correcto/Error] + breve nota.
- Item: [Descripción y N° de Parte].
- Certificado de Origen (COO): [Aplica/No aplica] + motivo.
- Número de Factura en PL: [Número]. Validar coincidencia ignorando ceros iniciales.

2. ESTADO DE REFERENCIAS PARA ASUNTO:
(Validar brevemente Incoterm, Cliente, OC, SO, PO y PSlip)

3. OBSERVACIONES:
(Notas relevantes. Si no hay, escribir: "Sin observaciones")

ASUNTO EMAIL:
[INCOTERM] || OP DROPSHIP || [CLIENTE] || OC [N°] || FLS SO [N°] || PO [N°] (SO [N°]) || PSlip [N°] || [DESCRIPCIÓN DEL ITEM]

====================
REGLAS ESTRICTAS DE SALIDA
====================

- GENERAR LA RESPUESTA UNA SOLA VEZ
- NO repetir ningún bloque
- NO duplicar contenido
- TERMINAR inmediatamente después del ASUNTO EMAIL
- NO agregar texto adicional antes ni después
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
