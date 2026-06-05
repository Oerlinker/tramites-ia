from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import base64
import io
from datetime import datetime

router = APIRouter(prefix="/api/ia", tags=["Reportes"])


class ActividadReporte(BaseModel):
    nombre: str
    estado: str
    departamento: Optional[str] = None
    responsable: Optional[str] = None
    datosFormulario: Optional[dict] = None


class ReporteRequest(BaseModel):
    tramiteId: str
    titulo: str
    estado: str
    solicitante: str
    fechaInicio: str
    fechaFin: Optional[str] = None
    actividades: list[ActividadReporte] = []
    politicaNombre: Optional[str] = None


@router.post("/generar-reporte")
async def generar_reporte(request: ReporteRequest) -> JSONResponse:
    try:
        texto = _generar_texto_reporte(request)
        pdf_bytes = _generar_pdf(request, texto)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        audio_b64 = _generar_audio(texto)
        return JSONResponse(content={
            "pdf": pdf_b64,
            "audio": audio_b64,
            "texto": texto
        })
    except Exception as e:
        raise Exception(f"Error al generar reporte: {str(e)}")


def _generar_texto_reporte(req: ReporteRequest) -> str:
    fecha_inicio = req.fechaInicio[:10] if req.fechaInicio else "N/A"
    fecha_fin = req.fechaFin[:10] if req.fechaFin else "En proceso"
    completadas = sum(1 for a in req.actividades if a.estado == "COMPLETADO")
    total = len(req.actividades)

    texto = f"""Reporte del trámite: {req.titulo}.
Solicitado por {req.solicitante}.
Estado actual: {req.estado.lower().replace('_', ' ')}.
Política aplicada: {req.politicaNombre or 'no especificada'}.
Fecha de inicio: {fecha_inicio}. Fecha de finalización: {fecha_fin}.
Se completaron {completadas} de {total} actividades.

Detalle de actividades:
"""
    for i, act in enumerate(req.actividades, 1):
        estado_texto = {
            'COMPLETADO': 'completada',
            'PENDIENTE': 'pendiente',
            'EN_PROCESO': 'en proceso',
            'RECHAZADO': 'rechazada',
            'BLOQUEADO': 'bloqueada'
        }.get(act.estado, act.estado.lower())
        texto += f"\n{i}. {act.nombre}, {estado_texto}"
        if act.departamento:
            texto += f", a cargo de {act.departamento}"

    if req.estado == "COMPLETADO":
        texto += f"\n\nEl trámite fue completado exitosamente el {fecha_fin}."
    elif req.estado == "RECHAZADO":
        texto += "\n\nEl trámite fue rechazado durante el proceso."
    else:
        texto += f"\n\nEl trámite se encuentra actualmente en proceso con {total - completadas} actividades pendientes."

    return texto


def _generar_pdf(req: ReporteRequest, texto: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    azul = HexColor('#1a237e')
    verde = HexColor('#2e7d32')
    rojo = HexColor('#c62828')
    gris = HexColor('#757575')

    titulo_style = ParagraphStyle('titulo', parent=styles['Title'],
                                  textColor=azul, fontSize=18, spaceAfter=6)
    subtitulo_style = ParagraphStyle('subtitulo', parent=styles['Normal'],
                                     textColor=gris, fontSize=10, spaceAfter=16)
    seccion_style = ParagraphStyle('seccion', parent=styles['Heading2'],
                                   textColor=azul, fontSize=12, spaceBefore=12, spaceAfter=6)

    estado_color = verde if req.estado == 'COMPLETADO' else (rojo if req.estado == 'RECHAZADO' else HexColor('#e65100'))

    story = []
    story.append(Paragraph("Sistema de Gestión de Trámites", titulo_style))
    story.append(Paragraph(f"Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitulo_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Información del Trámite", seccion_style))
    datos_tabla = [
        ["Título", req.titulo],
        ["ID", req.tramiteId],
        ["Política", req.politicaNombre or "N/A"],
        ["Solicitante", req.solicitante],
        ["Estado", req.estado],
        ["Fecha Inicio", req.fechaInicio[:10] if req.fechaInicio else "N/A"],
        ["Fecha Fin", req.fechaFin[:10] if req.fechaFin else "En proceso"],
    ]
    tabla = Table(datos_tabla, colWidths=[4*cm, 13*cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#e8eaf6')),
        ('TEXTCOLOR', (0, 0), (0, -1), azul),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e0e0e0')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, HexColor('#fafafa')]),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.5*cm))

    if req.actividades:
        story.append(Paragraph("Detalle de Actividades", seccion_style))
        act_data = [["#", "Actividad", "Estado", "Departamento"]]
        for i, act in enumerate(req.actividades, 1):
            act_data.append([
                str(i),
                act.nombre,
                act.estado,
                act.departamento or "—"
            ])
        tabla_act = Table(act_data, colWidths=[1*cm, 7*cm, 4*cm, 5*cm])
        tabla_act.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), azul),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e0e0e0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f5f5f5')]),
        ]))
        story.append(tabla_act)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _generar_audio(texto: str) -> str:
    try:
        from gtts import gTTS
        tts = gTTS(text=texto, lang='es', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return base64.b64encode(audio_buffer.read()).decode("utf-8")
    except Exception:
        return ""
