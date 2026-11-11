"""
Genera las imágenes del ejemplo 6 (facturas PDF a Excel) para el portafolio y la galería de Fiverr.

Uso (desde esta carpeta, después de correr el ejemplo 6):
    python generar_imagenes_facturas.py

Lee portafolio/06-facturas-pdf-a-excel/ (una factura en PDF y libro_iva_compras.xlsx) y genera:
- ../4-facturas-pdf-a-excel.png                      (1024x768, README del ejemplo)
- ../fiverr/portafolio-4x3/4-facturas-pdf-excel-4x3.png (misma imagen, portafolio de Fiverr)
- ../fiverr/gig-facturas/2-ejemplo-libro-iva.png       (misma imagen, galería del gig)
- ../fiverr/gig-facturas/1-portada-facturas-pdf-excel.png (1280x769, portada del gig)
- ../fiverr/gig-facturas/3-libro-iva-ejemplo.pdf       (el libro de compras en PDF, con LibreOffice)

Requiere: pdfplumber, openpyxl, Pillow, Microsoft Edge o Google Chrome (para dibujar el HTML)
y LibreOffice (solo para el PDF del libro). Todos los datos son ficticios.
"""
import os
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

import pdfplumber
from openpyxl import load_workbook

AQUI = Path(__file__).resolve().parent
CAPTURAS = AQUI.parent
EJEMPLO = CAPTURAS.parent / "06-facturas-pdf-a-excel"
FACTURA_MUESTRA = "04_electromedicina_0012-00003906.pdf"
NAVEGADORES = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
               r"C:\Program Files\Google\Chrome\Application\chrome.exe", "/usr/bin/google-chrome", "/usr/bin/chromium"]
SOFFICE = [os.environ.get("SOFFICE", ""), shutil.which("soffice") or "", r"C:\Program Files\LibreOffice\program\soffice.exe"]
MENOS = "\u2212"


def miles(x: float) -> str:
    s = f"{abs(x):,.0f}".replace(",", ".")
    return (MENOS if x < 0 else "") + s


def filas_libro():
    ws = load_workbook(EJEMPLO / "libro_iva_compras.xlsx").worksheets[0]
    enc = [c.value for c in ws[4]]
    i = {t: enc.index(t) for t in enc}
    netos = [j for t, j in i.items() if t.startswith("Neto ")]
    ivas = [j for t, j in i.items() if t.startswith("IVA ")]
    filas = []
    for r in ws.iter_rows(min_row=5, values_only=True):
        if not r[0]:
            continue
        filas.append({"fecha": f"{r[0]:%d/%m}", "cuit": r[i["CUIT"]], "prov": r[i["Proveedor"]],
                      "tipo": r[i["Tipo"]], "neto": sum(r[j] or 0 for j in netos), "iva": sum(r[j] or 0 for j in ivas),
                      "total": r[i["Total"]], "control": r[i["Control"]]})
    return filas


def elegir(filas, n):
    """Las primeras facturas del mes, más una nota de crédito y el CUIT inválido (para mostrar los controles)."""
    malas = [f for f in filas if f["control"] != "OK"][:1]
    nc = [f for f in filas if f["tipo"].startswith("NC")][:1]
    resto = [f for f in filas if f not in malas + nc][: n - len(malas) - len(nc)]
    return sorted(resto + nc + malas, key=lambda f: f["fecha"])


def chip(control):
    if control == "OK":
        return '<span class="chip ok">OK</span>'
    return f'<span class="chip bad">{escape(control)}</span>'


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0B1325;color:#F4F6F8;font-family:Inter,system-ui,sans-serif;overflow:hidden;position:relative}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),
 linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:40px 40px}
.glow{position:absolute;right:-120px;top:-160px;width:520px;height:520px;border-radius:50%;
 background:radial-gradient(circle,rgba(0,102,255,.28),transparent 65%)}
h1{font-family:"Plus Jakarta Sans",Inter,sans-serif;font-weight:800;letter-spacing:-.03em;line-height:1.05}
.eyebrow{font-size:13px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#00E5FF}
.muted{color:rgba(244,246,248,.64)}
.factura{position:absolute;width:300px;border-radius:10px;overflow:hidden;box-shadow:0 30px 60px rgba(0,0,0,.45);
 background:#fff;transform:rotate(-3deg)}
.factura img{display:block;width:100%}
.panel{position:absolute;background:#131F37;border:1px solid #1E2D4A;border-radius:14px;padding:16px 18px;
 box-shadow:0 24px 50px rgba(0,0,0,.4)}
.panel__head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;font-size:14px}
.panel__head b{color:#10B981;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:12.5px;font-variant-numeric:tabular-nums;table-layout:auto}
th{color:rgba(244,246,248,.64);font-weight:500;text-align:left;padding:6px 5px;border-bottom:1px solid #1E2D4A}
td{padding:6.5px 5px;border-bottom:1px solid rgba(30,45,74,.6);white-space:nowrap}
.r{text-align:right}
.chip{font-size:11px;font-weight:600;padding:2px 7px;border-radius:99px}
.chip.ok{color:#10B981;background:rgba(16,185,129,.14)}
.chip.bad{color:#F87171;background:rgba(248,113,113,.14)}
.arrow{position:absolute;color:#00E5FF;font-size:30px}
"""


def html_cuadro(img, filas, n_pdf, n_cargadas, n_disenos):
    sel = elegir(filas, 10)
    cuerpo = "".join(
        f'<tr><td>{f["fecha"]}</td><td>{escape(f["prov"])}{" · NC" if f["tipo"].startswith("NC") else ""}</td>'
        f'<td class="r">{miles(f["neto"])}</td><td class="r">{miles(f["iva"])}</td><td class="r">{miles(f["total"])}</td>'
        f'<td>{chip(f["control"])}</td></tr>' for f in sel)
    stats = [(f"{n_pdf} PDF", f"{n_disenos} diseños distintos"), ("1 duplicado", "detectado y excluido"),
             ("1 CUIT", "con dígito inválido"), ("0 diferencias", "contra los totales")]
    tarjetas = "".join(f'<div class="stat"><b>{a}</b><span class="muted">{b}</span></div>' for a, b in stats)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}
body{{width:1024px;height:768px}}
.stats{{position:absolute;left:44px;right:44px;top:650px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.stat{{background:#131F37;border:1px solid #1E2D4A;border-radius:10px;padding:10px 14px}}
.stat b{{display:block;font-family:"Plus Jakarta Sans",Inter;font-size:19px;color:#00E5FF}}
.stat span{{font-size:13px}}
</style></head><body><div class="grid"></div>
<div style="position:absolute;left:44px;top:40px">
<div class="eyebrow">Facturas PDF → Excel · ejemplo con datos ficticios</div>
<h1 style="font-size:38px;margin-top:12px">Tus facturas en PDF,<br>en un Libro IVA en Excel</h1>
<p class="muted" style="font-size:16px;margin-top:8px">Extracción automática, sin cargar nada a mano, con controles de calidad.</p></div>
<div class="factura" style="left:44px;top:212px"><img src="{img}" alt=""></div>
<div class="arrow" style="left:360px;top:405px">→</div>
<div class="panel" style="left:404px;top:236px;width:580px">
<div class="panel__head"><span>Libro IVA Compras · 10/2026</span><b>{n_cargadas} cargadas</b></div>
<table><thead><tr><th>Fecha</th><th>Proveedor</th><th class="r">Neto</th><th class="r">IVA</th><th class="r">Total</th><th>Control</th></tr></thead>
<tbody>{cuerpo}</tbody></table></div>
<div class="stats">{tarjetas}</div>
<div class="muted" style="position:absolute;left:44px;bottom:22px;font-size:12px">FlowData Solutions</div>
<div class="muted" style="position:absolute;right:44px;bottom:22px;font-size:12px">Python · pdfplumber · Excel</div>
</body></html>"""


def html_portada(img, filas, n_cargadas):
    sel = elegir(filas, 9)
    cuerpo = "".join(
        f'<tr><td>{f["fecha"]}</td><td>{f["cuit"]}</td><td>{escape(f["prov"])}</td>'
        f'<td class="r">{miles(f["iva"])}</td><td class="r">{miles(f["total"])}</td><td>{chip(f["control"])}</td></tr>'
        for f in sel)
    puntos = ["Fecha, CUIT, número, neto, IVA, percepciones y total", "Compras y ventas, con notas de crédito",
              "Controles de CUIT, duplicados, totales y numeración"]
    lista = "".join(f'<li><span style="color:#10B981">✓</span>{p}</li>' for p in puntos)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}
body{{width:1280px;height:769px}}
ul{{list-style:none;display:grid;gap:12px;margin-top:26px;font-size:19px}} li{{display:flex;gap:12px}}
.logo{{display:flex;align-items:center;gap:12px;font-weight:600;font-size:19px}}
.logo img{{width:40px;height:40px;display:block}}
.excel{{background:linear-gradient(90deg,#00E5FF,#0066FF);-webkit-background-clip:text;color:transparent}}
</style></head><body><div class="grid"></div><div class="glow"></div>
<div style="position:absolute;left:64px;top:96px">
<div class="logo"><img src="isotipo.png" alt=""><span>Flow<span style="color:#00E5FF">Data</span></span></div>
<h1 style="font-size:84px;margin-top:64px">Facturas PDF<br>a <span class="excel">Excel</span></h1>
<p class="muted" style="font-size:21px;margin-top:22px">Libro IVA · Extracción automática de datos</p>
<ul>{lista}</ul></div>
<div class="factura" style="left:640px;top:96px;width:290px;transform:rotate(-4deg)"><img src="{img}" alt=""></div>
<div class="arrow" style="left:962px;top:240px">→</div>
<div class="panel" style="left:640px;top:340px;width:612px">
<div class="panel__head"><span>Libro IVA Compras · 10/2026</span><b>✓ {n_cargadas} cargadas</b></div>
<table><thead><tr><th>Fecha</th><th>CUIT</th><th>Proveedor</th><th class="r">IVA</th><th class="r">Total</th><th>Control</th></tr></thead>
<tbody>{cuerpo}</tbody></table></div>
<div class="muted" style="position:absolute;right:48px;bottom:24px;font-size:15px">Ejemplo con datos ficticios</div>
</body></html>"""


def dibujar(html: str, png: Path, ancho: int, alto: int, tmp: Path, nombre: str):
    nav = next((n for n in NAVEGADORES if Path(n).is_file()), None)
    if not nav:
        raise SystemExit("No encontré Edge ni Chrome para dibujar las imágenes.")
    archivo = tmp / f"{nombre}.html"
    archivo.write_text(html, encoding="utf-8")
    subprocess.run([nav, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--window-size={ancho},{alto}", "--virtual-time-budget=4000", f"--screenshot={png}",
                    archivo.as_uri()], capture_output=True, timeout=120, check=True)
    print(f"{png.relative_to(CAPTURAS)} ({ancho}x{alto})")


def main():
    filas = filas_libro()
    n_compras = len(list((EJEMPLO / "facturas").glob("*.pdf")))
    n_ventas = len(list((EJEMPLO / "facturas_ventas").glob("*.pdf")))
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        shutil.copyfile(CAPTURAS.parent.parent / "marca" / "isotipo-180.png", tmp / "isotipo.png")
        with pdfplumber.open(EJEMPLO / "facturas" / FACTURA_MUESTRA) as pdf:
            pdf.pages[0].crop((0, 0, pdf.pages[0].width, pdf.pages[0].height * 0.62)).to_image(resolution=110).save(tmp / "factura.png")
        cuadro = CAPTURAS / "4-facturas-pdf-a-excel.png"
        dibujar(html_cuadro("factura.png", filas, n_compras + n_ventas, len(filas), 3), cuadro, 1024, 768, tmp, "cuadro")
        for destino in ["fiverr/portafolio-4x3/4-facturas-pdf-excel-4x3.png", "fiverr/gig-facturas/2-ejemplo-libro-iva.png"]:
            shutil.copyfile(cuadro, CAPTURAS / destino)
            print(f"{destino} (copia)")
        dibujar(html_portada("factura.png", filas, len(filas)), CAPTURAS / "fiverr/gig-facturas/1-portada-facturas-pdf-excel.png",
                1280, 769, tmp, "portada")
        soffice = next((s for s in SOFFICE if s and Path(s).is_file()), None)
        if soffice:
            perfil = "-env:UserInstallation=" + (tmp / "perfil").resolve().as_uri()
            subprocess.run([soffice, perfil, "--headless", "--convert-to", "pdf", "--outdir", str(tmp),
                            str(EJEMPLO / "libro_iva_compras.xlsx")], capture_output=True, timeout=180, check=True)
            shutil.copyfile(tmp / "libro_iva_compras.pdf", CAPTURAS / "fiverr/gig-facturas/3-libro-iva-ejemplo.pdf")
            print("fiverr/gig-facturas/3-libro-iva-ejemplo.pdf")
        else:
            print("Aviso: sin LibreOffice no se regenera 3-libro-iva-ejemplo.pdf")


if __name__ == "__main__":
    main()
