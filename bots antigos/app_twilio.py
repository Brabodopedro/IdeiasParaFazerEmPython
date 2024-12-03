from flask import Flask, request
import logging
from chatbot import ChatBot

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        message_data = request.form
        logging.info(f"Dados recebidos: {message_data}")

        if not message_data:
            logging.error("Nenhum dado recebido.")
            return '', 200

        from_number = message_data.get('From')
        body = message_data.get('Body')

        if not from_number or not body:
            logging.error("Faltando 'From' ou 'Body' nos dados recebidos.")
            return '', 200

        message_data = {
            'from': from_number,
            'body': body,
        }

        bot = ChatBot(message_data)
        response = bot.Processing_incoming_messages()

        return '', 200

    except Exception as e:
        logging.error(f"Ocorreu um erro no webhook: {e}")
        return '', 200

if __name__ == '__main__':
    app.run(debug=True)
