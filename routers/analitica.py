from fastapi import APIRouter, HTTPException
from models.schemas import AnaliticaRequest, AnaliticaResponse
from services.analitica_service import analizar_tramites

router = APIRouter(prefix="/api/ia", tags=["Analítica IA"])


@router.post("/analitica", response_model=AnaliticaResponse)
async def analizar(request: AnaliticaRequest) -> AnaliticaResponse:
    try:
        return analizar_tramites(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar los trámites: {str(e)}")
