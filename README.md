# Uso y declaración de IA generativa en artículos WoS 2025-2026: Computación/Ingeniería

Repositorio del equipo Computación/Ingeniería (CIN) del trabajo de investigación del Magíster en Data Science, Universidad Católica del Maule. Profesor: Dr. José Alejandro González Campos.

Equipo: Rocío Guajardo González (RMG) y Fabiola Aguilar Rojas (FAR).

> Repositorio privado. Los registros de Web of Science están sujetos a licencia y no se redistribuyen. Los textos completos de los artículos no se guardan aquí.

## Estructura

```
data/
  raw/CIN/        Exportaciones de WoS sin modificar (403 archivos) en 9 .zip de hasta 50 archivos
  processed/      Salidas del script de muestreo
scripts/          Scripts de muestreo, validación y análisis
docs/             Protocolo, registro de búsqueda, capturas y video de la búsqueda
base/             Base codificada (.xlsx y .csv), diccionario de variables y bitácora de desacuerdos
```

## Búsqueda en Web of Science

- Fecha y hora de la búsqueda total: 07-10-2026, 18:34 (UTC−3). A las ~19:52 se repitió y seguía dando 400.520 registros.
- Exportación por bloques: 07-10-2026, 19:52-21:41 (UTC−3), en orden P6 a P1. Inicio según capturas de la sesión (±1 min); término según la hora del último archivo de cada bloque.

| Bloque | Inicio | Término (último lote) |
|---|---|---|
| P6 | 19:52 | ~20:14 |
| P5 | 20:14 | 20:36 |
| P4 | 20:37 | 20:51 |
| P3 | 20:52 | 21:08 |
| P2 | 21:08 | 21:23 |
| P1 | 21:24 | 21:41 |
- Base: Web of Science Core Collection (acceso institucional UCM vía CINCEL)
- Ediciones: SCI-EXPANDED, SSCI, ESCI
- Consulta (búsqueda avanzada, sin ajustes de sintaxis):

```
WC=("Computer Science, Information Systems" OR "Computer Science, Software Engineering" OR "Computer Science, Interdisciplinary Applications" OR "Computer Science, Theory & Methods" OR "Engineering, Electrical & Electronic") AND PY=(2025-2026) AND DT=(Article) AND LA=(English OR Spanish)
```

- Resultados: 400.520 registros
- Exportación: WoS solo exporta los primeros 100.000 registros de una búsqueda, por lo que el universo se exportó en seis bloques excluyentes (P1-P6) por año, categoría y, en EE&E 2025, fecha de publicación. Formato Tab delimited file, Full Record, lotes de hasta 1.000 registros: 403 archivos en total. Las consultas de cada bloque están en el protocolo (sección 5).

| Bloque | Año | Categoría | Corte adicional | Registros |
|---|---|---|---|---|
| P1 | 2025 | CS, Information Systems | — | 62.028 |
| P2 | 2025 | CS Software Eng., Interdisciplinary Appl. o Theory & Methods, sin Information Systems | — | 57.748 |
| P3 | 2025 | Solo EE&E (sin las 4 de CS) | Publicado ene-jun 2025 | 60.047 |
| P4 | 2025 | Solo EE&E | Fuera de ene-jun 2025 | 52.969 |
| P5 | 2026, sin 2025 | Cualquiera de las 4 de CS | — | 85.980 |
| P6 | 2026, sin 2025 | Solo EE&E | — | 81.748 |
| Total | | | | 400.520 |

- Verificación (`scripts/verificar_wos.py`): 400.520 filas, 400.520 UT únicos, 0 duplicados.

## Cómo reproducir el muestreo

Requisitos: Python 3.10 o superior, `numpy` y `pandas`.

```
pip install numpy pandas
```

1. Descomprimir los .zip de `data/raw/CIN/` en una sola carpeta local (por ejemplo, `universo_CIN/`), con los 403 archivos y nada más.
2. Reunir las listas de UT de los universos de Salud y Educación (`UT_SAL.csv` y `UT_EDU.csv`, generadas por cada equipo con `extraer_ut.py`) en una carpeta `otros/`.
3. Ejecutar:

```
python scripts/muestreo_cin.py --entrada universo_CIN --otros otros/UT_SAL.csv otros/UT_EDU.csv --salida data/processed
```

El script elimina duplicados por UT, descarta los registros fuera del periodo (por año final de publicación), de otro tipo documental o idioma, elimina los registros compartidos con Salud y Educación, genera una permutación aleatoria con semilla 2026 y calcula cuotas proporcionales por año para n = 300.

Salidas en `data/processed/`:

- `lista_ordenada_CIN.csv`: universo en orden aleatorio (A03), con estrato (A04), posición dentro del estrato, cuota y codificadora asignada.
- `cuotas_CIN.csv`: tamaño del universo y cuota por año.
- `resumen_muestreo_CIN.json`: conteos para el diagrama de flujo, huellas SHA-256 de los archivos de entrada y versiones de software.

Con los mismos archivos de entrada, el resultado es idéntico en cualquier computador, independiente del orden de los lotes.

## Lista de UT para intercambio entre áreas

Para eliminar los registros compartidos entre áreas, cada equipo genera la lista de UT de su universo y la comparte con los otros dos:

```
python scripts/extraer_ut.py --entrada universo_CIN --salida UT_CIN.csv
```

## Organización del equipo y responsabilidades

Rocío Guajardo González (RMG) y Fabiola Aguilar Rojas (FAR) se dividieron las tareas de exportación de los registros de Web of Science. Ambas participaron en la revisión, organización y verificación de los registros. Esta descripción recoge las responsabilidades compartidas del equipo, sin asignar bloques ni tareas específicas a una integrante en particular.

- **Exportación y organización del universo.** La exportación se realizó el 07-10-2026 (19:52-21:41, UTC−3), en seis bloques excluyentes (P1-P6), en formato Tab delimited (Full Record) y lotes de hasta 1.000 registros. La búsqueda original fue ejecutada y grabada como parte del trabajo del equipo. La organización de las descargas incluyó comprobar con PowerShell el número de archivos (403) y de registros por archivo, separar las descargas de prueba, comprimir los archivos y subir los datos al repositorio.
- **Verificación de integridad.** Se ejecutó `verificar_wos.py`, elaborado el 08-10-2026, para comprobar la integridad del universo. El resultado fue de 400.520 registros únicos por UT, sin duplicados.
- **Revisión del protocolo, scripts y documentación.** Las autoras revisaron y validaron el contenido y el código, y asumen la responsabilidad por ellos. Las instrucciones anteriores documentan el uso de `muestreo_cin.py` y `extraer_ut.py` para reproducir el muestreo y generar la lista de UT para el intercambio entre áreas.

La codificación de los artículos es exclusivamente humana.
