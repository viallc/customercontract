import requests
import json
MONDAY_API_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjUwNTAwNTIwNSwiYWFpIjoxMSwidWlkIjo3NTMxNTc3OSwiaWFkIjoiMjAyNS0wNC0yN1QwMTo0ODo0MS4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjcxNDA4MzgsInJnbiI6InVzZTEifQ.PJM61IpSMbsPU1JlrlkZTEJXY_bqqog8QgFgCzsGozk'
MONDAY_API_URL = 'https://api.monday.com/v2'
STAFF_BOARD_ID = "9060673210"  # Debe ser STRING porque el tipo es ID!
COLUMN_ID = "status_mkn8wdk2"  # Aquí pones el column ID

query = """
query ($boardId: ID!, $columnId: [String!]) {
  boards(ids: [$boardId]) {
    columns(ids: $columnId) {
      id
      title
      settings_str
    }
  }
}
"""

variables = {"boardId": STAFF_BOARD_ID, "columnId": [COLUMN_ID]}
headers = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json"
}

response = requests.post(MONDAY_API_URL, headers=headers, json={"query": query, "variables": variables})
data = response.json()

print(json.dumps(data, indent=2))  # Ver la respuesta

# Extraer los labels de la columna status
if 'data' in data and data['data']['boards']:
    columns = data['data']['boards'][0]['columns']
    if columns:
        settings = json.loads(columns[0]['settings_str'])
        labels = settings.get('labels', {})
        print("Labels encontrados:")
        for key, value in labels.items():
            print(f"- {value}")
    else:
        print("No se encontró la columna.")
else:
    print("❌ No se pudo obtener la información. Verifica el board y la estructura.")
