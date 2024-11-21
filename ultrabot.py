import json
import requests
import pandas as pd
import os
import logging
import time  # Importar time para trabalhar com timestamps

STATE_FILE = 'conversation_states.json'

class ultraChatBot():
    def __init__(self, message_data):
        self.message = message_data
        self.chatID = message_data.get('from')
        self.ultraAPIUrl = 'https://api.ultramsg.com/instance99723/'
        self.token = '2str21gem9r5za4u'
        self.states = self.load_states()
       
    def load_states(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logging.error("Erro ao decodificar o arquivo de estados. Criando novo dicionário de estados.")
                    return {}
        else:
            return {}
    
    def save_states(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.states, f)
   
    def send_requests(self, type, data):
        url = f"{self.ultraAPIUrl}{type}?token={self.token}"
        headers = {'Content-type': 'application/json'}
        answer = requests.post(url, data=json.dumps(data), headers=headers)
        return answer.json()

    def send_message(self, chatID, text):
        data = {
            "to": chatID,
            "body": text
        }
        answer = self.send_requests('messages/chat', data)
        return answer

    def greet_and_ask_model(self):
        greeting = "Olá! Bem-vindo à nossa loja de celulares."
        question = "Qual modelo de celular você está procurando?"
        self.send_message(self.chatID, greeting)
        self.send_message(self.chatID, question)
        # Atualiza o estado para 'ASKED_MODEL' e o timestamp
        self.states[self.chatID] = {'state': 'ASKED_MODEL', 'last_interaction': time.time()}
        self.save_states()

    def search_and_send_model_info(self, model_name):
        try:
            df = pd.read_excel('ESTOQUE_.xlsx', header=None, usecols=[1, 2, 3, 5, 6])
            df.columns = ['Modelo', 'Cor', 'Bateria', 'Condição', 'Valor']
            df = df.iloc[::-1].reset_index(drop=True)
            resultados = df[df['Modelo'].str.contains(model_name, case=False, na=False)]
            if not resultados.empty:
                mensagem = "Encontramos os seguintes modelos:\n"
                for index, row in resultados.iterrows():
                    modelo = row['Modelo']
                    cor = row['Cor']
                    condicao = row['Condição']
                    valor = row['Valor']
                    mensagem += f"- Modelo: {modelo}, Cor: {cor}, Condição: {condicao}, Valor: R${valor}\n"
                self.send_message(self.chatID, mensagem)
                # Atualiza o estado para 'FINISHED' e o timestamp
                self.states[self.chatID]['state'] = 'FINISHED'
                self.states[self.chatID]['last_interaction'] = time.time()
                self.save_states()
            else:
                self.send_message(self.chatID, "Desculpe, não encontramos esse modelo em nosso estoque.")
                # Mantém o estado em 'ASKED_MODEL' e atualiza o timestamp
                self.states[self.chatID]['state'] = 'ASKED_MODEL'
                self.states[self.chatID]['last_interaction'] = time.time()
                self.save_states()
        except Exception as e:
            logging.error(f"Erro ao ler a planilha: {e}")
            self.send_message(self.chatID, "Desculpe, ocorreu um erro ao buscar o modelo.")
            # Mantém o estado em 'ASKED_MODEL' e atualiza o timestamp
            self.states[self.chatID]['state'] = 'ASKED_MODEL'
            self.states[self.chatID]['last_interaction'] = time.time()
            self.save_states()

    def Processingـincomingـmessages(self):
        message = self.message
        if message:
            if 'body' in message and 'from' in message:
                text = message['body'].strip()
                if not message['fromMe']:
                    # Verifica se o chatID está nos estados, se não estiver, inicializa
                    if self.chatID not in self.states:
                        self.states[self.chatID] = {'state': 'INITIAL', 'last_interaction': time.time()}
                    else:
                        # Se o estado for uma string antiga, atualiza para o novo formato
                        if isinstance(self.states[self.chatID], str):
                            logging.info(f"Atualizando estado antigo para novo formato para {self.chatID}")
                            self.states[self.chatID] = {'state': self.states[self.chatID], 'last_interaction': time.time()}
                        
                        # Verifica se passaram mais de 20 minutos desde a última interação
                        last_interaction = self.states[self.chatID].get('last_interaction', time.time())
                        elapsed_time = time.time() - last_interaction
                        if elapsed_time > 2 * 60:
                            # Mais de 20 minutos sem interação, resetar estado para 'INITIAL'
                            self.states[self.chatID]['state'] = 'INITIAL'
                    
                    # Atualiza o timestamp da última interação
                    self.states[self.chatID]['last_interaction'] = time.time()
                    self.save_states()
                    
                    # Continua o processamento com base no estado atual
                    state = self.states[self.chatID]['state']
                    if state == 'INITIAL':
                        self.greet_and_ask_model()
                        return 'Greeted and asked for model'
                    elif state == 'ASKED_MODEL':
                        model_name = text
                        self.search_and_send_model_info(model_name)
                        return 'Searched and sent model info'
                    elif state == 'FINISHED':
                        self.send_message(self.chatID, "Posso ajudar em algo mais?")
                        # Resetar o estado para 'ASKED_MODEL' para continuar a conversa
                        self.states[self.chatID]['state'] = 'ASKED_MODEL'
                        self.states[self.chatID]['last_interaction'] = time.time()
                        self.save_states()
                        return 'Asked if need more help'
                    else:
                        # Estado desconhecido, resetar para 'INITIAL'
                        self.states[self.chatID]['state'] = 'INITIAL'
                        self.states[self.chatID]['last_interaction'] = time.time()
                        self.save_states()
                        self.greet_and_ask_model()
                        return 'Reset state and greeted'
                else:
                    return 'No action for messages sent by bot'
            else:
                logging.error("Faltando 'body' ou 'from' nos dados da mensagem.")
                return 'Erro: Dados da mensagem incompletos'
        else:
            return 'Nenhuma mensagem para processar'
