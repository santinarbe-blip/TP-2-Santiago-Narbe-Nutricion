# Datos del proyecto

## Procedencia

`productos.csv` y `productos.json` son versiones equivalentes de datos sintéticos generados por `python src/generar_datos.py`. La semilla fija `2026` permite reproducir los mismos registros. No se consultan fuentes externas ni se incluyen datos personales; por lo tanto, no hay una licencia de terceros aplicable. Fecha de generación del conjunto inicial: 2026-10-21.

El conjunto contiene 60 fichas válidas distribuidas entre Cereales, Bebidas, Lácteos, Snacks y Conservas, además de dos filas con errores intencionales. Esas filas se conservan para probar el registro de rechazos; no forman parte del análisis. Los números se diseñaron con fines didácticos y no corresponden a marcas o productos reales.

## Unidad de análisis y esquema

Cada objeto/fila representa un producto. Todos los nutrientes se expresan por cada 100 gramos, para que la comparación no dependa de tamaños de porción distintos.

| Campo | Tipo | Unidad/uso |
|---|---|---|
| `codigo` | texto | Identificador sintético con patrón EAN de 8 o 13 dígitos |
| `nombre` | texto | Nombre ficticio |
| `categoria` | texto | Grupo del producto |
| `energia_kcal_100g` | número | kilocalorías por 100 g |
| `proteinas_g_100g` | número | gramos por 100 g |
| `carbohidratos_g_100g` | número | gramos por 100 g |
| `azucares_g_100g` | número | gramos por 100 g |
| `grasas_g_100g` | número | gramos por 100 g |
| `grasas_saturadas_g_100g` | número | gramos por 100 g |
| `fibra_g_100g` | número | gramos por 100 g |
| `sal_g_100g` | número | gramos por 100 g |

Los códigos EAN se usan como texto para preservar ceros iniciales. La expresión regular comprueba solo 8 o 13 dígitos: no comprueba que el código exista ni calcula su dígito de control.

## Limitaciones

Los valores fueron simulados, no obtenidos de análisis de laboratorio ni de etiquetas comerciales. Las categorías simplifican productos diversos y los rangos plausibles no equivalen a criterios oficiales o recomendaciones nutricionales. No usar estos datos para decisiones de salud.
