# Comparador de etiquetas nutricionales

Proyecto educativo de Santiago Narbe para comparar datos nutricionales sintéticos por cada 100 g. Permite leer CSV o JSON, validar registros, registrar rechazos y generar tablas y gráficos. Los nutrientes faltantes se muestran como “no disponible”, nunca como cero.

## Inicio rápido

```bash
git clone https://github.com/santinarbe-blip/TP-2-Santiago-Narbe-Nutricion.git
cd TP-2-Santiago-Narbe-Nutricion/proyecto
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.main --entrada data/productos.csv --categoria Snacks
python -m unittest discover -s tests -v
```

La ejecución crea resultados en `proyecto/outputs/`. Los datos incluyen 60 productos sintéticos válidos y dos filas inválidas de prueba.

### Ejemplo de resultado

Comparación de azúcares en la categoría Snacks:

![Gráfico de azúcares por producto para la categoría Snacks](proyecto/docs/ejemplo_azucares_snacks.png)

## Documentación completa

En [proyecto/README.md](proyecto/README.md) se describen el flujo de procesamiento, la estructura del código, los conceptos del curso, las decisiones de limpieza, el resultado de ejemplo y sus limitaciones. La fuente, licencia, fecha, unidad de análisis, esquema y generación reproducible de los datos están explicados en [proyecto/data/README.md](proyecto/data/README.md).
