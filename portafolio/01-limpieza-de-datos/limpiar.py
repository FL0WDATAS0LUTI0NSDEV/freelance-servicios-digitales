"""
Limpieza de una planilla de ventas desordenada.

Uso:
    python limpiar.py ventas_original.csv ventas_limpias.csv

Qué corrige:
- Fechas en distintos formatos (2026-03-05, 05/03/2026, 5-3-26...)
- Nombres de clientes, productos, vendedores y provincias escritos de varias formas
- Montos con "$", puntos de miles y comas decimales
- Cantidades o montos faltantes (se calculan con el precio unitario)
- Filas vacías y filas duplicadas
Genera además un informe (informe_limpieza.md) con todo lo que se cambió.
"""
import sys
import unicodedata
from datetime import datetime

import pandas as pd


# --- Catálogos: la forma "oficial" de escribir cada valor -------------------
CLIENTES = ["Almacén Don Pepe", "Kiosco La Esquina", "Supermercado Sol",
            "Dietética Natura", "Bar El Faro", "Rotisería Doña Rosa"]
PRODUCTOS = ["Yerba 1kg", "Café 500g", "Azúcar 1kg", "Aceite 900ml", "Harina 1kg"]
VENDEDORES = ["Laura Gómez", "Martín Ruiz", "Sofía Paz"]
PROVINCIAS = {
    "buenos aires": "Buenos Aires", "bs as": "Buenos Aires", "bs. as.": "Buenos Aires",
    "cordoba": "Córdoba", "cba": "Córdoba",
    "santa fe": "Santa Fe", "sta fe": "Santa Fe",
}
FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%y"]


def clave(texto) -> str:
    """Pasa a minúsculas, saca tildes y espacios de más: '  ALMACÉN  don pepe' -> 'almacen don pepe'."""
    if pd.isna(texto):
        return ""
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.lower().split())


def normalizar(valor, catalogo):
    return {clave(c): c for c in catalogo}.get(clave(valor), valor)


def normalizar_vendedor(valor):
    k = clave(valor)
    for v in VENDEDORES:
        nombre, apellido = clave(v).split()
        if k in (f"{nombre} {apellido}", f"{nombre} {apellido[0]}."):
            return v
    return valor


def normalizar_provincia(valor):
    k = clave(valor)
    return PROVINCIAS.get(k, PROVINCIAS.get(clave(k), valor))


def parsear_fecha(valor):
    for fmt in FORMATOS_FECHA:
        try:
            return datetime.strptime(str(valor).strip(), fmt).date()
        except ValueError:
            continue
    return pd.NaT


def parsear_monto(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return float("nan")
    s = str(valor).replace("$", "").strip()
    if "," in s:  # formato argentino: 1.234,50
        s = s.replace(".", "").replace(",", ".")
    return float(s)


def main(entrada, salida):
    df = pd.read_csv(entrada, dtype=str)
    informe = [f"# Informe de limpieza\n", f"- Filas originales: **{len(df)}**"]

    vacias = df.isna().all(axis=1) | (df.fillna("").apply(lambda c: c.str.strip()) == "").all(axis=1)
    df = df[~vacias]
    informe.append(f"- Filas vacías eliminadas: **{vacias.sum()}**")

    df["Fecha"] = df["Fecha"].map(parsear_fecha)
    df["Cliente"] = df["Cliente"].map(lambda v: normalizar(v, CLIENTES))
    df["Producto"] = df["Producto"].map(lambda v: normalizar(v, PRODUCTOS))
    df["Vendedor"] = df["Vendedor"].map(normalizar_vendedor)
    df["Provincia"] = df["Provincia"].map(normalizar_provincia)
    df["Monto"] = df["Monto"].map(parsear_monto)
    df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce")

    # Completar faltantes con el precio unitario de cada producto
    precio = (df["Monto"] / df["Cantidad"]).groupby(df["Producto"]).median()
    falta_monto = df["Monto"].isna() & df["Cantidad"].notna()
    falta_cant = df["Cantidad"].isna() & df["Monto"].notna()
    df.loc[falta_monto, "Monto"] = df.loc[falta_monto, "Cantidad"] * df.loc[falta_monto, "Producto"].map(precio)
    df.loc[falta_cant, "Cantidad"] = (df.loc[falta_cant, "Monto"] / df.loc[falta_cant, "Producto"].map(precio)).round()
    informe.append(f"- Montos faltantes completados: **{falta_monto.sum()}**")
    informe.append(f"- Cantidades faltantes completadas: **{falta_cant.sum()}**")

    antes = len(df)
    df = df.drop_duplicates()
    informe.append(f"- Filas duplicadas eliminadas: **{antes - len(df)}**")

    df["Cantidad"] = df["Cantidad"].astype(int)
    df["Monto"] = df["Monto"].round(2)
    df = df.sort_values(["Fecha", "Cliente"]).reset_index(drop=True)
    df.to_csv(salida, index=False, encoding="utf-8")

    informe.append(f"- Filas finales: **{len(df)}**\n")
    informe.append("## Valores únicos después de limpiar\n")
    for col in ["Cliente", "Producto", "Vendedor", "Provincia"]:
        informe.append(f"- **{col}** ({df[col].nunique()}): {', '.join(sorted(df[col].unique()))}")
    with open("informe_limpieza.md", "w", encoding="utf-8") as f:
        f.write("\n".join(informe) + "\n")
    print("\n".join(informe))


if __name__ == "__main__":
    entrada = sys.argv[1] if len(sys.argv) > 1 else "ventas_original.csv"
    salida = sys.argv[2] if len(sys.argv) > 2 else "ventas_limpias.csv"
    main(entrada, salida)
