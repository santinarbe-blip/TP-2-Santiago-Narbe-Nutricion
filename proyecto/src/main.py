import argparse
from pathlib import Path

import pandas as pd

from src.fuentes import fuente_desde_ruta
from src.pipeline import comparar_etiquetas, limpiar_productos, resumir_categorias

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


def generar_graficos(comparacion: pd.DataFrame, salida: Path) -> None:
    import matplotlib.pyplot as plt

    salida.mkdir(parents=True, exist_ok=True)
    for nutriente in ("azucares", "sal"):
        columna = f"{nutriente}_g_100g"
        datos = comparacion.nsmallest(10, columna).sort_values(columna)
        figura, eje = plt.subplots(figsize=(9, max(4, len(datos) * 0.38)))
        eje.barh(datos["nombre"], datos[columna], color="#287c78")
        eje.set_title(f"{nutriente.capitalize()} por producto (g/100 g)")
        eje.set_xlabel("Gramos por 100 g")
        eje.set_ylabel("Producto")
        eje.invert_yaxis()
        figura.tight_layout()
        figura.savefig(salida / f"grafico_{nutriente}.png", dpi=150)
        plt.close(figura)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara etiquetas nutricionales sintéticas por cada 100 g."
    )
    parser.add_argument("--entrada", type=Path, default=Path("data/productos.csv"))
    parser.add_argument("--categoria", help="Filtra por nombre de categoría.")
    parser.add_argument("--nutriente", choices=NUTRIENTES, default="azucares")
    parser.add_argument("--salida", type=Path, default=Path("outputs"))
    parser.add_argument("--sin-graficos", action="store_true")
    return parser


def main() -> None:
    argumentos = construir_parser().parse_args()
    registros = fuente_desde_ruta(argumentos.entrada).cargar(argumentos.entrada)
    productos, rechazos = limpiar_productos(registros)
    comparacion = comparar_etiquetas(
        productos, argumentos.categoria, argumentos.nutriente
    )
    if comparacion.empty:
        raise SystemExit("No hay productos válidos para los filtros indicados.")

    argumentos.salida.mkdir(parents=True, exist_ok=True)
    comparacion.to_csv(argumentos.salida / "comparacion.csv", index=False)
    pd.DataFrame(rechazos, columns=["fila", "codigo", "motivo"]).to_csv(
        argumentos.salida / "rechazos.csv", index=False
    )
    pd.DataFrame(resumir_categorias(productos)).to_csv(
        argumentos.salida / "resumen_categorias.csv", index=False
    )
    if not argumentos.sin_graficos:
        generar_graficos(comparacion, argumentos.salida)

    print(f"Registros leídos: {len(registros)}")
    print(f"Productos válidos: {len(productos)}")
    print(f"Filas rechazadas: {len(rechazos)}")
    print(f"Productos comparados: {len(comparacion)}")
    print(f"\nOrdenados por {argumentos.nutriente} (menor a mayor):")
    print(comparacion[["codigo", "nombre", "categoria", f"{argumentos.nutriente}_g_100g"]].to_string(index=False))
    print(f"\nResultados guardados en: {argumentos.salida}")


if __name__ == "__main__":
    main()
