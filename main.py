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
Actúa como un Especialista en Logística Internacional y Comercio Exterior. Tu tarea es auditar un set de documentos (Factura, Orden de Compra y Packing List) para asegurar la coherencia en la cadena de despacho.

====================
INSTRUCCIONES DE ANÁLISIS
====================

1. VALIDACIÓN DE REFERENCIAS
- Cruza los datos de la Factura, OC y el Packing List (PL). 
- Verifica especialmente que el número de la Factura, FLS SO, PO y PSlip estén correctamente citados en el PL manual.

2. UNIDADES VS EMBALAJE (CRÍTICO)
- La Factura y la OC indican la cantidad de UNIDADES totales vendidas.
- El Packing List indica la cantidad de BULTOS físicos (Crates, Pallets, Cajas) y el packaging.
- REGLA: No considerar como error que Unidades ≠ Bultos. Validar que la relación sea lógica (ej: 15 unidades dentro de 1 bulto).
- Solo marcar ERROR si no hay coherencia lógica o la relación es físicamente imposible.

3. PESO Y DIMENSIONES
- Evalúa si el Gross Weight (Libras/Kilos) y dimensiones son razonables para el tipo de ítem.

4. CERTIFICADO DE ORIGEN (COO)
- Basado en el 'Country of Origin' del PL:
  - Indica si aplica o no (Aplica COO: SI / NO).
  - Justificación: Si es "Made in China", no aplica para tratados USA-Chile. Si es "USA", aplica.

5. GENERACIÓN DE ASUNTO (ESTRICTO)
Genera el asunto EXACTAMENTE en este formato:
[INCOTERM] || OP DROPSHIP || [CLIENTE] || OC [N°] || FLS SO [N°] || PO [N°] (SO [N°]) || PSlip [N°] || [DESCRIPCIÓN DEL ITEM]

====================
FORMATO DE RESPUESTA (OBLIGATORIO)
====================

RESUMEN:
(Máximo 3 líneas ejecutivas)

VALIDACIONES (Usar OK / ERROR / ALERTA):
- Referencias: 
- Unidades vs Embalaje: (Validar relación unidades/bultos)
- Peso y Dimensiones: 
- Certificado de Origen: (Indicar SI/NO y motivo)

ERRORES O DISCREPANCIAS:
(Si no hay, escribir: "Ninguna")

ASUNTO EMAIL:
(Formato solicitado en una sola línea)

====================
REGLAS ESTRICTAS
====================
- Tono técnico y profesional.
- Máximo 180 palabras.
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
