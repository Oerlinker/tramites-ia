from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models.schemas import ConsultaRequest
from services import ia_service

router = APIRouter(prefix="/api/ia", tags=["Asistente IA"])


@router.post("/consulta")
async def consultar_asistente(request: ConsultaRequest) -> JSONResponse:
    try:
        result = await ia_service.procesar_consulta(request)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la consulta: {str(e)}")
