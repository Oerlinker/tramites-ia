from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TipoElemento(str, Enum):
    ACCION = "accion"
    DECISION = "decision"
    INICIO = "inicio"
    FIN = "fin"
    FORK = "fork"
    JOIN = "join"
    SWIMLANE = "swimlane"


# --- Asistente ---

class ConsultaRequest(BaseModel):
    texto: str = Field(..., min_length=5, description="Consulta del usuario sobre el trámite")
    contexto: Optional[str] = Field(None, description="Contexto adicional del flujo actual")

    model_config = {
        "json_schema_extra": {
            "example": {
                "texto": "Necesito modelar la aprobación de una solicitud de vacaciones",
                "contexto": "Empresa mediana, departamento de RRHH"
            }
        }
    }


class ElementoDiagrama(BaseModel):
    tipo: TipoElemento
    nombre: str
    descripcion: str
    swimlane: Optional[str] = None
    siguiente: Optional[list[str]] = None


class ConsultaResponse(BaseModel):
    sugerencia_principal: str
    elementos: list[ElementoDiagrama]
    swimlanes_sugeridos: list[str]
    politica_negocio: str
    notas: Optional[str] = None


# --- Analítica ---

class TramiteMetrica(BaseModel):
    nombre: str = Field(..., description="Nombre del trámite o actividad")
    duracion_promedio_horas: float = Field(..., ge=0)
    cantidad_instancias: int = Field(..., ge=0)
    tasa_rechazo: float = Field(..., ge=0, le=1, description="Proporción de rechazos (0-1)")
    responsable: Optional[str] = Field(None, description="Área o rol responsable")


class AnaliticaRequest(BaseModel):
    tramites: list[TramiteMetrica] = Field(..., min_length=1)
    periodo_dias: int = Field(30, ge=1, description="Período de análisis en días")
    objetivo_horas: Optional[float] = Field(None, description="Tiempo objetivo total del proceso en horas")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tramites": [
                    {
                        "nombre": "Recepción de solicitud",
                        "duracion_promedio_horas": 2.0,
                        "cantidad_instancias": 120,
                        "tasa_rechazo": 0.05,
                        "responsable": "Mesa de entrada"
                    },
                    {
                        "nombre": "Revisión legal",
                        "duracion_promedio_horas": 48.0,
                        "cantidad_instancias": 114,
                        "tasa_rechazo": 0.30,
                        "responsable": "Área Legal"
                    }
                ],
                "periodo_dias": 30,
                "objetivo_horas": 72.0
            }
        }
    }


class CuelloDeBottella(BaseModel):
    tramite: str
    nivel: str
    motivo: str
    impacto: str
    recomendacion: str


class AnaliticaResponse(BaseModel):
    resumen_ejecutivo: str
    duracion_total_promedio_horas: float
    cuellos_de_botella: list[CuelloDeBottella]
    tramite_critico: str
    eficiencia_general: str
    recomendaciones_swimlane: list[str]
    alertas: list[str]
