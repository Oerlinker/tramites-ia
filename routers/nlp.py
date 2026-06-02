from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import ia_service

router = APIRouter(prefix="/api/ia", tags=["NLP"])


class SugerirFormularioRequest(BaseModel):
    descripcion: str


class RecomendarPoliticaRequest(BaseModel):
    descripcion: str
    politicas: list


@router.post("/sugerir-formulario")
async def sugerir_formulario(request: SugerirFormularioRequest) -> JSONResponse:
    try:
        result = await ia_service.sugerir_campos_formulario(request.descripcion)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sugerir campos del formulario: {str(e)}")


@router.post("/recomendar-politica")
async def recomendar_politica(request: RecomendarPoliticaRequest) -> JSONResponse:
    try:
        result = await ia_service.recomendar_politica(request.descripcion, request.politicas)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al recomendar política: {str(e)}")
