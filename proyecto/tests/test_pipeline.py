import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.fuentes import FuenteCSV, FuenteJSON
from src.generar_datos import generar_registros
from src.pipeline import comparar_etiquetas, limpiar_productos, resumir_faltantes


class PipelineNutricionalTests(unittest.TestCase):
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
            import csv

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