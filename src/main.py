import argparse
from pathlib import Path

import pandas as pd

from src.fuentes import fuente_desde_ruta
from src.modelo import columna_nutriente
from src.pipeline import (
    comparar_etiquetas,
    limpiar_productos,
    resumir_categorias,
    resumir_faltantes,
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


def generar_graficos(
    comparacion: pd.DataFrame, faltantes: list[dict], salida: Path
) -> None:
    import matplotlib.pyplot as plt

    salida.mkdir(parents=True, exist_ok=True)
    for nutriente, unidad in (
        ("energia", "kcal/100 g"),
        ("azucares", "g/100 g"),
    ):
        columna = columna_nutriente(nutriente)
        datos = comparacion.dropna(subset=[columna]).nsmallest(10, columna)
        datos = datos.sort_values(columna, ascending=True)
        figura, eje = plt.subplots(figsize=(9, max(4, len(datos) * 0.38)))
        if datos.empty:
            eje.text(0.5, 0.5, "No disponible", ha="center", va="center")
        else:
            eje.barh(datos["nombre"], datos[columna], color="#287c78")
            eje.invert_yaxis()
        eje.set_title(f"Menores valores de {nutriente} por producto")
        eje.set_xlabel(unidad)
        eje.set_ylabel("Producto")
        figura.tight_layout()
        figura.savefig(salida / f"grafico_{nutriente}.png", dpi=150)
        plt.close(figura)

    figura, eje = plt.subplots(figsize=(8, 6))
    puntos = comparacion.dropna(subset=["azucares_g_100g", "grasas_g_100g"])
    for categoria, grupo in puntos.groupby("categoria"):
        eje.scatter(
            grupo["azucares_g_100g"],
            grupo["grasas_g_100g"],
            label=categoria,
            alpha=0.8,
        )
    if puntos.empty:
        eje.text(0.5, 0.5, "No disponible", ha="center", va="center")
    else:
        eje.legend(title="Categoría")
    eje.set_title("Azúcares y grasas por producto")
    eje.set_xlabel("Azúcares (g/100 g)")
    eje.set_ylabel("Grasas totales (g/100 g)")
    figura.tight_layout()
    figura.savefig(salida / "grafico_azucares_vs_grasas.png", dpi=150)
    plt.close(figura)

    faltantes_df = pd.DataFrame(faltantes)
    faltantes_df = faltantes_df[faltantes_df["faltantes"] > 0].sort_values(
        "faltantes", ascending=True
    )
    figura, eje = plt.subplots(figsize=(9, max(4, len(faltantes_df) * 0.38)))
    if faltantes_df.empty:
        eje.text(0.5, 0.5, "No hay datos faltantes", ha="center", va="center")
    else:
        etiquetas = {
            "azucares_g_100g": "Azúcares (g/100 g)",
            "sal_g_100g": "Sal (g/100 g)",
            "fibra_g_100g": "Fibra (g/100 g)",
            "proteinas_g_100g": "Proteínas (g/100 g)",
        }
        barras = eje.barh(
            faltantes_df["campo"].map(etiquetas).fillna(faltantes_df["campo"]),
            faltantes_df["faltantes"],
            color="#c76d4b",
        )
        max_faltantes = int(faltantes_df["faltantes"].max())
        eje.set_xticks(range(max_faltantes + 1))
        eje.set_xlim(right=max_faltantes + 0.5)
        eje.bar_label(barras, padding=4)
    eje.set_title("Datos no disponibles por campo")
    eje.set_xlabel("Cantidad de registros")
    eje.set_ylabel("Campo")
    figura.tight_layout()
    figura.savefig(salida / "grafico_datos_faltantes.png", dpi=150)
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
    parser = construir_parser()
    argumentos = parser.parse_args()
    try:
        registros = fuente_desde_ruta(argumentos.entrada).cargar(argumentos.entrada)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.error(f"No se pudo leer la entrada '{argumentos.entrada}': {error}")

    productos, rechazos = limpiar_productos(registros)
    faltantes = resumir_faltantes(
        [producto.como_registro() for producto in productos]
    )
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
    pd.DataFrame(resumir_categorias(productos)).to_csv(
        argumentos.salida / "resumen_categorias.csv",
        index=False,
        na_rep="no disponible",
    )
    if not argumentos.sin_graficos:
        generar_graficos(comparacion, faltantes, argumentos.salida)

    print(f"Registros leídos: {len(registros)}")
    print(f"Productos válidos: {len(productos)}")
    print(f"Filas rechazadas: {len(rechazos)}")
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
