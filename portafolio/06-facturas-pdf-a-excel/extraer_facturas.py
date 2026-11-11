"""Extrae los datos de facturas en PDF y arma el Libro IVA Compras o Ventas en Excel.

- Lee todos los PDF de una carpeta, aunque cada emisor use un diseño distinto.
- Saca fecha, código y tipo de comprobante, punto de venta, número, CUIT y razón social
  de la contraparte, neto e IVA por alícuota (27 %, 21 %, 10,5 %, 5 % y 2,5 %), no gravado,
  exento, percepciones de IVA y de IIBB, y total.
- Notas de crédito: se cargan en negativo, así los totales del libro ya quedan netos.
- Si el emisor no discrimina el neto por alícuota, lo calcula a partir del IVA.
- Facturas B con "IVA contenido" (Ley 27.743): separa neto e IVA desde ese dato.
- Controla: dígito verificador del CUIT, comprobantes duplicados, que la suma cuadre con
  el total, que el IVA corresponda a la alícuota, que la fecha esté dentro del período y,
  en ventas, que la numeración sea correlativa (saltos de número).

Uso:  python extraer_facturas.py [carpeta_pdf] [salida.xlsx] [MM/AAAA] [compras|ventas]
      python extraer_facturas.py ventas        (ejemplo de ventas con los valores por defecto)
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
TOL = 0.05       # tolerancia de redondeo en pesos para que la suma cuadre con el total
TOL_IVA = 1.00   # tolerancia para comparar el IVA con neto x alícuota (redondeos por renglón)
PERIODO = "10/2026"

# Alícuotas de IVA vigentes: (tasa, como aparece en la factura, sufijo de columna interna)
ALICUOTAS = [(27, "27", "27"), (21, "21", "21"), (10.5, "10,5", "105"), (5, "5", "5"), (2.5, "2,5", "25")]
SIEMPRE = {"21", "105"}  # alícuotas que siempre tienen columna en el libro, aunque estén vacías

# Códigos de comprobante de ARCA (ex AFIP)
CODIGOS = {
    ("factura", "A"): "01", ("nc", "A"): "03", ("factura", "B"): "06", ("nc", "B"): "08",
    ("factura", "C"): "11", ("nc", "C"): "13", ("factura", "M"): "51", ("nc", "M"): "53",
}
CONSUMIDOR_FINAL = "—"  # CUIT que se muestra cuando la factura B no identifica al comprador


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
    """'EQUIPOS MÉDICOS DEL SUR SRL' -> 'Equipos Médicos del Sur SRL'"""
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
CUIT = r"(\d{2}-\d{8}-\d)"
PATRONES = {
    "fecha": [r"Fecha(?: de Emisión)?:\s*(\d{2}/\d{2}/\d{4})"],
    "tipo": [r"(?:FACTURA|NOTA DE CR[ÉE]DITO)\s+([ABCM])\b", r"^([ABCM])$"],
    "pv_nro": [r"Punto de Venta:\s*(\d+)\s+Comp\. Nro:\s*(\d+)", r"N°\s*(\d{4,5})-(\d{8})"],
    "cuit": [r"C\.?U\.?I\.?T\.?:?\s*" + CUIT],
    "cuit_cliente": [r"CUIT cliente:\s*" + CUIT],
    "cliente": [r"^Cliente:\s*(.+?)\s*$"],
    "total": [r"Importe Total:\s*" + IMPORTE, r"^TOTAL\s+" + IMPORTE],
    "perc_iibb": [r"Percepci[oó]n IIBB:\s*" + IMPORTE, r"Perc\. Ingresos Brutos\s+" + IMPORTE],
    "perc_iva": [r"Percepci[oó]n IVA:\s*" + IMPORTE, r"Perc\. IVA\s+" + IMPORTE],
    # Anclados a la línea de totales: un renglón de detalle con alícuota "Exento" no debe confundirse
    "no_gravado": [r"Importe No Gravado:\s*" + IMPORTE, r"^No gravado\s+" + IMPORTE],
    "exento": [r"Importe Exento:\s*" + IMPORTE, r"^Exento\s+" + IMPORTE],
    "subtotal": [r"Subtotal neto\s+" + IMPORTE],
    "iva_contenido": [r"IVA Contenido:?\s*" + IMPORTE],
}
MONTOS = ["no_gravado", "exento", "perc_iva", "perc_iibb", "total"]


def buscar(clave: str, texto: str):
    for p in PATRONES[clave]:
        m = re.search(p, texto, re.MULTILINE)
        if m:
            return m.groups()
    return None


def monto(clave: str, texto: str) -> float:
    g = buscar(clave, texto)
    return a_numero(g[0]) if g else 0.0


def extraer(ruta: Path, modo: str = "compras") -> dict:
    t = texto_pdf(ruta)
    clase = "nc" if re.search(r"NOTA DE CR[ÉE]DITO", t) else "factura"
    tipo = buscar("tipo", t)[0]
    pv, nro = buscar("pv_nro", t)
    if modo == "ventas":  # la contraparte es el cliente
        g = buscar("cuit_cliente", t)
        cuit = g[0] if g else CONSUMIDOR_FINAL
        g = buscar("cliente", t)
        contraparte = g[0] if g else "Consumidor final"
    else:  # la contraparte es el proveedor, que encabeza la factura
        cuit = buscar("cuit", t)[0]
        primera = t.splitlines()[0]
        contraparte = nombre_prolijo(re.sub(r"\s+(FACTURA|NOTA DE CR[ÉE]DITO).*$", "", primera).strip())
    fila = {
        "archivo": ruta.name, "clase": clase, "tipo": tipo,
        "codigo": CODIGOS.get((clase, tipo), ""),
        "fecha": datetime.strptime(buscar("fecha", t)[0], "%d/%m/%Y").date(),
        "pv": int(pv), "numero": int(nro), "cuit": cuit, "contraparte": contraparte,
        "derivado": set(), "notas": [],
    }
    for clave in MONTOS:
        fila[clave] = monto(clave, t)

    # IVA y neto por alícuota ("IVA 21%: $ x", "IVA 21% $ x", "Neto Gravado 10,5%: $ x")
    presentes = []
    for tasa, txt, col in ALICUOTAS:
        m = re.search(rf"\bIVA {re.escape(txt)}%:?\s*" + IMPORTE, t)
        fila[f"iva_{col}"] = a_numero(m.group(1)) if m else 0.0
        m = re.search(rf"\bNeto(?: Gravado)? {re.escape(txt)}%:?\s*" + IMPORTE, t)
        fila[f"neto_{col}"] = a_numero(m.group(1)) if m else None
        if fila[f"iva_{col}"] or fila[f"neto_{col}"] is not None:
            presentes.append((tasa, col))
    # Si el emisor solo informa un subtotal neto, se reparte por alícuota: cada neto
    # faltante se calcula desde su IVA, y el de mayor IVA se lleva la diferencia del subtotal.
    faltan = [(tasa, col) for tasa, col in presentes if fila[f"neto_{col}"] is None]
    if faltan:
        subtotal = monto("subtotal", t) or None
        for tasa, col in faltan:
            fila[f"neto_{col}"] = round(fila[f"iva_{col}"] / (tasa / 100), 2)
            fila["derivado"].add(col)
        if subtotal is not None:
            tasa, col = max(faltan, key=lambda a: fila[f"iva_{a[1]}"])
            otros = sum(fila[f"neto_{c}"] for _, c in presentes if c != col)
            fila[f"neto_{col}"] = round(subtotal - otros, 2)
    for _, _, col in ALICUOTAS:
        if fila[f"neto_{col}"] is None:
            fila[f"neto_{col}"] = 0.0

    # Factura B sin IVA discriminado
    if not presentes and tipo in ("B", "C"):
        contenido = monto("iva_contenido", t)
        resto = fila["total"] - fila["no_gravado"] - fila["exento"] - fila["perc_iva"] - fila["perc_iibb"]
        if contenido and tipo == "B":
            neto = round(resto - contenido, 2)
            ratio = contenido / neto if neto else 0
            tasa, _, col = min(ALICUOTAS, key=lambda a: abs(a[0] / 100 - ratio))
            if abs(tasa / 100 - ratio) > 0.002:
                col = "21"
                fila["notas"].append("Revisar alícuota (B)")
            fila[f"neto_{col}"], fila[f"iva_{col}"] = neto, contenido
            fila["derivado"].add(col)
        elif resto > TOL:  # B o C sin IVA informado: no genera crédito fiscal
            fila["no_gravado"] = round(fila["no_gravado"] + resto, 2)
            fila["notas"].append(f"{tipo} sin IVA discriminado")
        # si resto ≈ 0, todo el comprobante es exento o no gravado y ya está cargado
    return fila


# ---------------------------------------------------------------- controles
def controlar(filas: list[dict], periodo: str, modo: str = "compras"):
    vistos, libro, obs = {}, [], []
    mes, anio = map(int, periodo.split("/"))
    for f in filas:
        clave = (f["cuit"], f["codigo"], f["pv"], f["numero"])
        if clave in vistos:
            obs.append(("Duplicado", f["archivo"], f"Mismo comprobante que {vistos[clave]}: no se carga dos veces."))
            continue
        vistos[clave] = f["archivo"]
        notas = list(f["notas"])
        for n in f["notas"]:
            obs.append((n, f["archivo"], "Revisar el comprobante a mano antes de presentar."))
        if f["cuit"] != CONSUMIDOR_FINAL and not cuit_ok(f["cuit"]):
            notas.append("CUIT inválido")
            quien = "al proveedor" if modo == "compras" else "al cliente sus datos y corregir la ficha"
            obs.append(("CUIT inválido", f["archivo"], f"{f['cuit']}: el dígito verificador no corresponde. Pedir {quien}."))
        suma = sum(f[f"neto_{c}"] + f[f"iva_{c}"] for _, _, c in ALICUOTAS) + sum(
            f[k] for k in MONTOS if k != "total")
        if abs(suma - f["total"]) > TOL:
            notas.append("No cuadra")
            obs.append(("Total no cuadra", f["archivo"], f"Netos + IVA + otros conceptos = {suma:,.2f} vs total {f['total']:,.2f}."))
        for tasa, txt, c in ALICUOTAS:
            if c in f["derivado"] or not f[f"neto_{c}"]:
                continue
            esperado = f[f"neto_{c}"] * tasa / 100
            if abs(esperado - f[f"iva_{c}"]) > TOL_IVA:
                notas.append(f"IVA {txt}% no coincide")
                obs.append(("IVA no coincide", f["archivo"], f"IVA {txt}% informado {f[f'iva_{c}']:,.2f}; neto x alícuota = {esperado:,.2f}."))
        if (f["fecha"].month, f["fecha"].year) != (mes, anio):
            notas.append("Fuera de período")
            obs.append(("Fuera de período", f["archivo"], f"Fecha {f['fecha']:%d/%m/%Y} fuera de {periodo}."))
        if f["clase"] == "nc":  # las notas de crédito restan
            for k in [f"neto_{c}" for _, _, c in ALICUOTAS] + [f"iva_{c}" for _, _, c in ALICUOTAS] + MONTOS:
                f[k] = -f[k]
        f["control"] = ", ".join(notas) or "OK"
        libro.append(f)
    if modo == "ventas":  # correlatividad de la numeración propia
        series = {}
        for f in libro:
            series.setdefault((f["codigo"], f["tipo"], f["clase"], f["pv"]), []).append(f["numero"])
        for (cod, tipo, clase, pv), nums in sorted(series.items()):
            nums.sort()
            faltan = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]
            if faltan:
                nombre = ("NC " if clase == "nc" else "Factura ") + tipo
                lista = ", ".join(f"{pv:05d}-{n:08d}" for n in faltan)
                obs.append(("Salto de numeración", f"{nombre} (cód. {cod})",
                            f"Faltan {lista} entre el {nums[0]} y el {nums[-1]}. ¿Anulado o sin cargar?"))
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


def escribir_excel(libro, obs, salida: Path, periodo: str, modo: str = "compras"):
    hoja = "Libro IVA Compras" if modo == "compras" else "Libro IVA Ventas"
    quien = "Proveedor" if modo == "compras" else "Cliente"
    alics = [(txt, c) for _, txt, c in ALICUOTAS
             if c in SIEMPRE or any(f[f"neto_{c}"] or f[f"iva_{c}"] for f in libro)]
    # columnas: (título, clave o función, formato, ancho)
    cols = [("Fecha", "fecha", "DD/MM/YYYY", 11), ("Cód.", "codigo", "@", 6),
            ("Tipo", lambda f: ("NC " if f["clase"] == "nc" else "Factura ") + f["tipo"], None, 10),
            ("Pto. Vta.", "pv", "00000", 9), ("Número", "numero", "00000000", 11),
            ("CUIT", "cuit", None, 15), (quien, "contraparte", None, 30)]
    for txt, c in alics:
        cols += [(f"Neto {txt}%", f"neto_{c}", MONEDA, 14), (f"IVA {txt}%", f"iva_{c}", MONEDA, 13)]
    cols += [("No gravado", "no_gravado", MONEDA, 12), ("Exento", "exento", MONEDA, 12),
             ("Perc. IVA", "perc_iva", MONEDA, 12), ("Perc. IIBB", "perc_iibb", MONEDA, 12),
             ("Total", "total", MONEDA, 15), ("Control", "control", None, 22), ("Archivo", "archivo", None, 38)]
    letra = {clave if isinstance(clave, str) else t: get_column_letter(j)
             for j, (t, clave, _, _) in enumerate(cols, 1)}

    wb = Workbook()
    ws = wb.active
    ws.title = hoja
    titulo(ws, f"{hoja} — {periodo}",
           "Ejemplo con datos ficticios · generado automáticamente desde los PDF · las notas de crédito restan")
    encabezado(ws, 4, [c[0] for c in cols])
    r0 = 5
    j_control = next(j for j, c in enumerate(cols, 1) if c[1] == "control")
    for i, f in enumerate(libro):
        r = r0 + i
        for j, (_, clave, formato, _) in enumerate(cols, 1):
            v = clave(f) if callable(clave) else f[clave]
            c = ws.cell(row=r, column=j, value=v)
            c.border = Border(bottom=FINO)
            if formato:
                c.number_format = formato
        cc = ws.cell(row=r, column=j_control)
        if f["control"] != "OK":
            cc.font = Font(bold=True, color="B91C1C")
            cc.fill = PatternFill("solid", fgColor="FDECEC")
        else:
            cc.font = Font(color="047857")
    rt = r0 + len(libro)
    ws.cell(row=rt, column=7, value="TOTALES").font = Font(bold=True)
    for j, (_, _, formato, _) in enumerate(cols, 1):
        if formato == MONEDA:
            L = get_column_letter(j)
            c = ws.cell(row=rt, column=j, value=f"=SUM({L}{r0}:{L}{rt - 1})")
            c.font = Font(bold=True)
            c.number_format = MONEDA
            c.border = Border(top=Side(style="medium", color=AZUL))
    for j, (_, _, _, ancho) in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(j)].width = ancho
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A4:{get_column_letter(len(cols))}{rt - 1}"

    # --- Resumen por contraparte (con fórmulas, se recalcula si se edita el libro)
    rp = wb.create_sheet(f"Por {quien.lower()}")
    titulo(rp, f"Resumen por {quien.lower()}", f"Fórmulas SUMAR.SI sobre la hoja {hoja}")
    iva_txt = "IVA crédito fiscal" if modo == "compras" else "IVA débito fiscal"
    encabezado(rp, 4, [quien, "CUIT", "Comprobantes", "Neto gravado", iva_txt,
                       "No gravado y exento", "Percepciones", "Total"])
    def rango(L):
        return f"'{hoja}'!${L}${r0}:${L}${rt - 1}"
    crit = rango(letra["cuit"])
    def sumas(claves, r):
        return "=" + "+".join(f"SUMIF({crit},B{r},{rango(letra[k])})" for k in claves)
    grupos = {
        4: [f"neto_{c}" for _, c in alics], 5: [f"iva_{c}" for _, c in alics],
        6: ["no_gravado", "exento"], 7: ["perc_iva", "perc_iibb"], 8: ["total"],
    }
    contras = sorted({(f["contraparte"], f["cuit"]) for f in libro})
    for i, (p, c) in enumerate(contras):
        r = 5 + i
        rp.cell(row=r, column=1, value=p)
        rp.cell(row=r, column=2, value=c)
        rp.cell(row=r, column=3, value=f"=COUNTIF({crit},B{r})")
        for j, claves in grupos.items():
            rp.cell(row=r, column=j, value=sumas(claves, r)).number_format = MONEDA
    rf = 5 + len(contras)
    rp.cell(row=rf, column=1, value="TOTAL").font = Font(bold=True)
    for j in range(3, 9):
        L = get_column_letter(j)
        c = rp.cell(row=rf, column=j, value=f"=SUM({L}5:{L}{rf - 1})")
        c.font = Font(bold=True)
        c.border = Border(top=Side(style="medium", color=AZUL))
        if j > 3:
            c.number_format = MONEDA
    rp.cell(row=rf + 2, column=1, value="Control: total del resumen = total del libro").font = Font(italic=True)
    rp.cell(row=rf + 2, column=8,
            value=f"=IF(ABS(H{rf}-'{hoja}'!{letra['total']}{rt})<0.01,\"OK\",\"REVISAR\")").font = Font(bold=True, color="047857")
    for j, w in enumerate([32, 15, 13, 16, 17, 16, 14, 16], 1):
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
    for j, w in enumerate([20, 38, 90], 1):
        rc.column_dimensions[get_column_letter(j)].width = w

    for h in wb.worksheets:
        h.sheet_view.showGridLines = False
        h.page_setup.orientation = "landscape"
        h.page_setup.fitToWidth = 1
        h.page_setup.fitToHeight = 0
        h.sheet_properties.pageSetUpPr.fitToPage = True
    wb.save(salida)


def procesar(carpeta: Path, salida: Path, periodo: str, modo: str):
    pdfs = sorted(carpeta.glob("*.pdf"))
    filas, errores = [], []
    for p in pdfs:
        try:
            filas.append(extraer(p, modo))
        except Exception as e:  # un PDF ilegible no frena el resto
            errores.append(("No se pudo leer", p.name, f"{type(e).__name__}: {e}. Revisar a mano (¿PDF escaneado?)."))
    libro, obs = controlar(filas, periodo, modo)
    escribir_excel(libro, errores + obs, salida, periodo, modo)
    return pdfs, libro, errores + obs


def main():
    args = sys.argv[1:]
    modo = "compras"
    if args and args[-1] in ("compras", "ventas"):
        modo = args.pop()
    defecto = "facturas" if modo == "compras" else "facturas_ventas"
    carpeta = Path(args[0]) if len(args) > 0 else AQUI / defecto
    salida = Path(args[1]) if len(args) > 1 else AQUI / f"libro_iva_{modo}.xlsx"
    periodo = args[2] if len(args) > 2 else PERIODO
    pdfs, libro, obs = procesar(carpeta, salida, periodo, modo)
    print(f"[{modo}] PDF leídos: {len(pdfs)} · cargados en el libro: {len(libro)} · observaciones: {len(obs)}")
    for o in obs:
        print("  -", o[0], "|", o[1])
    print(f"Excel: {salida}")


if __name__ == "__main__":
    main()
