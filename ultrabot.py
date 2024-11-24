import json
import requests
import pandas as pd
import os
import logging
import time

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

    def send_greeting(self):
        greeting = "Olá! Bem-vindo à nossa loja de celulares."
        self.send_message(self.chatID, greeting)

    def send_options(self):
        options = (
            "Por favor, selecione uma das opções abaixo:\n"
            "1 - Comprar um aparelho\n"
            "2 - Assistência Técnica\n"
            "3 - Falar com um atendente\n"
            "4 - Sair"
        )
        self.send_message(self.chatID, options)

    def greet_and_ask_options(self):
        self.send_greeting()
        self.send_options()
        # Atualiza o estado para 'ASKED_OPTION' e o timestamp
        self.states[self.chatID] = {'state': 'ASKED_OPTION', 'last_interaction': time.time()}
        self.save_states()

    def handle_buy_device(self):
        # Pergunta qual modelo o cliente está procurando
        question = "Qual modelo de celular você está procurando?"
        self.send_message(self.chatID, question)
        # Atualiza o estado para 'ASKED_MODEL_NAME'
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
                mensagem = "Encontramos os seguintes modelos:\n"
                modelos = []
                for idx, (_, row) in enumerate(resultados.iterrows(), start=1):
                    modelo = row['Modelo']
                    cor = row['Cor']
                    condicao = row['Condição']
                    valor = row['Valor']
                    mensagem += f"{idx} - Modelo: {modelo}, Cor: {cor}, Condição: {condicao}, Valor: R${valor}\n"
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
            self.states[self.chatID]['last_interaction'] = time.time()
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
            self.states[self.chatID]['last_interaction'] = time.time()
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
        # Atualiza o estado para 'WAITING_FOR_AGENT' e o timestamp
        self.states[self.chatID]['state'] = 'WAITING_FOR_AGENT'
        self.states[self.chatID]['last_interaction'] = time.time()
        self.save_states()

    def Processing_incoming_messages(self):
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
                        
                        # Verifica se passaram mais de 10 minutos desde a última interação
                        last_interaction = self.states[self.chatID].get('last_interaction', time.time())
                        elapsed_time = time.time() - last_interaction
                        if elapsed_time > 10 * 60:
                            # Mais de 10 minutos sem interação, resetar estado para 'INITIAL'
                            self.states[self.chatID]['state'] = 'INITIAL'
                    
                    # Atualiza o timestamp da última interação
                    self.states[self.chatID]['last_interaction'] = time.time()
                    self.save_states()
                    
                    # Continua o processamento com base no estado atual
                    state = self.states[self.chatID]['state']
                    if state == 'INITIAL':
                        self.greet_and_ask_options()
                        return 'Greeted and asked for options'
                    elif state == 'ASKED_OPTION':
                        choice = text
                        if choice == '1':
                            self.handle_buy_device()
                            return 'Client chose to buy a device'
                        elif choice == '2':
                            self.handle_technical_assistance()
                            return 'Client chose technical assistance'
                        elif choice == '3':
                            self.handle_talk_to_agent()
                            return 'Client chose to talk to an agent'
                        elif choice == '4':
                            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
                            self.states[self.chatID]['state'] = 'FINISHED'
                            self.states[self.chatID]['last_interaction'] = time.time()
                            self.save_states()
                            return 'Client chose to exit'
                        else:
                            self.send_message(self.chatID, "Opção inválida. Por favor, selecione uma das opções enviadas.")
                            return 'Invalid option selected'
                    elif state == 'ASKED_MODEL_NAME':
                        model_name = text
                        self.handle_model_search(model_name)
                        return 'Searched and listed models for user to choose'
                    elif state == 'ASKED_MODEL_NUMBER':
                        self.handle_model_number_choice(text)
                        return 'Handled model number choice'
                    elif state == 'CONFIRM_PURCHASE':
                        self.handle_confirm_purchase(text)
                        return 'Handled purchase confirmation'
                    elif state == 'TECH_ASSISTANCE':
                        # Aqui você pode processar a mensagem do cliente relacionada à assistência técnica
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
                        self.send_message(self.chatID, "Posso ajudar em algo mais? Se precisar, por favor, digite uma das opções:")
                        # Enviar apenas as opções, sem a saudação
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
                logging.error("Faltando 'body' ou 'from' nos dados da mensagem.")
                return 'Erro: Dados da mensagem incompletos'
        else:
            return 'Nenhuma mensagem para processar'
