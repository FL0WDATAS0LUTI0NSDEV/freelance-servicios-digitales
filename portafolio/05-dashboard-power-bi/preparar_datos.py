"""
Prepara los datos del ejemplo de Power BI en modelo estrella (datos ficticios).

Lee las ventas de ../04-dashboard-interactivo/ventas_2025.csv y genera en ./datos:
- Ventas.csv        (tabla de hechos)
- Clientes.csv      (dimensión)
- Productos.csv     (dimensión)
- Vendedores.csv    (dimensión)
- Calendario.csv    (dimensión de fechas en español)
- Objetivos.csv     (objetivo mensual de ventas por vendedor)

Uso:
    python preparar_datos.py
"""
import csv
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

random.seed(7)
BASE = Path(__file__).parent
OUT = BASE / "datos"
OUT.mkdir(exist_ok=True)
ventas = list(csv.DictReader(open(BASE.parent / "04-dashboard-interactivo" / "ventas_2025.csv", encoding="utf-8")))

TIPO = {"Almacén Don Pepe": "Almacén", "Kiosco La Esquina": "Kiosco", "Supermercado Sol": "Supermercado",
        "Dietética Natura": "Dietética", "Bar El Faro": "Gastronomía", "Rotisería Doña Rosa": "Gastronomía",
        "Autoservicio Mitre": "Supermercado", "Mercadito Central": "Almacén"}
CATEGORIA = {"Yerba 1kg": "Infusiones", "Café 500g": "Infusiones", "Azúcar 1kg": "Almacén",
             "Aceite 900ml": "Almacén", "Harina 1kg": "Almacén", "Galletitas 300g": "Snacks"}
PRECIO_LISTA = {"Yerba 1kg": 4200, "Café 500g": 6800, "Azúcar 1kg": 1500, "Aceite 900ml": 3100,
                "Harina 1kg": 1100, "Galletitas 300g": 1900}
ZONA = {"Laura Gómez": "Centro", "Martín Ruiz": "Norte", "Sofía Paz": "Sur"}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

def ids(values, prefix):
    return {v: f"{prefix}{i:02d}" for i, v in enumerate(sorted(values), start=1)}

cli_id = ids({v["cliente"] for v in ventas}, "C")
prod_id = ids({v["producto"] for v in ventas}, "P")
vend_id = ids({v["vendedor"] for v in ventas}, "V")
prov_cli = {v["cliente"]: v["provincia"] for v in ventas}

def write(name, header, rows):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

write("Ventas.csv", ["VentaID", "Fecha", "ClienteID", "ProductoID", "VendedorID", "Cantidad", "Monto"],
      [[f"V{i:05d}", v["fecha"], cli_id[v["cliente"]], prod_id[v["producto"]], vend_id[v["vendedor"]],
        v["cantidad"], v["monto"]] for i, v in enumerate(ventas, start=1)])
write("Clientes.csv", ["ClienteID", "Cliente", "TipoCliente", "Provincia"],
      [[i, c, TIPO[c], prov_cli[c]] for c, i in sorted(cli_id.items(), key=lambda x: x[1])])
write("Productos.csv", ["ProductoID", "Producto", "Categoria", "PrecioLista"],
      [[i, p, CATEGORIA[p], PRECIO_LISTA[p]] for p, i in sorted(prod_id.items(), key=lambda x: x[1])])
write("Vendedores.csv", ["VendedorID", "Vendedor", "Zona"],
      [[i, v, ZONA[v]] for v, i in sorted(vend_id.items(), key=lambda x: x[1])])

d, cal = date(2025, 1, 1), []
while d <= date(2025, 12, 31):
    cal.append([d.isoformat(), d.year, d.month, MESES[d.month - 1], f"{MESES[d.month - 1]} {d.year}",
                f"T{(d.month - 1) // 3 + 1}", d.isocalendar()[1], d.isoweekday(), DIAS[d.weekday()]])
    d += timedelta(days=1)
write("Calendario.csv", ["Fecha", "Anio", "MesNum", "Mes", "MesAnio", "Trimestre", "SemanaNum", "DiaSemanaNum", "DiaSemana"], cal)

# Objetivo mensual por vendedor: ventas reales del mes ajustadas entre -10 % y +20 % (ficticio)
real = defaultdict(float)
for v in ventas:
    real[(v["fecha"][:7], v["vendedor"])] += float(v["monto"])
obj = []
for (mes, vend), monto in sorted(real.items()):
    obj.append([f"{mes}-01", vend_id[vend], int(round(monto * random.uniform(0.9, 1.2), -3))])
write("Objetivos.csv", ["Fecha", "VendedorID", "Objetivo"], obj)

for f in sorted(OUT.iterdir()):
    print(f"{f.name}: {sum(1 for _ in open(f, encoding='utf-8')) - 1} filas")
