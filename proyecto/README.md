# Comparador de etiquetas nutricionales

**Autor:** Santiago Narbe  
**Materia:** Programación Orientada a Datos  
**Trabajo:** TP2 individual

## 3. Instalación y ejecución

Clona el repositorio y entra en `proyecto/`, donde se encuentran `requirements.txt`, `src/` y `tests/`:

```bash
git clone https://github.com/santinarbe-blip/TP-2-Santiago-Narbe-Nutricion.git
cd TP-2-Santiago-Narbe-Nutricion/proyecto
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows, activa el entorno con `.venv\Scripts\activate` en lugar de `source .venv/bin/activate`.

### Ejecutar la aplicación

La categoría debe ser una de estas opciones: `Cereales`, `Bebidas`, `Lácteos`, `Snacks` o `Conservas`.

```bash
python -m src.main --entrada data/productos.csv --categoria Snacks
python -m src.main --entrada data/productos.json --categoria Snacks
```

La ejecución crea `outputs/` con tablas, filas rechazadas y gráficos. Para omitir los gráficos, agrega `--sin-graficos`.

### Ejecutar las pruebas

```bash
python -m unittest discover -s tests -v
```

## Problema y solución

Comparar la información nutricional de productos requiere usar la misma base de referencia. Las etiquetas pueden expresar cantidades de formas distintas y un dato ausente no significa que el nutriente esté presente en cantidad cero. Esta aplicación organiza fichas simuladas y compara nutrientes expresados por cada 100 gramos. Los valores ausentes se muestran como “no disponible”; los registros con identificadores incompletos o valores imposibles se informan aparte.

La herramienta está pensada para una persona que explora etiquetas con fines educativos. Permite filtrar por categoría, ordenar por un nutriente, revisar resúmenes por categoría y exportar resultados. No clasifica alimentos como saludables o no saludables, no recomienda dietas y no reemplaza asesoramiento profesional.

### Preguntas que permite explorar

1. Dentro de una categoría, ¿qué productos tienen menos azúcares, sal o energía por 100 g?
2. ¿Cómo varían los promedios de azúcares, fibra y proteínas entre categorías?
3. ¿Qué campos tienen datos no disponibles y qué registros se rechazan por identificadores o cantidades imposibles?
4. ¿Se obtiene la misma tabla al leer el mismo conjunto desde CSV y JSON?

Los resultados describen únicamente este conjunto sintético; no permiten generalizar a productos reales ni determinar por sí solos la calidad global de un alimento.

## Datos y procedencia

`data/productos.csv` y `data/productos.json` son dos representaciones equivalentes de un conjunto creado para este trabajo mediante `src/generar_datos.py`, con semilla fija. Incluyen 60 productos analizables (con cuatro nutrientes ausentes deliberadamente) y 2 registros inválidos para demostrar el tratamiento de errores. No se usan datos personales ni una fuente externa. La generación, el esquema, las unidades y las limitaciones están documentados en [data/README.md](data/README.md).

Cada fila representa una ficha de producto. Se utilizan código EAN como texto, nombre, categoría, energía en kcal/100 g y nutrientes en g/100 g. El código se valida con una expresión regular para EAN de 8 o 13 dígitos; esto valida el formato, no el dígito de control.

## 4. Flujo de procesamiento

El flujo de procesamiento es:

**leer → inspeccionar y validar → limpiar y transformar → analizar → comunicar**

| Etapa | Qué hace | Dónde está |
|---|---|---|
| Leer | Carga CSV o JSON y convierte cada fila/objeto en un registro con la misma estructura. | `src/fuentes.py` |
| Inspeccionar y validar | Comprueba campos obligatorios, formato del código, valores numéricos y rangos de plausibilidad. | `src/pipeline.py` |
| Limpiar y transformar | Rechaza registros inválidos y códigos duplicados; normaliza nutrientes a números y conserva los faltantes como nulos. | `src/pipeline.py` |
| Analizar | Filtra por categoría, ordena por el nutriente elegido y calcula resúmenes por categoría. | `src/pipeline.py` |
| Comunicar | Imprime la comparación en consola y exporta tablas, faltantes, rechazos y gráficos. | `src/main.py`; archivos en `outputs/` por defecto |

El directorio de resultados se puede cambiar con `--salida`. Los nutrientes ausentes se representan como “no disponible” en las salidas que muestran valores y se excluyen solo de los cálculos que requieren ese dato. El motivo de cada registro rechazado queda en `outputs/rechazos.csv`; las cantidades faltantes por campo se guardan en `outputs/faltantes.csv`.

Los valores vacíos nunca se convierten en cero. Se rechazan nutrientes negativos, por encima de 100 g/100 g, energía por encima de 900 kcal/100 g, azúcares mayores que carbohidratos o grasas saturadas mayores que grasas totales. Son reglas de plausibilidad para este ejercicio, no una validación regulatoria de etiquetado.

## Otros ejemplos de uso

```bash
python -m src.main --entrada data/productos.csv --nutriente azucares
python -m src.main --entrada data/productos.json --categoria Snacks --nutriente azucares
python -m src.main --entrada data/productos.csv --nutriente sal --sin-graficos
python -m src.generar_datos
```

Las opciones disponibles son `energia`, `proteinas`, `carbohidratos`, `azucares`, `grasas`, `grasas_saturadas`, `fibra` y `sal`. `--salida` permite cambiar la carpeta de resultados y `--sin-graficos` evita generar imágenes.

## Ejemplo de salida

Al ejecutar con el conjunto incluido, se leen 62 filas: se conservan 60 productos y se informan 2 rechazos deliberados. La consola y `comparacion.csv` muestran los productos ordenados por el nutriente seleccionado, con los valores ausentes visibles como “no disponible”.

### Gráficos

Las imágenes se guardan en `outputs/` y respetan la categoría seleccionada. Los gráficos de barras muestran hasta diez productos con valores disponibles, ordenados de menor a mayor.

- `grafico_energia.png`: barras horizontales; eje X en kcal/100 g y eje Y con el producto. Una barra menor indica menos energía declarada por 100 g en este conjunto; no es una evaluación global del alimento.
- `grafico_azucares.png`: barras horizontales; eje X en g/100 g y eje Y con el producto. Una barra menor indica menos azúcares por 100 g en los productos comparados.
- `grafico_azucares_vs_grasas.png`: dispersión; eje X en azúcares (g/100 g) y eje Y en grasas totales (g/100 g). Los puntos muestran productos con ambos datos disponibles; proximidad no implica causalidad.
- `grafico_datos_faltantes.png`: barras horizontales; eje X con la cantidad de registros y eje Y con el campo. Una barra mayor indica que ese dato está menos disponible, no que su valor sea cero.

## Organización del código

```text
proyecto/
|-- README.md
|-- requirements.txt
|-- data/
|   |-- README.md
|   |-- productos.csv
|   `-- productos.json
|-- src/
|   |-- fuentes.py
|   |-- generar_datos.py
|   |-- main.py
|   |-- modelo.py
|   `-- pipeline.py
`-- tests/
	`-- test_pipeline.py
```

`FuenteDatos`, `FuenteCSV` y `FuenteJSON` normalizan el acceso a los archivos. `ProductoNutricional` representa una ficha y da acceso a sus nutrientes. `pipeline.py` valida, limpia y compara; `main.py` coordina argumentos, exportaciones y gráficos.

## Pruebas y reproducibilidad

Ejecuta `python -m unittest discover -s tests`. Las pruebas cubren una comparación normal, filas inválidas y duplicadas, faltantes y equivalencia entre CSV y JSON. El generador usa una semilla fija para volver a crear el mismo conjunto. Las dependencias y el comando están especificados en `requirements.txt`.

## Alcance y limitaciones

La primera versión compara datos declarados por 100 g para una categoría y un nutriente a la vez. No convierte porciones, no verifica normas locales, no consulta productos en línea y no realiza recomendaciones dietarias. Los datos son sintéticos, por lo que los valores y las diferencias entre categorías no representan el mercado.
