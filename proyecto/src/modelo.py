from dataclasses import dataclass


@dataclass(frozen=True)
class ProductoNutricional:
    codigo: str
    nombre: str
    categoria: str
    energia_kcal_100g: float
    proteinas_g_100g: float
    carbohidratos_g_100g: float
    azucares_g_100g: float
    grasas_g_100g: float
    grasas_saturadas_g_100g: float
    fibra_g_100g: float
    sal_g_100g: float

    def obtener_nutriente(self, nutriente: str) -> float:
        if nutriente == "energia":
            return self.energia_kcal_100g
        atributo = f"{nutriente}_g_100g"
        if not hasattr(self, atributo):
            raise ValueError(f"Nutriente desconocido: {nutriente}")
        return getattr(self, atributo)

    def como_registro(self) -> dict:
        return {
            "codigo": self.codigo,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "energia_kcal_100g": self.energia_kcal_100g,
            "proteinas_g_100g": self.proteinas_g_100g,
            "carbohidratos_g_100g": self.carbohidratos_g_100g,
            "azucares_g_100g": self.azucares_g_100g,
            "grasas_g_100g": self.grasas_g_100g,
            "grasas_saturadas_g_100g": self.grasas_saturadas_g_100g,
            "fibra_g_100g": self.fibra_g_100g,
            "sal_g_100g": self.sal_g_100g,
        }