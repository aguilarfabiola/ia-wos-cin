"""
Verifica y une las exportaciones de Web of Science (Tab delimited, Full Record).

Uso:  pon este script en la misma carpeta que los savedrecs*.txt y ejecuta
      python verificar_wos.py
Genera: wos_unido.txt (todos los registros, sin duplicados por UT)
"""
import csv, glob, sys
from collections import Counter

csv.field_size_limit(sys.maxsize)
ESPERADO = 400_520
# Último lote (registros < 1000) que debería tener cada bloque
ULTIMOS = {28: "P1", 748: "P2 o P6", 47: "P3", 969: "P4", 980: "P5"}

def leer(ruta):
    raw = open(ruta, "rb").read()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    filas = list(csv.reader(raw.decode(enc).splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE))
    return filas[0], [f for f in filas[1:] if any(c.strip() for c in f)]

def bloque(cab, filas):
    """Adivina a qué bloque pertenece un archivo según PY y WC de sus registros."""
    iPY, iWC = cab.index("PY"), cab.index("WC")
    votos = Counter()
    for f in filas:
        py = f[iPY] if iPY < len(f) else ""
        wc = f[iWC] if iWC < len(f) else ""
        cs = [c for c in ("Information Systems", "Software Engineering",
                          "Interdisciplinary Applications", "Theory & Methods")
              if "Computer Science, " + c in wc]
        if py == "2025":
            votos["P1" if "Information Systems" in cs else ("P2" if cs else "P3/P4")] += 1
        else:
            votos["P5" if cs else "P6"] += 1
    return votos.most_common(1)[0][0] if votos else "?"

archivos = sorted(glob.glob("savedrecs*.txt"))
print(f"Archivos encontrados: {len(archivos)}")
cabecera, vistos, total = None, {}, 0
por_bloque, raros = Counter(), []
for a in archivos:
    cab, filas = leer(a)
    cabecera = cabecera or cab
    iUT = cab.index("UT")
    total += len(filas)
    b = bloque(cab, filas)
    por_bloque[b] += 1
    if len(filas) != 1000:
        raros.append((a, len(filas), ULTIMOS.get(len(filas), "¿?"), b))
    for f in filas:
        vistos.setdefault(f[iUT], f)

esperado_archivos = {"P1": 63, "P2": 58, "P3/P4": 114, "P5": 86, "P6": 82}
print(f"Filas leídas: {total:,}  |  UT únicos: {len(vistos):,}  |  esperado: {ESPERADO:,}")
print(f"Duplicados eliminados: {total - len(vistos):,}")
print("\nArchivos por bloque (encontrados / esperados):")
for k, v in esperado_archivos.items():
    marca = "OK" if por_bloque[k] == v else "<-- REVISAR"
    print(f"  {k:6} {por_bloque[k]:4} / {v:<4} {marca}")
print("\nArchivos con menos de 1000 registros (deberían ser solo los últimos lotes):")
for a, n, esp, b in raros:
    print(f"  {a}: {n} registros  (último lote de {esp}; clasificado como {b})")

with open("wos_unido.txt", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
    w.writerow(cabecera)
    w.writerows(vistos.values())
print(f"\nGuardado wos_unido.txt con {len(vistos):,} registros únicos.")
if len(vistos) == ESPERADO:
    print("✔ Está completo.")
else:
    print(f"✘ Faltan {ESPERADO - len(vistos):,} registros: revisa el bloque marcado arriba.")
