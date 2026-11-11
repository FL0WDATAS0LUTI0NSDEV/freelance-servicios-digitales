"""Genera facturas de compra en PDF con DATOS FICTICIOS para el ejemplo 6.

Crea 14 comprobantes de 6 proveedores inventados, con dos diseños distintos
(como pasa en la realidad: cada proveedor factura con su propio sistema).
Incluye a propósito un comprobante duplicado y uno con CUIT mal cargado,
para mostrar los controles del extractor.

Uso:  python generar_facturas.py
"""
from pathlib import Path
import random

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

CARPETA = Path(__file__).parent / "facturas"

PROVEEDORES = [
    # razón social, CUIT (rango ficticio 30-99...), diseño
    ("Distribuidora Andina SA", "30-99000025-3", "clasico"),
    ("Herramientas del Sur SRL", "30-99000033-4", "moderno"),
    ("Pinturas Litoral SA", "30-99000041-5", "clasico"),
    ("Electro Cuyo SRL", "30-99000059-8", "moderno"),
    ("Bulonera Central SA", "30-99000067-9", "clasico"),
    ("Logística Pampa SRL", "30-99000075-0", "moderno"),
]


def digito_cuit(base10: str) -> int:
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    r = 11 - sum(int(d) * p for d, p in zip(base10, pesos)) % 11
    return 0 if r == 11 else 9 if r == 10 else r


def cuit_valido(base10: str) -> str:
    d = digito_cuit(base10)
    return f"{base10[:2]}-{base10[2:]}-{d}"


# Recalcula los CUIT para que el dígito verificador sea correcto
COMPRADOR = ("Ferretería El Tornillo SRL (ficticia)", cuit_valido("3099000017"))
PROVEEDORES = [(n, cuit_valido(c.replace("-", "")[:10]), d) for n, c, d in PROVEEDORES]

ITEMS = {
    "Distribuidora Andina SA": [("Tornillos autoperforantes x100", 21), ("Tarugos nylon x50", 21)],
    "Herramientas del Sur SRL": [("Taladro percutor 650 W", 21), ("Juego de mechas x10", 21)],
    "Pinturas Litoral SA": [("Látex interior 20 L", 21), ("Rodillo antigota", 21)],
    "Electro Cuyo SRL": [("Cable unipolar 2,5 mm x100 m", 21), ("Térmica bipolar 20 A", 10.5)],
    "Bulonera Central SA": [("Bulones 8 x 40 x100", 21), ("Arandelas planas x500", 21)],
    "Logística Pampa SRL": [("Flete Rosario - Córdoba", 21)],
}


def armar_comprobantes():
    random.seed(7)
    comps = []
    numero = {p[0]: random.randint(1200, 4800) for p in PROVEEDORES}
    for i in range(12):
        nombre, cuit, diseno = PROVEEDORES[i % len(PROVEEDORES)]
        numero[nombre] += random.randint(3, 40)
        dia = 2 + i * 2
        lineas = []
        for desc, alic in ITEMS[nombre]:
            cant = random.randint(1, 12)
            precio = round(random.uniform(4000, 95000), 2)
            lineas.append((desc, cant, precio, alic))
        percep = round(random.choice([0, 0, 0.03]) * sum(c * p for _, c, p, _ in lineas), 2)
        comps.append({
            "proveedor": nombre, "cuit": cuit, "diseno": diseno,
            "tipo": "A", "pv": 3 if diseno == "clasico" else 12,
            "numero": numero[nombre], "fecha": f"{dia:02d}/10/2026",
            "lineas": lineas, "percepcion_iibb": percep,
        })
    # Duplicado: el mismo comprobante llegó dos veces por mail
    dup = dict(comps[4])
    comps.append(dup)
    # CUIT mal tipeado por el sistema del proveedor (dígito verificador inválido)
    malo = dict(comps[7])
    malo["numero"] += 9
    c = malo["cuit"]
    malo["cuit"] = c[:-1] + str((int(c[-1]) + 1) % 10)
    malo["fecha"] = "28/10/2026"
    comps.append(malo)
    return comps


def montos(comp):
    netos = {}
    for _, cant, precio, alic in comp["lineas"]:
        netos[alic] = round(netos.get(alic, 0) + cant * precio, 2)
    ivas = {a: round(n * a / 100, 2) for a, n in netos.items()}
    total = round(sum(netos.values()) + sum(ivas.values()) + comp["percepcion_iibb"], 2)
    return netos, ivas, total


def fmt(x: float) -> str:
    s = f"{x:,.2f}"
    return "$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def marca_ficticia(c):
    c.saveState()
    c.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.12))
    c.setFont("Helvetica-Bold", 54)
    c.translate(105 * mm, 150 * mm)
    c.rotate(35)
    c.drawCentredString(0, 0, "DATOS FICTICIOS")
    c.restoreState()


def pdf_clasico(c, comp):
    netos, ivas, total = montos(comp)
    w, h = A4
    c.setFont("Helvetica-Bold", 15)
    c.drawString(20 * mm, h - 25 * mm, comp["proveedor"])
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, h - 31 * mm, f"CUIT: {comp['cuit']}   IVA Responsable Inscripto")
    c.rect(95 * mm, h - 40 * mm, 20 * mm, 18 * mm)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(105 * mm, h - 33 * mm, comp["tipo"])
    c.setFont("Helvetica-Bold", 13)
    c.drawString(125 * mm, h - 25 * mm, "FACTURA")
    c.setFont("Helvetica", 9)
    c.drawString(125 * mm, h - 31 * mm, f"Punto de Venta: {comp['pv']:05d}  Comp. Nro: {comp['numero']:08d}")
    c.drawString(125 * mm, h - 36 * mm, f"Fecha de Emisión: {comp['fecha']}")
    c.line(20 * mm, h - 45 * mm, 190 * mm, h - 45 * mm)
    c.drawString(20 * mm, h - 52 * mm, f"Señor(es): {COMPRADOR[0]}   CUIT: {COMPRADOR[1]}")
    y = h - 65 * mm
    c.setFont("Helvetica-Bold", 9)
    for x, t in [(20, "Descripción"), (115, "Cant."), (135, "P. Unit."), (160, "Alic."), (175, "Subtotal")]:
        c.drawString(x * mm, y, t)
    c.setFont("Helvetica", 9)
    for desc, cant, precio, alic in comp["lineas"]:
        y -= 7 * mm
        c.drawString(20 * mm, y, desc)
        c.drawString(115 * mm, y, str(cant))
        c.drawString(135 * mm, y, fmt(precio))
        c.drawString(160 * mm, y, f"{alic:g}%".replace(".", ","))
        c.drawRightString(195 * mm, y, fmt(cant * precio))
    y = 90 * mm
    c.line(110 * mm, y + 8 * mm, 195 * mm, y + 8 * mm)
    filas = []
    for a in sorted(netos, reverse=True):
        etiqueta = f"{a:g}".replace(".", ",")
        filas += [(f"Importe Neto Gravado {etiqueta}%:", netos[a]), (f"IVA {etiqueta}%:", ivas[a])]
    if comp["percepcion_iibb"]:
        filas.append(("Percepción IIBB:", comp["percepcion_iibb"]))
    filas.append(("Importe Total:", total))
    for t, v in filas:
        c.setFont("Helvetica-Bold" if t.startswith("Importe Total") else "Helvetica", 10)
        c.drawString(110 * mm, y, t)
        c.drawRightString(195 * mm, y, fmt(v))
        y -= 6 * mm
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, 25 * mm, f"CAE N°: 7{comp['numero']:013d}   Vto. CAE: 30/11/2026")


def pdf_moderno(c, comp):
    netos, ivas, total = montos(comp)
    w, h = A4
    c.setFillColor(colors.HexColor("#0B1325"))
    c.rect(0, h - 38 * mm, w, 38 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(18 * mm, h - 18 * mm, comp["proveedor"].upper())
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, h - 25 * mm, f"C.U.I.T. {comp['cuit']}")
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(192 * mm, h - 16 * mm, f"FACTURA {comp['tipo']}  -  Cód. 01")
    c.setFont("Helvetica", 9)
    c.drawRightString(192 * mm, h - 23 * mm, f"N° {comp['pv']:04d}-{comp['numero']:08d}")
    c.drawRightString(192 * mm, h - 29 * mm, f"Fecha: {comp['fecha']}")
    c.setFillColor(colors.black)
    c.drawString(18 * mm, h - 48 * mm, f"Cliente: {COMPRADOR[0]}")
    c.drawString(18 * mm, h - 54 * mm, f"CUIT cliente: {COMPRADOR[1]}   Condición de venta: Cuenta corriente")
    y = h - 68 * mm
    c.setFillColor(colors.HexColor("#E8EEF7"))
    c.rect(18 * mm, y - 2 * mm, 174 * mm, 7 * mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    for x, t in [(20, "Cant."), (35, "Detalle"), (130, "IVA"), (150, "Precio"), (175, "Importe")]:
        c.drawString(x * mm, y, t)
    c.setFont("Helvetica", 9)
    for desc, cant, precio, alic in comp["lineas"]:
        y -= 7 * mm
        c.drawString(20 * mm, y, f"{cant:>3}")
        c.drawString(35 * mm, y, desc)
        c.drawString(130 * mm, y, f"{alic:g}%".replace(".", ","))
        c.drawString(150 * mm, y, fmt(precio))
        c.drawRightString(192 * mm, y, fmt(cant * precio))
    y = 85 * mm
    c.setFont("Helvetica", 10)
    filas = [("Subtotal neto", sum(netos.values()))]
    if len(netos) > 1:  # con varias alícuotas, este diseño discrimina el neto de cada una
        filas += [(f"Neto {a:g}%".replace(".", ","), netos[a]) for a in sorted(netos, reverse=True)]
    for a in sorted(netos, reverse=True):
        filas.append((f"IVA {a:g}%".replace(".", ","), ivas[a]))
    if comp["percepcion_iibb"]:
        filas.append(("Perc. Ingresos Brutos", comp["percepcion_iibb"]))
    for t, v in filas:
        c.drawString(120 * mm, y, t)
        c.drawRightString(192 * mm, y, fmt(v))
        y -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(120 * mm, y - 2 * mm, "TOTAL")
    c.drawRightString(192 * mm, y - 2 * mm, fmt(total))
    c.setFont("Helvetica", 8)
    c.drawString(18 * mm, 22 * mm, f"CAE {8000000000000 + comp['numero']}  -  Vencimiento CAE 30/11/2026")


def main():
    CARPETA.mkdir(exist_ok=True)
    for f in CARPETA.glob("*.pdf"):
        f.unlink()
    comps = armar_comprobantes()
    for i, comp in enumerate(comps, 1):
        slug = comp['proveedor'].split()[0].lower().replace('í', 'i')
        nombre = f"{i:02d}_{slug}_{comp['pv']:04d}-{comp['numero']:08d}.pdf"
        c = canvas.Canvas(str(CARPETA / nombre), pagesize=A4)
        c.setTitle("Factura de ejemplo - datos ficticios")
        (pdf_clasico if comp["diseno"] == "clasico" else pdf_moderno)(c, comp)
        marca_ficticia(c)
        c.showPage()
        c.save()
    print(f"{len(comps)} facturas generadas en {CARPETA}")


if __name__ == "__main__":
    main()
