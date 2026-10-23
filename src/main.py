import argparse
from pathlib import Path

import pandas as pd

from src.fuentes import fuente_desde_ruta
from src.graficos import ETIQUETAS_NUTRIENTES, generar_graficos
from src.modelo import columna_nutriente
from src.pipeline import (
    PATRON_EAN,
    buscar_producto,
    comparar_etiquetas,
    limpiar_productos,
    resumir_categorias,
    resumir_faltantes,
    verificar_conservacion,
)

NUTRIENTES = (
    "energia",
    "proteinas",
    "carbohidratos",
    "azucares",
    "grasas",
    "grasas_saturadas",
    "fibra",
    "sal",
)


def construir_parser() -> argparse.ArgumentParser:
    """Construye el analizador de argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Compara etiquetas nutricionales sintéticas por cada 100 g."
    )
    parser.add_argument("--entrada", type=Path, default=Path("data/productos.csv"))
    parser.add_argument("--categoria", help="Filtra por nombre de categoría.")
    parser.add_argument("--codigo", help="Busca y muestra un producto por código.")
    parser.add_argument("--nutriente", choices=NUTRIENTES, default="azucares")
    parser.add_argument("--salida", type=Path, default=Path("outputs"))
    parser.add_argument("--sin-graficos", action="store_true")
    return parser


def main() -> None:
    """Ejecuta el análisis de etiquetas a partir de los argumentos recibidos."""
    parser = construir_parser()
    argumentos = parser.parse_args()
    if argumentos.codigo is not None:
        argumentos.codigo = argumentos.codigo.strip()
        if not PATRON_EAN.fullmatch(argumentos.codigo):
            parser.error("el código debe tener 8 o 13 dígitos")
    try:
        registros = fuente_desde_ruta(argumentos.entrada).cargar(argumentos.entrada)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.error(f"No se pudo leer la entrada '{argumentos.entrada}': {error}")

    productos, rechazos = limpiar_productos(registros)
    verificar_conservacion(registros, productos, rechazos)
    if argumentos.codigo is not None:
        producto = buscar_producto(productos, argumentos.codigo)
        if producto is None:
            parser.error(
                f"No se encontró el producto con código {argumentos.codigo}"
            )
        print(f"Código: {producto.codigo}")
        print(f"Nombre: {producto.nombre}")
        print(f"Categoría: {producto.categoria}")
        for nutriente in NUTRIENTES:
            columna = columna_nutriente(nutriente)
            valor = getattr(producto, columna)
            nombre, unidad = ETIQUETAS_NUTRIENTES[nutriente]
            texto_valor = (
                "no disponible" if valor is None else f"{valor:g} {unidad}"
            )
            print(f"{nombre}: {texto_valor}")
        return

    faltantes = resumir_faltantes(
        [producto.como_registro() for producto in productos]
    )
    resumen_categorias = resumir_categorias(productos)
    comparacion = comparar_etiquetas(
        productos, argumentos.categoria, argumentos.nutriente
    )
    if comparacion.empty:
        raise SystemExit("No hay productos válidos para los filtros indicados.")

    argumentos.salida.mkdir(parents=True, exist_ok=True)
    comparacion.to_csv(
        argumentos.salida / "comparacion.csv",
        index=False,
        na_rep="no disponible",
    )
    pd.DataFrame(rechazos, columns=["registro", "codigo", "motivo"]).to_csv(
        argumentos.salida / "rechazos.csv", index=False
    )
    pd.DataFrame(faltantes).to_csv(
        argumentos.salida / "faltantes.csv", index=False
    )
    pd.DataFrame(resumen_categorias).to_csv(
        argumentos.salida / "resumen_categorias.csv",
        index=False,
        na_rep="no disponible",
    )
    if not argumentos.sin_graficos:
        generar_graficos(
            comparacion,
            faltantes,
            argumentos.salida,
            argumentos.nutriente,
            argumentos.categoria,
            resumen_categorias,
            productos,
            rechazos,
        )

    print(f"Registros leídos: {len(registros)}")
    print(f"Productos válidos: {len(productos)}")
    print(f"Registros rechazados: {len(rechazos)}")
    print(f"Productos comparados: {len(comparacion)}")
    print(f"\nOrdenados por {argumentos.nutriente} (menor a mayor):")
    columna = columna_nutriente(argumentos.nutriente)
    print(
        comparacion[["codigo", "nombre", "categoria", columna]]
        .fillna("no disponible")
        .to_string(index=False)
    )
    print(f"\nResultados guardados en: {argumentos.salida}")


if __name__ == "__main__":
    main()
