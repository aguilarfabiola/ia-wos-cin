"""
extraer_ut.py
Extrae la lista de identificadores UT de todos los lotes exportados de WoS
y la guarda en un CSV para compartir con los otros equipos.

Uso:
  python extraer_ut.py --entrada "ruta/lotes_CIN" --salida UT_CIN.csv
"""
import argparse
import csv
from pathlib import Path

import pandas as pd


def leer(ruta):
    if ruta.suffix.lower() in (".xls", ".xlsx"):
        return pd.read_excel(ruta, dtype=str)
    for cod in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return pd.read_csv(ruta, sep="\t", dtype=str, encoding=cod,
                               quoting=csv.QUOTE_NONE, index_col=False)
        except (UnicodeError, pd.errors.ParserError):
            continue
    raise ValueError(f"No se pudo leer {ruta}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", required=True, help="Carpeta con los lotes de WoS")
    ap.add_argument("--salida", required=True, help="Archivo CSV de salida")
    args = ap.parse_args()

    uts, n_archivos = [], 0
    for p in sorted(Path(args.entrada).iterdir()):
        if p.suffix.lower() not in (".txt", ".tsv", ".xls", ".xlsx"):
            continue
        df = leer(p)
        df.columns = [str(c).strip() for c in df.columns]
        col = next((c for c in ("UT", "UT (Unique WOS ID)", "UT (Unique ID)") if c in df.columns), None)
        if col is None:
            print(f"AVISO: {p.name} no tiene columna UT; se omite")
            continue
        uts.extend(df[col].dropna().str.strip().str.upper())
        n_archivos += 1

    unicos = sorted(set(u for u in uts if u))
    pd.DataFrame({"UT": unicos}).to_csv(args.salida, index=False)
    print(f"Archivos leídos: {n_archivos}")
    print(f"UT leídos: {len(uts)} | UT únicos guardados: {len(unicos)}")
    print(f"Guardado en {args.salida}")


if __name__ == "__main__":
    main()
