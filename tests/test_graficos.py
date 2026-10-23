import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.generar_datos import generar_registros
from src.graficos import COLORES_CATEGORIA, generar_graficos
from src.pipeline import normalizar_ficha


class GraficosTests(unittest.TestCase):
    def setUp(self):
        """Prepara el backend y captura los ejes creados por cada gráfico."""
        self.subplots_original = plt.subplots
        self.ejes = []

        def registrar_subplot(*args, **kwargs):
            figura, eje = self.subplots_original(*args, **kwargs)
            self.ejes.append(eje)
            return figura, eje

        self.subplots_patcher = patch(
            "matplotlib.pyplot.subplots", side_effect=registrar_subplot
        )
        self.subplots_patcher.start()

    def tearDown(self):
        """Cierra las figuras abiertas y restaura el generador de subplots."""
        self.subplots_patcher.stop()
        plt.close("all")

    def _generar(self, comparacion, salida):
        registros = [dict(registro) for registro in generar_registros()[:2]]
        categorias = (
            comparacion["categoria"].dropna().unique()
            if "categoria" in comparacion
            else []
        )
        if len(categorias) == 1:
            registros[0]["categoria"] = categorias[0]
            registros[1]["categoria"] = categorias[0]
        else:
            registros[0]["categoria"] = "Bebidas"
            registros[1]["categoria"] = "Snacks"
        registros[0]["sal_g_100g"] = 0.8
        registros[1]["sal_g_100g"] = 0.2
        productos = [normalizar_ficha(registro) for registro in registros]
        resumen_categorias = [
            {
                "categoria": "Bebidas",
                "azucares_g_100g": 2.5,
                "fibra_g_100g": 0.5,
                "proteinas_g_100g": 3.0,
            },
            {
                "categoria": "Snacks",
                "azucares_g_100g": 6.0,
                "fibra_g_100g": 2.0,
                "proteinas_g_100g": 5.0,
            },
        ]
        generar_graficos(
            comparacion,
            [{"campo": "sal_g_100g", "faltantes": 0}],
            salida,
            "sal",
            None,
            resumen_categorias,
            productos,
            [{"motivo": "código inválido"}],
        )

    def test_genera_los_seis_archivos_de_graficos(self):
        """Comprueba los seis archivos y el contenido del gráfico comparativo."""
        comparacion = pd.DataFrame(
            [
                {
                    "nombre": "Producto B",
                    "categoria": "Bebidas",
                    "sal_g_100g": 0.8,
                    "azucares_g_100g": 2.0,
                    "grasas_g_100g": 1.0,
                },
                {
                    "nombre": "Producto A",
                    "categoria": "Snacks",
                    "sal_g_100g": 0.2,
                    "azucares_g_100g": 3.0,
                    "grasas_g_100g": 2.0,
                },
            ]
        )
        esperados = {
            "grafico_comparacion.png",
            "grafico_azucares_vs_grasas.png",
            "grafico_datos_faltantes.png",
            "grafico_promedios_categoria.png",
            "grafico_distribucion_categoria.png",
            "grafico_rechazos_por_motivo.png",
        }

        with tempfile.TemporaryDirectory() as directorio:
            salida = Path(directorio)
            self._generar(comparacion, salida)

            self.assertEqual(
                {archivo.name for archivo in salida.iterdir()}, esperados
            )

        eje = self.ejes[0]
        self.assertIn("Sal", eje.get_title())
        self.assertIn("todas las categorías", eje.get_title())
        self.assertIn("2 productos", eje.get_title())
        self.assertEqual(eje.get_ylabel(), "")
        self.assertEqual(list(eje.containers[0].datavalues), [0.2, 0.8])
        self.assertEqual(
            {texto.get_text() for texto in eje.get_legend().get_texts()},
            {"Bebidas", "Snacks"},
        )
        self.assertIn("0.2", {texto.get_text() for texto in eje.texts})
        colores_barras = [
            tuple(parche.get_facecolor()) for parche in eje.containers[0]
        ]
        self.assertEqual(
            colores_barras,
            [
                plt.matplotlib.colors.to_rgba(COLORES_CATEGORIA["Snacks"]),
                plt.matplotlib.colors.to_rgba(COLORES_CATEGORIA["Bebidas"]),
            ],
        )
        self.assertEqual(
            [
                tuple(coleccion.get_facecolors()[0])
                for coleccion in self.ejes[1].collections
            ],
            [
                plt.matplotlib.colors.to_rgba(
                    COLORES_CATEGORIA["Bebidas"], alpha=0.8
                ),
                plt.matplotlib.colors.to_rgba(
                    COLORES_CATEGORIA["Snacks"], alpha=0.8
                ),
            ],
        )
        self.assertEqual(len(self.ejes[3].containers), 3)
        self.assertEqual(list(self.ejes[3].containers[0].datavalues), [2.5, 6.0])
        self.assertIn("Distribución de Sal", self.ejes[4].get_title())
        self.assertGreaterEqual(len(self.ejes[4].lines), 12)
        self.assertEqual(
            [etiqueta.get_text() for etiqueta in self.ejes[4].get_xticklabels()],
            ["Snacks\n(n=1)", "Bebidas\n(n=1)"],
        )
        self.assertEqual(
            [tuple(caja.get_facecolor()) for caja in self.ejes[4].patches],
            [
                plt.matplotlib.colors.to_rgba(COLORES_CATEGORIA["Snacks"]),
                plt.matplotlib.colors.to_rgba(COLORES_CATEGORIA["Bebidas"]),
            ],
        )
        self.assertEqual(
            [
                tuple(coleccion.get_facecolors()[0])
                for coleccion in self.ejes[4].collections
            ],
            [
                plt.matplotlib.colors.to_rgba(COLORES_CATEGORIA["Snacks"]),
                plt.matplotlib.colors.to_rgba(COLORES_CATEGORIA["Bebidas"]),
            ],
        )
        self.assertIn("1 registros", self.ejes[5].get_title())
        self.assertEqual(list(self.ejes[5].containers[0].datavalues), [1])

    def test_dispersion_sin_filtro_muestra_todas_las_categorias(self):
        """Comprueba que el título de dispersión conserva el contexto global."""
        comparacion = pd.DataFrame(
            [
                {
                    "nombre": "Producto B",
                    "categoria": "Bebidas",
                    "sal_g_100g": 0.8,
                    "azucares_g_100g": 2.0,
                    "grasas_g_100g": 1.0,
                },
                {
                    "nombre": "Producto A",
                    "categoria": "Snacks",
                    "sal_g_100g": 0.2,
                    "azucares_g_100g": 3.0,
                    "grasas_g_100g": 2.0,
                },
            ]
        )
        with tempfile.TemporaryDirectory() as directorio:
            self._generar(comparacion, Path(directorio))

        titulo = self.ejes[1].get_title()
        self.assertIn("todas las categorías", titulo)
        self.assertNotIn("Snacks", titulo)
        self.assertNotIn("Bebidas", titulo)

    def test_categoria_desconocida_usa_gris_y_jitter_es_determinista(self):
        comparacion = pd.DataFrame(
            [
                {
                    "nombre": f"Producto {indice}",
                    "categoria": "Nueva",
                    "sal_g_100g": indice,
                    "azucares_g_100g": indice,
                    "grasas_g_100g": indice,
                }
                for indice in range(1, 4)
            ]
        )
        with tempfile.TemporaryDirectory() as directorio:
            self._generar(comparacion, Path(directorio))
        offsets_primera_ejecucion = self.ejes[4].collections[0].get_offsets().copy()
        color_caja = tuple(self.ejes[4].patches[0].get_facecolor())

        with tempfile.TemporaryDirectory() as directorio:
            self._generar(comparacion, Path(directorio))
        offsets_segunda_ejecucion = self.ejes[10].collections[0].get_offsets()

        self.assertEqual(
            color_caja, plt.matplotlib.colors.to_rgba(COLORES_CATEGORIA["desconocida"])
        )
        self.assertEqual(
            offsets_primera_ejecucion.tolist(),
            offsets_segunda_ejecucion.tolist(),
        )

    def test_comparacion_vacia_o_con_nulos_no_falla(self):
        """Comprueba que datos vacíos o nulos generan gráficos sin errores."""
        comparaciones = (
            pd.DataFrame(),
            pd.DataFrame(
                [
                    {
                        "nombre": "Producto sin datos",
                        "categoria": "Snacks",
                        "sal_g_100g": None,
                        "azucares_g_100g": None,
                        "grasas_g_100g": None,
                    }
                ]
            ),
        )
        for comparacion in comparaciones:
            with self.subTest(vacia=comparacion.empty), tempfile.TemporaryDirectory() as directorio:
                self._generar(comparacion, Path(directorio))
                self.assertTrue(
                    (Path(directorio) / "grafico_comparacion.png").is_file()
                )
                self.assertTrue(
                    (Path(directorio) / "grafico_azucares_vs_grasas.png").is_file()
                )


if __name__ == "__main__":
    unittest.main()
