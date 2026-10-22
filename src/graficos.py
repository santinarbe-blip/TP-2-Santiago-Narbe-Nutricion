from pathlib import Path

import pandas as pd

from src.modelo import ProductoNutricional, columna_nutriente

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
NUTRIENTES_PROMEDIO = (
    ("azucares_g_100g", "Azúcares"),
    ("fibra_g_100g", "Fibra"),
    ("proteinas_g_100g", "Proteínas"),
)


def graficar_promedios_categorias(
    resumen_categorias: list[dict], total_validos: int, salida: Path
) -> None:
    """Grafica los promedios de azúcares, fibra y proteínas por categoría."""
    import matplotlib.pyplot as plt

    tabla = pd.DataFrame(resumen_categorias)
    figura, eje = plt.subplots(figsize=(9, 5))
    posiciones = range(len(tabla))
    ancho = 0.8 / len(NUTRIENTES_PROMEDIO)
    for indice, (columna, etiqueta) in enumerate(NUTRIENTES_PROMEDIO):
        valores = tabla[columna]
        barras = eje.bar(
            [
                posicion + (indice - (len(NUTRIENTES_PROMEDIO) - 1) / 2) * ancho
                for posicion in posiciones
            ],
            valores,
            width=ancho,
            label=etiqueta,
        )
        eje.bar_label(
            barras,
            labels=[
                f"{valor:g}" if pd.notna(valor) else "" for valor in valores
            ],
            padding=2,
        )
    eje.set_xticks(list(posiciones), tabla["categoria"])
    eje.set_title(
        "Promedios de azúcares, fibra y proteínas por categoría "
        f"({len(tabla)} categorías; {total_validos} productos)"
    )
    eje.set_xlabel("Categoría")
    eje.set_ylabel("Promedio (g/100 g)")
    eje.legend(title="Nutriente")
    figura.tight_layout()
    figura.savefig(salida / "grafico_promedios_categoria.png", dpi=150)
    plt.close(figura)


def graficar_distribucion_categorias(
    productos: list[ProductoNutricional], nutriente: str, salida: Path
) -> None:
    """Grafica la distribución del nutriente seleccionado por categoría."""
    import matplotlib.pyplot as plt

    nombre_nutriente, unidad = ETIQUETAS_NUTRIENTES[nutriente]
    columna = columna_nutriente(nutriente)
    tabla = pd.DataFrame([producto.como_registro() for producto in productos])
    valores = []
    etiquetas = []
    for categoria in sorted(tabla["categoria"].unique()):
        grupo = tabla.loc[tabla["categoria"] == categoria, columna].dropna()
        if not grupo.empty:
            valores.append(grupo)
            etiquetas.append(f"{categoria}\n(n={len(grupo)})")

    figura, eje = plt.subplots(figsize=(9, 5))
    if valores:
        eje.boxplot(valores)
        eje.set_xticks(range(1, len(etiquetas) + 1), etiquetas)
    else:
        eje.text(0.5, 0.5, "No disponible", ha="center", va="center")
    eje.set_title(
        f"Distribución de {nombre_nutriente} por categoría "
        f"({len(productos)} productos válidos)"
    )
    eje.set_xlabel("Categoría y cantidad de valores disponibles")
    eje.set_ylabel(unidad)
    figura.tight_layout()
    figura.savefig(salida / "grafico_distribucion_categoria.png", dpi=150)
    plt.close(figura)


def generar_graficos(
    comparacion: pd.DataFrame,
    faltantes: list[dict],
    salida: Path,
    nutriente: str,
    categoria: str | None,
    cantidad_productos: int,
    total_validos: int,
    resumen_categorias: list[dict],
    productos: list[ProductoNutricional],
) -> None:
    """Genera gráficos comparativos, distribuciones, promedios y faltantes."""
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
    graficar_promedios_categorias(resumen_categorias, total_validos, salida)
    graficar_distribucion_categorias(productos, nutriente, salida)
