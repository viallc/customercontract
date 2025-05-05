import fitz  # PyMuPDF

# Datos de ejemplo (ajusta según tu formulario real)
data = {
    "agreement_date": "2025-05-03",
    "owner_name": "John Doe",
    "company_name": "Acme Corp",
    "property_address": "123 Main St, Springfield, IL",
    "insurance_carrier": "Best Insurance",
    "email": "john@example.com",
    "cell_phone": "555-123-4567",
    "work_phone": "555-987-6543",
    "claim_number": "CLM-2025-001",
    "representative_name": "Jane Rep",
    "representative_phone": "555-555-5555",
    "representative_email": "jane@vi-a.com"
}

def generar_contrato_pdf(data, output_path="contract_filled.pdf"):
    doc = fitz.open("contract_template.pdf")
    page = doc[0]

    # Escribe los datos en las posiciones aproximadas (ajusta según tu PDF)
    page.insert_text((120, 79), data.get("agreement_date", ""), fontsize=10)
    page.insert_text((145, 239), data.get("owner_name", ""), fontsize=10)
    page.insert_text((120, 255), data.get("company_name", ""), fontsize=10)
    page.insert_text((120, 277), data.get("property_address", ""), fontsize=10)
    page.insert_text((120, 295), data.get("insurance_carrier", ""), fontsize=10)
    page.insert_text((470, 240), data.get("email", ""), fontsize=10)
    page.insert_text((490, 255), data.get("cell_phone", ""), fontsize=10)
    ##page.insert_text((495, 278), data.get("work_phone", ""), fontsize=10)
    page.insert_text((480, 298), data.get("claim_number", ""), fontsize=10)
    page.insert_text((400, 100), data.get("representative_name", ""), fontsize=10)
    page.insert_text((400, 123), data.get("representative_phone", ""), fontsize=10)
    page.insert_text((400, 140), data.get("representative_email", ""), fontsize=10)
    
    # Firma del CLIENTE (Propietario)
    page.insert_text((100, 665), data["owner_name"], fontsize=10)  # Ajusta (100, 700) según tu PDF

    # Firma del REPRESENTANTE
    page.insert_text((400, 665), data["representative_name"], fontsize=10)  # Ajusta (400, 700) según tu PDF
    page.insert_text((410, 685), data["agreement_date"], fontsize=10)
    doc.save(output_path)
    doc.close()
    print(f"¡PDF generado como {output_path}!")

if __name__ == "__main__":
    generar_contrato_pdf(data)