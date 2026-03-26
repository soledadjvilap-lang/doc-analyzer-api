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
Actúa como un Especialista en Logística Internacional.

Tu tarea es auditar documentos: Factura, Orden de Compra (OC) y Packing List (PL) para validar coherencia documental en un despacho internacional.

====================
INSTRUCCIONES
====================

1. VALIDACIÓN DE REFERENCIAS
- Verifica coherencia entre Invoice, SO y PO
- Detecta inconsistencias en numeración

2. UNIDADES VS EMBALAJE
- Factura y OC = unidades
- Packing List = bultos
- No confundir unidades con bultos
- Detecta diferencias relevantes

3. PESO Y DIMENSIONES
- Evalúa si el Gross Weight y dimensiones son razonables
- Marca inconsistencias evidentes

4. CERTIFICADO DE ORIGEN
- Según "Country of Origin":
  - Aplica COO: SI / NO
  - Justificación breve

====================
FORMATO DE RESPUESTA (OBLIGATORIO)
====================

RESUMEN:
Máximo 4 líneas claras

VALIDACIONES:
- Referencias: OK / ERROR + breve explicación
- Unidades vs Embalaje: OK / ERROR + explicación
- Peso y Dimensiones: OK / ALERTA + explicación
- Certificado de Origen: SI / NO + motivo

ERRORES CRÍTICOS:
- Lista breve (máx 5)

ASUNTO EMAIL:
[INCOTERM] || OP DROPSHIP || [CLIENTE] || OC [N°] || FLS SO [N°] || PO [N°] (SO [N°]) || PSlip [N°] || [DESCRIPCIÓN DEL ITEM]

====================
REGLAS
====================

- No repetir información
- No inventar datos faltantes
- No explicar de más
- Máximo 200 palabras
- Tono técnico y profesional

Si falta la OC, indícalo explícitamente en VALIDACIONES.
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
