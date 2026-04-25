from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import asistente, analitica

app = FastAPI(
    title="Trámites IA",
    description="Microservicio de inteligencia artificial para gestión de trámites empresariales",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asistente.router)
app.include_router(analitica.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "servicio": "tramites-ia"}
