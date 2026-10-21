from abc import ABC, abstractmethod
import json
from pathlib import Path

import pandas as pd


class FuenteDatos(ABC):
    @abstractmethod
    def cargar(self, ruta: Path) -> list[dict]:
        """Devuelve registros con la misma representación de diccionarios."""


class FuenteCSV(FuenteDatos):
    def cargar(self, ruta: Path) -> list[dict]:
        tabla = pd.read_csv(ruta, dtype={"codigo": str}, keep_default_na=False)
        return tabla.to_dict(orient="records")


class FuenteJSON(FuenteDatos):
    def cargar(self, ruta: Path) -> list[dict]:
        with ruta.open(encoding="utf-8") as archivo:
            registros = json.load(archivo)
        if not isinstance(registros, list) or not all(
            isinstance(registro, dict) for registro in registros
        ):
            raise ValueError("El JSON debe contener una lista de objetos.")
        return registros


def fuente_desde_ruta(ruta: Path) -> FuenteDatos:
    extension = ruta.suffix.lower()
    if extension == ".csv":
        return FuenteCSV()
    if extension == ".json":
        return FuenteJSON()
    raise ValueError("El formato de entrada debe ser CSV o JSON.")