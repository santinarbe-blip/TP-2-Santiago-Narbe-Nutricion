import contextlib
import csv
import io
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.generar_datos import generar_registros
from src.main import main
from src.pipeline import (
    buscar_producto,
    comparar_etiquetas,
    limpiar_productos,
    normalizar_ficha,
    resumir_faltantes,
    verificar_conservacion,
)


class PipelineNutricionalTests(unittest.TestCase):
    def test_comparacion_ordena_y_filtra_categoria(self):
        productos, rechazos = limpiar_productos(generar_registros())
        tabla = comparar_etiquetas(productos, "Snacks", "azucares")

        self.assertEqual(len(productos), 60)
        self.assertEqual(len(rechazos), 2)
        self.assertEqual(len(tabla), 12)
        self.assertTrue(tabla["azucares_g_100g"].is_monotonic_increasing)
        self.assertEqual(set(tabla["categoria"]), {"Snacks"})

    def test_buscar_producto_devuelve_producto_por_codigo(self):
        productos, _ = limpiar_productos(generar_registros())

        encontrado = buscar_producto(productos, " 2000000000001 ")

        self.assertIsNotNone(encontrado)
        self.assertEqual(encontrado.codigo, "2000000000001")

    def test_buscar_producto_inexistente_devuelve_none(self):
        productos, _ = limpiar_productos(generar_registros())

        self.assertIsNone(buscar_producto(productos, "99999999"))

    def test_verificar_conservacion_con_registros_generados(self):
        registros = generar_registros()
        productos, rechazos = limpiar_productos(registros)

        verificar_conservacion(registros, productos, rechazos)
        self.assertEqual(len(registros), len(productos) + len(rechazos))

    def test_verificar_conservacion_rechaza_conteos_inconsistentes(self):
        with self.assertRaisesRegex(ValueError, "No se conserva la cantidad"):
            verificar_conservacion([{}], [], [])

    def test_filas_invalidas_y_codigos_duplicados_se_rechazan(self):
        registros = generar_registros()[:2]
        registros.append(dict(registros[0]))
        productos, rechazos = limpiar_productos(registros)

        self.assertEqual(len(productos), 2)
        self.assertEqual(rechazos[0]["motivo"], "código duplicado")
        self.assertEqual(rechazos[0]["registro"], 3)
        self.assertNotIn("fila", rechazos[0])

    def test_codigo_de_siete_digitos_se_rechaza(self):
        registro = dict(generar_registros()[0])
        registro["codigo"] = "1234567"

        productos, rechazos = limpiar_productos([registro])

        self.assertEqual(productos, [])
        self.assertIn("8 o 13 dígitos", rechazos[0]["motivo"])

    def test_codigo_con_digitos_arabigo_indicos_se_rechaza(self):
        registro = dict(generar_registros()[0])
        registro["codigo"] = "١٢٣٤٥٦٧٨٩٠١٢٣"

        with self.assertRaisesRegex(ValueError, "8 o 13 dígitos"):
            normalizar_ficha(registro)

    def test_azucares_mayores_que_carbohidratos_se_rechazan(self):
        registro = dict(generar_registros()[0])
        registro["carbohidratos_g_100g"] = 10
        registro["azucares_g_100g"] = 11

        productos, rechazos = limpiar_productos([registro])

        self.assertEqual(productos, [])
        self.assertEqual(
            rechazos[0]["motivo"], "azúcares no pueden superar carbohidratos"
        )

    def test_valor_negativo_se_rechaza(self):
        registro = dict(generar_registros()[0])
        registro["proteinas_g_100g"] = -1

        productos, rechazos = limpiar_productos([registro])

        self.assertEqual(productos, [])
        self.assertIn("fuera del rango permitido", rechazos[0]["motivo"])

    def test_nutriente_mayor_que_cien_se_rechaza(self):
        registro = dict(generar_registros()[0])
        registro["fibra_g_100g"] = 101

        productos, rechazos = limpiar_productos([registro])

        self.assertEqual(productos, [])
        self.assertIn("no puede superar 100 g/100 g", rechazos[0]["motivo"])

    def test_obtener_nutriente_desconocido_lanza_error(self):
        producto = normalizar_ficha(generar_registros()[0])

        with self.assertRaisesRegex(ValueError, "Nutriente desconocido: vitamina_c"):
            producto.obtener_nutriente("vitamina_c")

    def test_como_registro_coincide_con_asdict(self):
        producto = normalizar_ficha(generar_registros()[0])

        self.assertEqual(producto.como_registro(), asdict(producto))

    def test_conteo_de_faltantes_excluye_registros_rechazados(self):
        registros = [dict(registro) for registro in generar_registros()[:2]]
        for registro in registros:
            registro["proteinas_g_100g"] = ""
        registros[1]["codigo"] = "1234567"

        with tempfile.TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "productos.csv"
            salida = Path(directorio) / "outputs"
            with ruta_csv.open("w", newline="", encoding="utf-8") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=registros[0].keys())
                escritor.writeheader()
                escritor.writerows(registros)

            with (
                patch(
                    "sys.argv",
                    [
                        "main",
                        "--entrada",
                        str(ruta_csv),
                        "--salida",
                        str(salida),
                        "--sin-graficos",
                    ],
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                main()

            faltantes = pd.read_csv(salida / "faltantes.csv")
            rechazos = pd.read_csv(salida / "rechazos.csv")

        self.assertEqual(len(rechazos), 1)
        self.assertEqual(rechazos.loc[0, "registro"], 2)
        self.assertNotIn("fila", rechazos.columns)
        self.assertEqual(
            faltantes.loc[
                faltantes["campo"] == "proteinas_g_100g", "faltantes"
            ].item(),
            1,
        )

    def test_nutrientes_ausentes_se_conservan_como_no_disponibles(self):
        registro = dict(generar_registros()[0])
        registro["azucares_g_100g"] = ""
        productos, rechazos = limpiar_productos([registro])
        tabla = comparar_etiquetas(productos, None, "azucares")
        faltantes = resumir_faltantes([registro])

        self.assertEqual(rechazos, [])
        self.assertIsNone(productos[0].azucares_g_100g)
        self.assertTrue(pd.isna(tabla.loc[0, "azucares_g_100g"]))
        self.assertEqual(
            next(item["faltantes"] for item in faltantes if item["campo"] == "azucares_g_100g"),
            1,
        )


if __name__ == "__main__":
    unittest.main()
