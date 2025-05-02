from flask import Flask, render_template, request, redirect
import requests
import json

app = Flask(__name__)

MONDAY_API_TOKEN = 'TU_API_TOKEN'  # Reemplaza esto por tu token real
MONDAY_API_URL = 'https://api.monday.com/v2'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']

        query = """
        mutation ($itemName: String!, $columnVals: JSON!) {
          create_item (
            board_id: TU_BOARD_ID,
            item_name: $itemName,
            column_values: $columnVals
          ) {
            id
          }
        }
        """

        variables = {
            'itemName': nombre,
            'columnVals': json.dumps({
                'email': {'email': email, 'text': email}
            })
        }

        headers = {
            "Authorization": MONDAY_API_TOKEN,
            "Content-Type": "application/json"
        }

        data = {'query': query, 'variables': variables}
        response = requests.post(MONDAY_API_URL, headers=headers, json=data)
        print(response.text)

        return redirect('/')
    return render_template('index.html')
