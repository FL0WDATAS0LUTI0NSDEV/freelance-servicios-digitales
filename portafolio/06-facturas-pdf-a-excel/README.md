# Ejemplo 6 — Facturas en PDF a Libro IVA Compras y Ventas en Excel

> **Ejemplo con datos ficticios.** El centro médico, sus proveedores y clientes, los CUIT y los montos son inventados; cada PDF lleva la marca "DATOS FICTICIOS". El tratamiento de IVA de cada prestación es ilustrativo: en un caso real lo define el contador.

![Facturas PDF a Excel](../capturas/4-facturas-pdf-a-excel.png)

## El problema
Un centro médico recibe todos los meses decenas de facturas de compra en PDF (insumos, equipos, lavadero, energía), cada proveedor con su propio diseño, y emite sus propias facturas: a empresas, a pacientes particulares y a obras sociales. Alguien las abre una por una y copia fecha, número, CUIT, netos, IVA y percepciones a una planilla para el Libro IVA. Es lento, aburrido y propenso a errores: facturas cargadas dos veces, CUIT mal tipeados, notas de crédito sumadas en vez de restadas, montos que no cierran.

## La solución
Un script en Python que lee la carpeta de PDF y arma el libro solo:

| Paso | Qué hace |
|---|---|
| Lectura | Extrae el texto de cada PDF con `pdfplumber`, ignorando marcas de agua |
| Extracción | Reconoce tres diseños de comprobante con expresiones regulares: fecha, código y tipo (factura o nota de crédito A, B, C o M), punto de venta, número, CUIT, razón social, neto e IVA por alícuota (27 %, 21 %, 10,5 %, 5 % y 2,5 %), no gravado, exento, percepciones de IVA y de IIBB, y total |
| Normalización | Montos en formato argentino a número, nombres prolijos ("EQUIPOS MÉDICOS DEL SUR SRL" → "Equipos Médicos del Sur SRL"), neto repartido por alícuota cuando el emisor solo informa un subtotal, neto e IVA de las facturas B desde el "IVA contenido" (Ley 27.743), y notas de crédito en negativo |
| Controles | Dígito verificador del CUIT, duplicados (mismo CUIT + código + punto de venta + número), que todos los conceptos sumen el total, que el IVA corresponda a neto × alícuota, fecha dentro del período y, en ventas, saltos en la numeración |
| Excel | Hoja **Libro IVA Compras** o **Ventas** con totales, hoja de resumen **por proveedor** o **por cliente** con fórmulas `SUMAR.SI` y control cruzado, y hoja **Controles** con cada observación |

Si un PDF no se puede leer (por ejemplo, un escaneo sin texto), no frena el proceso: queda listado en Controles para revisarlo a mano.

## Resultado del ejemplo
**Compras** (`facturas/` → `libro_iva_compras.xlsx`)
- 18 PDF leídos, de 7 proveedores y 2 diseños distintos.
- 17 comprobantes cargados: 15 facturas y 2 notas de crédito (restan del total).
- Incluye IVA 27 % (energía), IVA 10,5 % (equipo médico), percepciones de IVA, un concepto no gravado y un seguro exento.
- 1 duplicado detectado y excluido; 1 CUIT con dígito verificador inválido, marcado en rojo.

**Ventas** (`facturas_ventas/` → `libro_iva_ventas.xlsx`)
- 8 comprobantes propios: facturas A a empresas (exámenes laborales), facturas B a pacientes particulares, una factura B exenta a una obra social y una nota de crédito.
- 1 salto de numeración detectado (falta la factura A 00002-00000103).

**En los dos libros:** 0 diferencias contra los importes originales, verificado comprobante por comprobante y campo por campo, y el resumen recalculado coincide con el total del libro.

## Cómo correrlo
```bash
pip install pdfplumber openpyxl reportlab
python generar_facturas.py          # crea las facturas de ejemplo en facturas/ y facturas_ventas/
python extraer_facturas.py          # arma libro_iva_compras.xlsx
python extraer_facturas.py ventas   # arma libro_iva_ventas.xlsx
python extraer_facturas.py <carpeta_pdf> <salida.xlsx> <MM/AAAA> [compras|ventas]
```

## Para un cliente real
- Se ajustan los patrones a los diseños de sus proveedores (los más frecuentes primero) y al sistema con el que factura.
- Las facturas escaneadas necesitan OCR; se cotiza aparte.
- Las facturas B o C recibidas sin IVA discriminado se cargan como no gravado y quedan marcadas para revisar.
- Los datos reales se procesan solo en la carpeta privada del cliente, nunca en este repositorio.
