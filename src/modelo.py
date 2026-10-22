from dataclasses import asdict, dataclass


COLUMNAS_NUTRIENTES = {
    "energia": "energia_kcal_100g",
    "proteinas": "proteinas_g_100g",
    "carbohidratos": "carbohidratos_g_100g",
    "azucares": "azucares_g_100g",
    "grasas": "grasas_g_100g",
    "grasas_saturadas": "grasas_saturadas_g_100g",
    "fibra": "fibra_g_100g",
    "sal": "sal_g_100g",
}


def columna_nutriente(nutriente: str) -> str:
    """Devuelve el nombre de campo asociado a un nutriente."""
    try:
        return COLUMNAS_NUTRIENTES[nutriente]
    except KeyError:
        raise ValueError(f"Nutriente desconocido: {nutriente}") from None


@dataclass(frozen=True)
class ProductoNutricional:
    codigo: str
    nombre: str
    categoria: str
    energia_kcal_100g: float | None
    proteinas_g_100g: float | None
    carbohidratos_g_100g: float | None
    azucares_g_100g: float | None
    grasas_g_100g: float | None
    grasas_saturadas_g_100g: float | None
    fibra_g_100g: float | None
    sal_g_100g: float | None

    def obtener_nutriente(self, nutriente: str) -> float | None:
        """Devuelve el valor del nutriente solicitado."""
        return getattr(self, columna_nutriente(nutriente))

    def como_registro(self) -> dict:
        """Convierte la ficha en un diccionario de campos."""
        return asdict(self)