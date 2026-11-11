"""
Genera la exportación desordenada de facturación de un centro médico (DATOS FICTICIOS).

Uso:
    python generar_datos.py [facturacion_octubre_2026.xlsx]

Simula lo que exporta un sistema de facturación médica y que llega al analista:
- Hoja "Facturación Octubre": título y período encima de la tabla, fila "TOTAL GENERAL"
  al pie con una fórmula, dos filas vacías.
- Fechas en 4 formatos (fecha de Excel, 15/10/2026, 20261015, 24-10-26).
- Obras sociales, especialidades y profesionales escritos de varias formas
  (mayúsculas, sin tilde, espacios de más, iniciales "L. Ibáñez").
- CUIT con y sin guiones; uno con dígito verificador inválido.
- Aranceles como texto ("$ 18.000", "18000,00", "18000").
- Totales y una cantidad vacíos, 8 renglones duplicados.
- Débitos de las obras sociales (prestaciones rechazadas) cargados con cantidad negativa.
- Hoja "Objetivos" con nombres sin tilde, un monto como texto y montos en otra unidad.

No incluye datos de pacientes: cada renglón es una liquidación a una obra social o prepaga.
Semilla fija: siempre genera el mismo archivo.
"""
import random
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

CARPETA = Path(__file__).resolve().parent
SEMILLA = 2026

# --- Catálogos "oficiales" (inventados) ----------------------------------------
FINANCIADORES = [  # nombre, CUIT base (10 dígitos, rango ficticio 30-99...); el dígito verificador se calcula
    ("Obra Social Andina", "3099000130"),
    ("Prepaga Litoral Salud", "3099000148"),
    ("Mutual del Sur", "3099000156"),
    ("Plan Salud Pampa", "3099000164"),
    ("Cobertura Norte", "3099000172"),
]
CUIT_INVALIDO = "Cobertura Norte"  # su sistema lo tiene mal cargado (se detecta en la limpieza)
PROFESIONALES = ["Laura Ibáñez", "Martín Suárez", "Sofía Ríos"]
PRESTACIONES = [  # prestación, especialidad, arancel, profesional que la realiza
    ("Consulta clínica", "Clínica Médica", 18000, "Laura Ibáñez"),
    ("Electrocardiograma", "Cardiología", 22000, "Laura Ibáñez"),
    ("Ergometría", "Cardiología", 65000, "Laura Ibáñez"),
    ("Ecocardiograma", "Cardiología", 85000, "Laura Ibáñez"),
    ("Consulta pediátrica", "Pediatría", 18000, "Martín Suárez"),
    ("Control de niño sano", "Pediatría", 20000, "Martín Suárez"),
    ("Ecografía abdominal", "Diagnóstico por Imágenes", 48000, "Sofía Ríos"),
    ("Radiografía de tórax", "Diagnóstico por Imágenes", 26000, "Sofía Ríos"),
    ("Ecografía obstétrica", "Diagnóstico por Imágenes", 52000, "Sofía Ríos"),
]
OBJETIVOS = {"Laura Ibáñez": 5_200_000, "Martín Suárez": 3_300_000, "Sofía Ríos": 4_100_000}


def digito(base10: str) -> int:
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    r = 11 - sum(int(d) * p for d, p in zip(base10, pesos)) % 11
    return 0 if r == 11 else 9 if r == 10 else r


def cuit(nombre: str, base: str) -> str:
    d = digito(base)
    if nombre == CUIT_INVALIDO:
        d = (d + 3) % 10
    return f"{base[:2]}-{base[2:]}-{d}"


# --- Variantes "sucias" ---------------------------------------------------------
def sin_tildes(s: str) -> str:
    return s.translate(str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN"))


def variante_texto(rng, s: str) -> str:
    return rng.choice([s, s, s, s.upper(), s.lower() + "  ", sin_tildes(s), s + " "])


def variante_profesional(rng, s: str) -> str:
    nombre, apellido = s.split()
    return rng.choice([s, s, s.upper(), f"{nombre[0]}. {apellido}", f"{nombre} {sin_tildes(apellido)}"])


def variante_cuit(rng, c: str) -> str:
    return c.replace("-", "") if rng.random() < 0.18 else c


def variante_fecha(rng, f: datetime):
    r = rng.random()
    if r < 0.75:
        return f
    return rng.choice([f"{f:%d/%m/%Y}", f"{f:%Y%m%d}", f"{f:%d-%m-%y}"])


def variante_precio(rng, p: int):
    r = rng.random()
    if r < 0.76:
        return p
    miles = f"{p:,}".replace(",", ".")
    return rng.choice([f"$ {miles}", f"{p},00", str(p)])


def dias_habiles():
    dias = []
    for d in range(1, 32):
        f = datetime(2026, 10, d)
        if f.weekday() < 5 or (f.weekday() == 5 and d not in (3, 17)):  # lunes a viernes y casi todos los sábados
            dias.append(f)
    return dias


def main(salida):
    rng = random.Random(SEMILLA)
    cuits = {n: cuit(n, b) for n, b in FINANCIADORES}
    dias = dias_habiles()

    # 1) 210 liquidaciones únicas (una factura por renglón, numeración correlativa)
    filas = []
    for i in range(210):
        prest, esp, arancel, prof = rng.choice(PRESTACIONES)
        fin = rng.choice([f for f, _ in FINANCIADORES] + ["Obra Social Andina", "Prepaga Litoral Salud"])
        cant = rng.randint(4, 40) if "Consulta" in prest or "Control" in prest else rng.randint(2, 14)
        filas.append({"fecha": rng.choice(dias), "nro": f"B-0003-{20000 + i:08d}", "fin": fin, "esp": esp,
                      "prest": prest, "prof": prof, "cant": cant, "precio": arancel})
    # 2) Débitos de las obras sociales: 8 renglones con cantidad negativa
    for f in rng.sample(filas, 8):
        f["cant"] = -rng.randint(1, 3)
    rng.shuffle(filas)

    # 3) Renglones como los exporta el sistema (con los problemas de formato)
    renglones = []
    for f in filas:
        total = f["cant"] * f["precio"]
        renglones.append([variante_fecha(rng, f["fecha"]), f["nro"], variante_texto(rng, f["fin"]),
                          variante_cuit(rng, cuits[f["fin"]]), variante_texto(rng, f["esp"]), f["prest"],
                          variante_profesional(rng, f["prof"]), f["cant"], variante_precio(rng, f["precio"]), total])
    # Totales vacíos (20) y una cantidad vacía
    for r in rng.sample([r for r in renglones if r[7] > 0], 21)[:20]:
        r[9] = None
    sin_cant = next(r for r in renglones if r[9] is not None and r[7] > 0)
    sin_cant[7] = None
    # Duplicados: 8 renglones repetidos más abajo, idénticos
    for _ in range(8):
        origen = rng.randrange(0, 150)
        renglones.insert(rng.randrange(origen + 5, len(renglones)), list(renglones[origen]))
    # Filas vacías: una en el medio y otra antes del pie
    renglones.insert(120, [None] * 10)
    renglones.append([None] * 10)

    wb = Workbook()
    ws = wb.active
    ws.title = "Facturación Octubre"
    ws.append(["CENTRO MEDICO - EXPORTACION SISTEMA DE FACTURACION"] + [None] * 9)
    ws.append(["Periodo: 10/2026"] + [None] * 9)
    ws.append([None] * 10)
    ws.append(["Fecha", "Nro Factura", "Obra Social", "CUIT", "Especialidad", "Prestación", "Profesional",
               "Cant.", "Precio Unit.", "Total"])
    for r in renglones:
        ws.append(r)
    ultima = ws.max_row
    ws.append([None] * 8 + ["TOTAL GENERAL", f"=SUM(J5:J{ultima})"])
    for c in ws["A"][4:]:
        if isinstance(c.value, datetime):
            c.number_format = "dd/mm/yyyy"

    obj = wb.create_sheet("Objetivos")
    obj.append(["Profesional", "Objetivo Octubre"])
    for prof, monto in OBJETIVOS.items():
        nombre = sin_tildes(prof) if prof != "Laura Ibáñez" else prof
        obj.append([nombre, f"{monto:,}".replace(",", ".") if prof == "Martín Suárez" else monto])
    wb.save(salida)
    print(f"{salida.name}: {len(renglones)} filas de datos (210 únicas + 8 duplicadas + 2 vacías) y hoja Objetivos")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA / "facturacion_octubre_2026.xlsx")
