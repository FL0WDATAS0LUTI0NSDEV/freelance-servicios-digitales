"""
Genera los datos (ficticios) del dashboard: 12 meses de ventas de una distribuidora.

Uso:
    python generar_datos.py

Crea:
- ventas_2025.csv  -> datos en formato planilla
- datos.js         -> los mismos datos para el dashboard (window.FDS_DATA)

En un proyecto real, este paso se reemplaza por la planilla o el sistema del cliente.
"""
import csv
import json
import random
from datetime import date, timedelta

random.seed(2025)

CLIENTES = {"Almacén Don Pepe": 1.0, "Kiosco La Esquina": 1.3, "Supermercado Sol": 2.2,
            "Dietética Natura": 0.8, "Bar El Faro": 0.9, "Rotisería Doña Rosa": 0.7,
            "Autoservicio Mitre": 1.6, "Mercadito Central": 1.2}
PROVINCIA = {"Almacén Don Pepe": "Buenos Aires", "Kiosco La Esquina": "Buenos Aires",
             "Supermercado Sol": "Córdoba", "Dietética Natura": "Santa Fe", "Bar El Faro": "Córdoba",
             "Rotisería Doña Rosa": "Santa Fe", "Autoservicio Mitre": "Buenos Aires",
             "Mercadito Central": "Mendoza"}
PRODUCTOS = {"Yerba 1kg": 4200, "Café 500g": 6800, "Azúcar 1kg": 1500, "Aceite 900ml": 3100,
             "Harina 1kg": 1100, "Galletitas 300g": 1900}
VENDEDORES = ["Laura Gómez", "Martín Ruiz", "Sofía Paz"]
# Estacionalidad: más ventas en invierno (yerba/café) y en diciembre
ESTACION = {1: .85, 2: .8, 3: .95, 4: 1.0, 5: 1.1, 6: 1.25, 7: 1.3, 8: 1.15, 9: 1.0, 10: 1.0, 11: 1.05, 12: 1.35}
INFLACION_MENSUAL = 0.02  # los precios suben 2 % por mes (dato ficticio)

filas = []
d = date(2025, 1, 1)
while d <= date(2025, 12, 31):
    if d.weekday() < 6:  # lunes a sábado
        for _ in range(random.choices([0, 1, 2, 3], [25, 40, 25, 10])[0]):
            if random.random() > ESTACION[d.month] * 0.75:
                continue
            cliente = random.choices(list(CLIENTES), list(CLIENTES.values()))[0]
            producto = random.choice(list(PRODUCTOS))
            cantidad = max(1, int(random.gauss(10, 5) * CLIENTES[cliente]))
            precio = PRODUCTOS[producto] * (1 + INFLACION_MENSUAL) ** (d.month - 1)
            filas.append({"fecha": d.isoformat(), "cliente": cliente, "producto": producto,
                          "cantidad": cantidad, "monto": round(cantidad * precio),
                          "vendedor": random.choice(VENDEDORES), "provincia": PROVINCIA[cliente]})
    d += timedelta(days=1)

with open("ventas_2025.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)

with open("datos.js", "w", encoding="utf-8") as f:
    f.write("// Datos ficticios generados por generar_datos.py\n")
    f.write("window.FDS_DATA = " + json.dumps(filas, ensure_ascii=False, separators=(",", ":")) + ";\n")

print(f"{len(filas)} ventas generadas · total $ {sum(r['monto'] for r in filas):,.0f}".replace(",", "."))
