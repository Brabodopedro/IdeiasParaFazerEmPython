from flask import Flask, request, jsonify
import logging
import json
from ultrabot import ultraChatBot  # Certifique-se de que 'ultrabot.py' está no mesmo diretório
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time

app = Flask(__name__)

# Configuração do logging para exibir mensagens no console
logging.basicConfig(level=logging.INFO)

# Importar as funções globais do ultrabot
from ultrabot import load_states, save_states, send_message

# Definir a função que verifica conversas inativas
def check_inactive_conversations():
    try:
        states = load_states()
        current_time = time.time()
        for chatID, state_info in list(states.items()):
            last_interaction = state_info.get('last_interaction', current_time)
            if current_time - last_interaction > 10 * 60 and state_info['state'] != 'SESSION_ENDED':
                # Envia mensagem ao usuário
                send_message(chatID, "Sua sessão foi encerrada por inatividade. Se precisar de algo, por favor, envie uma nova mensagem para iniciar um novo atendimento.")
                # Atualiza o estado para 'SESSION_ENDED'
                states[chatID]['state'] = 'SESSION_ENDED'
                states[chatID]['pause_start_time'] = time.time()
        save_states(states)
    except Exception as e:
        logging.error(f"Erro ao verificar conversas inativas: {e}")

# Inicializar o scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_inactive_conversations, trigger="interval", seconds=60)
scheduler.start()

# Encerra o scheduler ao sair da aplicação
atexit.register(lambda: scheduler.shutdown())

@app.route('/', methods=['POST'])
def webhook():
    try:
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
        if 'body' not in message_data or 'from' not in message_data:
            logging.error("Faltando 'body' ou 'from' nos dados recebidos.")
            return jsonify({'error': 'Faltando body ou from nos dados'}), 400

        # Instancie o bot com 'message_data'
        bot = ultraChatBot(message_data)
        response = bot.Processing_incoming_messages()
        return jsonify({'status': 'sucesso', 'response': response}), 200

    except Exception as e:
        logging.error(f"Ocorreu um erro no webhook: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(debug=True)
