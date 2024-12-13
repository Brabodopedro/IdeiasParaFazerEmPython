from flask import Flask, request, jsonify
import logging
import json
from ultrabot import load_states, save_states, send_message_api  # Apenas send_message_api aqui
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time
import pandas as pd
from ultrabot import ultraChatBot  # Certifique-se de importar a classe do ultrabot

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

def check_inactive_conversations():
    try:
        states = load_states()
        current_time = time.time()
        for chatID, state_info in list(states.items()):
            last_interaction = state_info.get('last_interaction', current_time)
            if current_time - last_interaction > 10 * 60 and state_info['state'] != 'SESSION_ENDED':
                # Use send_message_api no lugar de send_message
                send_message_api(chatID, "Sua sessão foi encerrada por inatividade. Se precisar de algo, por favor, envie uma nova mensagem para iniciar um novo atendimento.")
                states[chatID]['state'] = 'SESSION_ENDED'
                states[chatID]['pause_start_time'] = time.time()
        save_states(states)
    except Exception as e:
        logging.error(f"Erro ao verificar conversas inativas: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_inactive_conversations, trigger="interval", seconds=60)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())

@app.route('/', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        logging.info(f"Dados recebidos: {json_data}")

        if not json_data:
            logging.error("Nenhum dado JSON recebido.")
            return jsonify({'error': 'Nenhum dado recebido'}), 400

        if 'results' not in json_data or not json_data['results']:
            logging.error("Faltando 'results' no JSON recebido.")
            return jsonify({'error': 'Faltando results no JSON'}), 400

        result = json_data['results'][0]

        if 'content' not in result or not result['content']:
            logging.error("Nenhuma mensagem no campo 'content'.")
            return jsonify({'error': 'Faltando conteúdo da mensagem'}), 400
        
        user_message = result['content'][0].get('text')
        sender = result.get('sender')

        if not user_message or not sender:
            logging.error("Faltando 'sender' ou 'text' nos dados recebidos.")
            return jsonify({'error': 'Faltando sender ou text nos dados'}), 400

        message_data = {
            'body': user_message,
            'from': sender
        }

        bot = ultraChatBot(message_data)
        response = bot.Processing_incoming_messages()
        return jsonify({'status': 'sucesso', 'response': response}), 200

    except Exception as e:
        logging.error(f"Ocorreu um erro no webhook: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(debug=True)
