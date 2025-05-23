from flask import Flask, request, jsonify
import logging
import json
from owenbot import OwenChatBot  # Certifique-se de que o arquivo `owenbot.py` está no mesmo diretório

app = Flask(__name__)

# Configuração do logging para exibir mensagens no console
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['POST'])
def webhook():
    try:
        # Obtendo os dados do webhook
        json_data = request.get_json()
        logging.info(f"Dados recebidos: {json_data}")

        if not json_data:
            logging.error("Nenhum dado JSON recebido.")
            return jsonify({'error': 'Nenhum dado recebido'}), 400

        # Verifique se 'data' está presente no JSON
        if 'data' not in json_data:
            logging.error("Faltando 'data' no JSON recebido.")
            return jsonify({'error': 'Faltando dados no JSON'}), 400

        message_data = json_data['data']

        # Verificar o tipo de message_data
        logging.info(f"Tipo de message_data: {type(message_data)}")
        logging.info(f"Conteúdo de message_data: {message_data}")

        # Se message_data for uma string, parsear como JSON
        if isinstance(message_data, str):
            logging.info("message_data é uma string, parseando como JSON")
            message_data = json.loads(message_data)

        # Verifique se 'body' e 'from' estão presentes em 'message_data'
        if 'body' not in message_data and 'from' not in message_data:
            logging.error("Faltando 'body' ou 'from' nos dados recebidos.")
            return jsonify({'error': 'Faltando body ou from nos dados'}), 400

        # Instancie o bot com os dados recebidos
        bot = OwenChatBot(message_data)
        response = bot.Processing_incoming_messages()

        # Retorna uma resposta ao webhook
        return jsonify({'status': 'sucesso', 'response': response}), 200

    except Exception as e:
        logging.error(f"Ocorreu um erro no webhook: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    # Inicia o servidor Flask
    app.run(debug=True)
