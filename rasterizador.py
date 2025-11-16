import os
import pdfplumber

def pdf_a_txt_simple(ruta_pdf, ruta_salida_txt):
    texto_total = []

    with pdfplumber.open(ruta_pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Procesando página {i+1}/{len(pdf.pages)}...")
            texto = page.extract_text() or ""
            texto_total.append(f"\n\n===== PÁGINA {i+1} =====\n\n")
            texto_total.append(texto)

    with open(ruta_salida_txt, "w", encoding="utf-8") as f:
        f.write("".join(texto_total))

    print(f"Listo. Texto guardado en: {ruta_salida_txt}")

if __name__ == "__main__":
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    # PON AQUÍ EL NOMBRE REAL DE TU PDF
    ruta_pdf = os.path.join(ruta_base, "CHF - Guia Emprendedores.pdf")
    ruta_txt = os.path.join(ruta_base, "base_conocimiento_childfund.txt")
    pdf_a_txt_simple(ruta_pdf, ruta_txt)