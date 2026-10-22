import contextlib
import csv
import io
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.fuentes import FuenteCSV, FuenteJSON, fuente_desde_ruta
from src.generar_datos import generar_registros
from src.main import main
from src.pipeline import (
    comparar_etiquetas,
    limpiar_productos,
    normalizar_ficha,
    resumir_faltantes,
)


class PipelineNutricionalTests(unittest.TestCase):
    def test_entrada_inexistente_muestra_error_claro_sin_traceback(self):
        salida_error = io.StringIO()
        with (
            patch("sys.argv", ["main", "--entrada", "data/noexiste.csv"]),
            contextlib.redirect_stderr(salida_error),
            self.assertRaises(SystemExit) as resultado,
        ):
            main()

        self.assertEqual(resultado.exception.code, 2)
        self.assertIn("No se pudo leer la entrada 'data/noexiste.csv'", salida_error.getvalue())
        self.assertNotIn("Traceback", salida_error.getvalue())

    def test_comparacion_ordena_y_filtra_categoria(self):
        productos, rechazos = limpiar_productos(generar_registros())
        tabla = comparar_etiquetas(productos, "Snacks", "azucares")

        self.assertEqual(len(productos), 60)
        self.assertEqual(len(rechazos), 2)
        self.assertEqual(len(tabla), 12)
        self.assertTrue(tabla["azucares_g_100g"].is_monotonic_increasing)
        self.assertEqual(set(tabla["categoria"]), {"Snacks"})

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

    def test_codigo_csv_con_cero_inicial_se_conserva_como_texto(self):
        registro = dict(generar_registros()[0])
        registro["codigo"] = "01234567"
        with tempfile.TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "producto.csv"
            with ruta_csv.open("w", newline="", encoding="utf-8") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=registro.keys())
                escritor.writeheader()
                escritor.writerow(registro)

            leido = FuenteCSV().cargar(ruta_csv)[0]

        producto = normalizar_ficha(leido)
        self.assertEqual(leido["codigo"], "01234567")
        self.assertEqual(producto.codigo, "01234567")

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

    def test_json_que_no_es_una_lista_se_rechaza(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_json = Path(directorio) / "productos.json"
            ruta_json.write_text('{"producto": "ejemplo"}', encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "El JSON debe contener una lista de objetos"
            ):
                FuenteJSON().cargar(ruta_json)

    def test_csv_sin_columna_nutricional_se_rechaza_al_leer(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "productos.csv"
            ruta_csv.write_text(
                "codigo,nombre,categoria\n12345678,Producto,Snacks\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "Faltan columnas esperadas en el CSV:.*energia_kcal_100g"
            ):
                FuenteCSV().cargar(ruta_csv)

    def test_json_sin_columnas_nutricionales_se_rechaza_al_leer(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_json = Path(directorio) / "productos.json"
            ruta_json.write_text(
                json.dumps([{"codigo": "12345678", "nombre": "Producto", "categoria": "Snacks"}]),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "Faltan columnas esperadas en el registro 1 del JSON"
            ):
                FuenteJSON().cargar(ruta_json)

    def test_entrada_sin_columnas_obligatorias_muestra_error_claro(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "productos.csv"
            ruta_csv.write_text(
                "codigo,nombre,categoria\n12345678,Producto,Snacks\n",
                encoding="utf-8",
            )
            salida_error = io.StringIO()
            with (
                patch("sys.argv", ["main", "--entrada", str(ruta_csv)]),
                contextlib.redirect_stderr(salida_error),
                self.assertRaises(SystemExit) as resultado,
            ):
                main()

        self.assertEqual(resultado.exception.code, 2)
        self.assertIn("Faltan columnas esperadas", salida_error.getvalue())
        self.assertIn("energia_kcal_100g", salida_error.getvalue())
        self.assertNotIn("Traceback", salida_error.getvalue())

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

    def test_extension_no_soportada_se_rechaza(self):
        with self.assertRaisesRegex(ValueError, "formato de entrada debe ser CSV o JSON"):
            fuente_desde_ruta(Path("productos.xlsx"))

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

    def test_lecturas_csv_y_json_son_equivalentes(self):
        registros = generar_registros()
        with tempfile.TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "productos.csv"
            ruta_json = Path(directorio) / "productos.json"
            with ruta_csv.open("w", newline="", encoding="utf-8") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=registros[0].keys())
                escritor.writeheader()
                escritor.writerows(registros)
            ruta_json.write_text(json.dumps(registros), encoding="utf-8")

            csv_validos, csv_rechazos = limpiar_productos(FuenteCSV().cargar(ruta_csv))
            json_validos, json_rechazos = limpiar_productos(FuenteJSON().cargar(ruta_json))

        csv_resultado = comparar_etiquetas(csv_validos, None, "sal")
        json_resultado = comparar_etiquetas(json_validos, None, "sal")
        pd.testing.assert_frame_equal(csv_resultado, json_resultado)
        self.assertEqual(csv_rechazos, json_rechazos)


if __name__ == "__main__":
    unittest.main()