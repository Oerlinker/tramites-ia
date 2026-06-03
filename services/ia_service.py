import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
_MODEL = "llama-3.3-70b-versatile"


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

    response = _client.chat.completions.create(model=_MODEL, messages=[{"role": "user", "content": prompt}])
    text = response.choices[0].message.content.strip()

    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return json.loads(text.strip())


async def sugerir_campos_formulario(descripcion_actividad: str) -> dict:
    prompt = f"""Eres un experto en diseño de formularios empresariales.
Dada la descripción de una actividad empresarial, sugiere los campos necesarios para un formulario.

Actividad: "{descripcion_actividad}"

Responde SOLO con JSON válido, sin texto adicional ni backticks:
{{
  "campos": [
    {{"nombre": "nombre_campo", "etiqueta": "Etiqueta visible", "tipo": "texto", "requerido": true, "placeholder": "Texto de ejemplo"}}
  ]
}}

Tipos válidos: "texto", "numero", "fecha", "select", "textarea", "email", "telefono"
Genera entre 3 y 8 campos relevantes para la actividad descrita."""

    response = _client.chat.completions.create(model=_MODEL, messages=[{"role": "user", "content": prompt}])
    text = response.choices[0].message.content.strip()

    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return json.loads(text.strip())


async def audio_a_formulario(audio_bytes: bytes, filename: str) -> dict:
    transcripcion = _client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=(filename, audio_bytes, "audio/webm"),
        language="es"
    )
    campos = await sugerir_campos_formulario(transcripcion.text)
    return {"transcripcion": transcripcion.text, "campos": campos.get("campos", [])}


async def recomendar_politica(descripcion_tramite: str, politicas_disponibles: list) -> dict:
    politicas_str = json.dumps(politicas_disponibles, ensure_ascii=False)
    prompt = f"""Eres un experto en gestión de trámites y políticas empresariales.
Dado un trámite y una lista de políticas disponibles, determina cuál política es la más adecuada.

Trámite: "{descripcion_tramite}"

Políticas disponibles:
{politicas_str}

Responde SOLO con JSON válido, sin texto adicional ni backticks:
{{
  "politica_id": "id_de_la_politica",
  "politica_nombre": "Nombre de la política",
  "confianza": 0.95,
  "razon": "Explicación breve de por qué esta política es la más adecuada"
}}

El campo "confianza" debe ser un número entre 0.0 y 1.0."""

    response = _client.chat.completions.create(model=_MODEL, messages=[{"role": "user", "content": prompt}])
    text = response.choices[0].message.content.strip()

    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return json.loads(text.strip())
