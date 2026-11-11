"""Extrae los datos de facturas de compra en PDF y arma el Libro IVA Compras en Excel.

- Lee todos los PDF de una carpeta, aunque cada proveedor use un diseño distinto.
- Saca fecha, tipo, punto de venta, número, CUIT, razón social, netos por alícuota,
  IVA, percepciones y total.
- Si el proveedor no discrimina el neto por alícuota, lo calcula a partir del IVA.
- Controla: dígito verificador del CUIT, comprobantes duplicados, que la suma cuadre
  con el total y que la fecha esté dentro del período.

Uso:  python extraer_facturas.py [carpeta_pdf] [salida.xlsx] [MM/AAAA]
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

import pdfplumber
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

AQUI = Path(__file__).parent
TOL = 0.05  # tolerancia de redondeo en pesos


# ---------------------------------------------------------------- utilidades
def a_numero(txt: str) -> float:
    """'$ 1.234.567,89' -> 1234567.89"""
    return float(txt.replace("$", "").strip().replace(".", "").replace(",", "."))


def cuit_ok(cuit: str) -> bool:
    d = re.sub(r"\D", "", cuit)
    if len(d) != 11:
        return False
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    r = 11 - sum(int(a) * p for a, p in zip(d, pesos)) % 11
    esperado = 0 if r == 11 else 9 if r == 10 else r
    return esperado == int(d[-1])


def nombre_prolijo(razon: str) -> str:
    """'HERRAMIENTAS DEL SUR SRL' -> 'Herramientas del Sur SRL'"""
    if not razon.isupper():
        return razon
    chicas = {"de", "del", "la", "las", "los", "y", "e"}
    siglas = {"sa", "srl", "sas", "sh", "sci"}
    out = []
    for i, w in enumerate(razon.lower().split()):
        out.append(w.upper() if w in siglas else w if (i and w in chicas) else w.capitalize())
    return " ".join(out)


def texto_pdf(ruta: Path) -> str:
    with pdfplumber.open(ruta) as pdf:
        partes = []
        for page in pdf.pages:
            # Ignora letras gigantes (marcas de agua como "COPIA" o "DATOS FICTICIOS")
            limpia = page.filter(lambda o: not (o.get("object_type") == "char" and o.get("size", 0) > 30))
            partes.append(limpia.extract_text() or "")
    return "\n".join(partes)


IMPORTE = r"\$\s?([\d.]+,\d{2})"
PATRONES = {
    "fecha": [r"Fecha(?: de Emisión)?:\s*(\d{2}/\d{2}/\d{4})"],
    "tipo": [r"FACTURA\s+([ABCM])\b", r"^([ABCM])$"],
    "pv_nro": [r"Punto de Venta:\s*(\d+)\s+Comp\. Nro:\s*(\d+)", r"N°\s*(\d{4,5})-(\d{8})"],
    "cuit": [r"C\.?U\.?I\.?T\.?:?\s*(\d{2}-\d{8}-\d)"],
    "total": [r"Importe Total:\s*" + IMPORTE, r"^TOTAL\s+" + IMPORTE],
    "percepcion": [r"Percepci[oó]n IIBB:\s*" + IMPORTE, r"Perc\. Ingresos Brutos\s+" + IMPORTE],
}


def buscar(clave: str, texto: str):
    for p in PATRONES[clave]:
        m = re.search(p, texto, re.MULTILINE)
        if m:
            return m.groups()
    return None


def extraer(ruta: Path) -> dict:
    t = texto_pdf(ruta)
    primera = t.splitlines()[0]
    razon = re.sub(r"\s+FACTURA.*$", "", primera).strip()
    pv, nro = buscar("pv_nro", t)
    fila = {
        "archivo": ruta.name,
        "fecha": datetime.strptime(buscar("fecha", t)[0], "%d/%m/%Y").date(),
        "tipo": buscar("tipo", t)[0],
        "pv": int(pv),
        "numero": int(nro),
        "cuit": buscar("cuit", t)[0],
        "proveedor": nombre_prolijo(razon),
        "percepcion": a_numero(buscar("percepcion", t)[0]) if buscar("percepcion", t) else 0.0,
        "total": a_numero(buscar("total", t)[0]),
    }
    # IVA y neto por alícuota ("IVA 21%: $ x" o "IVA 21% $ x")
    for alic, col in (("21", "21"), ("10,5", "105")):
        m = re.search(rf"IVA {alic}%:?\s*" + IMPORTE, t)
        fila[f"iva_{col}"] = a_numero(m.group(1)) if m else 0.0
        m = re.search(rf"Neto(?: Gravado)? {alic}%:?\s*" + IMPORTE, t)
        fila[f"neto_{col}"] = a_numero(m.group(1)) if m else None
    # Si el proveedor solo informa un subtotal neto, se reparte por alícuota:
    # el 10,5 % se calcula desde su IVA y el resto queda en 21 %.
    m = re.search(r"Subtotal neto\s+" + IMPORTE, t)
    if fila["neto_21"] is None or fila["neto_105"] is None:
        subtotal = a_numero(m.group(1)) if m else None
        n105 = fila["neto_105"] if fila["neto_105"] is not None else round(fila["iva_105"] / 0.105, 2)
        n21 = fila["neto_21"] if fila["neto_21"] is not None else (
            round(subtotal - n105, 2) if subtotal is not None else round(fila["iva_21"] / 0.21, 2))
        fila["neto_21"], fila["neto_105"] = n21, n105
    return fila


# ---------------------------------------------------------------- controles
def controlar(filas: list[dict], periodo: str):
    vistos, libro, obs = {}, [], []
    mes, anio = map(int, periodo.split("/"))
    for f in filas:
        clave = (f["cuit"], f["tipo"], f["pv"], f["numero"])
        if clave in vistos:
            obs.append(("Duplicado", f["archivo"], f"Mismo comprobante que {vistos[clave]}: no se carga dos veces."))
            continue
        vistos[clave] = f["archivo"]
        notas = []
        if not cuit_ok(f["cuit"]):
            notas.append("CUIT inválido")
            obs.append(("CUIT inválido", f["archivo"], f"{f['cuit']}: el dígito verificador no corresponde. Pedir al proveedor que lo corrija."))
        suma = f["neto_21"] + f["iva_21"] + f["neto_105"] + f["iva_105"] + f["percepcion"]
        if abs(suma - f["total"]) > TOL:
            notas.append("No cuadra")
            obs.append(("Total no cuadra", f["archivo"], f"Netos + IVA + percepciones = {suma:,.2f} vs total {f['total']:,.2f}."))
        if (f["fecha"].month, f["fecha"].year) != (mes, anio):
            notas.append("Fuera de período")
            obs.append(("Fuera de período", f["archivo"], f"Fecha {f['fecha']:%d/%m/%Y} fuera de {periodo}."))
        f["control"] = ", ".join(notas) or "OK"
        libro.append(f)
    libro.sort(key=lambda f: (f["fecha"], f["cuit"], f["numero"]))
    return libro, obs


# ---------------------------------------------------------------- Excel
AZUL = "0B1325"
CIAN = "00B8D4"
FINO = Side(style="thin", color="D0D7E2")
MONEDA = '#,##0.00;[Red]-#,##0.00'


def encabezado(ws, fila, titulos):
    for i, t in enumerate(titulos, 1):
        c = ws.cell(row=fila, column=i, value=t)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=AZUL)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(bottom=Side(style="medium", color=CIAN))
    ws.row_dimensions[fila].height = 30


def titulo(ws, texto, sub):
    ws["A1"] = texto
    ws["A1"].font = Font(bold=True, size=14, color=AZUL)
    ws["A2"] = sub
    ws["A2"].font = Font(italic=True, size=9, color="6B7280")


def escribir_excel(libro, obs, salida: Path, periodo: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Libro IVA Compras"
    titulo(ws, f"Libro IVA Compras — {periodo}",
           "Ejemplo con datos ficticios · generado automáticamente desde los PDF de las facturas")
    cols = ["Fecha", "Tipo", "Pto. Vta.", "Número", "CUIT", "Proveedor", "Neto 21%", "IVA 21%",
            "Neto 10,5%", "IVA 10,5%", "Perc. IIBB", "Total", "Control", "Archivo"]
    encabezado(ws, 4, cols)
    r0 = 5
    for i, f in enumerate(libro):
        r = r0 + i
        vals = [f["fecha"], f["tipo"], f["pv"], f["numero"], f["cuit"], f["proveedor"], f["neto_21"],
                f["iva_21"], f["neto_105"], f["iva_105"], f["percepcion"], f["total"], f["control"], f["archivo"]]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=r, column=j, value=v)
            c.border = Border(bottom=FINO)
            if j == 1:
                c.number_format = "DD/MM/YYYY"
            elif j == 3:
                c.number_format = "00000"
            elif j == 4:
                c.number_format = "00000000"
            elif 7 <= j <= 12:
                c.number_format = MONEDA
        if f["control"] != "OK":
            ws.cell(row=r, column=13).font = Font(bold=True, color="B91C1C")
            ws.cell(row=r, column=13).fill = PatternFill("solid", fgColor="FDECEC")
        else:
            ws.cell(row=r, column=13).font = Font(color="047857")
    rt = r0 + len(libro)
    ws.cell(row=rt, column=6, value="TOTALES").font = Font(bold=True)
    for j in range(7, 13):
        L = get_column_letter(j)
        c = ws.cell(row=rt, column=j, value=f"=SUM({L}{r0}:{L}{rt - 1})")
        c.font = Font(bold=True)
        c.number_format = MONEDA
        c.border = Border(top=Side(style="medium", color=AZUL))
    anchos = [11, 6, 9, 11, 15, 28, 14, 13, 13, 12, 12, 15, 18, 36]
    for j, w in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:N{rt - 1}"

    # --- Resumen por proveedor (con fórmulas, se recalcula si se edita el libro)
    rp = wb.create_sheet("Por proveedor")
    titulo(rp, "Resumen por proveedor", "Fórmulas SUMAR.SI sobre la hoja Libro IVA Compras")
    encabezado(rp, 4, ["Proveedor", "CUIT", "Comprobantes", "Neto gravado", "IVA crédito fiscal", "Perc. IIBB", "Total"])
    provs = sorted({(f["proveedor"], f["cuit"]) for f in libro})
    rango = f"'Libro IVA Compras'!$E${r0}:$E${rt - 1}"
    def col(L):
        return f"'Libro IVA Compras'!${L}${r0}:${L}${rt - 1}"
    for i, (p, c) in enumerate(provs):
        r = 5 + i
        rp.cell(row=r, column=1, value=p)
        rp.cell(row=r, column=2, value=c)
        rp.cell(row=r, column=3, value=f"=COUNTIF({rango},B{r})")
        rp.cell(row=r, column=4, value=f"=SUMIF({rango},B{r},{col('G')})+SUMIF({rango},B{r},{col('I')})")
        rp.cell(row=r, column=5, value=f"=SUMIF({rango},B{r},{col('H')})+SUMIF({rango},B{r},{col('J')})")
        rp.cell(row=r, column=6, value=f"=SUMIF({rango},B{r},{col('K')})")
        rp.cell(row=r, column=7, value=f"=SUMIF({rango},B{r},{col('L')})")
        for j in range(4, 8):
            rp.cell(row=r, column=j).number_format = MONEDA
    rf = 5 + len(provs)
    rp.cell(row=rf, column=1, value="TOTAL").font = Font(bold=True)
    for j in range(3, 8):
        L = get_column_letter(j)
        c = rp.cell(row=rf, column=j, value=f"=SUM({L}5:{L}{rf - 1})")
        c.font = Font(bold=True)
        c.border = Border(top=Side(style="medium", color=AZUL))
        if j > 3:
            c.number_format = MONEDA
    rp.cell(row=rf + 2, column=1, value="Control: total del resumen = total del libro").font = Font(italic=True)
    rp.cell(row=rf + 2, column=7, value=f"=IF(ABS(G{rf}-'Libro IVA Compras'!L{rt})<0.01,\"OK\",\"REVISAR\")").font = Font(bold=True, color="047857")
    for j, w in enumerate([28, 15, 13, 16, 17, 13, 16], 1):
        rp.column_dimensions[get_column_letter(j)].width = w

    # --- Controles
    rc = wb.create_sheet("Controles")
    titulo(rc, "Controles de calidad", f"{len(libro)} comprobantes cargados · {len(obs)} observaciones")
    encabezado(rc, 4, ["Tipo de control", "Archivo", "Detalle"])
    if not obs:
        rc.cell(row=5, column=1, value="Sin observaciones")
    for i, (tipo, arch, det) in enumerate(obs):
        rc.cell(row=5 + i, column=1, value=tipo).font = Font(bold=True, color="B91C1C")
        rc.cell(row=5 + i, column=2, value=arch)
        rc.cell(row=5 + i, column=3, value=det)
    for j, w in enumerate([18, 36, 80], 1):
        rc.column_dimensions[get_column_letter(j)].width = w

    for hoja in wb.worksheets:
        hoja.sheet_view.showGridLines = False
        hoja.page_setup.orientation = "landscape"
        hoja.page_setup.fitToWidth = 1
        hoja.page_setup.fitToHeight = 0
        hoja.sheet_properties.pageSetUpPr.fitToPage = True
    wb.save(salida)


def main():
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "facturas"
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else AQUI / "libro_iva_compras.xlsx"
    periodo = sys.argv[3] if len(sys.argv) > 3 else "10/2026"
    pdfs = sorted(carpeta.glob("*.pdf"))
    filas, errores = [], []
    for p in pdfs:
        try:
            filas.append(extraer(p))
        except Exception as e:  # un PDF ilegible no frena el resto
            errores.append(("No se pudo leer", p.name, f"{type(e).__name__}: {e}. Revisar a mano (¿PDF escaneado?)."))
    libro, obs = controlar(filas, periodo)
    escribir_excel(libro, errores + obs, salida, periodo)
    print(f"PDF leídos: {len(pdfs)} · cargados en el libro: {len(libro)} · observaciones: {len(errores) + len(obs)}")
    for o in errores + obs:
        print("  -", o[0], "|", o[1])
    print(f"Excel: {salida}")


if __name__ == "__main__":
    main()
