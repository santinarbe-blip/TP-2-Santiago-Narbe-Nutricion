# Documentación del proyecto

La documentación completa, incluidos instalación, ejecución, flujo de procesamiento, procedencia de los datos, decisiones de limpieza, ejemplo de resultados e interpretación, está en el [README de la raíz](../README.md).

Desde esta carpeta se ejecuta la aplicación y la suite de pruebas:

```bash
python -m src.main --entrada data/productos.csv --categoria Snacks
python -m unittest discover -s tests -v
```
