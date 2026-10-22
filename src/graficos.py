from pathlib import Path

import pandas as pd

from src.modelo import columna_nutriente

ETIQUETAS_NUTRIENTES = {
    "energia": ("Energía", "kcal/100 g"),
    "proteinas": ("Proteínas", "g/100 g"),
    "carbohidratos": ("Carbohidratos", "g/100 g"),
    "azucares": ("Azúcares", "g/100 g"),
    "grasas": ("Grasas", "g/100 g"),
    "grasas_saturadas": ("Grasas saturadas", "g/100 g"),
    "fibra": ("Fibra", "g/100 g"),
    "sal": ("Sal", "g/100 g"),
}


def generar_graficos(
    comparacion: pd.DataFrame,
    faltantes: list[dict],
    salida: Path,
    nutriente: str,
    categoria: str | None,
    cantidad_productos: int,
    total_validos: int,
) -> None:
    """Genera gráficos de comparación nutricional y datos faltantes."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    salida.mkdir(parents=True, exist_ok=True)
    nombre_nutriente, unidad = ETIQUETAS_NUTRIENTES[nutriente]
    columna = columna_nutriente(nutriente)
    datos = comparacion.dropna(subset=[columna]).nsmallest(10, columna)
    datos = datos.sort_values(columna, ascending=True)
    categorias = sorted(comparacion["categoria"].unique())
    paleta = dict(zip(categorias, plt.get_cmap("tab10").colors))
    etiquetas = (
        datos["nombre"]
        if len(categorias) == 1
        else datos["nombre"] + " (" + datos["categoria"] + ")"
    )
    figura, eje = plt.subplots(figsize=(9, max(4, len(datos) * 0.38)))
    if datos.empty:
        eje.text(0.5, 0.5, "No disponible", ha="center", va="center")
    else:
        barras = eje.barh(
            etiquetas,
            datos[columna],
            color=[paleta[categoria_producto] for categoria_producto in datos["categoria"]],
        )
        eje.invert_yaxis()
        eje.bar_label(barras, labels=[f"{valor:g}" for valor in datos[columna]], padding=3)
        if len(categorias) > 1:
            eje.legend(
                handles=[
                    Patch(facecolor=paleta[nombre], label=nombre)
                    for nombre in categorias
                ],
                title="Categoría",
            )
        maximo = float(datos[columna].max())
        eje.set_xlim(right=maximo * 1.15 if maximo else 1)
    contexto = categoria or "todas las categorías"
    eje.set_title(
        f"Menores valores de {nombre_nutriente} — {contexto} "
        f"({cantidad_productos} productos; muestra de {len(datos)})"
    )
    eje.set_xlabel(unidad)
    eje.set_ylabel("")
    figura.tight_layout()
    figura.savefig(salida / "grafico_comparacion.png", dpi=150)
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
    eje.set_title(
        f"Azúcares y grasas — {categoria or 'todas las categorías'} "
        f"({len(puntos)} productos con ambos datos)"
    )
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
    eje.set_title(
        "Datos no disponibles por campo — todas las categorías "
        f"({total_validos} productos válidos)"
    )
    eje.set_xlabel("Cantidad de registros")
    eje.set_ylabel("Campo")
    figura.tight_layout()
    figura.savefig(salida / "grafico_datos_faltantes.png", dpi=150)
    plt.close(figura)
