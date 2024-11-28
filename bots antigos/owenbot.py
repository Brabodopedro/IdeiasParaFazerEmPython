import json
import requests
import pandas as pd
import os
import logging
import time

STATE_FILE = 'conversation_states.json'

class OwenChatBot():
    def __init__(self, message_data):
        self.message = message_data
        self.chatID = message_data.get('from')
        self.apiUrl = 'https://api.apizap.me/v1/message/text'  # Atualize com o endpoint correto
        self.token = 'B45CC04E-DF1CB2DE-0BE1931E-3A93E3FE-31B455DB'  # Substitua pelo seu token da Owen Brazil
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
   
    def send_requests(self, data, endpoint='message/text'):
        url = f'https://api.apizap.me/v1/{endpoint}'
        headers = {
            'Content-type': 'application/json'
        }
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar a mensagem: {e}")
            return None

    def send_message(self, chatID, text):
        data = {
            "tokenKey": self.token,
            "envioGrupo": False,  # Estamos enviando para um número individual
            "numero": chatID,  # Número do destinatário
            "texto": text  # Mensagem a ser enviada
        }
        return self.send_requests(data)

    def send_message_with_buttons(self, chatID, text, buttons):
        data = {
            "tokenKey": self.token,
            "numero": chatID,
            "texto": text,
            "botoes": buttons  # ou o campo correto de acordo com a API
        }
        return self.send_requests(data)

    def send_greeting(self):
        greeting = "Olá! Bem-vindo à nossa loja de celulares."
        self.send_message(self.chatID, greeting)

    def send_options(self):
        text = "Como podemos te ajudar? Por favor, escolha uma das opções abaixo:"
        buttons = [
            {
                "buttonText": {"displayText": "📱 Comprar um aparelho"},
                "buttonId": "option_buy_device"
            },
            {
                "buttonText": {"displayText": "🔧 Assistência Técnica"},
                "buttonId": "option_technical_assistance"
            },
            {
                "buttonText": {"displayText": "👨‍💼 Falar com um atendente"},
                "buttonId": "option_talk_to_agent"
            },
            {
                "buttonText": {"displayText": "❌ Sair"},
                "buttonId": "option_exit"
            }
        ]
        self.send_message_with_buttons(self.chatID, text, buttons)

    def send_confirm_purchase_options(self):
        text = "Você gostaria de prosseguir com a compra?"
        buttons = [
            {
                "type": "reply",
                "reply": {
                    "id": "confirm_yes",
                    "title": "✅ Sim"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "confirm_choose_another",
                    "title": "❌ Escolher outro modelo"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "confirm_main_menu",
                    "title": "🔄 Menu Principal"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "confirm_exit",
                    "title": "🚪 Sair"
                }
            }
        ]
        self.send_message_with_buttons(self.chatID, text, buttons)

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
                buttons = []
                for idx, (_, row) in enumerate(resultados.iterrows(), start=1):
                    modelo = row['Modelo']
                    cor = row['Cor']
                    condicao = row['Condição']
                    valor = row['Valor']
                    mensagem += f"{idx} - Modelo: {modelo}, Cor: {cor}, Condição: {condicao}, Valor: R${valor} \n"
                    modelos.append(row.to_dict())
                    # Adiciona botão para cada modelo
                    buttons.append({
                        "type": "reply",
                        "reply": {
                            "id": f"model_{idx}",
                            "title": f"{idx}"
                        }
                    })
                self.send_message(self.chatID, mensagem)
                # Envia botões para o cliente escolher o modelo
                self.send_message_with_buttons(self.chatID, "Por favor, selecione o número do modelo que você deseja:", buttons)
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
            self.states[self.chatID]['last_interaction'] = time.time()
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
                    # Pergunta se o cliente deseja prosseguir com a compra
                    self.send_confirm_purchase_options()
                    # Atualiza o estado para 'CONFIRM_PURCHASE'
                    self.states[self.chatID]['state'] = 'CONFIRM_PURCHASE'
                    self.states[self.chatID]['last_interaction'] = time.time()
                    self.save_states()
                else:
                    self.send_message(self.chatID, "Opção inválida. Por favor, selecione o número correspondente ao modelo desejado.")
            except ValueError:
                self.send_message(self.chatID, "Entrada inválida. Por favor, selecione o número correspondente ao modelo desejado.")

    def handle_confirm_purchase(self, choice):
        choice = choice.strip().upper()
        if choice == 'confirm_yes':
            # Processa a compra
            self.send_message(self.chatID, "Obrigado por sua compra! Entraremos em contato para finalizar os detalhes.")
            self.states[self.chatID]['state'] = 'FINISHED'
            self.states[self.chatID]['last_interaction'] = time.time()
            self.save_states()
        elif choice == 'confirm_choose_another':
            # Volta a perguntar qual modelo o cliente procura
            self.handle_buy_device()
        elif choice == 'confirm_main_menu':
            # Retorna ao menu principal
            self.send_options()
            self.states[self.chatID]['state'] = 'ASKED_OPTION'
            self.states[self.chatID]['last_interaction'] = time.time()
            self.save_states()
        elif choice == 'confirm_exit':
            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
            self.states[self.chatID]['state'] = 'FINISHED'
            self.states[self.chatID]['last_interaction'] = time.time()
            self.save_states()
        else:
            self.send_message(self.chatID, "Opção inválida. Por favor, selecione uma das opções enviadas.")

    def handle_technical_assistance(self):
        message = "Para assistência técnica, por favor descreva o problema que está enfrentando."
        self.send_message(self.chatID, message)
        # Defina um novo estado para assistência técnica, se necessário
        self.states[self.chatID]['state'] = 'TECH_ASSISTANCE'
        self.states[self.chatID]['last_interaction'] = time.time()
        self.save_states()

    def handle_talk_to_agent(self):
        message = "Um de nossos atendentes entrará em contato com você em breve."
        self.send_message(self.chatID, message)
        # Atualiza o estado para 'WAITING_FOR_AGENT' e o timestamp
        self.states[self.chatID]['state'] = 'WAITING_FOR_AGENT'
        self.states[self.chatID]['last_interaction'] = time.time()
        self.save_states()

    def Processing_incoming_messages(self):
        message = self.message
        if message:
            # Lida com mensagens do tipo STATUS_MESSAGE
            if message.get('type') == 'STATUS_MESSAGE':
                logging.info(f"Mensagem de status recebida: {message}. Ignorando.")
                return 'Status message received and ignored.'

            if 'type' in message and 'from' in message:
                message_type = message['type']
                from_user = message['from']

                # Ignora mensagens enviadas pelo próprio bot
                if not message.get('fromMe', False):
                    if self.chatID not in self.states:
                        # Inicia um novo estado para o chat
                        self.states[self.chatID] = {'state': 'INITIAL', 'last_interaction': time.time()}
                    else:
                        last_interaction = self.states[self.chatID].get('last_interaction', time.time())
                        # Reinicia o estado se a última interação tiver mais de 10 minutos
                        if time.time() - last_interaction > 10 * 60:
                            self.states[self.chatID]['state'] = 'INITIAL'

                    # Atualiza o timestamp da última interação
                    self.states[self.chatID]['last_interaction'] = time.time()
                    self.save_states()

                    # Obtém o estado atual do usuário
                    state = self.states[self.chatID]['state']

                    # Identifica o texto ou payload da mensagem
                    if message_type == 'button':
                        button_id = message.get('button', {}).get('payload', '')
                        text = button_id  # Usar o ID do botão como texto para processamento
                    elif 'content' in message and 'message' in message['content']:
                        text = message['content']['message'].strip()  # Para mensagens normais
                    else:
                        text = ''

                    # Processa com base no estado atual
                    if state == 'INITIAL':
                        self.send_greeting()
                        self.send_options()
                        self.states[self.chatID]['state'] = 'ASKED_OPTION'
                        return 'Greeted and asked for options'

                    elif state == 'ASKED_OPTION':
                        # Processa a escolha do usuário
                        if text == 'option_buy_device':
                            self.handle_buy_device()
                            return 'Client chose to buy a device'
                        elif text == 'option_technical_assistance':
                            self.handle_technical_assistance()
                            return 'Client chose technical assistance'
                        elif text == 'option_talk_to_agent':
                            self.handle_talk_to_agent()
                            return 'Client chose to talk to an agent'
                        elif text == 'option_exit':
                            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
                            self.states[self.chatID]['state'] = 'FINISHED'
                            return 'Client chose to exit'
                        else:
                            self.send_message(self.chatID, "Opção inválida. Por favor, selecione uma das opções.")
                            return 'Invalid option selected'

                    elif state == 'ASKED_MODEL_NAME':
                        # Processa o nome do modelo que o cliente quer comprar
                        self.handle_model_search(text)
                        return 'Searched and listed models for user to choose'

                    elif state == 'ASKED_MODEL_NUMBER':
                        # Processa a escolha do número do modelo
                        if message_type == 'button':
                            choice = text.replace('model_', '')  # Extrai o número do ID do botão
                            self.handle_model_number_choice(choice)
                            return 'Handled model number choice via button'
                        else:
                            self.handle_model_number_choice(text)
                            return 'Handled model number choice'

                    elif state == 'CONFIRM_PURCHASE':
                        # Processa a confirmação de compra
                        self.handle_confirm_purchase(text)
                        return 'Handled purchase confirmation'

                    elif state == 'TECH_ASSISTANCE':
                        # Processa a mensagem do cliente relacionada à assistência técnica
                        issue_description = text
                        self.send_message(self.chatID, "Obrigado por nos informar. Nossa equipe de suporte entrará em contato em breve.")
                        self.states[self.chatID]['state'] = 'FINISHED'
                        self.states[self.chatID]['last_interaction'] = time.time()
                        self.save_states()
                        return 'Handled technical assistance'

                    elif state == 'WAITING_FOR_AGENT':
                        self.send_message(self.chatID, "Um de nossos atendentes já foi notificado e entrará em contato em breve.")
                        return 'Notified client that agent will contact'

                    elif state == 'FINISHED':
                        self.send_message(self.chatID, "Posso ajudar em algo mais? Se precisar, por favor, escolha uma das opções:")
                        self.send_options()
                        # Atualiza o estado para 'ASKED_OPTION' e o timestamp
                        self.states[self.chatID]['state'] = 'ASKED_OPTION'
                        self.states[self.chatID]['last_interaction'] = time.time()
                        self.save_states()
                        return 'Asked if need more help and sent options'

                    else:
                        # Estado desconhecido, resetar para 'INITIAL'
                        self.states[self.chatID]['state'] = 'INITIAL'
                        self.states[self.chatID]['last_interaction'] = time.time()
                        self.save_states()
                        self.greet_and_ask_options()
                        return 'Reset state and greeted with options'
                else:
                    return 'No action for messages sent by bot'
            else:
                logging.error("Faltando 'type' ou 'from' nos dados da mensagem.")
                return 'Erro: Dados da mensagem incompletos'
        else:
            return 'Nenhuma mensagem para processar'
