import csv
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.fuentes import FuenteCSV, FuenteJSON, fuente_desde_ruta
from src.generar_datos import generar_registros
from src.pipeline import limpiar_productos, normalizar_ficha, comparar_etiquetas


class FuentesTests(unittest.TestCase):
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

    def test_extension_no_soportada_se_rechaza(self):
        with self.assertRaisesRegex(ValueError, "formato de entrada debe ser CSV o JSON"):
            fuente_desde_ruta(Path("productos.xlsx"))

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
