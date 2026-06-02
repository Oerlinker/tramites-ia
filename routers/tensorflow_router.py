from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import tensorflow_service

router = APIRouter(prefix="/api/ia", tags=["TensorFlow IA"])


class PredecirTiempoRequest(BaseModel):
    orden: int
    num_campos: int
    hora: int
    dia: int


class DetectarAnomaliaRequest(BaseModel):
    tiempo_actual: float
    tiempo_esperado: float


class PredecirExitoRequest(BaseModel):
    orden_actual: int
    total_actividades: int
    completadas: int


@router.post("/tensorflow/predecir-tiempo")
async def predecir_tiempo(request: PredecirTiempoRequest) -> JSONResponse:
    try:
        horas = tensorflow_service.predecir_tiempo(
            request.orden, request.num_campos, request.hora, request.dia
        )
        return JSONResponse(content={"tiempo_estimado_horas": horas})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al predecir tiempo: {str(e)}")


@router.post("/tensorflow/detectar-anomalia")
async def detectar_anomalia(request: DetectarAnomaliaRequest) -> JSONResponse:
    try:
        resultado = tensorflow_service.es_anomalia(
            request.tiempo_actual, request.tiempo_esperado
        )
        return JSONResponse(content=resultado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al detectar anomalía: {str(e)}")


@router.post("/tensorflow/predecir-exito")
async def predecir_exito(request: PredecirExitoRequest) -> JSONResponse:
    try:
        resultado = tensorflow_service.predecir_exito(
            request.orden_actual, request.total_actividades, request.completadas
        )
        return JSONResponse(content=resultado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al predecir éxito: {str(e)}")


@router.get("/tensorflow/estado")
async def estado_modelos() -> JSONResponse:
    try:
        resumen = tensorflow_service.get_resumen_modelos()
        return JSONResponse(content=resumen)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado de modelos: {str(e)}")
