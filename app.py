from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os
from urllib.parse import urljoin, urlparse, urlunparse, urlencode
import fitz  # PyMuPDF
import tempfile
import urllib.request
import time

app = Flask(__name__)
app.secret_key = 'super-secret-key-1234567890'

MONDAY_API_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUwNTAwNTIwNSwiYWFpIjoxMSwidWlkIjo3NTMxNTc3OSwiaWFkIjoiMjAyNS0wNC0yN1QwMTo0ODo0MS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjcxNDA4MzgsInJnbiI6InVzZTEifQ.PJM61IpSMbsPU1JlrlkZTEJXY_bqqog8QgFgCzsGozk'
MONDAY_API_URL = 'https://api.monday.com/v2'
MONDAY_API_FILE_URL = 'https://api.monday.com/v2/file'
BOARD_ID = "9060673210"

COMPANYCAM_TOKEN = "tWcIKqLxjG9S9xLIX-BsL0vKEpEIoJiqPG5TZ1gWa68"

def crear_proyecto_companycam(nombre, direccion, labels=None):
    url = "https://api.companycam.com/v2/projects"
    headers = {
        "Authorization": f"Bearer {COMPANYCAM_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "name": nombre,
        "address": direccion
    }
    print("DEBUG: Creando proyecto en CompanyCam con datos:", json.dumps(data, indent=2))
    response = requests.post(url, headers=headers, json=data)
    print("Respuesta de CompanyCam:", response.status_code, response.text)
    if response.status_code == 201:
        project = response.json()
        project_id = project["id"]
        project_link = f"https://app.companycam.com/projects/{project_id}"
        
        # Si hay labels, primero obtenemos la lista de labels disponibles
        if labels:
            # Obtener lista de labels disponibles
            labels_list_url = "https://api.companycam.com/v2/labels"
            labels_list_response = requests.get(labels_list_url, headers=headers)
            print("DEBUG: Respuesta de lista de labels:", labels_list_response.status_code, labels_list_response.text)
            
            if labels_list_response.status_code == 200:
                available_labels = labels_list_response.json()
                # Crear un diccionario de display_value a ID
                label_map = {label["display_value"]: label["id"] for label in available_labels}
                print("DEBUG: Mapa de labels disponibles:", label_map)
                
                # Filtrar solo los labels que existen
                valid_label_ids = []
                for label in labels:
                    if label in label_map:
                        valid_label_ids.append(label_map[label])
                    else:
                        print(f"DEBUG: Label no encontrado: {label}")
                
                if valid_label_ids:
                    # Asignar los labels usando sus IDs
                    labels_url = f"https://api.companycam.com/v2/projects/{project_id}"
                    # Actualizar el proyecto con los labels y mantener los datos originales
                    update_data = {
                        "name": nombre,
                        "address": {
                            "street_address_1": direccion,
                            "street_address_2": "",
                            "city": "",
                            "state": "",
                            "postal_code": "",
                            "country": ""
                        },
                        "labels": valid_label_ids
                    }
                    print("DEBUG: Actualizando proyecto con labels:", json.dumps(update_data, indent=2))
                    update_response = requests.put(labels_url, headers=headers, json=update_data)
                    print("Respuesta de actualización de labels:", update_response.status_code, update_response.text)
        
        return project_link
    else:
        print("Error creando proyecto en CompanyCam:", response.text)
        return None

@app.route('/commercial', methods=['GET', 'POST'])
def commercial_form():
    if request.method == 'POST':
        form = request.form
        nombre = form.get('company_name')
        direccion = f"{form.get('address_line')}, {form.get('city')}, {form.get('state')} {form.get('zip')}"
        contact_status = form.get("contact_status")

        # Usa los labels exactos enviados desde los campos ocultos del formulario
        labels = []
        if form.get("companycam_source_label"):
            labels.append(form.get("companycam_source_label"))
        if form.get("companycam_roof_label"):
            labels.append(form.get("companycam_roof_label"))
        if form.get("companycam_property_label"):
            labels.append(form.get("companycam_property_label"))
        print("DEBUG LABELS PARA COMPANYCAM:", labels)

        companycam_link = None
        if contact_status != "Do not contact this client":
            companycam_link = crear_proyecto_companycam(nombre, direccion, labels)

        location_dict = {
            "lat": "0",
            "lng": "0",
            "address": direccion
        }

        column_values = {
            "location_mkn76b10": location_dict,
            "text_mkn9rsf7": form.get("Building Owner"),
            "text_mkn9613s": form.get("owner_email"),
            "text_mkn926rr": form.get("owner_phone"),
            "text_mkn8rzyk": form.get("Point of Contact"),
            "text_mkn83a0h": form.get("Point of Contact"),
            "text_mkn8264c": form.get("Point of Contact Phone"),
            "color_mkqkhd0a": {"label": contact_status},
            "status_mkn88p2w": {"label": form.get("roof_type")},
            "status_mkn8wdk2": {"label": form.get("status_mkn8wdk2")},
            "connect_boards_mkn7js4k": {
                "item_ids": [int(form.get("salesperson"))]
            },
            "status_mkn81f2b": {"label": "Commercial"},
            # Representative Info
            "text_mkqmk6e6": form.get("rep_name"),
            "email_mkqms6fy": {
                "email": form.get("rep_email"),
                "text": form.get("rep_name") or form.get("rep_email") or ""
            },
            "text_mkqm3b3r": form.get("rep_phone"),
        }

        if companycam_link:
            column_values["link_mkn7g1jw"] = {
                "url": companycam_link,
                "text": f"CompanyCam - {nombre}"
            }

        mutation = '''
        mutation ($boardId: ID!, $itemName: String!, $columnVals: JSON!) {
          create_item (
            board_id: $boardId,
            item_name: $itemName,
            column_values: $columnVals
          ) {
            id
          }
        }
        '''

        variables = {
            "boardId": BOARD_ID,
            "itemName": nombre,
            "columnVals": json.dumps(column_values)
        }

        headers = {
            "Authorization": MONDAY_API_TOKEN,
            "Content-Type": "application/json"
        }

        response = requests.post(MONDAY_API_URL, headers=headers, json={"query": mutation, "variables": variables})
        result = response.json()

        if "errors" in result:
            return f"Monday.com error: {result['errors']}"

        item_id = result["data"]["create_item"]["id"]
        flash('Submitted Successfully.', 'success')

        # Solo genera links si se puede contactar al cliente
        if contact_status != "Do not contact this client":
            # Genera el link para el vendedor
            base_url = request.url_root.rstrip('/')
            seller_link = f"{base_url}/contract_form?inspection_id={item_id}"
            # Guarda el link en la columna link_seller
            mutation_link = '''
            mutation ($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
              change_column_value(board_id: $boardId, item_id: $itemId, column_id: $columnId, value: $value) {
                id
              }
            }
            '''
            variables_link = {
                "boardId": BOARD_ID,
                "itemId": str(item_id),
                "columnId": "text_mkqmdq68",
                "value": f'"{seller_link}"'
            }
            response_link = requests.post(MONDAY_API_URL, headers=headers, json={"query": mutation_link, "variables": variables_link})
            print("DEBUG: Monday.com seller link save response =", response_link.text)

        return redirect(url_for('commercial_form'))

    return render_template("commercial_form.html")

@app.route('/contract_form', methods=['GET', 'POST'])
def contract_form():
    inspection_id = request.args.get('inspection_id')
    is_client = request.args.get('client') == '1'
    prefill_data = {}
    seller_signed_at = None
    customer_signed_at = None
    link_customer_sign = None
    seller_signature_url = None
    customer_signature_url = None

    # Diccionario de mapeo de IDs de Monday.com a nombres de campo del formulario
    monday_to_form = {
        # Point of Contact
        "text_mkn8rzyk": "point_of_contact",  # Solo para mostrar
        "text_mkn83a0h": "point_of_contact_email",
        "text_mkn8264c": "point_of_contact_phone",
        # Owner
        "text_mkn9rsf7": "owner_name",
        "text_mkn9613s": "owner_email",
        "text_mkn926rr": "owner_phone",
        # Dirección y compañía
        "location_mkn76b10": "property_address",
        "name": "company_name",
        # Representative Info
        "text_mkqmk6e6": "rep_name",
        "email_mkqms6fy": "rep_email",
        "text_mkqm3b3r": "rep_phone",
    }

    real_item_id = None
    if inspection_id:
        real_item_id = inspection_id
        print("DEBUG: Using inspection_id as item_id:", real_item_id)

    if real_item_id:
        # Consulta a Monday.com para obtener los datos del item de inspección
        query = """
        query ($itemId: [ID!]) {
          items(ids: $itemId) {
            name
            column_values {
              id
              text
              value
              type
              column { title }
            }
          }
        }
        """
        variables = {"itemId": [str(real_item_id)]}
        headers = {
            "Authorization": MONDAY_API_TOKEN,
            "Content-Type": "application/json"
        }
        response = requests.post(MONDAY_API_URL, headers=headers, json={"query": query, "variables": variables})
        result = response.json()
        print("DEBUG: Monday.com item result =", json.dumps(result, indent=2))
        if "data" in result and result["data"].get("items"):
            item = result["data"]["items"][0]
            for col in item["column_values"]:
                form_key = monday_to_form.get(col["id"])
                if form_key:
                    if col["id"] == "location_mkn76b10" and col.get("value"):
                        import json as pyjson
                        loc = pyjson.loads(col["value"])
                        prefill_data[form_key] = loc.get("address", "")
                    else:
                        prefill_data[form_key] = col["text"]
                if col["id"] == "text_mkqmfm3y":
                    seller_signed_at = col["text"]
                if col["id"] == "text_mkqmrv1e":
                    customer_signed_at = col["text"]
                if col["id"] == "text_mkqm8s8x":
                    link_customer_sign = col["text"]
                if col["id"] == "file_mkqm8j5r" and col.get("value"):
                    import json as pyjson
                    file_info = pyjson.loads(col["value"])
                    if file_info and "files" in file_info and file_info["files"]:
                        file0 = file_info["files"][0]
                        if "public_url" in file0:
                            seller_signature_url = file0["public_url"]
                        else:
                            print("DEBUG: 'public_url' not found in file0:", file0)
                            if "assetId" in file0:
                                seller_signature_url = obtener_public_url_por_asset_id(file0["assetId"])
                if col["id"] == "file_mkqmnwqm" and col.get("value"):
                    import json as pyjson
                    file_info = pyjson.loads(col["value"])
                    if file_info and "files" in file_info and file_info["files"]:
                        file0 = file_info["files"][0]
                        if "public_url" in file0:
                            customer_signature_url = file0["public_url"]
                        else:
                            print("DEBUG: 'public_url' not found in file0:", file0)
                            if "assetId" in file0:
                                customer_signature_url = obtener_public_url_por_asset_id(file0["assetId"])
            if "name" in item:
                prefill_data["company_name"] = item["name"]
            # Sobrescribe el phone del point of contact con el del rep
            if "rep_phone" in prefill_data:
                prefill_data["point_of_contact_phone"] = prefill_data["rep_phone"]

    print("DEBUG: prefill_data =", prefill_data)
    if request.method == 'POST':
        # Recoge los datos del formulario
        seller_signature = request.form.get('seller_signature')
        seller_signed_at_val = request.form.get('seller_signed_at')
        customer_signature = request.form.get('customer_signature')
        customer_signed_at_val = request.form.get('customer_signed_at')
        mutation = '''
        mutation ($itemId: ID!, $columnId: String!, $value: String!) {
          change_column_value(item_id: $itemId, column_id: $columnId, value: $value) {
            id
          }
        }
        '''
        headers = {
            "Authorization": MONDAY_API_TOKEN,
            "Content-Type": "application/json"
        }
        # Si es flujo de cliente, guarda la firma y fecha del cliente
        if is_client:
            # Guarda la fecha SOLO si existe
            if customer_signed_at_val:
                print(f"DEBUG: Guardando fecha de firma del cliente en Monday.com: {customer_signed_at_val}")
                variables_date = {
                    "itemId": str(inspection_id),
                    "columnId": "text_mkqmrv1e",
                    "value": f'"{customer_signed_at_val}"'
                }
                requests.post(MONDAY_API_URL, headers=headers, json={"query": mutation, "variables": variables_date})
            else:
                print("ADVERTENCIA: No se recibió fecha de firma del cliente, no se guarda en Monday.com")
            # Esperar y reintentar obtener la URL pública de la firma del cliente
            customer_signature_url = customer_signature_url  # valor inicial
            # Buscar assetId de la firma del cliente
            asset_id_cliente = None
            query = '''
            query ($itemId: [ID!]) {
              items(ids: $itemId) {
                column_values {
                  id
                  value
                }
              }
            }
            '''
            variables = {"itemId": [str(inspection_id)]}
            headers = {
                "Authorization": MONDAY_API_TOKEN,
                "Content-Type": "application/json"
            }
            response = requests.post(MONDAY_API_URL, headers=headers, json={"query": query, "variables": variables})
            result = response.json()
            for col in result["data"]["items"][0]["column_values"]:
                if col["id"] == "file_mkqmnwqm" and col.get("value"):
                    import json as pyjson
                    file_info = pyjson.loads(col["value"])
                    if file_info and "files" in file_info and file_info["files"]:
                        file0 = file_info["files"][0]
                        if "assetId" in file0:
                            asset_id_cliente = file0["assetId"]
            if asset_id_cliente:
                customer_signature_url = esperar_url_publica(asset_id_cliente, max_intentos=20, delay=3)
            # Sube la firma como archivo
            if customer_signature:
                import base64
                import tempfile
                header, encoded = customer_signature.split(',', 1)
                data = base64.b64decode(encoded)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                    tmpfile.write(data)
                    tmpfile_path = tmpfile.name
                file_mutation = '''
                mutation ($file: File!, $itemId: ID!, $columnId: String!) {
                  add_file_to_column (file: $file, item_id: $itemId, column_id: $columnId) {
                    id
                  }
                }
                '''
                with open(tmpfile_path, 'rb') as f:
                    file_bytes = f.read()
                m = MultipartEncoder(
                    fields={
                        'query': file_mutation,
                        'variables': f'{{"file": null, "itemId": "{inspection_id}", "columnId": "file_mkqmnwqm"}}',
                        'map': '{"0": ["variables.file"]}',
                        '0': ('customer_signature.png', file_bytes, 'image/png')
                    }
                )
                file_headers = {
                    "Authorization": MONDAY_API_TOKEN,
                    "Content-Type": m.content_type
                }
                requests.post(MONDAY_API_FILE_URL, headers=file_headers, data=m)
                os.remove(tmpfile_path)
            # --- NUEVO: Esperar ambas URLs públicas (cliente y vendedor) ---
            # Buscar assetId de la firma del vendedor
            asset_id_seller = None
            query = '''
            query ($itemId: [ID!]) {
              items(ids: $itemId) {
                column_values {
                  id
                  value
                }
              }
            }
            '''
            variables = {"itemId": [str(inspection_id)]}
            headers = {
                "Authorization": MONDAY_API_TOKEN,
                "Content-Type": "application/json"
            }
            response = requests.post(MONDAY_API_URL, headers=headers, json={"query": query, "variables": variables})
            result = response.json()
            for col in result["data"]["items"][0]["column_values"]:
                if col["id"] == "file_mkqm8j5r" and col.get("value"):
                    import json as pyjson
                    file_info = pyjson.loads(col["value"])
                    if file_info and "files" in file_info and file_info["files"]:
                        file0 = file_info["files"][0]
                        if "assetId" in file0:
                            asset_id_seller = file0["assetId"]
                if col["id"] == "file_mkqmnwqm" and col.get("value"):
                    import json as pyjson
                    file_info = pyjson.loads(col["value"])
                    if file_info and "files" in file_info and file_info["files"]:
                        file0 = file_info["files"][0]
                        if "assetId" in file0:
                            asset_id_cliente = file0["assetId"]
            # Esperar ambas URLs públicas
            seller_signature_url = esperar_url_publica(asset_id_seller, max_intentos=20, delay=3) if asset_id_seller else None
            customer_signature_url = esperar_url_publica(asset_id_cliente, max_intentos=20, delay=3) if asset_id_cliente else None
            # --- FIN NUEVO ---
            # --- NUEVA CONDICIÓN: Solo generar PDF si ambas firmas existen ---
            if not seller_signature_url or not customer_signature_url:
                flash('No se puede generar el PDF: ambas firmas deben estar presentes. Por favor, asegúrate de que tanto el vendedor como el cliente hayan firmado.', 'danger')
                return redirect(request.url)
            # --------------------------------------------------------------
            # Después de guardar la firma del cliente, generar el PDF y subirlo a Monday.com
            # Recopilar datos para el PDF
            pdf_data = {
                "agreement_date": customer_signed_at_val or "",
                "seller_signed_at": seller_signed_at,
                "customer_signed_at": customer_signed_at_val,
                "owner_name": prefill_data.get("owner_name", ""),
                "company_name": prefill_data.get("company_name", ""),
                "property_address": prefill_data.get("property_address", ""),
                "insurance_carrier": "",  # Agrega si tienes este dato
                "email": prefill_data.get("owner_email", ""),
                "cell_phone": prefill_data.get("owner_phone", ""),
                "work_phone": prefill_data.get("rep_phone", ""),
                "claim_number": "",  # Agrega si tienes este dato
                "representative_name": prefill_data.get("rep_name", ""),
                "representative_phone": prefill_data.get("rep_phone", ""),
                "representative_email": prefill_data.get("rep_email", "")
            }
            # Generar el PDF
            pdf_path = os.path.join(tempfile.gettempdir(), "contract_filled.pdf")
            generar_contrato_pdf_con_firmas(
                pdf_data,
                seller_signature_url,
                customer_signature_url,
                pdf_path
            )
            # Subir el PDF a Monday.com
            file_mutation = '''
            mutation ($file: File!, $itemId: ID!, $columnId: String!) {
              add_file_to_column (file: $file, item_id: $itemId, column_id: $columnId) {
                id
              }
            }
            '''
            with open(pdf_path, 'rb') as f:
                file_bytes = f.read()
            m = MultipartEncoder(
                fields={
                    'query': file_mutation,
                    'variables': f'{{"file": null, "itemId": "{inspection_id}", "columnId": "files_mkn9pg5s"}}',
                    'map': '{"0": ["variables.file"]}',
                    '0': ('contract_filled.pdf', file_bytes, 'application/pdf')
                }
            )
            file_headers = {
                "Authorization": MONDAY_API_TOKEN,
                "Content-Type": m.content_type
            }
            requests.post(MONDAY_API_FILE_URL, headers=file_headers, data=m)
            flash('Customer contract signed successfully!', 'success')
            return redirect(url_for('commercial_form'))
        else:
            # Flujo del vendedor: guarda la firma y fecha del vendedor, y genera el link para el cliente
            # Actualizar campos editables en Monday.com
            update_mutation = '''
            mutation ($boardId: ID!, $itemId: ID!, $columnVals: JSON!) {
              change_multiple_column_values(board_id: $boardId, item_id: $itemId, column_values: $columnVals) {
                id
              }
            }
            '''
            editable_fields = {
                # Solo campos del owner y representante
                "text_mkn9rsf7": request.form.get("owner_name"),
                "text_mkn9613s": request.form.get("owner_email"),
                "text_mkn926rr": request.form.get("owner_phone"),
                "text_mkqmk6e6": request.form.get("rep_name"),
                "text_mkqm3b3r": request.form.get("rep_phone"),
                "email_mkqms6fy": {
                    "email": request.form.get("rep_email"),
                    "text": request.form.get("rep_name") or request.form.get("rep_email") or ""
                },
            }
            update_variables = {
                "boardId": BOARD_ID,
                "itemId": str(inspection_id),
                "columnVals": json.dumps(editable_fields)
            }
            response_update = requests.post(MONDAY_API_URL, headers=headers, json={"query": update_mutation, "variables": update_variables})
            print("DEBUG: Monday.com update response =", response_update.text)
            # Guarda la firma y fecha del vendedor SOLO si existe
            if seller_signed_at_val:
                print(f"DEBUG: Guardando fecha de firma del vendedor en Monday.com: {seller_signed_at_val}")
                variables_date = {
                    "itemId": str(inspection_id),
                    "columnId": "text_mkqmfm3y",
                    "value": f'"{seller_signed_at_val}"'
                }
                requests.post(MONDAY_API_URL, headers=headers, json={"query": mutation, "variables": variables_date})
            if seller_signature:
                import base64
                import tempfile
                header, encoded = seller_signature.split(',', 1)
                data = base64.b64decode(encoded)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
                    tmpfile.write(data)
                    tmpfile_path = tmpfile.name
                file_mutation = '''
                mutation ($file: File!, $itemId: ID!, $columnId: String!) {
                  add_file_to_column (file: $file, item_id: $itemId, column_id: $columnId) {
                    id
                  }
                }
                '''
                with open(tmpfile_path, 'rb') as f:
                    file_bytes = f.read()
                m = MultipartEncoder(
                    fields={
                        'query': file_mutation,
                        'variables': f'{{"file": null, "itemId": "{inspection_id}", "columnId": "file_mkqm8j5r"}}',
                        'map': '{"0": ["variables.file"]}',
                        '0': ('seller_signature.png', file_bytes, 'image/png')
                    }
                )
                file_headers = {
                    "Authorization": MONDAY_API_TOKEN,
                    "Content-Type": m.content_type
                }
                requests.post(MONDAY_API_FILE_URL, headers=file_headers, data=m)
                os.remove(tmpfile_path)
            # Genera el link único para el cliente y lo guarda en Monday.com
            base_url = request.url_root.rstrip('/')
            client_link = f"{base_url}/contract_form?inspection_id={inspection_id}&client=1"
            print("DEBUG: Generating client link:", client_link)
            print("DEBUG: Saving client link to Monday.com in column text_mkqm8s8x")
            mutation_link = '''
            mutation ($boardId: ID!, $itemId: ID!, $columnId: String!, $value: JSON!) {
              change_column_value(board_id: $boardId, item_id: $itemId, column_id: $columnId, value: $value) {
                id
              }
            }
            '''
            variables_link = {
                "boardId": BOARD_ID,
                "itemId": str(inspection_id),
                "columnId": "text_mkqm8s8x",
                "value": f'"{client_link}"'
            }
            response_link = requests.post(MONDAY_API_URL, headers=headers, json={"query": mutation_link, "variables": variables_link})
            print("DEBUG: Monday.com link save response =", response_link.text)
            flash('Contract form submitted successfully! Link for client signature generated.', 'success')
            return redirect(url_for('commercial_form'))

    return render_template(
        "contract_form.html",
        prefill=prefill_data,
        seller_signed_at=seller_signed_at,
        customer_signed_at=customer_signed_at,
        link_customer_sign=link_customer_sign,
        is_client=is_client,
        seller_signature_url=seller_signature_url,
        customer_signature_url=customer_signature_url
    )

def generar_contrato_pdf_con_firmas(data, seller_signature_url, customer_signature_url, output_path="contract_filled.pdf"):
    doc = fitz.open("contract_template.pdf")
    page = doc[0]  # Siempre la primera página
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
    page.insert_text((100, 665), data.get("owner_name", ""), fontsize=10)
    # Fecha de firma del cliente a la derecha de la firma, más pequeña
    if data.get("customer_signed_at"):
        page.insert_text((180, 730), f"Signed: {data['customer_signed_at']}", fontsize=6, color=(0,0,1))
    # Firma del REPRESENTANTE
    page.insert_text((400, 665), data.get("representative_name", ""), fontsize=10)
    # Fecha de firma del seller a la derecha de la firma, más pequeña
    if data.get("seller_signed_at"):
        page.insert_text((460, 730), f"Signed: {data['seller_signed_at']}", fontsize=6, color=(0,0,1))
    page.insert_text((410, 685), data.get("agreement_date", ""), fontsize=10)
    # Insertar imágenes de firmas si existen
    print("DEBUG: Customer signature URL:", customer_signature_url)
    if customer_signature_url:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpimg:
            urllib.request.urlretrieve(customer_signature_url, tmpimg.name)
            print("DEBUG: Customer signature image saved at:", tmpimg.name)
            # Firma del cliente, 20 puntos a la derecha
            page.insert_image(fitz.Rect(120, 710, 175, 750), filename=tmpimg.name)
    print("DEBUG: Seller signature URL:", seller_signature_url)
    if seller_signature_url:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpimg:
            urllib.request.urlretrieve(seller_signature_url, tmpimg.name)
            print("DEBUG: Seller signature image saved at:", tmpimg.name)
            # Firma del representante, 15 puntos más angosta
            page.insert_image(fitz.Rect(395, 710, 455, 750), filename=tmpimg.name)
    doc.save(output_path)
    doc.close()

def obtener_public_url_por_asset_id(asset_id):
    query = '''
    query ($assetId: [ID!]!) {
      assets(ids: $assetId) {
        public_url
        url
        name
      }
    }
    '''
    variables = {"assetId": [str(asset_id)]}
    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json"
    }
    response = requests.post(MONDAY_API_URL, headers=headers, json={"query": query, "variables": variables})
    result = response.json()
    print("DEBUG: Asset query result =", result)
    if "data" in result and result["data"].get("assets"):
        asset = result["data"]["assets"][0]
        return asset.get("public_url") or asset.get("url")
    return None

def esperar_url_publica(asset_id, max_intentos=5, delay=2):
    for intento in range(max_intentos):
        url = obtener_public_url_por_asset_id(asset_id)
        if url:
            return url
        print(f"Intento {intento+1}: URL pública aún no disponible, esperando {delay} segundos...")
        time.sleep(delay)
    return None

if __name__ == '__main__':
    app.run(debug=True)
