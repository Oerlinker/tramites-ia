import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
_MODEL = "gemini-2.5-flash"


async def procesar_consulta(request) -> dict:
    prompt = f"""Eres un experto en modelado de procesos empresariales UML.
El usuario describe un proceso y debes generar elementos para un
diagrama de actividad con swimlanes.

Proceso: "{request.texto}"
{f'Contexto: {request.contexto}' if request.contexto else ''}

Responde SOLO con JSON válido, sin texto adicional ni backticks:
{{
  "elementos": [
    {{"id": "e1", "tipo": "inicio", "nombre": "Inicio", "swimlane": "Sistema", "orden": 1}},
    {{"id": "e2", "tipo": "accion", "nombre": "Nombre actividad", "swimlane": "Actor responsable", "orden": 2}},
    {{"id": "e3", "tipo": "decision", "nombre": "¿Condición?", "swimlane": "Actor", "orden": 3}},
    {{"id": "e4", "tipo": "fin", "nombre": "Fin", "swimlane": "Sistema", "orden": 4}}
  ],
  "swimlanes": ["Sistema", "Actor1", "Actor2"],
  "descripcion": "Descripción breve del proceso"
}}

Tipos válidos: inicio, accion, decision, fin, fork, join
Genera entre 5 y 8 elementos. Swimlanes = departamentos o actores reales del proceso."""

    response = _client.models.generate_content(model=_MODEL, contents=prompt)
    text = response.text.strip()


    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return json.loads(text.strip())
