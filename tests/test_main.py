import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.generar_datos import generar_registros
from src.main import main


class MainTests(unittest.TestCase):
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

    def test_busqueda_rechaza_codigo_con_formato_invalido(self):
        error = io.StringIO()
        with (
            patch(
                "sys.argv",
                ["main", "--codigo", "123", "--entrada", "data/noexiste.csv"],
            ),
            contextlib.redirect_stderr(error),
            self.assertRaises(SystemExit) as resultado,
        ):
            main()

        self.assertEqual(resultado.exception.code, 2)
        self.assertIn("el código debe tener 8 o 13 dígitos", error.getvalue())

    def test_busqueda_csv_con_cero_inicial_y_nutriente_nulo(self):
        registros = [dict(generar_registros()[0])]
        registros[0]["codigo"] = "01234567"
        registros[0]["azucares_g_100g"] = None
        with tempfile.TemporaryDirectory() as directorio:
            ruta_csv = Path(directorio) / "productos.csv"
            with ruta_csv.open("w", newline="", encoding="utf-8") as archivo:
                escritor = csv.DictWriter(archivo, fieldnames=registros[0].keys())
                escritor.writeheader()
                escritor.writerows(registros)

            salida = io.StringIO()
            with (
                patch(
                    "sys.argv",
                    ["main", "--entrada", str(ruta_csv), "--codigo", "01234567"],
                ),
                contextlib.redirect_stdout(salida),
            ):
                main()

        self.assertIn("Código: 01234567", salida.getvalue())
        self.assertIn("Azúcares: no disponible", salida.getvalue())

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


if __name__ == "__main__":
    unittest.main()
