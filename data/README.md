# Datos del proyecto

## Procedencia

| Campo | Detalle |
|---|---|
| Fuente | Datos sintéticos generados por `src/generar_datos.py`; no se utilizó Open Food Facts ni otra fuente externa. |
| URL o procedimiento | Desde la raíz del repositorio, ejecutar `python -m src.generar_datos` (o `python src/generar_datos.py`). Usa la semilla fija `2026` y crea `data/productos.csv` y `data/productos.json` con el mismo contenido. |
| Responsable | Santiago Narbe, autor del trabajo. |
| Licencia | Datos sintéticos propios, sin licencia de terceros aplicable. |
| Fecha de generación | 2026-10-21 (conjunto incluido en el proyecto). |
| Unidad de análisis | Cada fila representa un producto ficticio. |
| Cantidad de observaciones | 60 productos válidos (N = 60); los archivos también incluyen 2 registros de prueba deliberadamente inválidos, que se rechazan y no forman parte del análisis. |

### Variables utilizadas

| Variable | Tipo | Unidad | Descripción |
|---|---|---|---|
| `codigo` | texto | — | Identificador sintético; se conserva como texto. No identifica un producto comercial real. |
| `nombre` | texto | — | Nombre ficticio generado para la ficha del producto. |
| `categoria` | texto | — | Grupo sintético del producto: Cereales, Bebidas, Lácteos, Snacks o Conservas. |
| `energia_kcal_100g` (`energia`) | número | kcal / 100 g | Energía calculada a partir de los macronutrientes generados. |
| `azucares_g_100g` (`azucares`) | número | g / 100 g | Cantidad de azúcares generada para cada 100 g. |

### Procedimiento de generación

El generador usa `random.Random(2026)` localmente, sin depender del estado aleatorio global. Para cada una de las cinco categorías —Cereales, Bebidas, Lácteos, Snacks y Conservas— crea 12 nombres ficticios, para un total de 60 fichas analizables. Los valores se muestrean con `uniform` y se redondean a una o dos cifras decimales:

| Categoría | Proteínas (g/100 g) | Grasas (g/100 g) | Fibra (g/100 g) |
|---|---:|---:|---:|
| Cereales | 5–15 | 2–16 | 2–12 |
| Bebidas | 0–8 | 0–8 | 0–4 |
| Lácteos | 2–20 | 0.5–25 | 0–2 |
| Snacks | 3–15 | 5–30 | 0–10 |
| Conservas | 2–15 | 0.2–8 | 2–12 |

Los carbohidratos se generan entre 5 y `max(5, min(75, 90 - proteínas - grasas - fibra))`; los azúcares, entre 0 y los carbohidratos; las grasas saturadas, entre 0 y las grasas; y la sal, entre 0 y 3 g/100 g. La energía se calcula como `4 × proteínas + 4 × carbohidratos + 9 × grasas + 2 × fibra`, en kcal/100 g. Después se marcan cuatro nutrientes como ausentes (azúcares, sal, fibra y proteínas, uno por ficha) y se agregan dos registros deliberadamente inválidos para probar la validación: uno con código mal formado y otro con azúcares por encima de 100 g/100 g.

El generador serializa esa misma lista de registros en ambos formatos: las fichas y el orden de las filas coinciden entre CSV y JSON. Los faltantes se almacenan como celdas vacías en CSV y `null` en JSON; son marcadores de ausencia, no ceros. En las tablas y salidas destinadas a mostrarlos se representan como “no disponible”. Las dos filas inválidas sirven para probar el registro de rechazos y no forman parte del análisis. Los números se diseñaron con fines didácticos y no corresponden a marcas o productos reales.

## Unidad de análisis y esquema

Cada objeto/fila representa un producto. Todos los nutrientes se expresan por cada 100 gramos, para que la comparación no dependa de tamaños de porción distintos.

| Campo | Tipo | Unidad/uso |
|---|---|---|
| `codigo` | texto | Identificador sintético ficticio; se genera con 13 dígitos |
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

Los campos nutricionales pueden estar vacíos en CSV o ser `null` en JSON. Se conservan como faltantes, se excluyen de cálculos que requieren su valor y se exportan como “no disponible”. Los campos de identificación siguen siendo obligatorios.

Los códigos se usan como texto para preservar ceros iniciales. Aunque su formato numérico se parece al de un EAN, son identificadores ficticios: la expresión regular comprueba solo 8 o 13 dígitos, no comprueba que el código exista ni calcula su dígito de control.

## Limitaciones

Los valores fueron simulados, no obtenidos de análisis de laboratorio ni de etiquetas comerciales. Las categorías simplifican productos diversos y los rangos plausibles no equivalen a criterios oficiales o recomendaciones nutricionales. No usar estos datos para decisiones de salud.
