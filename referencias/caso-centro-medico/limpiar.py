"""
Limpieza de la exportación de facturación de octubre 2026 (centro médico, datos ficticios)
y preparación de tablas para un dashboard de Power BI.

Uso:
    python limpiar.py [facturacion_octubre_2026.xlsx] [facturacion_octubre_2026_limpio.xlsx]

Lee el original SIN modificarlo y genera:
- facturacion_octubre_2026_limpio.xlsx con un modelo estrella listo para Power BI:
    fFacturacion (hechos), dFinanciadores, dPrestaciones, dProfesionales, dCalendario y fObjetivos.
- informe_limpieza.md con todo lo que se cambió y lo que queda por decidir.

Qué corrige:
- Encabezado del sistema (título, período, fila vacía) y fila "TOTAL GENERAL" al pie
- Fechas mezcladas: celdas de fecha de Excel, 15/10/2026, 20261015, 24-10-26
- Obras sociales, especialidades y profesionales escritos de varias formas (mayúsculas,
  sin tilde, espacios de más, iniciales "L. Ibáñez")
- CUIT con y sin guiones
- Aranceles como texto: "$ 18.000", "18000,00", "18000"
- Totales y cantidades faltantes (se calculan con Cantidad x Precio, que coincide
  en el 100% de las filas completas)
- Filas vacías y filas duplicadas (misma factura repetida con todos los datos iguales)
- Débitos de las obras sociales (cantidad negativa): se conservan y restan
- Objetivos por profesional con nombres sin tilde y montos como texto
"""
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

CARPETA = Path(__file__).resolve().parent

# --- Catálogos: la forma "oficial" de escribir cada valor -------------------
# Se toma la variante más frecuente del propio archivo (con tildes correctas).
FINANCIADORES = ["Cobertura Norte", "Mutual del Sur", "Obra Social Andina", "Plan Salud Pampa",
                 "Prepaga Litoral Salud"]
ESPECIALIDADES = ["Clínica Médica", "Cardiología", "Pediatría", "Diagnóstico por Imágenes"]
PROFESIONALES = ["Laura Ibáñez", "Martín Suárez", "Sofía Ríos"]
FORMATOS_FECHA = ["%d/%m/%Y", "%Y%m%d", "%d-%m-%y"]
FILA_ENCABEZADO = 3  # 0-based: los encabezados están en la fila 4 de Excel
PERIODO = (datetime(2026, 10, 1), datetime(2026, 10, 31))


def clave(texto) -> str:
    """Pasa a minúsculas, saca tildes y espacios de más: '  MUTUAL del SUR ' -> 'mutual del sur'."""
    if pd.isna(texto):
        return ""
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


def normalizar(valor, catalogo):
    return {clave(c): c for c in catalogo}.get(clave(valor), valor)


def normalizar_profesional(valor):
    """Acepta 'Laura Ibáñez', 'LAURA IBÁÑEZ', 'L. Ibáñez' y 'Laura Ibanez'."""
    k = clave(valor)
    for v in PROFESIONALES:
        nombre, apellido = clave(v).split()
        if k in (f"{nombre} {apellido}", f"{nombre[0]}. {apellido}", f"{nombre[0]} {apellido}"):
            return v
    return valor


def normalizar_cuit(valor):
    """'30712345671' o '30-71234567-1' -> '30-71234567-1'."""
    digitos = "".join(ch for ch in str(valor) if ch.isdigit())
    if len(digitos) != 11:
        return valor
    return f"{digitos[:2]}-{digitos[2:10]}-{digitos[10]}"


def cuit_valido(cuit) -> bool:
    """Controla el dígito verificador del CUIT (módulo 11)."""
    d = [int(ch) for ch in str(cuit) if ch.isdigit()]
    if len(d) != 11:
        return False
    suma = sum(a * b for a, b in zip(d, [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]))
    verificador = {11: 0, 10: 9}.get(11 - suma % 11, 11 - suma % 11)
    return verificador == d[10]


def parsear_fecha(valor):
    if isinstance(valor, datetime):
        return valor
    for fmt in FORMATOS_FECHA:
        try:
            return datetime.strptime(str(valor).strip(), fmt)
        except ValueError:
            continue
    return pd.NaT


def parsear_monto(valor):
    """'$ 18.000' -> 18000 ; '18000,00' -> 18000 ; 18000 -> 18000."""
    if pd.isna(valor) or str(valor).strip() == "":
        return float("nan")
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).replace("$", "").strip()
    if "," in s:  # formato argentino: 1.234,50
        s = s.replace(".", "").replace(",", ".")
    else:         # sin coma, el punto es separador de miles: 18.000
        s = s.replace(".", "")
    return float(s)


def a_tabla_excel(ruta, hojas):
    """Da formato de Tabla de Excel a cada hoja (Power BI las detecta por nombre)."""
    wb = load_workbook(ruta)
    for nombre in hojas:
        ws = wb[nombre]
        rango = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
        tabla = Table(displayName=nombre, ref=rango)
        tabla.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(tabla)
        for i, col in enumerate(ws.iter_cols(min_row=1, max_row=1), start=1):
            ws.column_dimensions[get_column_letter(i)].width = max(12, len(str(col[0].value)) + 4)
        ws.freeze_panes = "A2"
    wb.save(ruta)


def main(entrada, salida):
    entrada, salida = Path(entrada), Path(salida)
    df = pd.read_excel(entrada, sheet_name="Facturación Octubre", header=FILA_ENCABEZADO, dtype=object)
    df["Fila_Excel"] = df.index + FILA_ENCABEZADO + 2  # para rastrear cada cambio hasta el original
    informe = ["# Informe de limpieza — Facturación octubre 2026\n",
               f"Archivo original: `{entrada.name}` (no se modificó)\n",
               "## Resumen\n",
               f"- Filas leídas debajo del encabezado: **{len(df)}**"]

    # Total de control del sistema, tal como lo calcularía la fórmula =SUM(J5:J224) del original
    total_original = pd.to_numeric(df["Total"], errors="coerce").sum()

    # 1) Fila "TOTAL GENERAL" del pie: no es una factura
    pie = df["Precio Unit."].astype(str).str.contains("TOTAL", case=False, na=False)
    df = df[~pie]
    informe.append(f"- Fila de pie 'TOTAL GENERAL' (fórmula `=SUM(J5:J224)`) quitada: **{pie.sum()}**")

    # 2) Filas vacías
    datos = df.drop(columns="Fila_Excel")
    vacias = datos.isna().all(axis=1)
    informe.append(f"- Filas vacías eliminadas: **{vacias.sum()}** (filas Excel: "
                   f"{', '.join(map(str, df.loc[vacias, 'Fila_Excel']))})")
    df = df[~vacias].copy()

    # 3) Columnas con nombres simples para Power BI
    df = df.rename(columns={"Nro Factura": "Nro_Factura", "Cant.": "Cantidad", "Obra Social": "Financiador",
                            "Prestación": "Prestacion", "Precio Unit.": "Precio_Unitario"})

    # 4) Normalizar textos y formatos
    antes = df.copy()
    df["Fecha"] = df["Fecha"].map(parsear_fecha)
    df["Financiador"] = df["Financiador"].map(lambda v: normalizar(v, FINANCIADORES))
    df["Especialidad"] = df["Especialidad"].map(lambda v: normalizar(v, ESPECIALIDADES))
    df["Profesional"] = df["Profesional"].map(normalizar_profesional)
    df["CUIT"] = df["CUIT"].map(normalizar_cuit)
    df["Prestacion"] = df["Prestacion"].map(lambda v: " ".join(str(v).split()))
    df["Precio_Unitario"] = df["Precio_Unitario"].map(parsear_monto)
    df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce")
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce")

    informe.append("\n## Normalización de formatos\n")
    fechas_texto = antes["Fecha"].map(lambda v: not isinstance(v, datetime))
    informe.append(f"- Fechas escritas como texto convertidas a fecha: **{fechas_texto.sum()}** "
                   f"(formatos: 15/10/2026, 20261015, 24-10-26)")
    for col in ["Financiador", "Especialidad", "Profesional", "CUIT"]:
        cambios = (antes[col].astype(str) != df[col].astype(str)).sum()
        variantes = antes[col].nunique()
        informe.append(f"- **{col}**: {cambios} celdas corregidas; {variantes} variantes -> {df[col].nunique()} valores")
    precio_texto = antes["Precio_Unitario"].map(lambda v: isinstance(v, str)).sum()
    informe.append(f"- Aranceles guardados como texto ('$ 18.000', '18000,00', '18000') convertidos a número: **{precio_texto}**")

    # Controles de calidad que deben dar cero
    sin_fecha = df["Fecha"].isna().sum()
    fuera_periodo = (~df["Fecha"].between(*PERIODO)).sum()
    sin_catalogo = (~df["Financiador"].isin(FINANCIADORES)).sum() + (~df["Especialidad"].isin(ESPECIALIDADES)).sum() \
        + (~df["Profesional"].isin(PROFESIONALES)).sum()
    cuit_por_financiador = df.groupby("Financiador")["CUIT"].nunique().max()
    precio_por_prestacion = df.groupby("Prestacion")["Precio_Unitario"].nunique().max()
    esp_por_prestacion = df.groupby("Prestacion")["Especialidad"].nunique().max()
    completos = df["Total"].notna() & df["Cantidad"].notna()
    no_cierra = ((df.loc[completos, "Cantidad"] * df.loc[completos, "Precio_Unitario"]
                  - df.loc[completos, "Total"]).abs() > 0.01).sum()
    informe.append("\n## Controles de calidad\n")
    informe.append(f"- Fechas sin poder interpretar: **{sin_fecha}**; fuera de octubre 2026: **{fuera_periodo}**")
    informe.append(f"- Valores fuera de catálogo (obra social, especialidad o profesional): **{sin_catalogo}**")
    informe.append(f"- CUIT distintos por obra social (máximo): **{cuit_por_financiador}**; "
                   f"aranceles distintos por prestación: **{precio_por_prestacion}**; especialidades por prestación: **{esp_por_prestacion}**")
    informe.append(f"- Filas completas donde Cantidad x Precio no coincide con Total: **{no_cierra}** de {completos.sum()}")

    # 5) Completar faltantes: Total = Cantidad x Precio (regla verificada arriba)
    falta_total = df["Total"].isna() & df["Cantidad"].notna() & df["Precio_Unitario"].notna()
    falta_cant = df["Cantidad"].isna() & df["Total"].notna() & df["Precio_Unitario"].notna()
    df["Origen_Dato"] = "Original"
    df.loc[falta_total, "Total"] = df.loc[falta_total, "Cantidad"] * df.loc[falta_total, "Precio_Unitario"]
    df.loc[falta_total, "Origen_Dato"] = "Total calculado (Cant x Precio)"
    df.loc[falta_cant, "Cantidad"] = (df.loc[falta_cant, "Total"] / df.loc[falta_cant, "Precio_Unitario"]).round()
    df.loc[falta_cant, "Origen_Dato"] = "Cantidad calculada (Total / Precio)"
    informe.append("\n## Datos completados\n")
    informe.append(f"- Totales vacíos calculados como Cantidad x Precio: **{falta_total.sum()}** "
                   f"(filas Excel: {', '.join(map(str, df.loc[falta_total, 'Fila_Excel']))})")
    informe.append(f"- Cantidades vacías calculadas como Total / Precio: **{falta_cant.sum()}** "
                   f"(filas Excel: {', '.join(map(str, df.loc[falta_cant, 'Fila_Excel']))})")

    # 6) Duplicados: misma factura con todos los datos iguales (la numeración es correlativa, 1 renglón por factura)
    columnas_factura = [c for c in df.columns if c not in ("Fila_Excel", "Origen_Dato")]
    dup = df.duplicated(subset=columnas_factura, keep="first")
    informe.append("\n## Duplicados\n")
    informe.append(f"- Filas duplicadas eliminadas: **{dup.sum()}** (se conserva la primera aparición)")
    for _, fila in df[dup].iterrows():
        primera = df[(df["Nro_Factura"] == fila["Nro_Factura"]) & ~dup]["Fila_Excel"].iloc[0]
        informe.append(f"  - {fila['Nro_Factura']}: fila {fila['Fila_Excel']} repite la fila {primera} "
                       f"(Total ${fila['Total']:,.0f})".replace(",", "."))
    dup_total = pd.to_numeric(antes.loc[dup[dup].index, "Total"], errors="coerce").sum()  # Total tal como venía
    df = df[~dup].copy()
    otros_dup = df["Nro_Factura"].duplicated().sum()
    informe.append(f"- Números de factura repetidos con datos distintos: **{otros_dup}**")

    # 7) Débitos de las obras sociales: cantidades negativas (se conservan; restan del neto)
    df["Tipo_Movimiento"] = df["Cantidad"].map(lambda c: "Débito" if c < 0 else "Facturado")
    devol = df[df["Tipo_Movimiento"] == "Débito"]
    informe.append("\n## Débitos (cantidades negativas)\n")
    monto_devol = f"{-devol['Total'].sum():,.0f}".replace(",", ".")
    informe.append(f"- Renglones con cantidad negativa: **{len(devol)}**, total **-${monto_devol}**" +
                   ". Se conservan con signo negativo y se marcan en `Tipo_Movimiento`.")

    # 8) Tipos finales y orden
    df["Fecha"] = pd.to_datetime(df["Fecha"]).dt.date
    df["Cantidad"] = df["Cantidad"].astype(int)
    df["Precio_Unitario"] = df["Precio_Unitario"].round(2)
    df["Total"] = df["Total"].round(2)
    df = df.sort_values(["Fecha", "Nro_Factura"]).reset_index(drop=True)

    # --- Modelo estrella para Power BI ------------------------------------
    ffacturacion = df[["Fecha", "Nro_Factura", "CUIT", "Prestacion", "Profesional", "Cantidad",
                       "Precio_Unitario", "Total", "Tipo_Movimiento", "Origen_Dato", "Fila_Excel"]]
    dfinanciadores = (df[["CUIT", "Financiador"]].drop_duplicates().sort_values("Financiador").reset_index(drop=True))
    dfinanciadores["CUIT_Valido"] = dfinanciadores["CUIT"].map(lambda c: "Sí" if cuit_valido(c) else "No")
    dprestaciones = (df[["Prestacion", "Especialidad", "Precio_Unitario"]].drop_duplicates()
                     .sort_values(["Especialidad", "Prestacion"]).reset_index(drop=True)
                     .rename(columns={"Precio_Unitario": "Precio_Lista"}))
    dprofesionales = pd.DataFrame({"Profesional": PROFESIONALES})
    dias = pd.date_range(*PERIODO, freq="D")
    nombres_dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dcalendario = pd.DataFrame({
        "Fecha": dias.date,
        "Anio": dias.year,
        "Mes": dias.month,
        "Mes_Nombre": "Octubre",
        "Dia": dias.day,
        "Dia_Semana": [nombres_dia[d] for d in dias.day_of_week],
        "Dia_Semana_Nro": dias.day_of_week + 1,
        "Semana_ISO": dias.isocalendar().week.values,
        "Es_Fin_De_Semana": ["Sí" if d >= 5 else "No" for d in dias.day_of_week],
    })

    # Objetivos por profesional
    obj = pd.read_excel(entrada, sheet_name="Objetivos", dtype=object)
    obj_antes = obj.copy()
    obj["Profesional"] = obj["Profesional"].map(normalizar_profesional)
    obj["Objetivo Octubre"] = obj["Objetivo Octubre"].map(parsear_monto)
    fobjetivos = pd.DataFrame({"Profesional": obj["Profesional"], "Mes": PERIODO[0].date(),
                               "Objetivo": obj["Objetivo Octubre"]})
    informe.append("\n## Hoja Objetivos\n")
    for (_, a), (_, d) in zip(obj_antes.iterrows(), obj.iterrows()):
        cambios = []
        if a["Profesional"] != d["Profesional"]:
            cambios.append(f"nombre '{a['Profesional']}' -> '{d['Profesional']}'")
        if isinstance(a["Objetivo Octubre"], str):
            cambios.append(f"monto texto '{a['Objetivo Octubre']}' -> {d['Objetivo Octubre']:,.0f}".replace(",", "."))
        informe.append(f"- {d['Profesional']}: {'; '.join(cambios) if cambios else 'sin cambios'}")
    informe.append(f"- Profesionales de objetivos que no figuran en la facturación: "
                   f"**{(~fobjetivos['Profesional'].isin(df['Profesional'])).sum()}**")

    with pd.ExcelWriter(salida, engine="openpyxl") as xls:
        for nombre, tabla in [("fFacturacion", ffacturacion), ("dFinanciadores", dfinanciadores),
                              ("dPrestaciones", dprestaciones), ("dProfesionales", dprofesionales),
                              ("dCalendario", dcalendario), ("fObjetivos", fobjetivos)]:
            tabla.to_excel(xls, sheet_name=nombre, index=False)
    a_tabla_excel(salida, ["fFacturacion", "dFinanciadores", "dPrestaciones", "dProfesionales", "dCalendario",
                           "fObjetivos"])

    # --- Verificación de totales ------------------------------------------
    total_calculado = df.loc[df["Origen_Dato"] == "Total calculado (Cant x Precio)", "Total"].sum()
    informe.append("\n## Verificación de totales\n")
    informe.append(f"- Suma de la columna Total en el original (lo que da `=SUM(J5:J224)`): "
                   f"**${total_original:,.0f}**".replace(",", "."))
    informe.append(f"- Menos Total original de los duplicados eliminados: **-${dup_total:,.0f}**".replace(",", "."))
    informe.append(f"- Más totales que estaban vacíos y se calcularon: **+${total_calculado:,.0f}**".replace(",", "."))
    esperado = total_original - dup_total + total_calculado
    informe.append(f"- Total esperado: **${esperado:,.0f}** | Total limpio (neto): **${df['Total'].sum():,.0f}**"
                   .replace(",", ".") + (" ✔ coinciden" if abs(esperado - df["Total"].sum()) < 0.01 else " ✘ NO coinciden"))
    informe.append(f"- Facturación bruta: **${df.loc[df['Total'] > 0, 'Total'].sum():,.0f}** | "
                   f"Débitos: **-${-df.loc[df['Total'] < 0, 'Total'].sum():,.0f}**".replace(",", "."))
    informe.append(f"- Renglones finales: **{len(df)}** (facturas únicas: {df['Nro_Factura'].nunique()})")

    informe.append("\n## Facturación neta vs. objetivo por profesional\n")
    informe.append("| Profesional | Facturación neta | Objetivo | Cumplimiento |")
    informe.append("|---|---:|---:|---:|")
    netas = df.groupby("Profesional")["Total"].sum()
    for _, o in fobjetivos.iterrows():
        v = netas.get(o["Profesional"], 0)
        informe.append(f"| {o['Profesional']} | ${v:,.0f} | ${o['Objetivo']:,.0f} | {v / o['Objetivo']:.0%} |".replace(",", "."))

    informe.append("\n## Valores únicos después de limpiar\n")
    for col in ["Financiador", "Prestacion", "Especialidad", "Profesional"]:
        informe.append(f"- **{col}** ({df[col].nunique()}): {', '.join(sorted(df[col].unique()))}")

    informe.append("\n## Pendiente de decidir con el cliente\n")
    invalidos = dfinanciadores[dfinanciadores["CUIT_Valido"] == "No"]
    informe.append(f"1. **Débitos:** {len(devol)} renglones con cantidad negativa numerados como facturas "
                   "(no como notas de crédito). ¿Son débitos reales de las obras sociales (prestaciones rechazadas) "
                   "o errores de carga? Hoy se incluyen restando.")
    informe.append(f"2. **Duplicados:** se eliminaron {int(dup.sum())} renglones idénticos (misma factura). "
                   "Confirmar que es un error de la exportación y no una factura cargada dos veces en el sistema.")
    informe.append(f"3. **Faltantes calculados:** {int(falta_total.sum())} totales y {int(falta_cant.sum())} cantidad "
                   "se completaron con Cantidad x Precio (marcados en `Origen_Dato`). Confirmar si hubo descuentos.")
    n_inv = len(invalidos)
    informe.append(f"4. **CUIT:** {n_inv} de {len(dfinanciadores)} CUIT "
                   + ("no pasa" if n_inv == 1 else "no pasan") + " el dígito verificador "
                   f"({', '.join(invalidos['Financiador'] + ' ' + invalidos['CUIT'])}). No se modificaron.")
    cumplimiento = (netas.reindex(fobjetivos["Profesional"]).values / fobjetivos["Objetivo"].values)
    informe.append(f"5. **Objetivos:** la facturación neta supera el objetivo entre {cumplimiento.min():.0%} y "
                   f"{cumplimiento.max():.0%}. Confirmar si los objetivos están en la misma unidad que la facturación "
                   "(¿pesos? ¿miles? ¿semanales? ¿solo particulares?) antes de mostrar % de cumplimiento en el dashboard.")
    informe.append("6. **Total del sistema:** la fórmula `=SUM(J5:J224)` del original suma duplicados y "
                   "deja afuera los totales vacíos; no usarla como cifra de control.")

    ruta_informe = salida.parent / "informe_limpieza.md"
    ruta_informe.write_text("\n".join(informe) + "\n", encoding="utf-8")
    print("\n".join(informe))


if __name__ == "__main__":
    entrada = sys.argv[1] if len(sys.argv) > 1 else CARPETA / "facturacion_octubre_2026.xlsx"
    salida = sys.argv[2] if len(sys.argv) > 2 else CARPETA / "facturacion_octubre_2026_limpio.xlsx"
    main(entrada, salida)
