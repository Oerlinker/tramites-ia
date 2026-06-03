import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


class TiempoPrediccionModel:
    """Predice el tiempo estimado de una actividad en horas."""

    def __init__(self):
        self.model = None
        self.entrenado = False
        self._construir_y_entrenar()

    def _generar_datos_sinteticos(self, n: int = 50):
        rng = np.random.default_rng(42)
        orden = rng.integers(1, 11, n).astype(float)
        num_campos = rng.integers(3, 16, n).astype(float)
        hora = rng.integers(0, 24, n).astype(float)
        dia = rng.integers(0, 7, n).astype(float)

        tiempo = (
            1.0
            + orden * 0.5
            + num_campos * 0.15
            + np.where(hora < 9, 0.5, 0.0)
            + np.where(dia >= 5, 1.0, 0.0)
            + rng.normal(0, 0.3, n)
        )
        tiempo = np.clip(tiempo, 0.5, 20.0)
        X = np.column_stack([orden, num_campos, hora, dia])
        return X, tiempo

    def _construir_y_entrenar(self):
        X, y = self._generar_datos_sinteticos()
        self.model = keras.Sequential(
            [
                layers.Dense(16, activation="relu", input_shape=(4,)),
                layers.Dense(8, activation="relu"),
                layers.Dense(1, activation="linear"),
            ]
        )
        self.model.compile(optimizer="adam", loss="mse", metrics=["mae"])
        self.model.fit(X, y, epochs=100, verbose=0)
        self.entrenado = True

    def predecir_tiempo(self, orden: int, num_campos: int, hora: int, dia: int) -> float:
        X = np.array([[float(orden), float(num_campos), float(hora), float(dia)]])
        pred = self.model.predict(X, verbose=0)
        return round(float(pred[0][0]), 2)


class AnomaliaDetectorModel:
    """Detecta anomalías en tiempos de actividades usando un Autoencoder."""

    def __init__(self):
        self.model = None
        self.mean = None
        self.std = None
        self.threshold = None
        self.entrenado = False
        self._construir_y_entrenar()

    def _generar_datos_normales(self, n: int = 50):
        rng = np.random.default_rng(42)
        tiempo_esperado = rng.uniform(1.0, 10.0, n)
        tiempo_actual = tiempo_esperado * (1.0 + rng.normal(0, 0.1, n))
        return np.column_stack([tiempo_actual, tiempo_esperado])

    def _construir_y_entrenar(self):
        X = self._generar_datos_normales()
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0) + 1e-8
        X_norm = (X - self.mean) / self.std

        inputs = keras.Input(shape=(2,))
        x = layers.Dense(4, activation="relu")(inputs)
        encoded = layers.Dense(2, activation="relu")(x)
        x = layers.Dense(4, activation="relu")(encoded)
        outputs = layers.Dense(2, activation="linear")(x)

        self.model = keras.Model(inputs, outputs)
        self.model.compile(optimizer="adam", loss="mse")
        self.model.fit(X_norm, X_norm, epochs=100, verbose=0)

        reconstructed = self.model.predict(X_norm, verbose=0)
        errors = np.mean(np.square(X_norm - reconstructed), axis=1)
        self.threshold = float(np.mean(errors) + 2.0 * np.std(errors))
        self.entrenado = True

    def es_anomalia(self, tiempo_actual_horas: float, tiempo_esperado_horas: float) -> dict:
        X = np.array([[tiempo_actual_horas, tiempo_esperado_horas]])
        X_norm = (X - self.mean) / self.std
        reconstructed = self.model.predict(X_norm, verbose=0)
        error = float(np.mean(np.square(X_norm - reconstructed)))
        es_anom = error > self.threshold
        score = round(min(error / (self.threshold + 1e-8), 5.0), 4)

        if es_anom:
            if tiempo_actual_horas > tiempo_esperado_horas * 1.5:
                mensaje = "Tiempo excesivo detectado: la actividad está tardando más del esperado."
            else:
                mensaje = "Patrón anómalo detectado en los tiempos de la actividad."
        else:
            mensaje = "Tiempo dentro de parámetros normales."

        return {"es_anomalia": bool(es_anom), "score": score, "mensaje": mensaje}


class RutaPrediccionModel:
    """Predice la probabilidad de completar exitosamente un trámite."""

    def __init__(self):
        self.model = None
        self.entrenado = False
        self._construir_y_entrenar()

    def _generar_datos_sinteticos(self, n: int = 50):
        rng = np.random.default_rng(42)
        total = rng.integers(3, 16, n).astype(float)
        orden_actual = np.array(
            [rng.integers(1, int(t) + 1) for t in total], dtype=float
        )
        porcentaje = orden_actual / total
        prob_exito = np.clip(0.4 + 0.6 * porcentaje + rng.normal(0, 0.1, n), 0.0, 1.0)
        etiquetas = (prob_exito > 0.5).astype(float)
        X = np.column_stack([orden_actual, total, porcentaje])
        return X, etiquetas

    def _construir_y_entrenar(self):
        X, y = self._generar_datos_sinteticos()
        self.model = keras.Sequential(
            [
                layers.Dense(8, activation="relu", input_shape=(3,)),
                layers.Dense(4, activation="relu"),
                layers.Dense(1, activation="sigmoid"),
            ]
        )
        self.model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
        )
        self.model.fit(X, y, epochs=100, verbose=0)
        self.entrenado = True

    def predecir_exito(
        self, orden_actual: int, total_actividades: int, completadas: int
    ) -> dict:
        porcentaje = completadas / max(total_actividades, 1)
        X = np.array([[float(orden_actual), float(total_actividades), porcentaje]])
        prob = round(float(self.model.predict(X, verbose=0)[0][0]), 4)

        if prob >= 0.8:
            recomendacion = "Alta probabilidad de éxito. Continuar con el proceso normal."
        elif prob >= 0.5:
            recomendacion = "Probabilidad moderada. Revisar actividades pendientes."
        else:
            recomendacion = "Baja probabilidad de éxito. Se recomienda intervención."

        return {"probabilidad": prob, "recomendacion": recomendacion}


_tiempo_model = None
_anomalia_model = None
_ruta_model = None


def predecir_tiempo(orden: int, num_campos: int, hora: int, dia: int) -> float:
    global _tiempo_model
    if _tiempo_model is None:
        _tiempo_model = TiempoPrediccionModel()
    return _tiempo_model.predecir_tiempo(orden, num_campos, hora, dia)


def es_anomalia(tiempo_actual: float, tiempo_esperado: float) -> dict:
    global _anomalia_model
    if _anomalia_model is None:
        _anomalia_model = AnomaliaDetectorModel()
    return _anomalia_model.es_anomalia(tiempo_actual, tiempo_esperado)


def predecir_exito(orden_actual: int, total_actividades: int, completadas: int) -> dict:
    global _ruta_model
    if _ruta_model is None:
        _ruta_model = RutaPrediccionModel()
    return _ruta_model.predecir_exito(orden_actual, total_actividades, completadas)


def get_resumen_modelos() -> dict:
    return {
        "estado": "operacional",
        "modelos": {
            "prediccion_tiempo": {
                "nombre": "TiempoPrediccionModel",
                "tipo": "Regresión — Dense Sequential",
                "entrenado": _tiempo_model.entrenado if _tiempo_model else False,
                "features": ["orden_actividad", "num_campos_formulario", "hora_del_dia", "dia_semana"],
                "salida": "tiempo_estimado_horas",
            },
            "deteccion_anomalia": {
                "nombre": "AnomaliaDetectorModel",
                "tipo": "Autoencoder — Encoder-Decoder",
                "entrenado": _anomalia_model.entrenado if _anomalia_model else False,
                "threshold": round(_anomalia_model.threshold, 4) if _anomalia_model and _anomalia_model.threshold else None,
                "features": ["tiempo_actual_horas", "tiempo_esperado_horas"],
            },
            "prediccion_ruta": {
                "nombre": "RutaPrediccionModel",
                "tipo": "Clasificación Binaria — Dense Sequential",
                "entrenado": _ruta_model.entrenado if _ruta_model else False,
                "features": ["orden_actual", "total_actividades", "porcentaje_completado"],
                "salida": "probabilidad_exito",
            },
        },
    }
