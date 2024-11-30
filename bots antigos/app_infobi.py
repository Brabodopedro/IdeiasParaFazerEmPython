from flask import Flask, request, jsonify
import logging
from infobipbot import InfobipChatBot  # Certifique-se de que o arquivo `infobipbot.py` atualizado está no mesmo diretório

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

        # Instancie o bot com os dados recebidos
        bot = InfobipChatBot(message_data)
        response = bot.Processing_incoming_messages()
        logging.info(f"Resposta do bot: {response}")

        # Retorna uma resposta ao webhook
        return jsonify({'status': 'sucesso'}), 200

    except Exception as e:
        logging.error(f"Ocorreu um erro no webhook: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    # Inicia o servidor Flask
    app.run(debug=True)
