"""
muestreo_cin.py
Muestreo del componente A - Computación/Ingeniería (CIN)
Trabajo IA-WoS, Magíster en Data Science UCM

Qué hace:
  1. Lee todos los lotes exportados de WoS (Tab delimited .txt o Excel .xls/.xlsx).
  2. Elimina duplicados por UT.
  3. Verifica filtros: PY 2025-2026, DT solo Article (o Article; Early Access),
     idioma inglés o español. Cuenta lo descartado por motivo.
  4. Elimina los UT compartidos con los universos de Salud y Educación.
  5. Ordena por UT (para que el resultado no dependa del orden de los lotes)
     y genera una permutación aleatoria completa con semilla 2026.
  6. Calcula cuotas por año con asignación proporcional (mayor resto).
  7. Guarda la lista ordenada, las cuotas y un resumen para el diagrama de flujo.

Uso:
  python muestreo_cin.py --entrada data/raw/CIN \
                         --otros data/raw/SAL data/raw/EDU \
                         --salida data/processed

  --otros acepta carpetas con exportaciones de WoS de las otras áreas,
  o archivos .csv con una columna llamada UT.
"""

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 2026
N_MUESTRA = 300
ANIOS = {2025, 2026}
IDIOMAS = {"english", "spanish"}
DT_PERMITIDOS = {"article", "early access"}

# Etiquetas de WoS: export Tab delimited (2 letras) y export Excel (nombre largo)
COLUMNAS = {
    "UT": ["UT", "UT (Unique WOS ID)", "UT (Unique ID)"],
    "PY": ["PY", "Publication Year"],
    "DT": ["DT", "Document Type"],
    "LA": ["LA", "Language"],
    "WC": ["WC", "WoS Categories", "Web of Science Categories"],
    "TI": ["TI", "Article Title"],
    "SO": ["SO", "Source Title"],
    "DI": ["DI", "DOI"],
}


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_txt(ruta):
    """Lee un export Tab delimited de WoS probando codificaciones comunes."""
    for cod in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return pd.read_csv(ruta, sep="\t", dtype=str, encoding=cod,
                               quoting=csv.QUOTE_NONE, index_col=False)
        except (UnicodeError, pd.errors.ParserError):
            continue
    raise ValueError(f"No se pudo leer {ruta}")


def leer_archivo(ruta):
    ext = ruta.suffix.lower()
    if ext in (".txt", ".tsv"):
        df = leer_txt(ruta)
    elif ext in (".xls", ".xlsx"):
        df = pd.read_excel(ruta, dtype=str)  # .xls requiere el paquete xlrd
    elif ext == ".csv":
        df = pd.read_csv(ruta, dtype=str)
    else:
        return None
    df.columns = [str(c).strip() for c in df.columns]
    salida = pd.DataFrame()
    for estandar, alias in COLUMNAS.items():
        col = next((a for a in alias if a in df.columns), None)
        salida[estandar] = df[col] if col else pd.NA
    salida["archivo_origen"] = ruta.name
    return salida


def leer_carpeta_o_archivo(ruta):
    ruta = Path(ruta)
    archivos = sorted(p for p in ruta.iterdir() if p.is_file()) if ruta.is_dir() else [ruta]
    tablas, huellas = [], {}
    for p in archivos:
        t = leer_archivo(p)
        if t is not None:
            tablas.append(t)
            huellas[p.name] = sha256(p)
    if not tablas:
        raise FileNotFoundError(f"No hay exportaciones legibles en {ruta}")
    return pd.concat(tablas, ignore_index=True), huellas


def limpiar_ut(serie):
    return serie.astype("string").str.strip().str.upper()


def dt_valido(dt):
    if pd.isna(dt):
        return False
    partes = {p.strip().lower() for p in str(dt).split(";") if p.strip()}
    return "article" in partes and partes <= DT_PERMITIDOS


def idioma_valido(la):
    """Acepta registros con al menos un idioma permitido (p. ej. 'English; Spanish')."""
    if pd.isna(la):
        return False
    partes = {p.strip().lower() for p in str(la).split(";") if p.strip()}
    return bool(partes & IDIOMAS)


def cuotas_mayor_resto(tamanos, n):
    total = sum(tamanos.values())
    exactas = {k: n * v / total for k, v in tamanos.items()}
    cuotas = {k: int(np.floor(x)) for k, x in exactas.items()}
    faltan = n - sum(cuotas.values())
    orden = sorted(exactas, key=lambda k: (exactas[k] - cuotas[k], tamanos[k]), reverse=True)
    for k in orden[:faltan]:
        cuotas[k] += 1
    return cuotas


def main():
    ap = argparse.ArgumentParser(description="Muestreo componente A - CIN")
    ap.add_argument("--entrada", required=True, help="Carpeta con los lotes de WoS del área CIN")
    ap.add_argument("--otros", nargs="*", default=[], help="Exportaciones o CSV con UT de Salud y Educación")
    ap.add_argument("--salida", default="data/processed")
    args = ap.parse_args()

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    flujo = {}

    # 1. Lectura
    df, huellas = leer_carpeta_o_archivo(args.entrada)
    df["UT"] = limpiar_ut(df["UT"])
    df = df[df["UT"].notna() & (df["UT"] != "")]
    flujo["registros_exportados"] = len(df)

    # 2. Duplicados
    df = df.drop_duplicates(subset="UT", keep="first")
    flujo["duplicados_eliminados"] = flujo["registros_exportados"] - len(df)

    # 3. Filtros
    df["PY_num"] = pd.to_numeric(df["PY"], errors="coerce")
    sin_anio = df["PY_num"].isna()
    fuera_anio = ~sin_anio & ~df["PY_num"].isin(ANIOS)
    mal_tipo = ~df["DT"].apply(dt_valido)
    mal_idioma = ~df["LA"].apply(idioma_valido)
    flujo["descartados_sin_PY"] = int(sin_anio.sum())
    flujo["descartados_PY_fuera_rango"] = int(fuera_anio.sum())
    flujo["descartados_tipo_documento"] = int((~sin_anio & ~fuera_anio & mal_tipo).sum())
    flujo["descartados_idioma"] = int((~sin_anio & ~fuera_anio & ~mal_tipo & mal_idioma).sum())
    df = df[~(sin_anio | fuera_anio | mal_tipo | mal_idioma)].copy()

    # 4. Compartidos con otras áreas
    compartidos = 0
    if args.otros:
        ut_otros = set()
        for ruta in args.otros:
            otros, h = leer_carpeta_o_archivo(ruta)
            huellas.update({f"otros/{k}": v for k, v in h.items()})
            ut_otros |= set(limpiar_ut(otros["UT"]).dropna())
        marca = df["UT"].isin(ut_otros)
        compartidos = int(marca.sum())
        df = df[~marca].copy()
        df[["UT"]].to_csv(salida / "UT_universo_CIN.csv", index=False)
    else:
        print("AVISO: no se entregaron universos de Salud/Educación; no se eliminaron compartidos.")
    flujo["compartidos_eliminados"] = compartidos
    flujo["universo_final"] = len(df)

    # 5. Orden aleatorio reproducible
    df = df.sort_values("UT").reset_index(drop=True)
    rng = np.random.default_rng(SEMILLA)
    df["A03"] = rng.permutation(len(df)) + 1
    df = df.sort_values("A03").reset_index(drop=True)
    df["A04"] = df["PY_num"].astype(int)
    df["posicion_estrato"] = df.groupby("A04").cumcount() + 1
    df["codificadora"] = np.where(df["posicion_estrato"] % 2 == 1, "RMG", "FAR")

    # 6. Cuotas
    tamanos = df["A04"].value_counts().to_dict()
    cuotas = cuotas_mayor_resto(tamanos, N_MUESTRA)
    df["cuota_estrato"] = df["A04"].map(cuotas)
    tabla_cuotas = pd.DataFrame(
        [{"A04": k, "N_universo": tamanos[k], "proporcion": tamanos[k] / len(df), "cuota_n": cuotas[k]}
         for k in sorted(tamanos)])
    flujo["universo_por_anio"] = {str(k): int(v) for k, v in sorted(tamanos.items())}
    flujo["cuotas"] = {str(k): int(v) for k, v in sorted(cuotas.items())}

    # 7. Guardar
    cols = ["A03", "A04", "posicion_estrato", "cuota_estrato", "codificadora",
            "UT", "DI", "TI", "SO", "WC", "DT", "LA", "archivo_origen"]
    df[cols].to_csv(salida / "lista_ordenada_CIN.csv", index=False, encoding="utf-8")
    tabla_cuotas.to_csv(salida / "cuotas_CIN.csv", index=False)
    resumen = {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "semilla": SEMILLA,
        "n_muestra": N_MUESTRA,
        "flujo": flujo,
        "archivos_sha256": huellas,
        "versiones": {"python": sys.version.split()[0], "numpy": np.__version__,
                      "pandas": pd.__version__, "sistema": platform.platform()},
    }
    with open(salida / "resumen_muestreo_CIN.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    print(json.dumps(flujo, ensure_ascii=False, indent=2))
    print(f"Archivos guardados en {salida.resolve()}")


if __name__ == "__main__":
    main()
