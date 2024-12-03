import json
import pandas as pd
import os
import logging
import time
from twilio.rest import Client

STATE_FILE = 'conversation_states.json'

class ChatBot():
    def __init__(self, message_data):
        self.message = message_data
        self.chatID = message_data.get('from')
        # Inicializar o cliente do Twilio
        self.account_sid = 'AC74142d3f16a917d226a79a942e3e6a80'  # Substitua pelo seu Account SID do Twilio
        self.auth_token = '3ed4ab921893ab5f4dffd083b45c789f'    # Substitua pelo seu Auth Token do Twilio
        self.twilio_client = Client(self.account_sid, self.auth_token)
        self.whatsapp_number = 'whatsapp:+556781687046'  # Substitua pelo seu número do WhatsApp no Twilio
        self.states = self.load_states()
           
    def save_states(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.states, f)
        logging.info(f"Estados salvos: {self.states}")

    def load_states(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                try:
                    states = json.load(f)
                    logging.info(f"Estados carregados: {states}")
                    return states
                except json.JSONDecodeError:
                    logging.error("Erro ao decodificar o arquivo de estados. Criando novo dicionário de estados.")
                    return {}
        else:
            return {}

       
    def send_message(self, chatID, text):
        message = self.twilio_client.messages.create(
            body=text,
            from_=self.whatsapp_number,
            to=chatID
        )
        return message.sid  

    def send_greeting(self):
        greeting = "Olá! Bem-vindo à nossa loja de celulares."
        self.send_message(self.chatID, greeting)
    
    def send_options(self):
        """Envia opções como texto para interação simulada"""
        options = (
            "Como podemos te ajudar? Por favor, escolha uma das opções abaixo:\n"
            "1️⃣ - 📱 Comprar um aparelho\n"
            "2️⃣ - 🔧 Assistência Técnica\n"
            "3️⃣ - 👨‍💼 Falar com um atendente\n"
            "4️⃣ - ❌ Sair"
        )
        self.send_message(self.chatID, options)

    def send_confirm_purchase_options(self):
        options = (
            "Você gostaria de prosseguir com a compra?\n"
            "Responda com:\n"
            "✅ S - Sim\n"
            "❌ N - Escolher outro modelo\n"
            "🔄 M - Menu Principal\n"
            "🚪 E - Sair"
        )
        self.send_message(self.chatID, options)

    def greet_and_ask_options(self):
        self.send_greeting()
        self.send_options()
        # Atualiza o estado para 'ASKED_OPTION' e o timestamp
        self.states[self.chatID] = {'state': 'ASKED_OPTION', 'last_interaction': time.time()}
        self.save_states()

    def handle_buy_device(self):
        question = (
            "Qual modelo de celular você está procurando? "
            "Por favor, digite o nome do modelo ou parte dele (exemplo: iPhone 12)."
        )
        self.send_message(self.chatID, question)
        self.states[self.chatID]['state'] = 'ASKED_MODEL_NAME'
        # Atualiza o timestamp de última interação
        self.states[self.chatID]['last_interaction'] = time.time()
        self.save_states()

    def handle_model_search(self, model_name):
        try:
            # Pesquisa os modelos correspondentes ao input do cliente
            df = pd.read_excel('ESTOQUE_.xlsx', header=None, usecols=[1, 2, 3, 5, 6])
            df.columns = ['Modelo', 'Cor', 'Bateria', 'Condição', 'Valor']
            df = df.iloc[::-1].reset_index(drop=True)
            resultados = df[df['Modelo'].str.contains(model_name, case=False, na=False)]
            if not resultados.empty:
                # Lista os modelos encontrados, enumerados
                mensagem = "Temos os seguintes modelos disponíveis: \n"
                modelos = []
                for idx, (_, row) in enumerate(resultados.iterrows(), start=1):
                    modelo = row['Modelo']
                    cor = row['Cor']
                    condicao = row['Condição']
                    valor = row['Valor']
                    mensagem += f"{idx} - Modelo: {modelo}, Cor: {cor}, Condição: {condicao}, Valor: R${valor} \n "
                    modelos.append(row.to_dict())
                self.send_message(self.chatID, mensagem)
                # Pergunta ao cliente para escolher um modelo, inclui N, M, S
                self.send_message(self.chatID, "Por favor, digite o número do modelo que você deseja: \n ou\n N - Escolher outro modelo\nM - Menu Principal\nS - Sair")
                # Atualiza o estado para 'ASKED_MODEL_NUMBER' e salva os modelos listados
                self.states[self.chatID]['state'] = 'ASKED_MODEL_NUMBER'
                self.states[self.chatID]['modelos'] = modelos
                self.states[self.chatID]['last_interaction'] = time.time()
                self.save_states()
            else:
                self.send_message(self.chatID, "Desculpe, não encontramos esse modelo em nosso estoque.")
                # Permanece no estado 'ASKED_MODEL_NAME' para o cliente tentar novamente
        except Exception as e:
            logging.error(f"Erro ao ler a planilha: {e}")
            self.send_message(self.chatID, "Desculpe, ocorreu um erro ao buscar o modelo.")
            # Permanece no estado 'ASKED_MODEL_NAME'

    def handle_model_number_choice(self, choice):
        choice = choice.strip().upper()
        if choice == 'N':
            # Volta a perguntar qual modelo o cliente procura
            self.handle_buy_device()
        elif choice == 'M':
            # Retorna ao menu principal
            self.send_options()
            self.states[self.chatID]['state'] = 'ASKED_OPTION'
            self.states[self.chatID]['last_interaction'] = time.time()
            self.save_states()
        elif choice == 'S':
            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
            self.states[self.chatID]['state'] = 'FINISHED'
            # Define o início da pausa
            self.states[self.chatID]['pause_start_time'] = time.time()
            self.save_states()
        else:
            try:
                choice_num = int(choice)
                modelos = self.states[self.chatID]['modelos']
                if 1 <= choice_num <= len(modelos):
                    modelo_escolhido = modelos[choice_num - 1]
                    # Fornece detalhes do modelo escolhido
                    mensagem = f"Você escolheu o modelo:\nModelo: {modelo_escolhido['Modelo']}, Cor: {modelo_escolhido['Cor']}, Condição: {modelo_escolhido['Condição']}, Valor: R${modelo_escolhido['Valor']}"
                    self.send_message(self.chatID, mensagem)
                    # Pergunta se o cliente deseja prosseguir com a compra, inclui N, M, S
                    self.send_message(self.chatID, "Você gostaria de prosseguir com a compra?\nDigite 'Sim' para confirmar, ou escolha uma opção:\nN - Escolher outro modelo\nM - Menu Principal\nS - Sair")
                    # Atualiza o estado para 'CONFIRM_PURCHASE'
                    self.states[self.chatID]['state'] = 'CONFIRM_PURCHASE'
                    self.states[self.chatID]['last_interaction'] = time.time()
                    self.save_states()
                else:
                    self.send_message(self.chatID, "Opção inválida. Por favor, digite o número correspondente ao modelo desejado, ou escolha uma das opções enviadas.")
            except ValueError:
                self.send_message(self.chatID, "Entrada inválida. Por favor, digite o número correspondente ao modelo desejado, ou escolha uma das opções enviadas.")

    def handle_confirm_purchase(self, choice):
        choice = choice.strip().upper()
        if choice == 'SIM':
            # Processa a compra
            self.send_message(self.chatID, "Obrigado por sua compra! Entraremos em contato para finalizar os detalhes.")
            self.states[self.chatID]['state'] = 'FINISHED'
            # Define o início da pausa
            self.states[self.chatID]['pause_start_time'] = time.time()
            self.save_states()
        elif choice == 'N':
            # Volta a perguntar qual modelo o cliente procura
            self.handle_buy_device()
        elif choice == 'M':
            # Retorna ao menu principal
            self.send_options()
            self.states[self.chatID]['state'] = 'ASKED_OPTION'
            self.states[self.chatID]['last_interaction'] = time.time()
            self.save_states()
        elif choice == 'S':
            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
            self.states[self.chatID]['state'] = 'FINISHED'
            # Define o início da pausa
            self.states[self.chatID]['pause_start_time'] = time.time()
            self.save_states()
        else:
            self.send_message(self.chatID, "Opção inválida. Por favor, digite 'Sim' para confirmar a compra, ou escolha uma das opções enviadas.\nN - Escolher outro modelo\nM - Menu Principal\nS - Sair")

    def handle_technical_assistance(self):
        message = "Para assistência técnica, por favor descreva o problema que está enfrentando."
        self.send_message(self.chatID, message)
        # Você pode definir um novo estado para assistência técnica, se necessário
        self.states[self.chatID]['state'] = 'TECH_ASSISTANCE'
        self.states[self.chatID]['last_interaction'] = time.time()
        self.save_states()

    def handle_talk_to_agent(self):
        message = "Um de nossos atendentes entrará em contato com você em breve."
        self.send_message(self.chatID, message)
        # Atualiza o estado para 'WAITING_FOR_AGENT' e define 'pause_start_time'
        self.states[self.chatID]['state'] = 'WAITING_FOR_AGENT'
        self.states[self.chatID]['pause_start_time'] = time.time()
        self.save_states()

    def Processing_incoming_messages(self):
        message = self.message
        if message:
            if 'body' in message and 'from' in message:
                text = message['body'].strip().upper()  # Captura o texto e padroniza para maiúsculas
                if not message.get('fromMe', False):  # Ignora mensagens enviadas pelo bot
                    if self.chatID not in self.states:
                        self.states[self.chatID] = {'state': 'INITIAL', 'last_interaction': time.time()}
                    else:
                        state = self.states[self.chatID]['state']
                        if state not in ['WAITING_FOR_AGENT', 'FINISHED']:
                            self.states[self.chatID]['last_interaction'] = time.time()
                        # Resetar estado após 10 minutos de inatividade
                        last_interaction = self.states[self.chatID].get('last_interaction', time.time())
                        if time.time() - last_interaction > 10 * 60:
                            self.states[self.chatID]['state'] = 'INITIAL'
                            self.states[self.chatID].pop('pause_start_time', None)  # Remove o timestamp de pausa se existir
                            self.save_states()

                    state = self.states[self.chatID]['state']

                    if state == 'INITIAL':
                        self.send_greeting()
                        self.send_options()
                        self.states[self.chatID]['state'] = 'ASKED_OPTION'
                        return 'Greeted and asked for options'

                    elif state == 'ASKED_OPTION':
                        # Processa a escolha do usuário
                        if text == '1':
                            self.handle_buy_device()
                            return 'Client chose to buy a device'
                        elif text == '2':
                            self.handle_technical_assistance()
                            return 'Client chose technical assistance'
                        elif text == '3':
                            self.handle_talk_to_agent()
                            return 'Client chose to talk to an agent'
                        elif text == '4' or text == 'S':  # Inclui 'S' para sair
                            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
                            self.states[self.chatID]['state'] = 'FINISHED'
                            self.states[self.chatID]['pause_start_time'] = time.time()
                            self.save_states()
                            return 'Client chose to exit'
                        else:
                            self.send_message(self.chatID, "Opção inválida. Por favor, responda com o número ou letra correspondente à sua escolha.")
                            return 'Invalid option selected'

                    elif state == 'ASKED_MODEL_NAME':
                        # Processa o nome do modelo que o cliente quer comprar
                        self.handle_model_search(text)
                        return 'Searched and listed models for user to choose'

                    elif state == 'ASKED_MODEL_NUMBER':
                        # Processa a escolha do número do modelo
                        self.handle_model_number_choice(text)
                        return 'Handled model number choice'

                    elif state == 'CONFIRM_PURCHASE':
                        # Processa a confirmação de compra
                        self.handle_confirm_purchase(text)
                        return 'Handled purchase confirmation'

                    elif state == 'TECH_ASSISTANCE':
                        issue_description = text
                        self.send_message(self.chatID, "Obrigado por nos informar. Nossa equipe de suporte entrará em contato em breve.")
                        self.states[self.chatID]['state'] = 'FINISHED'
                        self.states[self.chatID]['pause_start_time'] = time.time()
                        self.save_states()
                        return 'Handled technical assistance'

                    elif state == 'WAITING_FOR_AGENT' or state == 'FINISHED':
                        # Verifica se já se passou 1 hora desde o início da pausa
                        pause_duration = time.time() - self.states[self.chatID].get('pause_start_time', 0)
                        if pause_duration >= 3600:
                            self.send_message(self.chatID, "Desculpe pela espera. Posso ajudar em algo?")
                            self.send_options()
                            self.states[self.chatID]['state'] = 'ASKED_OPTION'
                            self.states[self.chatID].pop('pause_start_time', None)
                            self.save_states()
                            return 'Re-engaged after 1 hour pause'
                        else:
                            return 'Paused, waiting for agent'

                    else:
                        # Estado desconhecido, resetar para 'INITIAL'
                        self.states[self.chatID]['state'] = 'INITIAL'
                        self.states[self.chatID].pop('pause_start_time', None)
                        self.save_states()
                        self.greet_and_ask_options()
                        return 'Reset state and greeted with options'
                else:
                    return 'No action for messages sent by bot'
            else:
                logging.error("Faltando 'body' ou 'from' nos dados da mensagem.")
                return 'Erro: Dados da mensagem incompletos'
        else:
            return 'Nenhuma mensagem para processar'
