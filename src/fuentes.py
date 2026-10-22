from abc import ABC, abstractmethod
from dataclasses import fields
import json
from pathlib import Path

import pandas as pd

from src.modelo import ProductoNutricional


CAMPOS_ESPERADOS = {campo.name for campo in fields(ProductoNutricional)}


def _validar_campos(campos: set[str], origen: str) -> None:
    faltantes = sorted(CAMPOS_ESPERADOS - campos)
    if faltantes:
        raise ValueError(
            f"Faltan columnas esperadas en {origen}: {', '.join(faltantes)}."
        )


class FuenteDatos(ABC):
    @abstractmethod
    def cargar(self, ruta: Path) -> list[dict]:
        """Devuelve registros con la misma representación de diccionarios."""


class FuenteCSV(FuenteDatos):
    def cargar(self, ruta: Path) -> list[dict]:
        tabla = pd.read_csv(ruta, dtype={"codigo": str}, keep_default_na=False)
        _validar_campos(set(tabla.columns), "el CSV")
        return tabla.to_dict(orient="records")


class FuenteJSON(FuenteDatos):
    def cargar(self, ruta: Path) -> list[dict]:
        with ruta.open(encoding="utf-8") as archivo:
            registros = json.load(archivo)
        if not isinstance(registros, list) or not all(
            isinstance(registro, dict) for registro in registros
        ):
            raise ValueError("El JSON debe contener una lista de objetos.")
        for numero_registro, registro in enumerate(registros, start=1):
            _validar_campos(set(registro), f"el registro {numero_registro} del JSON")
        return registros


def fuente_desde_ruta(ruta: Path) -> FuenteDatos:
    extension = ruta.suffix.lower()
    if extension == ".csv":
        return FuenteCSV()
    if extension == ".json":
        return FuenteJSON()
    raise ValueError("El formato de entrada debe ser CSV o JSON.")