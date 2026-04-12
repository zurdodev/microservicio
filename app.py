from flask import Flask, request, jsonify
import os
import pdfplumber
import pytesseract
from PIL import Image
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "Microservicio activo en Railway"

@app.route('/extract', methods=['GET','POST'])
def extract():
    return "Ruta /extract funcionando"


@app.route('/pdf2json', methods=['POST'])
def pdf2json():
    file = request.files['file']
    orden_compra = {}

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""

            # ---------------- CABECERA ----------------
            match_noreq = re.search(r"No\. REQ\.\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_noreq:
                orden_compra["NOREQ"] = match_noreq.group(1)

            match_fecha = re.search(r"FECHA\s*/\s*DATE:\s*(\S+)", text, re.IGNORECASE)
            if match_fecha:
                orden_compra["FECHA"] = match_fecha.group(1)

            match_pagina = re.search(r"PAG\.\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_pagina:
                orden_compra["PAGINA"] = match_pagina.group(1)

            match_proveedor = re.search(r"PROVEEDOR/SUPPLIER:\s*(.+)", text, re.IGNORECASE)
            if match_proveedor:
                orden_compra["PROVEEDOR"] = match_proveedor.group(1).strip()

            match_shipto = re.search(r"EMBARCAR A\s*/SHIP TO:\s*(.+)", text, re.IGNORECASE)
            if match_shipto:
                orden_compra["SHIPTO"] = match_shipto.group(1).strip()

            match_mes = re.search(r"Delivery Month:\s*(.+)", text, re.IGNORECASE)
            if match_mes:
                orden_compra["MES_ENTREGA"] = match_mes.group(1).strip()

            # OCR para bloque Facturar a / Bill To
            if "Facturar a" in text or "Bill To" in text:
                for image in page.images:
                    im = page.crop((image["x0"], image["top"], image["x1"], image["bottom"])).to_image(resolution=300)
                    pil_img = im.original
                    ocr_text = pytesseract.image_to_string(pil_img, lang="spa+eng")

                    lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
                    if len(lines) > 0:
                        orden_compra["NOMBRE"] = lines[0]
                    if len(lines) > 1:
                        orden_compra["DIRECCION"] = lines[1]

                    match_phone = re.search(r"Phone:\s*(.+)", ocr_text, re.IGNORECASE)
                    if match_phone:
                        orden_compra["TELEFONO"] = match_phone.group(1).strip()

                    match_fax = re.search(r"Fax:\s*(.+)", ocr_text, re.IGNORECASE)
                    if match_fax:
                        orden_compra["FAX"] = match_fax.group(1).strip()

                    match_rfc = re.search(r"R\.F\.C:\s*(\S+)", ocr_text, re.IGNORECASE)
                    if match_rfc:
                        orden_compra["RFC"] = match_rfc.group(1)

            # ---------------- POSICIONES ----------------
            match_item = re.search(r"ITEM\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_item:
                orden_compra["ITEM"] = match_item.group(1)

            match_planta = re.search(r"(PLANTA|PLANT)\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_planta:
                orden_compra["PLANTA"] = match_planta.group(2)

            match_material = re.search(r"MATERIAL\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_material:
                orden_compra["MATERIAL"] = match_material.group(1)

            match_desc = re.search(r"(DESCRIPCION|DESCRIPTION)\s*:\s*(.+)", text, re.IGNORECASE)
            if match_desc:
                orden_compra["DESCRIPCION"] = match_desc.group(2).strip()

            match_cant = re.search(r"(CANTIDAD|QUANTITY)\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_cant:
                orden_compra["CANTIDAD"] = match_cant.group(2)

            match_matwrl = re.search(r"Mat\. WRL\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_matwrl:
                orden_compra["MAT_WRL"] = match_matwrl.group(1)

            match_mm2 = re.search(r"\$MM2\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_mm2:
                orden_compra["MM2"] = match_mm2.group(1)

            match_ton = re.search(r"\$TO\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_ton:
                orden_compra["TON"] = match_ton.group(1)

            match_imp_siniva = re.search(r"(IMPORTE S/IVA|AMOUNT)\s*:\s*(\S+)", text, re.IGNORECASE)
            if match_imp_siniva:
                orden_compra["IMPORTE_SINIVA"] = match_imp_siniva.group(2)

            # ---------------- PIE DE PÁGINA ----------------
            match_total_cant = re.search(r"TOTAL CANTIDAD:\s*(\S+)", text, re.IGNORECASE)
            if match_total_cant:
                orden_compra["TOTAL_CANTIDAD"] = match_total_cant.group(1)

            match_descuento = re.search(r"DESCUENTO:\s*(\S+)", text, re.IGNORECASE)
            if match_descuento:
                orden_compra["DESCUENTO"] = match_descuento.group(1)

            match_subtotal = re.search(r"SUBTOTAL:\s*(\S+)", text, re.IGNORECASE)
            if match_subtotal:
                orden_compra["SUBTOTAL"] = match_subtotal.group(1)

            match_iva = re.search(r"IVA:\s*(\S+)", text, re.IGNORECASE)
            if match_iva:
                orden_compra["IVA"] = match_iva.group(1)

            match_total = re.search(r"TOTAL:\s*(\S+)", text, re.IGNORECASE)
            if match_total:
                orden_compra["TOTAL"] = match_total.group(1)

            match_moneda = re.search(r"MONEDA\s*CURRENCY:\s*(\S+)", text, re.IGNORECASE)
            if match_moneda:
                orden_compra["MONEDA"] = match_moneda.group(1)

    return jsonify(orden_compra)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

