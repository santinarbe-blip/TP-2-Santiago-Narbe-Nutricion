# Comparador de etiquetas nutricionales

**Autor:** Santiago Narbe · **Materia:** Programación Orientada a Datos · **Trabajo:** TP2 individual

## Resumen

- Compara nutrientes de productos sintéticos por cada 100 g.
- Lee los mismos datos desde CSV o JSON.
- Valida registros, conserva faltantes y detalla los rechazos.
- Filtra por categoría, ordena productos y genera resúmenes y gráficos.
- Es una herramienta educativa: no evalúa alimentos ni recomienda dietas.

## 1. Problema y solución

Las etiquetas pueden expresar cantidades de formas distintas y un dato ausente no equivale a cero. Esta aplicación organiza fichas de productos y permite explorar sus nutrientes usando una referencia común de 100 g. Se pueden filtrar productos por categoría, ordenarlos por nutriente y consultar resúmenes. Los valores ausentes se muestran como “no disponible” y los registros inválidos se reportan.

## 2. Datos y procedencia

`data/productos.csv` y `data/productos.json` contienen representaciones equivalentes de un conjunto sintético generado con semilla fija. Incluyen 60 productos válidos, cuatro nutrientes ausentes deliberadamente y dos registros inválidos. No se usan datos personales ni fuentes externas. El esquema, las unidades y la generación se describen en [data/README.md](data/README.md).

Cada registro contiene código EAN (texto), nombre, categoría, energía (kcal/100 g) y nutrientes (g/100 g). El código se valida por formato (8 o 13 dígitos), no por dígito de control.

## 3. Instalación, ejecución y pruebas

Desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --entrada data/productos.csv --categoria Snacks
python -m unittest discover -s tests
```

En Windows, activa el entorno con `.venv\Scripts\activate`. Para usar JSON, cambia la entrada a `data/productos.json`. La aplicación crea `outputs/` con resultados; agrega `--sin-graficos` para omitir imágenes o `--salida RUTA` para elegir otra carpeta.
Si la entrada no se puede leer, por ejemplo porque el archivo no existe, se muestra un mensaje de error claro sin traceback.

Parámetros disponibles:

```bash
python -m src.main --entrada data/productos.csv --nutriente azucares --sin-graficos
python -m src.generar_datos
```

Las categorías son `Cereales`, `Bebidas`, `Lácteos`, `Snacks` y `Conservas`. Los nutrientes disponibles son energía, proteínas, carbohidratos, azúcares, grasas, grasas saturadas, fibra y sal.

## 4. Flujo de procesamiento

**Leer → validar → limpiar y transformar → analizar → comunicar**

| Etapa | Función |
|---|---|
| Leer | Carga CSV o JSON con una estructura común (`src/fuentes.py`). |
| Validar y limpiar | Comprueba identificadores, números, rangos y duplicados; conserva faltantes como nulos (`src/pipeline.py`). |
| Analizar | Filtra por categoría, ordena por nutriente y calcula resúmenes (`src/pipeline.py`). |
| Comunicar | Muestra resultados y exporta tablas, rechazos, faltantes y gráficos (`src/main.py`). |

Los faltantes no se imputan como cero y se excluyen solo de los cálculos que necesitan ese valor. Los rechazos incluyen un motivo. Las reglas de plausibilidad no son una validación regulatoria de etiquetado.

## 5. Organización del código

```text
.
├── data/       # datos de ejemplo y documentación
├── docs/       # ejemplo de gráfico
├── src/        # fuentes, modelo, pipeline, aplicación y generador
├── tests/      # pruebas automatizadas
├── outputs/    # resultados generados; no se versionan
└── README.md
```

`FuenteCSV` y `FuenteJSON` implementan la interfaz `FuenteDatos`. `ProductoNutricional` modela una ficha; `pipeline.py` valida y compara; `main.py` coordina argumentos, exportaciones y gráficos.

## 6. Conceptos del curso aplicados

- **Funciones con responsabilidades acotadas:** lectura, normalización, limpieza, comparación, resúmenes y exportación se separan en funciones.
- **Clases y abstracción:** una dataclass representa el producto y una interfaz común desacopla la lectura del formato.
- **Validación:** una expresión regular verifica el formato EAN; las reglas también comprueban campos obligatorios, valores y duplicados.
- **Manejo de faltantes y errores:** los nulos se conservan y cada registro rechazado informa el motivo.

## 7. Decisiones de limpieza

| Situación | Decisión |
|---|---|
| Código inválido o duplicado | Rechazar y registrar el motivo; se conserva la primera fila válida de cada código. |
| Nutriente faltante | Conservar como nulo; mostrar “no disponible”, nunca como cero. |
| Valor fuera de rango o inconsistente | Rechazar el registro completo. Se consideran nutrientes negativos o mayores a 100 g/100 g, energía mayor a 900 kcal/100 g, azúcares mayores que carbohidratos y grasas saturadas mayores que grasas totales. |

Son reglas didácticas de plausibilidad: no certifican cumplimiento regulatorio ni modifican o imputan valores.

## 8. Ejemplo de resultado

Al ejecutar `python -m src.main --entrada data/productos.csv --categoria Snacks --nutriente azucares --sin-graficos` se leen 62 registros: 60 productos válidos y 2 filas rechazadas. Se comparan 12 productos; Galletas 09 presenta el menor valor disponible de azúcares (5,2 g/100 g).

El gráfico correspondiente está disponible en [docs/ejemplo_azucares_snacks.png](docs/ejemplo_azucares_snacks.png). Las barras ordenan los productos por el valor disponible; no representan una evaluación global de salud.

## 9. Interpretación y limitaciones

Los resultados describen únicamente este conjunto sintético. Permiten comparar valores generados dentro de una categoría, pero no generalizar a productos reales ni al mercado. Ordenar por un nutriente no determina si un alimento es saludable o adecuado para una persona, y no permite hacer recomendaciones médicas o dietarias. La energía también es un cálculo derivado de nutrientes simulados.

La aplicación compara por 100 g y una categoría y nutriente a la vez. No convierte porciones, consulta productos en línea ni verifica normas locales. Como mejoras futuras se podrían incorporar fuentes reales documentadas, más filtros y pruebas específicas de exportaciones y gráficos.
