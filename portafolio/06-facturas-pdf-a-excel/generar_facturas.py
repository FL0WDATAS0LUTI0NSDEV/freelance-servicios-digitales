"""Genera facturas en PDF con DATOS FICTICIOS para el ejemplo 6.

Compras (carpeta facturas/): 18 comprobantes de 7 proveedores inventados, con dos
diseños distintos (como pasa en la realidad: cada proveedor factura con su sistema).
Incluye a propósito:
- un comprobante duplicado y uno con CUIT mal cargado, para mostrar los controles;
- dos notas de crédito, una factura de energía con IVA 27 %, percepción de IVA y
  concepto no gravado, y un flete con seguro exento.

Ventas (carpeta facturas_ventas/): 7 comprobantes que emite la ferretería con su
propio sistema: facturas A a responsables inscriptos, facturas B a consumidores
finales (con el IVA contenido de la Ley 27.743), una nota de crédito y un salto
de numeración, para mostrar el control de correlatividad.

Uso:  python generar_facturas.py
"""
from pathlib import Path
import random

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

AQUI = Path(__file__).parent
CARPETA = AQUI / "facturas"
CARPETA_VENTAS = AQUI / "facturas_ventas"

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
COOPERATIVA = ("Cooperativa Eléctrica del Centro Ltda", cuit_valido("3099000083"), "clasico")

CLIENTES = [  # clientes de la ferretería (ventas), responsables inscriptos
    ("Constructora Río Seco SRL", cuit_valido("3099000091")),
    ("Instalaciones Norte SA", cuit_valido("3099000105")),
]

ITEMS = {
    "Distribuidora Andina SA": [("Tornillos autoperforantes x100", 21), ("Tarugos nylon x50", 21)],
    "Herramientas del Sur SRL": [("Taladro percutor 650 W", 21), ("Juego de mechas x10", 21)],
    "Pinturas Litoral SA": [("Látex interior 20 L", 21), ("Rodillo antigota", 21)],
    "Electro Cuyo SRL": [("Cable unipolar 2,5 mm x100 m", 21), ("Térmica bipolar 20 A", 10.5)],
    "Bulonera Central SA": [("Bulones 8 x 40 x100", 21), ("Arandelas planas x500", 21)],
    "Logística Pampa SRL": [("Flete Rosario - Córdoba", 21)],
}


def comprobante(nombre, cuit, diseno, numero, fecha, lineas, **extra):
    comp = {
        "proveedor": nombre, "cuit": cuit, "diseno": diseno, "clase": "factura",
        "tipo": "A", "pv": 3 if diseno == "clasico" else 12, "numero": numero, "fecha": fecha,
        "lineas": lineas, "percepcion_iibb": 0.0, "percepcion_iva": 0.0,
        "no_gravado": 0.0, "exento": 0.0, "receptor": COMPRADOR,
    }
    comp.update(extra)
    return comp


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
        comps.append(comprobante(nombre, cuit, diseno, numero[nombre], f"{dia:02d}/10/2026",
                                 lineas, percepcion_iibb=percep))
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

    # Casos que aparecen en cualquier mes real de un estudio
    andina, herramientas, logistica = PROVEEDORES[0], PROVEEDORES[1], PROVEEDORES[5]
    # Energía: IVA 27 %, percepción de IVA y contribución municipal no gravada
    energia = [("Consumo energía comercial (T2) set-oct", 1, 412_380.55, 27)]
    comps.append(comprobante(*COOPERATIVA, 88_412, "21/10/2026", energia,
                             percepcion_iva=round(412_380.55 * 0.03, 2), no_gravado=18_640.00))
    # Nota de crédito por devolución de mercadería
    comps.append(comprobante(*herramientas, 731, "23/10/2026",
                             [("Devolución juego de mechas x10 (fallado)", 2, 12_480.00, 21)],
                             clase="nc"))
    # Flete con seguro de mercadería exento y percepción de IVA
    comps.append(comprobante(*logistica, numero[logistica[0]] + 18, "27/10/2026",
                             [("Flete Rosario - Córdoba", 1, 186_500.00, 21)],
                             exento=9_325.00, percepcion_iva=round(186_500.00 * 0.03, 2)))
    # Nota de crédito por bonificación comercial
    comps.append(comprobante(*andina, 418, "30/10/2026",
                             [("Bonificación por volumen octubre", 1, 25_000.00, 21)],
                             clase="nc"))
    return comps


def armar_ventas():
    """Comprobantes que emite la ferretería (punto de venta 2, su propio sistema)."""
    v = []
    base = dict(proveedor=COMPRADOR[0], cuit=COMPRADOR[1], diseno="propio", pv=2,
                percepcion_iibb=0.0, percepcion_iva=0.0, no_gravado=0.0, exento=0.0)
    a = [  # facturas A: el 103 falta a propósito (anulado o no informado)
        (101, "05/10/2026", CLIENTES[0], [("Cemento portland x50 kg", 40, 9_850.00, 21),
                                         ("Disyuntor diferencial 40 A", 2, 38_400.00, 10.5)]),
        (102, "12/10/2026", CLIENTES[1], [("Caño termofusión 20 mm x4 m", 60, 3_920.00, 21)]),
        (104, "26/10/2026", CLIENTES[0], [("Hierro del 8 x12 m", 30, 11_240.00, 21)]),
    ]
    for nro, fecha, cli, lineas in a:
        v.append(dict(base, clase="factura", tipo="A", numero=nro, fecha=fecha,
                      receptor=cli, lineas=lineas))
    b = [  # facturas B a consumidor final: precios con IVA incluido
        (501, "07/10/2026", [("Pintura látex 4 L", 2, 31_460.00, 21)]),
        (502, "15/10/2026", [("Llave francesa 10\"", 1, 24_200.00, 21), ("Cinta métrica 5 m", 1, 8_470.00, 21)]),
        (503, "29/10/2026", [("Escalera aluminio 6 escalones", 1, 96_800.00, 21)]),
    ]
    for nro, fecha, lineas in b:
        v.append(dict(base, clase="factura", tipo="B", numero=nro, fecha=fecha,
                      receptor=("Consumidor final", None), lineas=lineas))
    v.append(dict(base, clase="nc", tipo="A", numero=11, fecha="28/10/2026", receptor=CLIENTES[1],
                  lineas=[("Devolución caño termofusión 20 mm x4 m", 5, 3_920.00, 21)]))
    return v


def montos(comp):
    """Netos e IVA por alícuota y total. En las facturas B el precio incluye IVA."""
    netos = {}
    if comp.get("tipo") == "B":
        total = round(sum(c * p for _, c, p, _ in comp["lineas"]), 2)
        alic = comp["lineas"][0][3]
        iva = round(total - total / (1 + alic / 100), 2)
        return {alic: round(total - iva, 2)}, {alic: iva}, total
    for _, cant, precio, alic in comp["lineas"]:
        netos[alic] = round(netos.get(alic, 0) + cant * precio, 2)
    ivas = {a: round(n * a / 100, 2) for a, n in netos.items()}
    total = round(sum(netos.values()) + sum(ivas.values()) + comp["percepcion_iibb"]
                  + comp["percepcion_iva"] + comp["no_gravado"] + comp["exento"], 2)
    return netos, ivas, total


def fmt(x: float) -> str:
    s = f"{x:,.2f}"
    return "$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def alic_txt(a) -> str:
    return f"{a:g}".replace(".", ",")


def titulo_comp(comp) -> str:
    return "NOTA DE CRÉDITO" if comp["clase"] == "nc" else "FACTURA"


CODIGOS = {("factura", "A"): "01", ("nc", "A"): "03", ("factura", "B"): "06", ("nc", "B"): "08"}


def marca_ficticia(c):
    c.saveState()
    c.setFillColor(colors.Color(0.85, 0.1, 0.1, alpha=0.12))
    c.setFont("Helvetica-Bold", 54)
    c.translate(105 * mm, 150 * mm)
    c.rotate(35)
    c.drawCentredString(0, 0, "DATOS FICTICIOS")
    c.restoreState()


def otros_conceptos(comp, etiquetas):
    """Filas de no gravado, exento y percepciones, con las etiquetas de cada diseño."""
    filas = []
    for clave, texto in etiquetas:
        if comp[clave]:
            filas.append((texto, comp[clave]))
    return filas


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
    c.drawString(125 * mm, h - 25 * mm, titulo_comp(comp))
    c.setFont("Helvetica", 9)
    c.drawString(125 * mm, h - 31 * mm, f"Punto de Venta: {comp['pv']:05d}  Comp. Nro: {comp['numero']:08d}")
    c.drawString(125 * mm, h - 36 * mm, f"Fecha de Emisión: {comp['fecha']}")
    c.line(20 * mm, h - 45 * mm, 190 * mm, h - 45 * mm)
    c.drawString(20 * mm, h - 52 * mm, f"Señor(es): {comp['receptor'][0]}   CUIT: {comp['receptor'][1]}")
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
        c.drawString(160 * mm, y, f"{alic_txt(alic)}%")
        c.drawRightString(195 * mm, y, fmt(cant * precio))
    y = 90 * mm
    c.line(110 * mm, y + 8 * mm, 195 * mm, y + 8 * mm)
    filas = []
    for a in sorted(netos, reverse=True):
        filas += [(f"Importe Neto Gravado {alic_txt(a)}%:", netos[a]), (f"IVA {alic_txt(a)}%:", ivas[a])]
    filas += otros_conceptos(comp, [("no_gravado", "Importe No Gravado:"), ("exento", "Importe Exento:"),
                                    ("percepcion_iva", "Percepción IVA:"), ("percepcion_iibb", "Percepción IIBB:")])
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
    codigo = CODIGOS[(comp["clase"], comp["tipo"])]
    c.drawRightString(192 * mm, h - 16 * mm, f"{titulo_comp(comp)} {comp['tipo']}  -  Cód. {codigo}")
    c.setFont("Helvetica", 9)
    c.drawRightString(192 * mm, h - 23 * mm, f"N° {comp['pv']:04d}-{comp['numero']:08d}")
    c.drawRightString(192 * mm, h - 29 * mm, f"Fecha: {comp['fecha']}")
    c.setFillColor(colors.black)
    c.drawString(18 * mm, h - 48 * mm, f"Cliente: {comp['receptor'][0]}")
    c.drawString(18 * mm, h - 54 * mm, f"CUIT cliente: {comp['receptor'][1]}   Condición de venta: Cuenta corriente")
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
        c.drawString(130 * mm, y, f"{alic_txt(alic)}%")
        c.drawString(150 * mm, y, fmt(precio))
        c.drawRightString(192 * mm, y, fmt(cant * precio))
    y = 85 * mm
    c.setFont("Helvetica", 10)
    filas = [("Subtotal neto", sum(netos.values()))]
    if len(netos) > 1:  # con varias alícuotas, este diseño discrimina el neto de cada una
        filas += [(f"Neto {alic_txt(a)}%", netos[a]) for a in sorted(netos, reverse=True)]
    for a in sorted(netos, reverse=True):
        filas.append((f"IVA {alic_txt(a)}%", ivas[a]))
    filas += otros_conceptos(comp, [("no_gravado", "No gravado"), ("exento", "Exento"),
                                    ("percepcion_iva", "Perc. IVA"), ("percepcion_iibb", "Perc. Ingresos Brutos")])
    for t, v in filas:
        c.drawString(120 * mm, y, t)
        c.drawRightString(192 * mm, y, fmt(v))
        y -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(120 * mm, y - 2 * mm, "TOTAL")
    c.drawRightString(192 * mm, y - 2 * mm, fmt(total))
    c.setFont("Helvetica", 8)
    c.drawString(18 * mm, 22 * mm, f"CAE {8000000000000 + comp['numero']}  -  Vencimiento CAE 30/11/2026")


def pdf_propio(c, comp):
    """Diseño del sistema de facturación de la ferretería (ventas)."""
    netos, ivas, total = montos(comp)
    w, h = A4
    c.setStrokeColor(colors.HexColor("#00B8D4"))
    c.setLineWidth(1.5)
    c.line(18 * mm, h - 40 * mm, 192 * mm, h - 40 * mm)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(18 * mm, h - 20 * mm, comp["proveedor"])
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, h - 26 * mm, f"CUIT: {comp['cuit']} - IVA Responsable Inscripto")
    codigo = CODIGOS[(comp["clase"], comp["tipo"])]
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(192 * mm, h - 18 * mm, f"{titulo_comp(comp)} {comp['tipo']}")
    c.setFont("Helvetica", 9)
    c.drawRightString(192 * mm, h - 24 * mm, f"Código {codigo}")
    c.drawRightString(192 * mm, h - 29 * mm, f"Punto de Venta: {comp['pv']:05d} Comp. Nro: {comp['numero']:08d}")
    c.drawRightString(192 * mm, h - 34 * mm, f"Fecha: {comp['fecha']}")
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, h - 48 * mm, f"Cliente: {comp['receptor'][0]}")
    if comp["receptor"][1]:
        c.drawString(18 * mm, h - 54 * mm, f"CUIT cliente: {comp['receptor'][1]}")
        c.drawString(18 * mm, h - 60 * mm, "Condición frente al IVA: Responsable Inscripto")
    else:
        c.drawString(18 * mm, h - 54 * mm, "Condición frente al IVA: Consumidor Final")
    y = h - 72 * mm
    c.setFont("Helvetica-Bold", 9)
    for x, t in [(18, "Cant."), (32, "Producto"), (125, "Alic."), (145, "Precio"), (175, "Importe")]:
        c.drawString(x * mm, y, t)
    c.setFont("Helvetica", 9)
    for desc, cant, precio, alic in comp["lineas"]:
        y -= 7 * mm
        c.drawString(18 * mm, y, str(cant))
        c.drawString(32 * mm, y, desc)
        c.drawString(125 * mm, y, f"{alic_txt(alic)}%")
        c.drawString(145 * mm, y, fmt(precio))
        c.drawRightString(192 * mm, y, fmt(cant * precio))
    y = 85 * mm
    if comp["tipo"] == "B":
        c.setFont("Helvetica-Bold", 11)
        c.drawString(115 * mm, y, "Importe Total:")
        c.drawRightString(192 * mm, y, fmt(total))
        c.setFont("Helvetica", 8)
        c.drawString(18 * mm, y - 12 * mm, "Régimen de Transparencia Fiscal al Consumidor (Ley 27.743)")
        c.drawString(18 * mm, y - 17 * mm, f"IVA Contenido: {fmt(sum(ivas.values()))}")
    else:
        filas = []
        for a in sorted(netos, reverse=True):
            filas += [(f"Neto Gravado {alic_txt(a)}%:", netos[a]), (f"IVA {alic_txt(a)}%:", ivas[a])]
        filas.append(("Importe Total:", total))
        for t, v in filas:
            c.setFont("Helvetica-Bold" if t.startswith("Importe Total") else "Helvetica", 10)
            c.drawString(115 * mm, y, t)
            c.drawRightString(192 * mm, y, fmt(v))
            y -= 6 * mm
    c.setFont("Helvetica", 8)
    c.drawString(18 * mm, 22 * mm, f"CAE {9000000000000 + comp['numero']}  -  Vto. CAE 30/11/2026")


DISENOS = {"clasico": pdf_clasico, "moderno": pdf_moderno, "propio": pdf_propio}


def nombre_archivo(i: int, comp: dict, ventas: bool = False) -> str:
    if ventas:
        quien = "cf" if not comp["receptor"][1] else comp["receptor"][0].split()[0].lower().replace("í", "i")
        clase = "nc" if comp["clase"] == "nc" else "fc"
        return f"{i:02d}_{clase}{comp['tipo'].lower()}_{quien}_{comp['pv']:04d}-{comp['numero']:08d}.pdf"
    slug = comp["proveedor"].split()[0].lower().replace("í", "i")
    if comp["clase"] == "nc":
        slug += "_nc"
    return f"{i:02d}_{slug}_{comp['pv']:04d}-{comp['numero']:08d}.pdf"


def escribir(carpeta: Path, comps: list, ventas: bool = False):
    carpeta.mkdir(exist_ok=True)
    for f in carpeta.glob("*.pdf"):
        f.unlink()
    for i, comp in enumerate(comps, 1):
        c = canvas.Canvas(str(carpeta / nombre_archivo(i, comp, ventas)), pagesize=A4)
        c.setTitle("Factura de ejemplo - datos ficticios")
        DISENOS[comp["diseno"]](c, comp)
        marca_ficticia(c)
        c.showPage()
        c.save()
    print(f"{len(comps)} comprobantes generados en {carpeta}")


def main():
    escribir(CARPETA, armar_comprobantes())
    escribir(CARPETA_VENTAS, armar_ventas(), ventas=True)


if __name__ == "__main__":
    main()
