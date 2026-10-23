from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from src.modelo import ProductoNutricional, columna_nutriente

COLORES_CATEGORIA = {
    "Cereales": "#4C78A8",
    "Bebidas": "#F58518",
    "Lácteos": "#54A24B",
    "Snacks": "#E45756",
    "Conservas": "#B279A2",
    "desconocida": "#808080",
}
NOMBRES_CAMPOS_NUTRICIONALES = {
    "energia_kcal_100g": "Energía (kcal/100 g)",
    "proteinas_g_100g": "Proteínas (g/100 g)",
    "carbohidratos_g_100g": "Carbohidratos (g/100 g)",
    "azucares_g_100g": "Azúcares (g/100 g)",
    "grasas_g_100g": "Grasas (g/100 g)",
    "grasas_saturadas_g_100g": "Grasas saturadas (g/100 g)",
    "fibra_g_100g": "Fibra (g/100 g)",
    "sal_g_100g": "Sal (g/100 g)",
}
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
    tabla = pd.DataFrame(resumen_categorias)
    figura, eje = plt.subplots(figsize=(9, 5))
    if tabla.empty:
        eje.text(0.5, 0.5, "No disponible", ha="center", va="center")
        eje.set_title("Promedios por categoría (sin datos)")
        eje.set_xlabel("Categoría")
        eje.set_ylabel("Promedio (g/100 g)")
        figura.tight_layout()
        figura.savefig(salida / "grafico_promedios_categoria.png", dpi=150)
        plt.close(figura)
        return
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
    nombre_nutriente, unidad = ETIQUETAS_NUTRIENTES[nutriente]
    columna = columna_nutriente(nutriente)
    tabla = pd.DataFrame(
        [producto.como_registro() for producto in productos],
        columns=[
            "categoria",
            "codigo",
            "nombre",
            "energia_kcal_100g",
            "proteinas_g_100g",
            "carbohidratos_g_100g",
            "azucares_g_100g",
            "grasas_g_100g",
            "grasas_saturadas_g_100g",
            "fibra_g_100g",
            "sal_g_100g",
        ],
    )
    grupos = []
    for categoria in tabla["categoria"].dropna().unique():
        grupo = tabla.loc[tabla["categoria"] == categoria, columna].dropna()
        if not grupo.empty:
            grupos.append((float(grupo.median()), categoria, grupo))
    grupos.sort(key=lambda item: (item[0], item[1]))
    valores = [grupo for _, _, grupo in grupos]
    etiquetas = [f"{categoria}\n(n={len(grupo)})" for _, categoria, grupo in grupos]

    figura, eje = plt.subplots(figsize=(9, 5))
    if valores:
        posiciones = list(range(1, len(etiquetas) + 1))
        cajas = eje.boxplot(valores, positions=posiciones, patch_artist=True)
        colores = [
            COLORES_CATEGORIA.get(categoria, COLORES_CATEGORIA["desconocida"])
            for _, categoria, _ in grupos
        ]
        for caja, color in zip(cajas["boxes"], colores):
            caja.set_facecolor(color)
        for posicion, (_, _, grupo), color in zip(posiciones, grupos, colores):
            desplazamientos = [
                ((indice % 7) - 3) * 0.025 for indice in range(len(grupo))
            ]
            eje.scatter(
                [posicion + desplazamiento for desplazamiento in desplazamientos],
                grupo,
                color=color,
                edgecolors="black",
                linewidths=0.4,
                zorder=3,
            )
        eje.set_xticks(posiciones, etiquetas)
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


def graficar_rechazos(rechazos: list[dict], salida: Path) -> None:
    """Grafica la cantidad de registros rechazados agrupados por motivo."""
    conteos = pd.Series(
        [rechazo["motivo"] for rechazo in rechazos], dtype="string"
    ).value_counts()
    figura, eje = plt.subplots(figsize=(9, max(4, len(conteos) * 0.5)))
    if conteos.empty:
        eje.text(0.5, 0.5, "No hay registros rechazados", ha="center", va="center")
    else:
        barras = eje.barh(conteos.index, conteos.values, color="#c76d4b")
        eje.invert_yaxis()
        eje.bar_label(barras, padding=4)
        eje.set_xlim(right=float(conteos.max()) * 1.2)
    eje.set_title(f"Registros rechazados por motivo ({len(rechazos)} registros)")
    eje.set_xlabel("Cantidad de registros")
    eje.set_ylabel("Motivo")
    figura.tight_layout()
    figura.savefig(salida / "grafico_rechazos_por_motivo.png", dpi=150)
    plt.close(figura)


def _graficar_comparacion(
    comparacion: pd.DataFrame,
    salida: Path,
    nutriente: str,
    categoria: str | None,
) -> None:
    nombre_nutriente, unidad = ETIQUETAS_NUTRIENTES[nutriente]
    columna = columna_nutriente(nutriente)
    if columna in comparacion:
        comparacion_grafico = comparacion.copy()
        comparacion_grafico[columna] = pd.to_numeric(
            comparacion_grafico[columna], errors="coerce"
        )
        datos = comparacion_grafico.dropna(subset=[columna]).nsmallest(
            10, columna
        )
    else:
        datos = pd.DataFrame(columns=[columna, "nombre", "categoria"])
    datos = datos.sort_values(columna, ascending=True)
    categorias = (
        sorted(comparacion["categoria"].dropna().unique())
        if "categoria" in comparacion
        else []
    )
    etiquetas_barras = (
        datos["nombre"]
        if len(categorias) == 1
        else datos["nombre"] + " (" + datos["categoria"] + ")"
    )
    figura, eje = plt.subplots(figsize=(9, max(4, len(datos) * 0.38)))
    if datos.empty:
        eje.text(0.5, 0.5, "No disponible", ha="center", va="center")
    else:
        barras = eje.barh(
            etiquetas_barras,
            datos[columna],
            color=[
                COLORES_CATEGORIA.get(
                    categoria_producto, COLORES_CATEGORIA["desconocida"]
                )
                for categoria_producto in datos["categoria"]
            ],
        )
        eje.invert_yaxis()
        eje.bar_label(barras, labels=[f"{valor:g}" for valor in datos[columna]], padding=3)
        if len(categorias) > 1:
            eje.legend(
                handles=[
                    Patch(
                        facecolor=COLORES_CATEGORIA.get(
                            nombre, COLORES_CATEGORIA["desconocida"]
                        ),
                        label=nombre,
                    )
                    for nombre in categorias
                ],
                title="Categoría",
            )
        maximo = float(datos[columna].max())
        eje.set_xlim(right=maximo * 1.15 if maximo else 1)
    contexto = categoria or "todas las categorías"
    eje.set_title(
        f"Menores valores de {nombre_nutriente} — {contexto} "
        f"({len(comparacion)} productos; muestra de {len(datos)})"
    )
    eje.set_xlabel(unidad)
    eje.set_ylabel("")
    figura.tight_layout()
    figura.savefig(salida / "grafico_comparacion.png", dpi=150)
    plt.close(figura)


def _graficar_dispersion(
    comparacion: pd.DataFrame, salida: Path, categoria: str | None
) -> None:
    figura, eje = plt.subplots(figsize=(8, 6))
    columnas_dispersion = ["azucares_g_100g", "grasas_g_100g", "categoria"]
    puntos = (
        comparacion.dropna(subset=columnas_dispersion)
        if set(columnas_dispersion).issubset(comparacion.columns)
        else pd.DataFrame(columns=columnas_dispersion)
    )
    for nombre_categoria, grupo in puntos.groupby("categoria"):
        eje.scatter(
            grupo["azucares_g_100g"],
            grupo["grasas_g_100g"],
            label=nombre_categoria,
            color=COLORES_CATEGORIA.get(
                nombre_categoria, COLORES_CATEGORIA["desconocida"]
            ),
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


def _graficar_faltantes(
    faltantes: list[dict], salida: Path, total_validos: int
) -> None:
    faltantes_df = pd.DataFrame(faltantes)
    faltantes_df = faltantes_df[faltantes_df["faltantes"] > 0].sort_values(
        "faltantes", ascending=True
    )
    figura, eje = plt.subplots(figsize=(9, max(4, len(faltantes_df) * 0.38)))
    if faltantes_df.empty:
        eje.text(0.5, 0.5, "No hay datos faltantes", ha="center", va="center")
    else:
        barras = eje.barh(
            faltantes_df["campo"].map(NOMBRES_CAMPOS_NUTRICIONALES).fillna(
                faltantes_df["campo"]
            ),
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


def generar_graficos(
    comparacion: pd.DataFrame,
    faltantes: list[dict],
    salida: Path,
    nutriente: str,
    categoria: str | None,
    resumen_categorias: list[dict],
    productos: list[ProductoNutricional],
    rechazos: list[dict],
) -> None:
    """Genera gráficos de análisis nutricional, faltantes y rechazos."""
    salida.mkdir(parents=True, exist_ok=True)
    _graficar_comparacion(comparacion, salida, nutriente, categoria)
    _graficar_dispersion(comparacion, salida, categoria)
    _graficar_faltantes(faltantes, salida, len(productos))
    graficar_promedios_categorias(resumen_categorias, len(productos), salida)
    graficar_distribucion_categorias(productos, nutriente, salida)
    graficar_rechazos(rechazos, salida)
