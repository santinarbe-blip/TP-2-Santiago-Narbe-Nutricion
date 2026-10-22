import csv
import json
import random
from pathlib import Path


DIRECTORIO_DATOS = Path(__file__).resolve().parent.parent / "data"
CAMPOS = (
    "codigo",
    "nombre",
    "categoria",
    "energia_kcal_100g",
    "proteinas_g_100g",
    "carbohidratos_g_100g",
    "azucares_g_100g",
    "grasas_g_100g",
    "grasas_saturadas_g_100g",
    "fibra_g_100g",
    "sal_g_100g",
)
CATEGORIAS = {
    "Cereales": ("Avena", "Granola", "Copos", "Muesli"),
    "Bebidas": ("Bebida vegetal", "Jugo", "Infusión", "Licuado"),
    "Lácteos": ("Yogur", "Queso", "Leche", "Postre"),
    "Snacks": ("Galletas", "Barra", "Crackers", "Mix"),
    "Conservas": ("Garbanzos", "Tomates", "Lentejas", "Maíz"),
}
PERFILES = {
    "Cereales": ((5, 15), (2, 16), (2, 12)),
    "Bebidas": ((0, 8), (0, 8), (0, 4)),
    "Lácteos": ((2, 20), (0.5, 25), (0, 2)),
    "Snacks": ((3, 15), (5, 30), (0, 10)),
    "Conservas": ((2, 15), (0.2, 8), (2, 12)),
}


def generar_registros() -> list[dict]:
    """Genera el conjunto sintético reproducible de productos."""
    azar = random.Random(2026)
    registros = []
    consecutivo = 1
    for categoria, nombres in CATEGORIAS.items():
        for numero in range(12):
            rango_proteinas, rango_grasas, rango_fibra = PERFILES[categoria]
            proteinas = round(azar.uniform(*rango_proteinas), 1)
            grasas = round(azar.uniform(*rango_grasas), 1)
            fibra = round(azar.uniform(*rango_fibra), 1)
            max_carbohidratos = max(5, min(75, 90 - proteinas - grasas - fibra))
            carbohidratos = round(azar.uniform(5, max_carbohidratos), 1)
            azucares = round(azar.uniform(0, carbohidratos), 1)
            grasas_saturadas = round(azar.uniform(0, grasas), 1)
            sal = round(azar.uniform(0, 3), 2)
            registros.append(
                {
                    "codigo": f"200000{consecutivo:07d}",
                    "nombre": f"{nombres[numero % len(nombres)]} {numero + 1:02d}",
                    "categoria": categoria,
                    "energia_kcal_100g": round(
                        4 * proteinas + 4 * carbohidratos + 9 * grasas + 2 * fibra,
                        1,
                    ),
                    "proteinas_g_100g": proteinas,
                    "carbohidratos_g_100g": carbohidratos,
                    "azucares_g_100g": azucares,
                    "grasas_g_100g": grasas,
                    "grasas_saturadas_g_100g": grasas_saturadas,
                    "fibra_g_100g": fibra,
                    "sal_g_100g": sal,
                }
            )
            consecutivo += 1

    for indice, campo in ((0, "azucares_g_100g"), (13, "sal_g_100g"), (27, "fibra_g_100g"), (42, "proteinas_g_100g")):
        registros[indice][campo] = None

    registro_codigo_invalido = dict(registros[1])
    registro_codigo_invalido.update(codigo="EAN-INVALIDO", nombre="Registro de prueba")
    registros.append(registro_codigo_invalido)
    registro_nutriente_invalido = dict(registros[1])
    registro_nutriente_invalido.update(
        codigo="2999999999999",
        nombre="Registro con dato imposible",
        azucares_g_100g=101,
    )
    registros.append(registro_nutriente_invalido)
    return registros


def main() -> None:
    """Genera y guarda los datos sintéticos en CSV y JSON."""
    DIRECTORIO_DATOS.mkdir(parents=True, exist_ok=True)
    registros = generar_registros()
    with (DIRECTORIO_DATOS / "productos.csv").open(
        "w", newline="", encoding="utf-8"
    ) as archivo_csv:
        escritor = csv.DictWriter(archivo_csv, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(registros)
    with (DIRECTORIO_DATOS / "productos.json").open("w", encoding="utf-8") as archivo_json:
        json.dump(registros, archivo_json, ensure_ascii=False, indent=2)
    print("Se generaron 60 fichas, con 4 valores ausentes y 2 filas inválidas, en data/.")


if __name__ == "__main__":
    main()