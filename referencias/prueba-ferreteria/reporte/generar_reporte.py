"""
Reporte mensual de ventas — ferretería mayorista (cliente: prueba-ferreteria).

Lee la planilla limpia (tablas fVentas, dClientes, dProductos, dVendedores,
dCalendario y fObjetivos) y genera en esta carpeta:
- reporte_ventas_AAAA-MM.html  -> reporte para abrir en el navegador o el celular
- reporte_ventas_AAAA-MM.xlsx  -> Excel con las tablas de resumen (con fórmulas)

Uso:
    python generar_reporte.py                       # usa ../ventas_octubre_2026_limpio.xlsx
    python generar_reporte.py ruta/al/limpio.xlsx   # otro mes

Basado en portafolio/02-reporte-automatico/generar_reporte.py y en el diseño de
portafolio/04-dashboard-interactivo/index.html (FlowData Solutions).
"""
import sys
from datetime import date
from html import escape
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

AQUI = Path(__file__).resolve().parent
ENTRADA_POR_DEFECTO = AQUI.parent / "ventas_octubre_2026_limpio.xlsx"
CLIENTE = "Ferretería mayorista"

# Mientras el cliente no confirme la unidad de fObjetivos, no se calcula % de cumplimiento.
OBJETIVOS_CONFIRMADOS = False

MESES = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 7: "julio",
         8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
DIAS_CORTOS = {1: "lun", 2: "mar", 3: "mié", 4: "jue", 5: "vie", 6: "sáb", 7: "dom"}
TABLAS = ["fVentas", "dClientes", "dProductos", "dVendedores", "dCalendario", "fObjetivos"]


# ---------------------------------------------------------------- formato
def pesos(x: float) -> str:
    signo = "−" if x < 0 else ""
    return f"{signo}$\u00a0" + f"{abs(x):,.0f}".replace(",", ".")


def millones(x: float) -> str:
    signo = "−" if x < 0 else ""
    x = abs(x)
    if x >= 1e6:
        return f"{signo}$\u00a0" + f"{x / 1e6:.1f}".replace(".", ",") + "\u00a0M"
    return f"{signo}$\u00a0" + f"{x / 1e3:,.0f}".replace(",", ".") + "\u00a0k"


def entero(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def pct(x: float, dec: int = 1) -> str:
    return f"{x:.{dec}f}".replace(".", ",") + "\u00a0%"


def fecha_corta(d) -> str:
    return f"{d:%d/%m}"


# ---------------------------------------------------------------- lectura
def leer_tablas(ruta: Path) -> dict:
    """Lee las tablas de Excel por su nombre (no depende del nombre de la hoja)."""
    wb = load_workbook(ruta, data_only=True)
    tablas = {}
    for ws in wb.worksheets:
        for nombre, ref in ws.tables.items():
            filas = list(ws[ref])
            valores = [[c.value for c in fila] for fila in filas]
            tablas[nombre] = pd.DataFrame(valores[1:], columns=valores[0])
    faltan = [t for t in TABLAS if t not in tablas]
    if faltan:
        sys.exit(f"Faltan tablas en {ruta.name}: {', '.join(faltan)}")
    return tablas


def preparar(t: dict) -> dict:
    v = t["fVentas"].copy()
    v["Fecha"] = pd.to_datetime(v["Fecha"])
    for c in ["Cantidad", "Precio_Unitario", "Total"]:
        v[c] = pd.to_numeric(v[c])
    cal = t["dCalendario"].copy()
    cal["Fecha"] = pd.to_datetime(cal["Fecha"])

    n0 = len(v)
    v = (v.merge(t["dClientes"][["CUIT", "Cliente"]], on="CUIT", how="left")
          .merge(t["dProductos"][["Producto", "Rubro", "Precio_Lista"]], on="Producto", how="left")
          .merge(cal[["Fecha", "Semana_ISO", "Dia_Semana", "Dia_Semana_Nro"]], on="Fecha", how="left"))
    assert len(v) == n0, "El cruce con las dimensiones duplicó filas"
    sin_dim = v[v[["Cliente", "Rubro", "Semana_ISO"]].isna().any(axis=1)]
    if len(sin_dim):
        sys.exit(f"{len(sin_dim)} renglones sin cliente, rubro o fecha en calendario: revisar la limpieza")

    meses = v["Fecha"].dt.to_period("M").unique()
    if len(meses) != 1:
        sys.exit(f"Se esperaba un solo mes en fVentas y hay {len(meses)}")
    periodo = meses[0]
    cal = cal[cal["Fecha"].dt.to_period("M") == periodo]

    es_dev = v["Tipo_Movimiento"].eq("Devolución")
    ventas, devs = v[~es_dev], v[es_dev]
    neto = int(v["Total"].sum())

    def agrupar(col):
        g = v.groupby(col).agg(Neto=("Total", "sum"), Unidades=("Cantidad", "sum"),
                               Facturas=("Nro_Factura", "nunique"))
        g["Bruto"] = ventas.groupby(col)["Total"].sum()
        g["Devoluciones"] = devs.groupby(col)["Total"].sum()
        g["Facturas_venta"] = ventas.groupby(col)["Nro_Factura"].nunique()
        g = g.fillna(0)
        g["Ticket"] = g["Bruto"] / g["Facturas_venta"].where(g["Facturas_venta"] > 0)
        g["Participacion"] = 100 * g["Neto"] / neto
        return g.sort_values("Neto", ascending=False).reset_index()

    por_dia = cal[["Fecha", "Dia_Semana_Nro", "Semana_ISO", "Es_Fin_De_Semana"]].merge(
        v.groupby("Fecha").agg(Neto=("Total", "sum"), Facturas=("Nro_Factura", "nunique")).reset_index(),
        on="Fecha", how="left").fillna({"Neto": 0, "Facturas": 0})

    por_semana = por_dia.groupby("Semana_ISO").agg(
        Desde=("Fecha", "min"), Hasta=("Fecha", "max"), Dias=("Fecha", "size"),
        Neto=("Neto", "sum"), Facturas=("Facturas", "sum")).reset_index()
    por_semana["Participacion"] = 100 * por_semana["Neto"] / neto

    por_producto = agrupar("Producto").merge(t["dProductos"][["Producto", "Rubro", "Precio_Lista"]], on="Producto")

    obj = t["fObjetivos"].copy()
    por_vendedor = agrupar("Vendedor").merge(obj[["Vendedor", "Objetivo"]], on="Vendedor", how="left")

    d = {
        "v": v, "ventas": ventas, "devs": devs.sort_values("Fecha"), "periodo": periodo, "cal": cal,
        "neto": neto, "bruto": int(ventas["Total"].sum()), "dev": int(devs["Total"].sum()),
        "facturas": v["Nro_Factura"].nunique(), "facturas_venta": ventas["Nro_Factura"].nunique(),
        "unidades": int(v["Cantidad"].sum()), "clientes": v["Cliente"].nunique(),
        "por_dia": por_dia, "por_semana": por_semana, "por_rubro": agrupar("Rubro"),
        "por_vendedor": por_vendedor, "por_cliente": agrupar("Cliente"), "por_producto": por_producto,
        "origen": v["Origen_Dato"].value_counts(), "dClientes": t["dClientes"],
    }
    d["ticket"] = d["bruto"] / d["facturas_venta"]

    # Controles: cada corte tiene que sumar lo mismo que el total neto.
    for k in ["por_dia", "por_semana", "por_rubro", "por_vendedor", "por_cliente", "por_producto"]:
        s = int(d[k]["Neto"].sum())
        assert s == neto, f"{k} suma {s} y el total neto es {neto}"
    assert d["bruto"] + d["dev"] == neto
    return d


# ---------------------------------------------------------------- Excel
NAVY, BLANCO = "0B1325", "FFFFFF"
F_MONEDA, F_ENTERO, F_PCT, F_FECHA = '"$" #,##0;-"$" #,##0', "#,##0", "0.0%", "dd/mm/yyyy"
BORDE = Border(bottom=Side(style="thin", color="E2E8F0"))


def hoja(wb, titulo, encabezados, anchos):
    ws = wb.create_sheet(titulo)
    ws.append(encabezados)
    for i, ancho in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho
        c = ws.cell(row=1, column=i)
        c.font = Font(bold=True, color=BLANCO)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "A2"
    return ws


def formatear(ws, formatos: dict, desde=2):
    for fila in ws.iter_rows(min_row=desde, max_row=ws.max_row):
        for c in fila:
            c.border = BORDE
            letra = get_column_letter(c.column)
            if letra in formatos:
                c.number_format = formatos[letra]


def fila_total(ws, etiqueta, columnas_suma):
    r = ws.max_row + 1
    ws.cell(row=r, column=1, value=etiqueta).font = Font(bold=True)
    for col in columnas_suma:
        letra = get_column_letter(col)
        c = ws.cell(row=r, column=col, value=f"=SUM({letra}2:{letra}{r - 1})")
        c.font = Font(bold=True)
    return r


def generar_excel(d: dict, salida: Path):
    wb = Workbook()
    wb.remove(wb.active)
    v = d["v"].sort_values(["Fecha", "Nro_Factura"])
    n = len(v)
    last = n + 1

    def R(col):  # rango absoluto de una columna de la hoja Datos
        return f"Datos!${col}$2:${col}${last}"

    FEC, SEM, FAC, CLI, RUB, PRO, VEN, CAN, TOT, TIP = "A", "B", "D", "E", "G", "H", "I", "J", "L", "M"

    # --- Resumen (primera hoja)
    res = hoja(wb, "Resumen", ["Indicador", "Valor", "Nota"], [34, 18, 70])
    filas = [
        ("Ventas netas", f"=SUM({R(TOT)})", F_MONEDA, "Ventas menos devoluciones"),
        ("Ventas brutas", f'=SUMIFS({R(TOT)},{R(TIP)},"Venta")', F_MONEDA, "Solo renglones de venta"),
        ("Devoluciones", f'=SUMIFS({R(TOT)},{R(TIP)},"Devolución")', F_MONEDA, "Cantidades negativas (Tipo_Movimiento = Devolución)"),
        ("Devoluciones / ventas brutas", "=-B4/B3", F_PCT, ""),
        ("Facturas (únicas)", f"=SUMPRODUCT(1/COUNTIF({R(FAC)},{R(FAC)}))", F_ENTERO, "Incluye los renglones de devolución"),
        ("Facturas de venta", f'=COUNTIFS({R(TIP)},"Venta")', F_ENTERO, ""),
        ("Ticket promedio", "=B3/B7", F_MONEDA, "Ventas brutas / facturas de venta"),
        ("Unidades netas", f"=SUM({R(CAN)})", F_ENTERO, ""),
        ("Clientes con compras", f"=SUMPRODUCT(1/COUNTIF({R(CLI)},{R(CLI)}))", F_ENTERO, ""),
        ("Cumplimiento de objetivos", "Pendiente de confirmación", None,
         "Los objetivos cargados parecen estar en otra unidad; se calcula cuando el cliente la confirme"),
    ]
    for etiqueta, valor, fmt, nota in filas:
        res.append([etiqueta, valor, nota])
        if fmt:
            res.cell(row=res.max_row, column=2).number_format = fmt
    formatear(res, {})
    res["A13"] = f"Período: {MESES[d['periodo'].month]} {d['periodo'].year} · Generado el {date.today():%d/%m/%Y} por FlowData Solutions"
    res["A13"].font = Font(italic=True, color="64748B")

    # --- Datos (fuente de todas las fórmulas)
    cols = ["Fecha", "Semana_ISO", "Dia_Semana", "Nro_Factura", "Cliente", "CUIT", "Rubro", "Producto",
            "Vendedor", "Cantidad", "Precio_Unitario", "Total", "Tipo_Movimiento", "Origen_Dato"]
    datos = hoja(wb, "Datos", cols, [12, 8, 11, 18, 22, 15, 13, 20, 14, 10, 14, 14, 15, 32])
    for fila in v[cols].itertuples(index=False):
        datos.append([fila[0].to_pydatetime(), *[x.item() if hasattr(x, "item") else x for x in fila[1:]]])
    formatear(datos, {"A": F_FECHA, "J": F_ENTERO, "K": F_MONEDA, "L": F_MONEDA})
    tabla = Table(displayName="tVentas", ref=f"A1:N{last}")
    tabla.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    datos.add_table(tabla)

    # --- Por día
    ws = hoja(wb, "Por día", ["Fecha", "Día", "Facturas", "Ventas brutas", "Devoluciones", "Ventas netas"],
              [12, 8, 10, 16, 15, 16])
    for i, r in enumerate(d["por_dia"].itertuples(), start=2):
        ws.append([r.Fecha.to_pydatetime(), DIAS_CORTOS[r.Dia_Semana_Nro],
                   f"=COUNTIFS({R(FEC)},A{i})",
                   f'=SUMIFS({R(TOT)},{R(FEC)},A{i},{R(TIP)},"Venta")',
                   f'=SUMIFS({R(TOT)},{R(FEC)},A{i},{R(TIP)},"Devolución")',
                   f"=SUMIFS({R(TOT)},{R(FEC)},A{i})"])
    fila_total(ws, "Total", [3, 4, 5, 6])
    formatear(ws, {"A": F_FECHA, "C": F_ENTERO, "D": F_MONEDA, "E": F_MONEDA, "F": F_MONEDA})

    # --- Por semana
    ws = hoja(wb, "Por semana", ["Semana ISO", "Desde", "Hasta", "Días del mes", "Facturas", "Ventas netas", "% del mes"],
              [11, 12, 12, 12, 10, 16, 10])
    for i, r in enumerate(d["por_semana"].itertuples(), start=2):
        ws.append([int(r.Semana_ISO), r.Desde.to_pydatetime(), r.Hasta.to_pydatetime(), int(r.Dias),
                   f"=COUNTIFS({R(SEM)},A{i})", f"=SUMIFS({R(TOT)},{R(SEM)},A{i})", f"=F{i}/Resumen!$B$2"])
    fila_total(ws, "Total", [4, 5, 6, 7])
    formatear(ws, {"B": F_FECHA, "C": F_FECHA, "E": F_ENTERO, "F": F_MONEDA, "G": F_PCT})

    # --- Por rubro
    ws = hoja(wb, "Por rubro", ["Rubro", "Unidades netas", "Ventas netas", "% del mes"], [16, 14, 16, 10])
    for i, r in enumerate(d["por_rubro"].itertuples(), start=2):
        ws.append([r.Rubro, f"=SUMIFS({R(CAN)},{R(RUB)},A{i})", f"=SUMIFS({R(TOT)},{R(RUB)},A{i})",
                   f"=C{i}/Resumen!$B$2"])
    fila_total(ws, "Total", [2, 3, 4])
    formatear(ws, {"B": F_ENTERO, "C": F_MONEDA, "D": F_PCT})

    # --- Por vendedor
    ws = hoja(wb, "Por vendedor", ["Vendedor", "Facturas", "Ventas brutas", "Devoluciones", "Ventas netas",
                                   "% del mes", "Ticket promedio", "Objetivo cargado", "Cumplimiento"],
              [16, 10, 16, 15, 16, 10, 15, 16, 26])
    for i, r in enumerate(d["por_vendedor"].itertuples(), start=2):
        cumplimiento = f"=E{i}/H{i}" if OBJETIVOS_CONFIRMADOS else "Pendiente de confirmación"
        ws.append([r.Vendedor, f"=COUNTIFS({R(VEN)},A{i})",
                   f'=SUMIFS({R(TOT)},{R(VEN)},A{i},{R(TIP)},"Venta")',
                   f'=SUMIFS({R(TOT)},{R(VEN)},A{i},{R(TIP)},"Devolución")',
                   f"=SUMIFS({R(TOT)},{R(VEN)},A{i})", f"=E{i}/Resumen!$B$2",
                   f'=IFERROR(C{i}/COUNTIFS({R(VEN)},A{i},{R(TIP)},"Venta"),0)',
                   None if pd.isna(r.Objetivo) else int(r.Objetivo), cumplimiento])
    tot = fila_total(ws, "Total", [2, 3, 4, 5, 6])
    formatear(ws, {"B": F_ENTERO, "C": F_MONEDA, "D": F_MONEDA, "E": F_MONEDA, "F": F_PCT, "G": F_MONEDA,
                   "H": F_MONEDA, "I": F_PCT})
    ws.cell(row=tot + 2, column=1, value=(
        "Nota: el objetivo cargado (fObjetivos) es entre 5 y 7 veces menor que la venta neta. "
        "Falta que el cliente confirme la unidad (¿miles?, ¿semanal?, ¿sin IVA?) antes de calcular el cumplimiento.")
    ).font = Font(italic=True, color="B45309")

    # --- Por cliente
    ws = hoja(wb, "Por cliente", ["Cliente", "Facturas", "Ventas brutas", "Devoluciones", "Ventas netas", "% del mes",
                                  "Ticket promedio"], [24, 10, 16, 15, 16, 10, 15])
    for i, r in enumerate(d["por_cliente"].itertuples(), start=2):
        ws.append([r.Cliente, f"=COUNTIFS({R(CLI)},A{i})",
                   f'=SUMIFS({R(TOT)},{R(CLI)},A{i},{R(TIP)},"Venta")',
                   f'=SUMIFS({R(TOT)},{R(CLI)},A{i},{R(TIP)},"Devolución")',
                   f"=SUMIFS({R(TOT)},{R(CLI)},A{i})", f"=E{i}/Resumen!$B$2",
                   f'=IFERROR(C{i}/COUNTIFS({R(CLI)},A{i},{R(TIP)},"Venta"),0)'])
    fila_total(ws, "Total", [2, 3, 4, 5, 6])
    formatear(ws, {"B": F_ENTERO, "C": F_MONEDA, "D": F_MONEDA, "E": F_MONEDA, "F": F_PCT, "G": F_MONEDA})

    # --- Por producto
    ws = hoja(wb, "Por producto", ["Producto", "Rubro", "Precio de lista", "Unidades netas", "Ventas netas", "% del mes"],
              [22, 14, 15, 14, 16, 10])
    for i, r in enumerate(d["por_producto"].itertuples(), start=2):
        ws.append([r.Producto, r.Rubro, int(r.Precio_Lista), f"=SUMIFS({R(CAN)},{R(PRO)},A{i})",
                   f"=SUMIFS({R(TOT)},{R(PRO)},A{i})", f"=E{i}/Resumen!$B$2"])
    fila_total(ws, "Total", [4, 5, 6])
    formatear(ws, {"C": F_MONEDA, "D": F_ENTERO, "E": F_MONEDA, "F": F_PCT})

    # --- Devoluciones (detalle)
    ws = hoja(wb, "Devoluciones", ["Fecha", "Factura", "Cliente", "Producto", "Vendedor", "Cantidad", "Monto"],
              [12, 18, 22, 20, 14, 10, 14])
    for r in d["devs"].itertuples():
        ws.append([r.Fecha.to_pydatetime(), r.Nro_Factura, r.Cliente, r.Producto, r.Vendedor,
                   int(r.Cantidad), int(r.Total)])
    fila_total(ws, "Total", [6, 7])
    formatear(ws, {"A": F_FECHA, "F": F_ENTERO, "G": F_MONEDA})

    # --- Control: cada corte tiene que dar el mismo total neto
    ws = hoja(wb, "Control", ["Corte", "Total del corte", "Ventas netas (Resumen)", "Diferencia", "Estado"],
              [24, 18, 22, 12, 12])
    cortes = [("Por día", "F"), ("Por semana", "F"), ("Por rubro", "C"), ("Por vendedor", "E"),
              ("Por cliente", "E"), ("Por producto", "E")]
    for i, (nombre, col) in enumerate(cortes, start=2):
        n_filas = wb[nombre].max_row  # la última fila con datos es la del total
        if nombre == "Por vendedor":
            n_filas = tot
        ws.append([nombre, f"='{nombre}'!{col}{n_filas}", "=Resumen!$B$2", f"=B{i}-C{i}",
                   f'=IF(ABS(D{i})<0.5,"OK","Revisar")'])
    i = ws.max_row + 1
    ws.append(["Devoluciones (detalle)", f"=Devoluciones!G{wb['Devoluciones'].max_row}", "=Resumen!$B$4",
               f"=B{i}-C{i}", f'=IF(ABS(D{i})<0.5,"OK","Revisar")'])
    formatear(ws, {"B": F_MONEDA, "C": F_MONEDA, "D": F_MONEDA})

    wb.calculation.fullCalcOnLoad = True  # Excel recalcula todo al abrir
    wb.save(salida)


# ---------------------------------------------------------------- HTML
def hbars(filas, total_ref=None):
    """Barras horizontales accesibles (lista con texto, la barra es decorativa)."""
    maximo = max((f["valor"] for f in filas), default=1) or 1
    items = []
    for f in filas:
        ancho = max(0, 100 * f["valor"] / maximo)
        items.append(
            f'<li class="hbar"><span class="hbar__name">{f["nombre"]}</span>'
            f'<span class="hbar__val num">{f["texto"]}</span>'
            f'<span class="hbar__track" aria-hidden="true"><span class="hbar__fill" style="width:{ancho:.1f}%"></span></span>'
            + (f'<span class="hbar__meta muted">{f["meta"]}</span>' if f.get("meta") else "") + "</li>")
    return f'<ul class="hbars" role="list">{"".join(items)}</ul>'


FILAS_VISIBLES_CELULAR = 3   # en celular, las tablas largas muestran estas filas y un botón "Ver todas"
MIN_FILAS_PLEGAR = 6         # se pliegan las tablas con al menos esta cantidad de filas


def tabla(columnas, filas, clase="", pie=None, caption=None, plegable=True):
    """columnas: lista de (titulo, alineacion). Las celdas llevan data-label para la vista apilada en celular.
    Si la tabla es larga (y plegable), en celular se muestran solo las primeras filas con un botón para ver todas."""
    th = "".join(f'<th scope="col"{" class=r" if a == "r" else ""}>{escape(t)}</th>' for t, a in columnas)
    cuerpo = []
    for fila in filas:
        celdas = []
        for (t, a), valor in zip(columnas, fila):
            cls = ' class="r num"' if a == "r" else ""
            celdas.append(f'<td{cls} data-label="{escape(t)}">{valor}</td>')
        cuerpo.append(f"<tr>{''.join(celdas)}</tr>")
    tfoot = ""
    if pie:
        celdas = []
        for (t, a), valor in zip(columnas, pie):
            cls = ' class="r num"' if a == "r" else ""
            celdas.append(f'<td{cls} data-label="{escape(t)}">{valor}</td>')
        tfoot = f"<tfoot><tr>{''.join(celdas)}</tr></tfoot>"
    cap = f'<caption class="sr-only">{escape(caption)}</caption>' if caption else ""
    html = (f'<div class="table-wrap"><table class="stack {clase}">{cap}<thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(cuerpo)}</tbody>{tfoot}</table></div>')
    if plegable and len(filas) >= MIN_FILAS_PLEGAR:
        ocultas = len(filas) - FILAS_VISIBLES_CELULAR
        html = (f'<div class="fold" data-fold>{html}'
                f'<button type="button" class="fold__btn" aria-expanded="false" '
                f'data-more="Ver las {len(filas)} filas" data-less="Mostrar menos">Ver las {len(filas)} filas</button>'
                f'<p class="fold__hint">{ocultas} filas más</p></div>')
    return html


def grafico_dias(por_dia: pd.DataFrame, neto: int) -> str:
    maximo = max(por_dia["Neto"].max(), 1)
    paso = 2_000_000 if maximo <= 12_000_000 else 5_000_000
    tope = paso * int(-(-maximo // paso))  # redondeo hacia arriba
    pico = por_dia.loc[por_dia["Neto"].idxmax()]
    lineas = "".join(
        f'<span class="dchart__grid" style="bottom:{100 * y / tope:.2f}%"><span>{millones(y)}</span></span>'
        for y in range(paso, tope + 1, paso))
    cols = []
    for r in por_dia.itertuples():
        h = 100 * max(r.Neto, 0) / tope
        finde = r.Es_Fin_De_Semana == "Sí"
        es_pico = r.Fecha == pico["Fecha"]
        etiqueta_visible = r.Fecha.day in (1, 5, 10, 15, 20, 25) or r.Fecha.day == por_dia["Fecha"].max().day
        clases = ["dchart__col"] + (["is-weekend"] if finde else []) + (["is-peak"] if es_pico else [])
        texto = (f"{DIAS_CORTOS[r.Dia_Semana_Nro]} {fecha_corta(r.Fecha)}: {pesos(r.Neto)} "
                 f"en {int(r.Facturas)} facturas" + (" (fin de semana)" if finde else ""))
        cols.append(
            f'<li class="{" ".join(clases)}" title="{escape(texto)}">'
            f'<span class="sr-only">{escape(texto)}</span>'
            f'<span class="dchart__bar" style="height:{h:.2f}%" aria-hidden="true">'
            + (f'<span class="dchart__peak num">{millones(r.Neto)}</span>' if es_pico else "") +
            f'</span><span class="dchart__lbl{"" if etiqueta_visible else " is-minor"}" aria-hidden="true">'
            f'{r.Fecha.day}</span></li>')
    return (f'<div class="dchart"><div class="dchart__plot">{lineas}'
            f'<ol class="dchart__cols" aria-label="Ventas netas por día">{"".join(cols)}</ol></div></div>')


def generar_html(d: dict, salida: Path, entrada: Path):
    p = d["periodo"]
    mes, anio = MESES[p.month], p.year
    neto, bruto, dev = d["neto"], d["bruto"], d["dev"]
    pdia, psem = d["por_dia"], d["por_semana"]
    rub, ven, cli, prod = d["por_rubro"], d["por_vendedor"], d["por_cliente"], d["por_producto"]
    devs = d["devs"]

    pico = pdia.loc[pdia["Neto"].idxmax()]
    dias_con_venta = int((pdia["Neto"] != 0).sum())
    prom_dia = neto / len(pdia)
    sem_top = psem.loc[psem["Neto"].idxmax()]
    top_cli, top_rub, top_prod, top_ven = cli.iloc[0], rub.iloc[0], prod.iloc[0], ven.iloc[0]
    top2_cli = cli["Participacion"].iloc[:2].sum()
    dev_pct = 100 * -dev / bruto
    calculados = int(d["origen"].drop("Original", errors="ignore").sum())

    # ---- KPIs
    kpis = [
        ("Ventas netas", pesos(neto), f"Ventas brutas {pesos(bruto)}", True),
        ("Facturas", entero(d["facturas"]), f"{d['facturas_venta']} de venta · {len(devs)} de devolución", False),
        ("Ticket promedio", pesos(d["ticket"]), "Ventas brutas / facturas de venta", False),
        ("Unidades netas", entero(d["unidades"]), f"{len(prod)} productos · {d['clientes']} clientes", False),
        ("Promedio por día", pesos(prom_dia), f"{dias_con_venta} de {len(pdia)} días con ventas", False),
        ("Devoluciones", pesos(dev), f"{pct(dev_pct)} de las ventas brutas", False),
    ]
    kpis_html = "".join(
        f'<div class="card kpi{" kpi--main" if main else ""}"><div class="kpi__label">{l}</div>'
        f'<div class="kpi__value num">{valor}</div><div class="kpi__meta muted">{meta}</div></div>'
        for l, valor, meta, main in kpis)

    # ---- Lo más importante
    insights = [
        f"<b>{escape(top_rub['Rubro'])}</b> explicó el {pct(top_rub['Participacion'], 0)} de la venta neta "
        f"({millones(top_rub['Neto'])}); solo <b>{escape(top_prod['Producto'])}</b> aportó {millones(top_prod['Neto'])} "
        f"({pct(top_prod['Participacion'], 0)}).",
        f"<b>{escape(top_cli['Cliente'])}</b> fue el mejor cliente con {millones(top_cli['Neto'])} "
        f"({pct(top_cli['Participacion'], 0)}). Los dos primeros clientes suman el {pct(top2_cli, 0)} del mes.",
        f"El día más fuerte fue el <b>{fecha_corta(pico['Fecha'])}</b>: {millones(pico['Neto'])} en {int(pico['Facturas'])} facturas "
        f"({pct(100 * pico['Neto'] / neto, 0)} del mes). La semana del {fecha_corta(sem_top['Desde'])} al "
        f"{fecha_corta(sem_top['Hasta'])} concentró {millones(sem_top['Neto'])} ({pct(sem_top['Participacion'], 0)}).",
        f"<b>{escape(top_ven['Vendedor'])}</b> lideró las ventas con {millones(top_ven['Neto'])} "
        f"({pct(top_ven['Participacion'], 0)} del total).",
        f"Hubo {len(devs)} devoluciones por {pesos(dev)}, el {pct(dev_pct)} de lo vendido.",
    ]
    insights_html = "".join(f"<li>{t}</li>" for t in insights)

    # ---- Semanas
    sem_filas = []
    for r in psem.itertuples():
        parcial = r.Dias < 7
        sem_filas.append({
            "nombre": f"Semana {int(r.Semana_ISO)} · {r.Desde.day} al {r.Hasta.day}/{r.Hasta.month:02d}",
            "valor": r.Neto, "texto": f"{millones(r.Neto)} <span class='muted'>· {pct(r.Participacion, 0)}</span>",
            "meta": f"{int(r.Facturas)} facturas" + (f" · semana parcial ({r.Dias} días del mes)" if parcial else ""),
        })

    # ---- Rubros
    rub_filas = [{"nombre": escape(r.Rubro), "valor": r.Neto,
                  "texto": f"{millones(r.Neto)} <span class='muted'>· {pct(r.Participacion, 0)}</span>",
                  "meta": f"{entero(r.Unidades)} unidades netas"} for r in rub.itertuples()]

    # ---- Vendedores
    pendiente = ('<span class="status status--pending"><span class="status__dot" aria-hidden="true"></span>'
                 'Pendiente de confirmación</span>')
    ven_tabla = tabla(
        [("Vendedor", "l"), ("Facturas", "r"), ("Ventas netas", "r"), ("% del mes", "r"), ("Ticket promedio", "r"),
         ("Devoluciones", "r"), ("Cumplimiento de objetivo", "l")],
        [[escape(r.Vendedor), entero(r.Facturas), pesos(r.Neto), pct(r.Participacion), pesos(r.Ticket),
          pesos(r.Devoluciones) if r.Devoluciones else "—", pendiente] for r in ven.itertuples()],
        pie=["Total", entero(ven["Facturas"].sum()), pesos(ven["Neto"].sum()), pct(100), pesos(d["ticket"]),
             pesos(ven["Devoluciones"].sum()), ""],
        caption="Ventas por vendedor")
    objetivos_txt = ", ".join(f"{escape(r.Vendedor)} {millones(r.Objetivo)}" for r in ven.itertuples()
                              if not pd.isna(r.Objetivo))
    ratio = (ven["Neto"] / ven["Objetivo"]).dropna()
    ven_barras = hbars([{"nombre": escape(r.Vendedor), "valor": r.Neto,
                         "texto": f"{millones(r.Neto)} <span class='muted'>· {pct(r.Participacion, 0)}</span>"}
                        for r in ven.itertuples()])

    # ---- Clientes
    cli_tabla = tabla(
        [("Cliente", "l"), ("Facturas", "r"), ("Ventas netas", "r"), ("% del mes", "r"),
         ("Ticket promedio", "r")],
        [[f"<span class='muted num'>{i}.</span> <b>{escape(r.Cliente)}</b>", entero(r.Facturas), pesos(r.Neto), pct(r.Participacion),
          pesos(r.Ticket)] for i, r in enumerate(cli.itertuples(), start=1)],
        pie=["Total", entero(cli["Facturas"].sum()), pesos(cli["Neto"].sum()), pct(100), pesos(d["ticket"])],
        caption="Ranking de clientes por ventas netas")

    # ---- Productos
    prod_tabla = tabla(
        [("Producto", "l"), ("Rubro", "l"), ("Unidades netas", "r"), ("Precio de lista", "r"), ("Ventas netas", "r"),
         ("% del mes", "r")],
        [[f"<b>{escape(r.Producto)}</b>", escape(r.Rubro), entero(r.Unidades), pesos(r.Precio_Lista), pesos(r.Neto),
          pct(r.Participacion)] for r in prod.itertuples()],
        pie=["Total", "", entero(prod["Unidades"].sum()), "", pesos(prod["Neto"].sum()), pct(100)],
        caption="Ventas por producto")

    # ---- Devoluciones
    dev_tabla = tabla(
        [("Fecha", "l"), ("Factura", "l"), ("Cliente", "l"), ("Producto", "l"), ("Vendedor", "l"),
         ("Cantidad", "r"), ("Monto", "r")],
        [[fecha_corta(r.Fecha), f'<span class="num">{escape(r.Nro_Factura)}</span>', escape(r.Cliente),
          escape(r.Producto), escape(r.Vendedor), entero(r.Cantidad), pesos(r.Total)] for r in devs.itertuples()],
        pie=["Total", "", "", "", "", entero(devs["Cantidad"].sum()), pesos(dev)],
        caption="Detalle de devoluciones")
    dev_por_cli = devs.groupby("Cliente")["Total"].agg(["sum", "size"]).sort_values("sum")
    dev_top = dev_por_cli.iloc[0]
    dev_prod = devs.groupby("Producto")["Total"].sum().sort_values()

    # ---- Tabla diaria (para lectores de pantalla y para quien prefiera números)
    dia_tabla = tabla(
        [("Día", "l"), ("Facturas", "r"), ("Ventas netas", "r")],
        [[f"{DIAS_CORTOS[r.Dia_Semana_Nro]} {fecha_corta(r.Fecha)}", entero(r.Facturas), pesos(r.Neto)]
         for r in pdia.itertuples()],
        pie=["Total", entero(pdia["Facturas"].sum()), pesos(neto)], clase="compact",
        caption="Ventas netas por día", plegable=False)

    generado = date.today()
    titulo = f"Ventas de {mes} {anio}"
    html = f"""<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} · {CLIENTE}</title>
<meta name="description" content="Reporte mensual de ventas: indicadores, ventas por día y semana, rubros, vendedores, clientes, productos y devoluciones.">
<meta name="robots" content="noindex, nofollow">
<script>
  (function () {{
    var t = 'dark';
    try {{ t = localStorage.getItem('fds-theme') || 'dark'; }} catch (e) {{}}
    document.documentElement.dataset.theme = t;
  }})();
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
<style>
  :root, :root[data-theme="dark"] {{
    --fds-bg:#0B1325; --fds-card:#131F37; --fds-border:#1E2D4A; --fds-text:#F4F6F8;
    --fds-muted:rgba(244,246,248,.64); --fds-accent-text:#00E5FF; --fds-green-text:#10B981;
    --fds-red-text:#F87171; --fds-amber-text:#FBBF24; --fds-glass:rgba(19,31,55,.62); --fds-row:rgba(255,255,255,.04);
    --bar-from:#00E5FF; --bar-to:#0066FF; --weekend:rgba(255,255,255,.035); color-scheme:dark;
  }}
  :root[data-theme="light"] {{
    --fds-bg:#F8FAFC; --fds-card:#FFFFFF; --fds-border:#E2E8F0; --fds-text:#0F172A;
    --fds-muted:rgba(15,23,42,.64); --fds-accent-text:#0066FF; --fds-green-text:#047857;
    --fds-red-text:#B91C1C; --fds-amber-text:#B45309; --fds-glass:rgba(255,255,255,.78); --fds-row:rgba(15,23,42,.04);
    --bar-from:#38BDF8; --bar-to:#0066FF; --weekend:rgba(15,23,42,.045); color-scheme:light;
  }}
  :root {{ --fds-cyan:#00E5FF; --fds-blue:#0066FF; --fds-green:#10B981; --radius:14px;
    --font-body:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif;
    --font-head:"Plus Jakarta Sans","Inter",system-ui,sans-serif; }}

  *,*::before,*::after {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:var(--font-body); color:var(--fds-text); background:var(--fds-bg);
    line-height:1.5; -webkit-font-smoothing:antialiased; font-feature-settings:"calt" 0; }}
  h1,h2,h3 {{ font-family:var(--font-head); letter-spacing:-.02em; margin:0; line-height:1.2; }}
  p {{ margin:0; }}
  .num {{ font-variant-numeric:tabular-nums; }}
  .muted {{ color:var(--fds-muted); }}
  :focus-visible {{ outline:2px solid var(--fds-cyan); outline-offset:2px; border-radius:6px; }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:0 16px; }}
  .sr-only {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}
  .skip {{ position:absolute; left:16px; top:-48px; z-index:30; padding:8px 12px; border-radius:8px;
    background:var(--fds-blue); color:#fff; font-weight:600; text-decoration:none; }}
  .skip:focus {{ top:8px; }}

  /* Barra superior */
  .top {{ position:sticky; top:0; z-index:20; background:var(--fds-glass); -webkit-backdrop-filter:blur(12px);
    backdrop-filter:blur(12px); border-bottom:1px solid var(--fds-border); }}
  .top__in {{ display:flex; align-items:center; justify-content:space-between; gap:12px; min-height:60px; }}
  .brand {{ display:flex; align-items:center; gap:10px; font-weight:700; font-family:var(--font-head); }}
  .brand small {{ font-family:var(--font-body); font-weight:500; color:var(--fds-muted); display:none; }}
  .top__actions {{ display:flex; align-items:center; gap:8px; min-width:0; }}
  .status {{ display:inline-flex; align-items:center; gap:8px; font-size:.8rem; font-weight:600; white-space:nowrap; }}
  .status__dot {{ width:8px; height:8px; border-radius:50%; background:currentColor; flex:none; }}
  .status--success {{ color:var(--fds-green-text); }}
  .status--pending {{ color:var(--fds-amber-text); }}
  .status--pending .status__dot {{ background:transparent; border:1.5px solid currentColor; }}
  .top .status span:last-child {{ display:none; }}
  .btn {{ display:inline-flex; align-items:center; justify-content:center; gap:8px; min-height:40px; padding:8px 14px;
    border-radius:10px; border:1px solid var(--fds-border); background:var(--fds-card); color:var(--fds-text); font:inherit;
    font-size:.875rem; font-weight:600; cursor:pointer; transition:border-color .2s; }}
  .btn:hover {{ border-color:var(--fds-blue); }}
  .btn svg {{ width:16px; height:16px; }}
  .icon-btn {{ width:40px; padding:0; }}
  .icon-sun {{ display:none; }} :root[data-theme="light"] .icon-sun {{ display:block; }} :root[data-theme="light"] .icon-moon {{ display:none; }}

  /* Encabezado */
  .head {{ padding:28px 0 8px; }}
  .tag {{ display:inline-block; font-size:.75rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase;
    color:var(--fds-accent-text); margin-bottom:6px; }}
  .head h1 {{ font-size:clamp(1.6rem,5vw,2.25rem); }}
  .head p {{ margin-top:8px; font-size:.9rem; }}

  /* Navegación por secciones */
  .toc {{ display:flex; flex-wrap:wrap; gap:6px; margin:16px 0 4px; padding:0; list-style:none; }}
  .toc a {{ display:inline-block; padding:6px 10px; border:1px solid var(--fds-border); border-radius:99px; font-size:.8rem;
    color:var(--fds-muted); text-decoration:none; background:var(--fds-card); transition:border-color .2s, color .2s; }}
  .toc a:hover {{ color:var(--fds-text); border-color:var(--fds-blue); }}

  /* Tarjetas y KPIs */
  .card {{ background:var(--fds-card); background-image:linear-gradient(180deg,rgba(255,255,255,.035),transparent 40%);
    border:1px solid var(--fds-border); border-radius:var(--radius); padding:16px; min-width:0; }}
  section {{ scroll-margin-top:72px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin-top:16px; }}
  .kpi__label {{ font-size:.8rem; color:var(--fds-muted); font-weight:500; }}
  .kpi__value {{ font-family:var(--font-head); font-weight:700; font-size:clamp(1.05rem,4.4vw,1.6rem); margin-top:4px;
    white-space:nowrap; }}
  .kpi__meta {{ font-size:.75rem; margin-top:4px; }}
  .kpi--main {{ grid-column:1/-1; border-color:color-mix(in srgb,var(--fds-blue) 55%,var(--fds-border));
    box-shadow:0 0 24px rgba(0,229,255,.06); }}
  .kpi--main .kpi__value {{ font-size:clamp(1.8rem,8vw,2.4rem); color:var(--fds-accent-text); }}

  .insights {{ margin-top:12px; }}
  .insights ul {{ margin:10px 0 0; padding-left:1.1rem; display:grid; gap:6px; font-size:.92rem; }}
  .insights li::marker {{ color:var(--fds-accent-text); }}

  .grid {{ display:grid; gap:12px; margin-top:12px; }}
  .card__head {{ display:flex; flex-wrap:wrap; justify-content:space-between; align-items:baseline; gap:4px 12px; margin-bottom:14px; }}
  .card__head h2 {{ font-size:1.05rem; }}
  .card__head p {{ font-size:.8rem; }}
  .section-title {{ font-size:.75rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:var(--fds-muted);
    margin:28px 0 0; }}

  /* Gráfico diario */
  .dchart__plot {{ position:relative; height:220px; margin-left:44px; }}
  .dchart__grid {{ position:absolute; left:0; right:0; border-top:1px dashed var(--fds-border); }}
  .dchart__grid span {{ position:absolute; right:calc(100% + 6px); top:-8px; font-size:.68rem; color:var(--fds-muted);
    white-space:nowrap; font-variant-numeric:tabular-nums; }}
  .dchart__cols {{ position:absolute; inset:0; display:flex; align-items:stretch; gap:2px; margin:0; padding:0; list-style:none;
    border-bottom:1px solid var(--fds-border); }}
  .dchart__col {{ position:relative; flex:1 1 0; min-width:0; display:flex; align-items:flex-end; border-radius:4px 4px 0 0; }}
  .dchart__col.is-weekend {{ background:var(--weekend); }}
  .dchart__bar {{ position:relative; display:block; width:100%; min-height:2px; border-radius:3px 3px 0 0;
    background:linear-gradient(180deg,var(--bar-from),var(--bar-to)); }}
  .dchart__col.is-weekend .dchart__bar {{ opacity:.55; }}
  .dchart__col.is-peak .dchart__bar {{ box-shadow:0 0 0 1.5px var(--fds-cyan), 0 0 14px rgba(0,229,255,.35); }}
  .dchart__peak {{ position:absolute; bottom:calc(100% + 4px); right:0; font-size:.72rem; font-weight:700;
    color:var(--fds-text); white-space:nowrap; }}
  .dchart__lbl {{ position:absolute; top:calc(100% + 4px); left:50%; transform:translateX(-50%); font-size:.68rem;
    color:var(--fds-muted); font-variant-numeric:tabular-nums; }}
  .dchart__lbl.is-minor {{ display:none; }}
  .dchart {{ padding-bottom:22px; padding-top:18px; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:6px 16px; margin-top:8px; font-size:.75rem; color:var(--fds-muted); }}
  .legend i {{ display:inline-block; width:12px; height:12px; border-radius:3px; vertical-align:-2px; margin-right:6px; }}
  .legend .lg-bar {{ background:linear-gradient(180deg,var(--bar-from),var(--bar-to)); }}
  .legend .lg-weekend {{ background:var(--weekend); border:1px solid var(--fds-border); }}
  .legend .lg-peak {{ border:2px solid var(--fds-cyan); }}
  details {{ margin-top:14px; border-top:1px solid var(--fds-border); padding-top:10px; }}
  summary {{ cursor:pointer; font-size:.85rem; font-weight:600; color:var(--fds-accent-text); border-radius:6px; }}

  /* Barras horizontales */
  .hbars {{ display:grid; gap:14px; margin:0; padding:0; list-style:none; }}
  .hbar {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:4px 10px; font-size:.875rem; }}
  .hbar__name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:500; }}
  .hbar__track {{ grid-column:1/-1; height:8px; border-radius:99px; background:var(--fds-row); overflow:hidden; }}
  .hbar__fill {{ display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,var(--bar-from),var(--bar-to)); }}
  .hbar__meta {{ grid-column:1/-1; font-size:.75rem; }}

  /* Tablas: en celular cada fila se apila como tarjeta */
  .table-wrap {{ border:1px solid var(--fds-border); border-radius:10px; overflow:hidden; }}
  table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
  th, td {{ padding:10px 12px; text-align:left; border-bottom:1px solid var(--fds-border); }}
  th {{ background:var(--fds-row); font-size:.72rem; color:var(--fds-muted); font-weight:600; text-transform:uppercase; letter-spacing:.04em; }}
  td.r, th.r {{ text-align:right; }}
  td.num {{ white-space:nowrap; }}
  tbody tr:hover {{ background:var(--fds-row); }}
  tfoot td {{ font-weight:700; border-bottom:0; }}
  @media (max-width:719px) {{
    table.stack thead {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }}
    table.stack tr {{ display:block; padding:10px 12px; border-bottom:1px solid var(--fds-border); }}
    table.stack tfoot tr {{ border-bottom:0; background:var(--fds-row); }}
    table.stack td {{ display:flex; justify-content:space-between; gap:12px; padding:3px 0; border:0; text-align:right; }}
    table.stack td::before {{ content:attr(data-label); color:var(--fds-muted); font-size:.75rem; font-weight:500; text-align:left; }}
    table.stack td:empty {{ display:none; }}
    table.stack td:first-child {{ justify-content:flex-start; font-weight:600; padding-bottom:6px; text-align:left; }}
    table.stack td:first-child::before {{ content:none; }}
    .top .status {{ display:none; }}
    .kpis > .card:last-child {{ grid-column:1/-1; }}
    table.stack.compact tr {{ display:flex; justify-content:space-between; gap:8px; padding:6px 12px; }}
    table.stack.compact td {{ display:block; padding:0; }}
    table.stack.compact td::before {{ content:none; }}
    .fold:not(.is-open) tbody tr:nth-child(n+{FILAS_VISIBLES_CELULAR + 1}) {{ display:none; }}
    .fold:not(.is-open) tfoot {{ display:none; }}
    .fold .fold__btn {{ display:flex; }}
    .fold:not(.is-open) .fold__hint {{ display:block; }}
  }}
  .fold__btn {{ display:none; width:100%; justify-content:center; margin-top:10px; min-height:44px; padding:10px 14px;
    border-radius:10px; border:1px solid var(--fds-border); background:var(--fds-card); color:var(--fds-accent-text);
    font:inherit; font-size:.875rem; font-weight:600; cursor:pointer; }}
  .fold__btn:hover {{ border-color:var(--fds-blue); }}
  .fold__hint {{ display:none; margin:6px 0 0; text-align:center; font-size:.75rem; color:var(--fds-muted); }}

  .note {{ display:flex; gap:10px; align-items:flex-start; margin-top:14px; padding:12px 14px; border-radius:10px;
    border:1px solid color-mix(in srgb,var(--fds-amber-text) 45%,var(--fds-border));
    background:color-mix(in srgb,var(--fds-amber-text) 7%,transparent); font-size:.85rem; }}
  .note strong {{ color:var(--fds-amber-text); }}
  .note__icon {{ flex:none; width:18px; height:18px; color:var(--fds-amber-text); margin-top:2px; }}
  .mini-kpis {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-bottom:14px; }}
  .mini-kpis div {{ padding:10px 12px; border:1px solid var(--fds-border); border-radius:10px; }}
  .mini-kpis b {{ display:block; font-family:var(--font-head); font-size:1.1rem; }}
  .mini-kpis span {{ font-size:.75rem; color:var(--fds-muted); }}
  .neg {{ color:var(--fds-red-text); }}
  .data-notes {{ margin:10px 0 0; padding-left:1.1rem; display:grid; gap:6px; font-size:.85rem; }}

  footer {{ padding:32px 0 40px; font-size:.8rem; color:var(--fds-muted); display:grid; gap:4px; }}
  footer b {{ color:var(--fds-text); font-weight:600; }}

  @media (min-width:640px) {{
    .brand small {{ display:inline; }}
    .top .status span:last-child {{ display:inline; }}
    .kpis {{ grid-template-columns:repeat(3,minmax(0,1fr)); }}
    .kpi--main {{ grid-column:auto; }}
    .kpi--main .kpi__value {{ font-size:clamp(1.3rem,3vw,1.75rem); }}
    .kpi__value {{ font-size:clamp(1.2rem,2.6vw,1.6rem); }}
    .mini-kpis {{ grid-template-columns:repeat(4,minmax(0,1fr)); }}
    .dchart__lbl.is-minor {{ display:block; }}
    .dchart__plot {{ height:260px; margin-left:52px; }}
  }}
  @media (min-width:960px) {{
    .kpis {{ grid-template-columns:1.5fr repeat(5,minmax(0,1fr)); }}
    .kpi__value {{ font-size:1.3rem; }}
    .kpi--main .kpi__value {{ font-size:1.75rem; }}
    .grid--2 {{ grid-template-columns:3fr 2fr; }}
    .grid--even {{ grid-template-columns:1fr 1fr; }}
  }}
  @media (prefers-reduced-motion:reduce) {{ *,*::before,*::after {{ transition:none !important; animation:none !important; }} }}
  @media print {{
    .top, .toc, .skip {{ display:none; }}
    body {{ background:#fff; color:#0F172A; }}
    .card {{ break-inside:avoid; }}
    details > *:not(summary) {{ display:block; }}
    .fold tbody tr, .fold tfoot {{ display:table-row-group !important; }}
    .fold tbody tr {{ display:table-row !important; }}
    .fold__btn, .fold__hint {{ display:none !important; }}
  }}
</style>
</head>
<body>
<a class="skip" href="#contenido">Saltar al reporte</a>
<header class="top">
  <div class="wrap top__in">
    <div class="brand">
      <svg width="28" height="28" viewBox="0 0 34 34" fill="none" aria-hidden="true">
        <defs><linearGradient id="fds-g" x1="0" y1="0" x2="34" y2="34" gradientUnits="userSpaceOnUse"><stop stop-color="#00E5FF"/><stop offset="1" stop-color="#0066FF"/></linearGradient></defs>
        <rect x="1" y="1" width="32" height="32" rx="9" stroke="url(#fds-g)" stroke-width="1.5"/>
        <path d="M8 11h7l4 6h7M8 23h5l3-6" stroke="url(#fds-g)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="8" cy="11" r="2" fill="#00E5FF"/><circle cx="8" cy="23" r="2" fill="#00E5FF"/><circle cx="26" cy="17" r="2.5" fill="#0066FF"/>
      </svg>
      <span>FlowData <small>· Reporte de ventas</small></span>
    </div>
    <div class="top__actions">
      <span class="status status--success" title="Totales controlados contra los datos limpios">
        <span class="status__dot" aria-hidden="true"></span><span>✓ Datos verificados</span></span>
      <button class="btn icon-btn" id="theme-toggle" type="button" aria-label="Cambiar a modo claro" aria-pressed="false">
        <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      </button>
    </div>
  </div>
</header>

<main class="wrap" id="contenido">
  <div class="head">
    <span class="tag">{CLIENTE} · Reporte mensual</span>
    <h1>{titulo}</h1>
    <p class="muted">Período: {pdia['Fecha'].min():%d/%m/%Y} al {pdia['Fecha'].max():%d/%m/%Y} · {d['facturas']} facturas · Generado el {generado:%d/%m/%Y}</p>
  </div>

  <nav aria-label="Secciones del reporte">
    <ul class="toc">
      <li><a href="#indicadores">Indicadores</a></li><li><a href="#tiempo">Día y semana</a></li>
      <li><a href="#rubros">Rubros</a></li><li><a href="#vendedores">Vendedores</a></li>
      <li><a href="#clientes">Clientes</a></li><li><a href="#productos">Productos</a></li>
      <li><a href="#devoluciones">Devoluciones</a></li><li><a href="#notas">Notas</a></li>
    </ul>
  </nav>

  <section id="indicadores" aria-labelledby="t-ind">
    <h2 id="t-ind" class="sr-only">Indicadores clave</h2>
    <div class="kpis">{kpis_html}</div>
    <div class="card insights">
      <h2 style="font-size:1.05rem">Lo más importante del mes</h2>
      <ul>{insights_html}</ul>
    </div>
  </section>

  <h2 class="section-title">Evolución</h2>
  <div class="grid grid--2">
    <section class="card" id="tiempo" aria-labelledby="t-dia">
      <div class="card__head"><h2 id="t-dia">Ventas netas por día</h2>
        <p class="muted">Promedio diario {millones(prom_dia)}</p></div>
      {grafico_dias(pdia, neto)}
      <div class="legend" aria-hidden="true"><span><i class="lg-bar"></i>Venta neta del día</span>
        <span><i class="lg-weekend"></i>Sábado y domingo (banda de fondo)</span><span><i class="lg-peak"></i>Día más alto</span></div>
      <details><summary>Ver la tabla día por día</summary>{dia_tabla}</details>
    </section>
    <section class="card" aria-labelledby="t-sem">
      <div class="card__head"><h2 id="t-sem">Por semana</h2><p class="muted">Lunes a domingo (semana ISO)</p></div>
      {hbars(sem_filas)}
    </section>
  </div>

  <h2 class="section-title">Qué y quién vende</h2>
  <div class="grid grid--even">
    <section class="card" id="rubros" aria-labelledby="t-rub">
      <div class="card__head"><h2 id="t-rub">Por rubro</h2><p class="muted">Ventas netas · % del mes</p></div>
      {hbars(rub_filas)}
    </section>
    <section class="card" id="vendedores" aria-labelledby="t-ven">
      <div class="card__head"><h2 id="t-ven">Por vendedor</h2><p class="muted">Ventas netas · % del mes</p></div>
      {ven_barras}
      <div class="note" role="note">
        <svg class="note__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>
        <p><strong>Cumplimiento de objetivos: pendiente de confirmación.</strong> Los objetivos cargados ({objetivos_txt})
        son entre {f'{ratio.min():.1f}'.replace('.', ',')} y {f'{ratio.max():.1f}'.replace('.', ',')} veces menores que la venta neta, así que probablemente estén en otra unidad
        (¿miles de pesos?, ¿semanales?, ¿sin IVA?). Lo calculamos cuando lo confirmes.</p>
      </div>
    </section>
  </div>
  <section class="card" style="margin-top:12px" aria-labelledby="t-ven2">
    <div class="card__head"><h2 id="t-ven2">Detalle por vendedor</h2><p class="muted">Ticket = ventas brutas / facturas de venta</p></div>
    {ven_tabla}
  </section>

  <h2 class="section-title">Clientes y productos</h2>
  <div class="grid">
    <section class="card" id="clientes" aria-labelledby="t-cli">
      <div class="card__head"><h2 id="t-cli">Mejores clientes</h2><p class="muted">Ordenados por ventas netas</p></div>
      {cli_tabla}
    </section>
    <section class="card" id="productos" aria-labelledby="t-prod">
      <div class="card__head"><h2 id="t-prod">Productos</h2><p class="muted">Ordenados por ventas netas</p></div>
      {prod_tabla}
    </section>
  </div>

  <h2 class="section-title">Devoluciones</h2>
  <section class="card" id="devoluciones" style="margin-top:12px" aria-labelledby="t-dev">
    <div class="card__head"><h2 id="t-dev">Devoluciones del mes</h2><p class="muted">Renglones con cantidad negativa · ya restadas de las ventas netas</p></div>
    <div class="mini-kpis">
      <div><span>Monto devuelto</span><b class="num neg">{pesos(dev)}</b></div>
      <div><span>% de las ventas brutas</span><b class="num">{pct(dev_pct)}</b></div>
      <div><span>Renglones</span><b class="num">{len(devs)}</b></div>
      <div><span>Unidades devueltas</span><b class="num">{entero(-devs['Cantidad'].sum())}</b></div>
    </div>
    <p class="muted" style="font-size:.85rem;margin-bottom:12px"><b style="color:var(--fds-text)">{escape(dev_por_cli.index[0])}</b> concentró
      {int(dev_top['size'])} de las {len(devs)} devoluciones ({pesos(dev_top['sum'])}). Por monto, lo más devuelto fue
      {escape(dev_prod.index[0])} ({pesos(dev_prod.iloc[0])}).</p>
    {dev_tabla}
  </section>

  <section class="card" id="notas" style="margin-top:12px" aria-labelledby="t-notas">
    <div class="card__head"><h2 id="t-notas">Notas sobre los datos</h2>
      <span class="status status--pending"><span class="status__dot" aria-hidden="true"></span>Puntos a confirmar</span></div>
    <ul class="data-notes">
      <li>Las ventas netas ya descuentan las {len(devs)} devoluciones. Están cargadas como facturas con cantidad negativa
        (no como notas de crédito): confirmá si son devoluciones reales.</li>
      <li>{calculados} renglones tenían el total o la cantidad vacíos y se completaron con cantidad × precio. Si hubo descuentos, avisanos y lo corregimos.</li>
      <li>En la limpieza se quitaron 8 renglones duplicados de la exportación. Por eso el total no coincide con la fórmula de "TOTAL GENERAL" de la planilla original.</li>
      <li>El cumplimiento de objetivos queda pendiente hasta confirmar la unidad de los objetivos.</li>
    </ul>
  </section>
</main>

<footer class="wrap">
  <span>Preparado por <b>FlowData Solutions</b> · Automatización de Procesos &amp; Soluciones de Datos</span>
  <span>Fuente: {escape(entrada.name)} · Reporte confidencial para uso interno del cliente.</span>
</footer>

<script>
(function () {{
  var root = document.documentElement, toggle = document.getElementById('theme-toggle');
  function sync() {{
    var light = root.dataset.theme === 'light';
    toggle.setAttribute('aria-pressed', String(light));
    toggle.setAttribute('aria-label', light ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro');
  }}
  toggle.addEventListener('click', function () {{
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    try {{ localStorage.setItem('fds-theme', root.dataset.theme); }} catch (e) {{}}
    sync();
  }});
  sync();
}})();
  document.querySelectorAll('[data-fold]').forEach(function (f) {{
    var b = f.querySelector('.fold__btn');
    b.addEventListener('click', function () {{
      var open = f.classList.toggle('is-open');
      b.setAttribute('aria-expanded', String(open));
      b.textContent = open ? b.dataset.less : b.dataset.more;
      if (!open) f.scrollIntoView({{ block: 'nearest' }});
    }});
  }});
</script>
</body>
</html>
"""
    salida.write_text(html, encoding="utf-8")


# ---------------------------------------------------------------- main
def main():
    entrada = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ENTRADA_POR_DEFECTO
    d = preparar(leer_tablas(entrada))
    sufijo = f"{d['periodo'].year}-{d['periodo'].month:02d}"
    html, xlsx = AQUI / f"reporte_ventas_{sufijo}.html", AQUI / f"reporte_ventas_{sufijo}.xlsx"
    generar_excel(d, xlsx)
    generar_html(d, html, entrada)
    print(f"Listo: {html.name} y {xlsx.name}")
    print(f"Ventas netas {pesos(d['neto'])} · brutas {pesos(d['bruto'])} · devoluciones {pesos(d['dev'])} · "
          f"{d['facturas']} facturas · {d['unidades']} unidades")


if __name__ == "__main__":
    main()
