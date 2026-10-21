import math
import re

import pandas as pd

from src.modelo import ProductoNutricional

CAMPOS_NUMERICOS = (
    "energia_kcal_100g",
    "proteinas_g_100g",
    "carbohidratos_g_100g",
    "azucares_g_100g",
    "grasas_g_100g",
    "grasas_saturadas_g_100g",
    "fibra_g_100g",
    "sal_g_100g",
)
CAMPOS_IDENTIFICACION = ("codigo", "nombre", "categoria")
PATRON_EAN = re.compile(r"(?:\d{8}|\d{13})\Z")


def normalizar_ficha(registro: dict) -> ProductoNutricional:
    faltantes = [campo for campo in CAMPOS_IDENTIFICACION if campo not in registro]
    if faltantes:
        raise ValueError(f"faltan campos obligatorios: {', '.join(faltantes)}")

    codigo = str(registro["codigo"]).strip()
    nombre = str(registro["nombre"]).strip()
    categoria = str(registro["categoria"]).strip()
    if not PATRON_EAN.fullmatch(codigo):
        raise ValueError("el código debe tener 8 o 13 dígitos")
    if not nombre or not categoria:
        raise ValueError("nombre y categoría no pueden estar vacíos")

    valores = {}
    for campo in CAMPOS_NUMERICOS:
        dato = registro.get(campo)
        if dato is None or (isinstance(dato, str) and not dato.strip()):
            valores[campo] = None
            continue
        try:
            valor = float(dato)
        except (TypeError, ValueError):
            raise ValueError(f"{campo} debe ser numérico") from None
        if not math.isfinite(valor):
            raise ValueError(f"{campo} debe ser un valor finito")
        if valor < 0 or valor > 900:
            raise ValueError(f"{campo} está fuera del rango permitido")
        if campo.endswith("_g_100g") and valor > 100:
            raise ValueError(f"{campo} no puede superar 100 g/100 g")
        valores[campo] = valor

    azucares = valores["azucares_g_100g"]
    carbohidratos = valores["carbohidratos_g_100g"]
    if azucares is not None and carbohidratos is not None and azucares > carbohidratos:
        raise ValueError("azúcares no pueden superar carbohidratos")
    grasas_saturadas = valores["grasas_saturadas_g_100g"]
    grasas = valores["grasas_g_100g"]
    if (
        grasas_saturadas is not None
        and grasas is not None
        and grasas_saturadas > grasas
    ):
        raise ValueError("grasas saturadas no pueden superar grasas totales")
    return ProductoNutricional(codigo, nombre, categoria, **valores)


def limpiar_productos(registros: list[dict]) -> tuple[list[ProductoNutricional], list[dict]]:
    productos = []
    rechazos = []
    codigos_vistos = set()
    for numero_fila, registro in enumerate(registros, start=2):
        codigo = str(registro.get("codigo", "")).strip()
        try:
            producto = normalizar_ficha(registro)
            if producto.codigo in codigos_vistos:
                raise ValueError("código duplicado")
        except ValueError as error:
            rechazos.append(
                {"fila": numero_fila, "codigo": codigo, "motivo": str(error)}
            )
            continue
        productos.append(producto)
        codigos_vistos.add(producto.codigo)
    return productos, rechazos


def comparar_etiquetas(
    productos: list[ProductoNutricional], categoria: str | None, nutriente: str
) -> pd.DataFrame:
    columna = "energia_kcal_100g" if nutriente == "energia" else f"{nutriente}_g_100g"
    registros = [producto.como_registro() for producto in productos]
    tabla = pd.DataFrame(registros)
    if tabla.empty:
        return tabla
    if categoria:
        tabla = tabla[tabla["categoria"].str.casefold() == categoria.casefold()]
    return tabla.sort_values(
        columna, ascending=True, na_position="last"
    ).reset_index(drop=True)


def resumir_faltantes(registros: list[dict]) -> list[dict]:
    campos = (*CAMPOS_IDENTIFICACION, *CAMPOS_NUMERICOS)
    resumen = []
    for campo in campos:
        cantidad = sum(
            registro.get(campo) is None
            or (isinstance(registro.get(campo), str) and not registro[campo].strip())
            for registro in registros
        )
        resumen.append({"campo": campo, "faltantes": cantidad})
    return resumen


def resumir_categorias(productos: list[ProductoNutricional]) -> list[dict]:
    tabla = pd.DataFrame([producto.como_registro() for producto in productos])
    if tabla.empty:
        return []
    columnas = ["energia_kcal_100g", "azucares_g_100g", "proteinas_g_100g", "fibra_g_100g", "sal_g_100g"]
    resumen = tabla.groupby("categoria", as_index=False)[columnas].mean()
    return resumen.round(2).to_dict(orient="records")