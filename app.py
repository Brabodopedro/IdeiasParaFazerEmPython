from flask import Flask, request, jsonify
import pandas as pd
import requests
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load the Excel data
try:
    df = pd.read_excel(r'C:\Users\pho_0\OneDrive\Área de Trabalho\IdeiasParaFazerEmPython\iPhone_Models.xlsx')
except Exception as e:
    logging.error("Error loading Excel file: %s", e)
    exit(1)

def send_message(to, message):
    url = 'https://api.ultramsg.com/instance99723'  # Update with the correct endpoint
    headers = {
        'Content-Type': 'application/json',
        'Authorization': '2str21gem9r5za4u'  # Replace with your actual API token
    }
    payload = {
        'phone': to,
        'message': message
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        logging.info("Response from Ultramensager: %s %s", response.status_code, response.text)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error("Error sending message: %s", e)
        return None

@app.route('/', methods=['POST'])
def bot():
    try:
        incoming_data = request.get_json()
        logging.info("Incoming data: %s", incoming_data)
        incoming_msg = incoming_data.get('message', {}).get('body', '').lower()
        sender = incoming_data.get('sender', {}).get('number', '')

        if not incoming_msg or not sender:
            logging.error("Missing 'message' or 'sender' in incoming data.")
            return jsonify({'status': 'error', 'message': 'Missing data'}), 400

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
    except Exception as e:
        logging.error("Error in bot function: %s", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
