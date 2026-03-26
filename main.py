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

Tu tarea es auditar un set de documentos (Factura, Orden de Compra y Packing List) para validar la coherencia documental en un despacho internacional.

====================
INSTRUCCIONES DE ANÁLISIS
====================

1. VALIDACIÓN DE REFERENCIAS
- Verifica que Invoice, SO y PO coincidan entre documentos
- Detecta inconsistencias en numeración
- Indica si falta algún documento

2. UNIDADES VS EMBALAJE
- La Factura y la OC representan cantidad total de unidades
- El Packing List representa cantidad de bultos (cajas, pallets, crates)

IMPORTANTE:
- NO considerar como error que unidades ≠ bultos
- Evaluar si la relación es razonable
- Solo marcar ERROR si:
  - no hay coherencia lógica
  - o la relación es claramente inconsistente
- Si falta información (ej: unidades por bulto), marcar ALERTA
- Indicar explícitamente si no se puede validar completamente

3. PESO Y DIMENSIONES
- Evalúa si el Gross Weight y dimensiones son razonables
- Si falta contexto suficiente → ALERTA
- Solo marcar ERROR si es claramente inconsistente

4. CERTIFICADO DE ORIGEN (COO)
- Según el "Country of Origin":
  - Aplica COO: SI / NO
  - Justificación breve
- Detectar inconsistencias (ej: indica "No aplica" pero debería aplicar)

5. GENERACIÓN DE ASUNTO
Genera el asunto EXACTAMENTE en este formato:
[INCOTERM] || OP DROPSHIP || [CLIENTE] || OC [N°] || FLS SO [N°] || PO [N°] (SO [N°]) || PSlip [N°] || [DESCRIPCIÓN DEL ITEM]

====================
FORMATO DE RESPUESTA (OBLIGATORIO)
====================

RESUMEN:
(Máximo 3 líneas, claro y ejecutivo)

VALIDACIONES:
- Referencias: OK / ERROR / ALERTA + breve explicación
- Unidades vs Embalaje: OK / ERROR / ALERTA + explicación
- Peso y Dimensiones: OK / ERROR / ALERTA + explicación
- Certificado de Origen: SI / NO / ALERTA + motivo

ERRORES CRÍTICOS:
(Lista solo errores relevantes, máximo 5)

ASUNTO EMAIL:
(Texto final en una sola línea)

====================
REGLAS ESTRICTAS
====================

- Entregar la respuesta UNA SOLA VEZ
- NO repetir secciones
- NO duplicar contenido
- NO agregar texto fuera del formato
- NO inventar datos faltantes
- Máximo 180 palabras
- Tono técnico, claro y profesional

Si falta la Orden de Compra, indícalo explícitamente en VALIDACIONES.
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
