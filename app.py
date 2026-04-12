from flask import Flask, request, jsonify
import pdfplumber
import pytesseract
from PIL import Image
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "Microservicio activo en Railway"

@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files['file']
    text = ""

    try:
        # Extraer texto digital u OCR
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                else:
                    pil_image = page.to_image(resolution=300).original
                    ocr_text = pytesseract.image_to_string(pil_image, lang="spa")
                    text += ocr_text + "\n"

        # ---------------------------
        # REGEX por secciones
        # ---------------------------

        # CABECERA
        no_req = re.search(r'No\.?\s*REQ.*?(\d+)', text, re.IGNORECASE)
        fecha = re.search(r'(?:FECHA|DATE)\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})', text, re.IGNORECASE)
        pagina = re.search(r'PAG.*?(\d+)', text, re.IGNORECASE)
        proveedor = re.search(r'(?:PROVEEDOR|SUPPLIER)\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        shipto = re.search(r'(?:EMBARCAR A|SHIP TO)\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        mes_entrega = re.search(r'Delivery Month\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        billto_nombre = re.search(r'FACTURAR A.*?\n(.+)', text, re.IGNORECASE)
        billto_direccion = re.search(r'FACTURAR A.*?\n.+\n(.+)', text, re.IGNORECASE)
        telefono = re.search(r'PHONE\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        fax = re.search(r'FAX\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        rfc = re.search(r'R\.?F\.?C\.?\s*[:\-]?\s*(.+)', text, re.IGNORECASE)

        # POSICIÓN
        partida = re.search(r'PARTIDA\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
        item = re.search(r'ITEM\s*[:\-]?\s*(\d+)', text, re.IGNORECASE)
        planta = re.search(r'(?:PLANTA|PLANT)\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        unidad = re.search(r'(?:UNIDAD|UNIT)\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        material = re.search(r'MATERIAL\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        descripcion = re.search(r'(?:DESCRIPCION|DESCRIPTION)\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        cantidad = re.search(r'(?:CANTIDAD|QUANTITY)\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        mat_wrl = re.search(r'Mat\.?\s*WRL\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        mm2 = re.search(r'\$MM2\s*[:\-]?\s*([\d.,]+)', text)
        ton = re.search(r'\$TO\s*[:\-]?\s*([\d.,]+)', text)
        importe_siniva = re.search(r'(?:IMPORTE S/IVA|AMOUNT)\s*[:\-]?\s*([\d.,]+)', text, re.IGNORECASE)

        # PIE DE PÁGINA
        total_cantidad = re.search(r'TOTAL CANTIDAD\s*[:\-]?\s*(.+)', text, re.IGNORECASE)
        descuento = re.search(r'DESCUENTO\s*[:\-]?\s*([\d.,]+)', text, re.IGNORECASE)
        subtotal = re.search(r'SUBTOTAL\s*[:\-]?\s*([\d.,]+)', text, re.IGNORECASE)
        iva = re.search(r'IVA\s*[:\-]?\s*([\d.,]+)', text, re.IGNORECASE)
        total = re.search(r'TOTAL\s*[:\-]?\s*([\d.,]+)', text, re.IGNORECASE)
        moneda = re.search(r'(?:MONEDA|CURRENCY)\s*[:\-]?\s*([A-Z]{3})', text, re.IGNORECASE)

        # ---------------------------
        # Respuesta JSON
        # ---------------------------
        return jsonify({
            "contenido": text.strip(),
            "cabecera": {
                "noreq": no_req.group(1) if no_req else None,
                "fecha": fecha.group(1) if fecha else None,
                "pagina": pagina.group(1) if pagina else None,
                "proveedor": proveedor.group(1) if proveedor else None,
                "shipto": shipto.group(1) if shipto else None,
                "mes_entrega": mes_entrega.group(1) if mes_entrega else None,
                "nombre": billto_nombre.group(1) if billto_nombre else None,
                "direccion": billto_direccion.group(1) if billto_direccion else None,
                "telefono": telefono.group(1) if telefono else None,
                "fax": fax.group(1) if fax else None,
                "rfc": rfc.group(1) if rfc else None
            },
            "posicion": {
                "partida": partida.group(1) if partida else None,
                "item": item.group(1) if item else None,
                "planta": planta.group(1) if planta else None,
                "unidad": unidad.group(1) if unidad else None,
                "material": material.group(1) if material else None,
                "descripcion": descripcion.group(1) if descripcion else None,
                "cantidad": cantidad.group(1) if cantidad else None,
                "mat_wrl": mat_wrl.group(1) if mat_wrl else None,
                "mm2": mm2.group(1) if mm2 else None,
                "ton": ton.group(1) if ton else None,
                "importe_siniva": importe_siniva.group(1) if importe_siniva else None
            },
            "pie": {
                "total_cantidad": total_cantidad.group(1) if total_cantidad else None,
                "descuento": descuento.group(1) if descuento else None,
                "subtotal": subtotal.group(1) if subtotal else None,
                "iva": iva.group(1) if iva else None,
                "total": total.group(1) if total else None,
                "moneda": moneda.group(1) if moneda else None
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)