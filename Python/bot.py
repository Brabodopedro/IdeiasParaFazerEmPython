from flask import Flask, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)

# Carrega os dados da planilha Excel
df = pd.read_excel('iPhone_Models.xlsx')

def send_message(to, message):
    url = 'https://api.ultramensager.com.br/send-message'  # Replace with actual Ultramensager API endpoint
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_TOKEN'  # Replace with your API token
    }
    payload = {
        'number': to,
        'message': message
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

@app.route('/bot', methods=['POST'])
def bot():
    incoming_data = request.get_json()
    incoming_msg = incoming_data.get('message', {}).get('body', '').lower()
    sender = incoming_data.get('sender', {}).get('number', '')

    if 'iphone' in incoming_msg:
        modelos_novos = df[(df['Modelo'].str.contains('iPhone', case=False)) & (df['Condição'] == 'Novo')]
        if not modelos_novos.empty:
            resposta = 'Temos os seguintes iPhones novos disponíveis:\n'
            for index, row in modelos_novos.iterrows():
                resposta += f"{row['Modelo']} - R${row['Preço']}\n"
            resposta += 'Você gostaria de algum desses, ou prefere ver os iPhones usados?'
            send_message(sender, resposta)
        else:
            send_message(sender, 'Desculpe, não temos iPhones novos disponíveis no momento. Gostaria de ver os modelos usados?')
    elif 'usado' in incoming_msg or 'usados' in incoming_msg:
        modelos_usados = df[(df['Modelo'].str.contains('iPhone', case=False)) & (df['Condição'] == 'Usado')]
        if not modelos_usados.empty:
            resposta = 'Aqui estão os iPhones usados disponíveis:\n'
            for index, row in modelos_usados.iterrows():
                resposta += f"{row['Modelo']} - R${row['Preço']}\n"
            send_message(sender, resposta)
        else:
            send_message(sender, 'Desculpe, não temos iPhones usados disponíveis no momento.')
    else:
        send_message(sender, 'Olá! Qual modelo de celular você está procurando?')

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(debug=True)
