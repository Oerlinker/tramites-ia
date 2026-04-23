from models.schemas import (
    AnaliticaRequest,
    AnaliticaResponse,
    CuelloDeBottella,
    TramiteMetrica,
)


_UMBRAL_DURACION_ALTA = 24.0
_UMBRAL_DURACION_CRITICA = 72.0
_UMBRAL_RECHAZO_ALTO = 0.20
_UMBRAL_RECHAZO_CRITICO = 0.40


def _nivel_duracion(horas: float) -> str:
    if horas >= _UMBRAL_DURACION_CRITICA:
        return "CRÍTICO"
    if horas >= _UMBRAL_DURACION_ALTA:
        return "ALTO"
    return "NORMAL"


def _nivel_rechazo(tasa: float) -> str:
    if tasa >= _UMBRAL_RECHAZO_CRITICO:
        return "CRÍTICO"
    if tasa >= _UMBRAL_RECHAZO_ALTO:
        return "ALTO"
    return "NORMAL"


def _analizar_tramite(t: TramiteMetrica) -> CuelloDeBottella | None:
    nivel_d = _nivel_duracion(t.duracion_promedio_horas)
    nivel_r = _nivel_rechazo(t.tasa_rechazo)

    if nivel_d == "NORMAL" and nivel_r == "NORMAL":
        return None

    nivel = "CRÍTICO" if "CRÍTICO" in (nivel_d, nivel_r) else "ALTO"
    motivos = []
    recomendaciones = []

    if nivel_d != "NORMAL":
        motivos.append(f"duración promedio de {t.duracion_promedio_horas:.1f}h supera el umbral")
        recomendaciones.append("revisar el proceso interno y considerar paralelización de tareas")

    if nivel_r != "NORMAL":
        motivos.append(f"tasa de rechazo del {t.tasa_rechazo * 100:.0f}% indica criterios poco claros")
        recomendaciones.append("documentar criterios de aceptación y capacitar al responsable")

    impacto = (
        f"Afecta a {t.cantidad_instancias} instancias en el período. "
        f"Costo estimado: {t.cantidad_instancias * t.duracion_promedio_horas:.0f} horas-hombre acumuladas."
    )

    return CuelloDeBottella(
        tramite=t.nombre,
        nivel=nivel,
        motivo="; ".join(motivos).capitalize() + ".",
        impacto=impacto,
        recomendacion="; ".join(recomendaciones).capitalize() + ".",
    )


def _calcular_eficiencia(duracion_total: float, objetivo: float | None) -> str:
    if objetivo is None:
        return "Sin objetivo definido — establezca un SLA para medir la eficiencia del proceso."
    ratio = duracion_total / objetivo
    if ratio <= 1.0:
        return f"Óptimo — el proceso completa en {duracion_total:.1f}h, dentro del objetivo de {objetivo:.1f}h."
    if ratio <= 1.5:
        return (
            f"Aceptable — el proceso tarda {duracion_total:.1f}h vs objetivo de {objetivo:.1f}h "
            f"({(ratio - 1) * 100:.0f}% de desviación)."
        )
    return (
        f"Crítico — el proceso tarda {duracion_total:.1f}h vs objetivo de {objetivo:.1f}h "
        f"({(ratio - 1) * 100:.0f}% sobre el SLA). Requiere rediseño urgente."
    )


def _generar_recomendaciones_swimlane(cuellos: list[CuelloDeBottella], tramites: list[TramiteMetrica]) -> list[str]:
    recomendaciones: list[str] = []
    responsables_criticos = {
        t.responsable
        for t in tramites
        if t.responsable and _nivel_duracion(t.duracion_promedio_horas) != "NORMAL"
    }

    for responsable in responsables_criticos:
        recomendaciones.append(
            f"Revisar carga de trabajo del swimlane '{responsable}': concentra actividades con alta duración."
        )

    if len(cuellos) > 2:
        recomendaciones.append(
            "Evaluar introducción de un swimlane 'Control de Calidad' para centralizar validaciones "
            "y reducir rechazos en etapas intermedias."
        )

    recomendaciones.append(
        "Agregar un swimlane 'Sistema' para automatizar notificaciones y registros, "
        "liberando tiempo humano en transiciones rutinarias."
    )

    if any(c.nivel == "CRÍTICO" for c in cuellos):
        recomendaciones.append(
            "Considerar un swimlane 'Escalamiento' para derivar casos complejos sin bloquear el flujo principal."
        )

    return recomendaciones


def _generar_alertas(tramites: list[TramiteMetrica], duracion_total: float, objetivo: float | None) -> list[str]:
    alertas: list[str] = []

    for t in tramites:
        if t.tasa_rechazo >= _UMBRAL_RECHAZO_CRITICO:
            alertas.append(
                f"ALERTA CRÍTICA: '{t.nombre}' tiene {t.tasa_rechazo * 100:.0f}% de rechazo. "
                "Revisar políticas de admisión de inmediato."
            )

    tramites_sin_responsable = [t.nombre for t in tramites if not t.responsable]
    if tramites_sin_responsable:
        alertas.append(
            f"Sin responsable asignado: {', '.join(tramites_sin_responsable)}. "
            "Todo trámite debe tener un swimlane propietario."
        )

    if objetivo and duracion_total > objetivo * 2:
        alertas.append(
            "El proceso supera el doble del tiempo objetivo. Se recomienda auditoría completa del flujo."
        )

    return alertas


def analizar_tramites(request: AnaliticaRequest) -> AnaliticaResponse:
    duracion_total = sum(t.duracion_promedio_horas for t in request.tramites)

    cuellos = [c for t in request.tramites if (c := _analizar_tramite(t)) is not None]

    tramite_critico = max(request.tramites, key=lambda t: t.duracion_promedio_horas * (1 + t.tasa_rechazo))

    eficiencia = _calcular_eficiencia(duracion_total, request.objetivo_horas)
    recomendaciones_swimlane = _generar_recomendaciones_swimlane(cuellos, request.tramites)
    alertas = _generar_alertas(request.tramites, duracion_total, request.objetivo_horas)

    total_instancias = sum(t.cantidad_instancias for t in request.tramites)
    resumen = (
        f"Análisis de {len(request.tramites)} trámites en {request.periodo_dias} días "
        f"({total_instancias} instancias totales). "
        f"Duración acumulada promedio: {duracion_total:.1f}h. "
        f"Se identificaron {len(cuellos)} cuellos de botella "
        f"({'ninguno crítico' if not any(c.nivel == 'CRÍTICO' for c in cuellos) else 'con cuellos CRÍTICOS'})."
    )

    return AnaliticaResponse(
        resumen_ejecutivo=resumen,
        duracion_total_promedio_horas=duracion_total,
        cuellos_de_botella=cuellos,
        tramite_critico=tramite_critico.nombre,
        eficiencia_general=eficiencia,
        recomendaciones_swimlane=recomendaciones_swimlane,
        alertas=alertas,
    )
