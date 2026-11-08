"""
Reporte de ventas automático.

Lee la planilla limpia de ventas y genera, con un solo comando:
- reporte_ventas.html  -> reporte listo para mandar o abrir en el navegador
- reporte_ventas.xlsx  -> Excel con una hoja por análisis

Uso:
    python generar_reporte.py ../01-limpieza-de-datos/ventas_limpias.csv

Se puede programar para que corra solo todas las semanas
(Programador de tareas de Windows, cron o GitHub Actions).
"""
import sys
from datetime import date
from html import escape

import pandas as pd

MESES = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
         7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}


def pesos(x: float) -> str:
    return "$ " + f"{x:,.0f}".replace(",", ".")


def tabla_html(df: pd.DataFrame, col_valor: str) -> str:
    maximo = df[col_valor].max()
    filas = []
    for _, r in df.iterrows():
        ancho = 100 * r[col_valor] / maximo
        celdas = "".join(f"<td>{escape(str(v))}</td>" for v in r.drop(col_valor))
        filas.append(f"<tr>{celdas}<td class='num'>{pesos(r[col_valor])}"
                     f"<div class='bar' style='width:{ancho:.0f}%'></div></td></tr>")
    encabezado = "".join(f"<th>{escape(c)}</th>" for c in df.columns)
    return f"<table><tr>{encabezado}</tr>{''.join(filas)}</table>"


def main(entrada: str):
    df = pd.read_csv(entrada, parse_dates=["Fecha"])
    df["Mes"] = df["Fecha"].dt.month.map(MESES)

    total = df["Monto"].sum()
    pedidos = len(df)
    ticket = total / pedidos

    por_mes = (df.groupby(df["Fecha"].dt.month)["Monto"].sum().reset_index()
               .assign(Mes=lambda d: d["Fecha"].map(MESES))[["Mes", "Monto"]])
    por_cliente = df.groupby("Cliente", as_index=False)["Monto"].sum().sort_values("Monto", ascending=False)
    por_producto = (df.groupby("Producto", as_index=False)
                    .agg(Unidades=("Cantidad", "sum"), Monto=("Monto", "sum"))
                    .sort_values("Monto", ascending=False))
    por_vendedor = df.groupby("Vendedor", as_index=False)["Monto"].sum().sort_values("Monto", ascending=False)
    por_provincia = df.groupby("Provincia", as_index=False)["Monto"].sum().sort_values("Monto", ascending=False)

    mejor_cliente = por_cliente.iloc[0]
    mejor_producto = por_producto.iloc[0]
    ultimo, anterior = por_mes["Monto"].iloc[-1], por_mes["Monto"].iloc[-2]
    variacion = 100 * (ultimo - anterior) / anterior

    # ---------- Excel ----------
    with pd.ExcelWriter("reporte_ventas.xlsx") as xl:
        pd.DataFrame({"Indicador": ["Ventas totales", "Pedidos", "Ticket promedio"],
                      "Valor": [total, pedidos, round(ticket, 2)]}).to_excel(xl, sheet_name="Resumen", index=False)
        por_mes.to_excel(xl, sheet_name="Por mes", index=False)
        por_cliente.to_excel(xl, sheet_name="Por cliente", index=False)
        por_producto.to_excel(xl, sheet_name="Por producto", index=False)
        por_vendedor.to_excel(xl, sheet_name="Por vendedor", index=False)
        df.drop(columns="Mes").to_excel(xl, sheet_name="Datos", index=False)

    # ---------- HTML ----------
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte de ventas</title>
<style>
:root{{--bg:#f7f8fa;--card:#fff;--text:#1d2433;--muted:#5b6475;--accent:#2563eb;--line:#e3e6ec}}
@media (prefers-color-scheme:dark){{:root{{--bg:#11151c;--card:#1a202b;--text:#e8ecf3;--muted:#a3adbf;--accent:#60a5fa;--line:#2a3140}}}}
body{{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--text)}}
main{{max-width:900px;margin:auto;padding:32px 16px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:20px 0}}
.kpi,.card{{background:var(--card);border-radius:12px;padding:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.kpi b{{display:block;font-size:1.6rem}} .kpi span,.muted{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}
table{{width:100%;border-collapse:collapse;font-size:.92rem}} th,td{{text-align:left;padding:6px 4px;border-bottom:1px solid var(--line)}}
td.num{{text-align:right;white-space:nowrap}} .bar{{height:4px;background:var(--accent);border-radius:2px;margin-top:3px;margin-left:auto}}
ul{{line-height:1.7}}
</style></head><body><main>
<h1>Reporte de ventas — Distribuidora (datos ficticios)</h1>
<p class="muted">Período: {df['Fecha'].min():%d/%m/%Y} al {df['Fecha'].max():%d/%m/%Y} · Generado automáticamente el {date.today():%d/%m/%Y}</p>
<div class="kpis">
  <div class="kpi"><span>Ventas totales</span><b>{pesos(total)}</b></div>
  <div class="kpi"><span>Pedidos</span><b>{pedidos}</b></div>
  <div class="kpi"><span>Ticket promedio</span><b>{pesos(ticket)}</b></div>
  <div class="kpi"><span>{por_mes['Mes'].iloc[-1]} vs. {por_mes['Mes'].iloc[-2]}</span><b>{f"{variacion:+.1f}".replace(".", ",")} %</b></div>
</div>
<div class="card"><h2>Lo más importante</h2><ul>
  <li>El mejor cliente fue <b>{escape(mejor_cliente['Cliente'])}</b> con {pesos(mejor_cliente['Monto'])} ({100*mejor_cliente['Monto']/total:.0f} % del total).</li>
  <li>El producto que más facturó fue <b>{escape(mejor_producto['Producto'])}</b> ({int(mejor_producto['Unidades'])} unidades).</li>
  <li>Las ventas de {por_mes['Mes'].iloc[-1].lower()} {'subieron' if variacion >= 0 else 'bajaron'} un {f"{abs(variacion):.1f}".replace(".", ",")} % respecto de {por_mes['Mes'].iloc[-2].lower()}.</li>
</ul></div>
<h2>Detalle</h2>
<div class="grid">
  <div class="card"><h3>Por mes</h3>{tabla_html(por_mes, 'Monto')}</div>
  <div class="card"><h3>Por cliente</h3>{tabla_html(por_cliente, 'Monto')}</div>
  <div class="card"><h3>Por producto</h3>{tabla_html(por_producto, 'Monto')}</div>
  <div class="card"><h3>Por vendedor</h3>{tabla_html(por_vendedor, 'Monto')}</div>
  <div class="card"><h3>Por provincia</h3>{tabla_html(por_provincia, 'Monto')}</div>
</div>
<p class="muted">Ejemplo de portafolio de FlowData Solutions. Todos los datos son ficticios.</p>
</main></body></html>"""
    with open("reporte_ventas.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Listo: reporte_ventas.html y reporte_ventas.xlsx · Ventas totales {pesos(total)} · {pedidos} pedidos")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../01-limpieza-de-datos/ventas_limpias.csv")
