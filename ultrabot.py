import json
import requests
import pandas as pd
import os
import logging
import time

STATE_FILE = 'conversation_states.json'

def load_states():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
                    logging.error("O arquivo de estados não contém um dicionário válido. Reiniciando estados.")
                    return {}
            except json.JSONDecodeError:
                logging.error("Erro ao decodificar o arquivo de estados. Criando novo dicionário de estados.")
                return {}
    else:
        return {}
    
def check_inactive_conversations():
    try:
        states = load_states()
        logging.info(f"Estados carregados: {states}")
        current_time = time.time()
        for chatID, state_info in list(states.items()):
            if not isinstance(state_info, dict):
                logging.error(f"O state_info para chatID {chatID} não é um dicionário: {state_info}")
                continue
            last_interaction = state_info.get('last_interaction', current_time)
            if current_time - last_interaction > 10 * 60 and state_info['state'] != 'SESSION_ENDED':
                send_message(chatID, "Sua sessão foi encerrada por inatividade. Se precisar de algo, por favor, envie uma nova mensagem para iniciar um novo atendimento.")
                states[chatID]['state'] = 'SESSION_ENDED'
                states[chatID]['pause_start_time'] = time.time()
        save_states(states)
    except Exception as e:
        logging.error(f"Erro ao verificar conversas inativas: {e}")

def save_states(states):
    with open(STATE_FILE, 'w') as f:
        json.dump(states, f)

def send_message(chatID, text):
    data = {
        "to": chatID,
        "body": text
    }
    url = f"https://api.ultramsg.com/instance99723/messages/chat?token=2str21gem9r5za4u"
    headers = {'Content-type': 'application/json'}
    answer = requests.post(url, data=json.dumps(data), headers=headers)
    return answer

class ultraChatBot():
    def __init__(self, message_data):
        self.message = message_data
        self.chatID = message_data.get('from')
        self.ultraAPIUrl = 'https://api.ultramsg.com/instance99723/'
        self.token = '2str21gem9r5za4u'
        self.states = load_states()

    def send_message(self, chatID, text):
        return send_message(chatID, text)

    def send_greeting(self):
        greeting = "Olá! Bem-vindo à nossa loja de celulares."
        self.send_message(self.chatID, greeting)

    def send_options(self):
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
            "✅ Sim\n"
            "❌ N - Escolher outro modelo\n"
            "🔄 M - Menu Principal\n"
            "🚪 S - Sair"
        )
        self.send_message(self.chatID, options)

    def greet_and_ask_options(self):
        self.send_greeting()
        self.send_options()
        self.states[self.chatID] = {'state': 'ASKED_OPTION', 'last_interaction': time.time()}
        save_states(self.states)  # Substituído self.save_states() por save_states(self.states)

    def handle_buy_device(self):
        question = (
            "Qual modelo de celular você está procurando? "
            "Por favor, digite o nome do modelo ou parte dele (exemplo: iphone 12)."
        )
        self.send_message(self.chatID, question)
        self.states[self.chatID]['state'] = 'ASKED_MODEL_NAME'
        self.states[self.chatID]['last_interaction'] = time.time()
        save_states(self.states)  # Substituído self.save_states() por save_states(self.states)

    def handle_model_search(self, model_name):
        try:
            # Criar um dicionário para mapear cores para emojis de coração
            cor_para_emoji = {  
                'Preto': '🖤',
                'Branco': '🤍',
                'Lilás': '💜',
                'Azul': '💙',
                'Dourado': '💛',
                'Cinza': '⚫️',
                'Verde': '💚',
                'Vermelho': '❤️',
                'Rosa': '💗',
                # Adicione outras cores conforme necessário
            }
           
            # Pesquisa os modelos correspondentes ao input do cliente
            df = pd.read_excel('ESTOQUE_.xlsx', header=None, usecols=[1, 2, 3, 5, 6])
            df.columns = ['Modelo', 'Cor', 'Bateria', 'Condição', 'Valor']
            df = df.iloc[::-1].reset_index(drop=True)
            resultados = df[df['Modelo'].str.contains(model_name, case=False, na=False)]
            if not resultados.empty:
                # Agrupa os modelos por nome
                grupos_modelos = resultados.groupby('Modelo')
                mensagem = "✨📱 LISTA DE APARELHOS DISPONÍVEIS 📱✨\n"
                mensagem += "🚨 Todos os aparelhos (seminovos) possuem 90 dias de garantia! 🚨\n\n"
                modelos = []
                idx = 1  # Contador para numerar os modelos

                for nome_modelo, grupo in grupos_modelos:
                    mensagem += f"🍏 {nome_modelo}\n"
                    detalhes_modelo = {}
                    for _, row in grupo.iterrows():
                        cor = row['Cor']
                        valor = row['Valor']
                        condicao = row['Condição']
                        # Obter o emoji correspondente à cor
                        emoji_cor = cor_para_emoji.get(cor, '🔳')  # Emoji padrão se não encontrar a cor
                        # Cria uma chave única para cada combinação de características
                        chave = f"{cor} - {valor}"
                        if chave not in detalhes_modelo:
                            detalhes_modelo[chave] = {'cor': cor, 'emoji_cor': emoji_cor, 'valor': valor, 'indices': []}
                        detalhes_modelo[chave]['indices'].append(idx)
                        modelos.append(row.to_dict())
                        idx += 1

                    for detalhe in detalhes_modelo.values():
                        indices = ', '.join(map(str, detalhe['indices']))
                        linha = f"{indices} - {detalhe['emoji_cor']} {detalhe['cor']} - R$ {detalhe['valor']}\n"
                        mensagem += linha
                    mensagem += "\n"

                mensagem += "🎁 Aproveite essa oportunidade incrível para garantir seu iPhone!\n"
                mensagem += "📦 Todos os aparelhos seminovos e passam por rigorosa inspeção de qualidade."

                self.send_message(self.chatID, mensagem)

                # Pergunta ao cliente para escolher um modelo, inclui N, M, S
                self.send_message(self.chatID, "Por favor, digite o número do modelo que você deseja: \n ou\n N - Escolher outro modelo\nM - Menu Principal\nS - Sair")

                # Atualiza o estado para 'ASKED_MODEL_NUMBER' e salva os modelos listados
                self.states[self.chatID]['state'] = 'ASKED_MODEL_NUMBER'
                self.states[self.chatID]['modelos'] = modelos
                self.states[self.chatID]['last_interaction'] = time.time()
                save_states(self.states)  # Substituído self.save_states() por save_states(self.states)
            else:
                self.send_message(self.chatID, "Desculpe, não encontramos esse modelo em nosso estoque.")
                # Permanece no estado 'ASKED_MODEL_NAME' para o cliente tentar novamente
        except Exception as e:
            logging.error(f"Erro ao ler a planilha: {e}")
            self.send_message(self.chatID, "Desculpe, ocorreu um erro ao buscar o modelo.")
            # Permanece no estado 'ASKED_MODEL_NAME'

    # Método para lidar com a escolha do número do modelo        
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
            save_states(self.states)
        elif choice == 'S':
            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
            self.states[self.chatID]['state'] = 'FINISHED'
            # Define o início da pausa
            self.states[self.chatID]['pause_start_time'] = time.time()
            save_states(self.states)
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
                    save_states(self.states)
                else:
                    self.send_message(self.chatID, "Opção inválida. Por favor, digite o número correspondente ao modelo desejado, ou escolha uma das opções enviadas.")
            except ValueError:
                self.send_message(self.chatID, "Entrada inválida. Por favor, digite o número correspondente ao modelo desejado, ou escolha uma das opções enviadas.")

    # Método para lidar com a confirmação da compra
    def handle_confirm_purchase(self, choice):
        choice = choice.strip().upper()
        if choice == 'SIM':
            # Processa a compra
            self.send_message(self.chatID, "Obrigado por sua compra! Entraremos em contato para finalizar os detalhes.")
            self.states[self.chatID]['state'] = 'FINISHED'
            # Define o início da pausa
            self.states[self.chatID]['pause_start_time'] = time.time()
            save_states(self.states)
        elif choice == 'N':
            # Volta a perguntar qual modelo o cliente procura
            self.handle_buy_device()
        elif choice == 'M':
            # Retorna ao menu principal
            self.send_options()
            self.states[self.chatID]['state'] = 'ASKED_OPTION'
            self.states[self.chatID]['last_interaction'] = time.time()
            save_states(self.states)
        elif choice == 'S':
            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
            self.states[self.chatID]['state'] = 'FINISHED'
            # Define o início da pausa
            self.states[self.chatID]['pause_start_time'] = time.time()
            save_states(self.states)
        else:
            self.send_message(self.chatID, "Opção inválida. Por favor, digite 'Sim' para confirmar a compra, ou escolha uma das opções enviadas.\nN - Escolher outro modelo\nM - Menu Principal\nS - Sair")

    # Método para lidar com a opção 2 - Assistência Técnica
    def handle_technical_assistance_options(self):
        options = (
            "Por favor, selecione o tipo de serviço de assistência técnica que você precisa:\n"
            "1️⃣ - Trocar Tela\n"
            "2️⃣ - Trocar Bateria\n"
            "3️⃣ - Trocar Tampa Traseira\n"
            "4️⃣ - Outro Problema"
        )
        self.send_message(self.chatID, options)
        self.states[self.chatID]['state'] = 'ASKED_TECH_OPTION'
        self.states[self.chatID]['last_interaction'] = time.time()
        save_states(self.states)
    
    # Método para lidar com a escolha do serviço de assistência técnica
    def handle_tech_option_choice(self, choice):
        choice = choice.strip()
        if choice in ['1', '2', '3']:
            service_map = {'1': 'Tela', '2': 'Bateria', '3': 'Tampa'}
            self.states[self.chatID]['service_type'] = service_map[choice]
            self.send_message(self.chatID, "Por favor, informe o modelo do seu iPhone (exemplo: iPhone 12).")
            self.states[self.chatID]['state'] = 'ASKED_PHONE_MODEL'
            self.states[self.chatID]['last_interaction'] = time.time()
            save_states(self.states)
        elif choice == '4':
            self.send_message(self.chatID, "Por favor, descreva o problema que está enfrentando.")
            self.states[self.chatID]['state'] = 'ASKED_PROBLEM_DESCRIPTION'
            self.states[self.chatID]['last_interaction'] = time.time()
            save_states(self.states)
        else:
            self.send_message(self.chatID, "Opção inválida. Por favor, selecione uma das opções enviadas.")

    # Método para lidar com o modelo do iPhone para reparo
    def handle_phone_model(self, model_name):
        service_type = self.states[self.chatID].get('service_type')
        if not service_type:
            self.send_message(self.chatID, "Desculpe, ocorreu um erro. Vamos começar novamente.")
            self.handle_technical_assistance_options()
            return

        try:
            df = pd.read_excel('reparo_iphones.xlsx')
            df = df[['Modelo', 'Tela', 'Bateria', 'Tampa']]
            df = df.dropna(subset=['Modelo'])

            # Filtrar pelo modelo fornecido
            matched_rows = df[df['Modelo'].str.contains(model_name, case=False, na=False)]
            if matched_rows.empty:
                self.send_message(self.chatID, f"Desculpe, não encontramos o modelo {model_name} em nosso sistema.")
                self.send_message(self.chatID, "Por favor, informe o modelo novamente! ")
                return

            # Obter o preço do serviço selecionado
            price = matched_rows.iloc[0][service_type]
            if pd.isna(price):
                self.send_message(self.chatID, f"Desculpe, não possuo o serviço de {service_type.lower()} para o modelo {model_name}.")
                self.send_message(self.chatID, "Por favor, informe outro modelo ou peça um orçaento específico.")
                self.handle_technical_assistance_options()
                return

            # Enviar o orçamento para o cliente
            self.send_message(self.chatID, f"O valor para trocar a {service_type.lower()} do seu {model_name} é R$ {price:.2f}.")
            self.send_message(self.chatID, "Deseja prosseguir com o serviço?\nResponda com:\nSim ✅\nNão ❌")
            self.states[self.chatID]['state'] = 'ASKED_SERVICE_CONFIRMATION'
            self.states[self.chatID]['last_interaction'] = time.time()
            save_states(self.states)

        except Exception as e:
            logging.error(f"Erro ao acessar a planilha: {e}")
            self.send_message(self.chatID, "Desculpe, ocorreu um erro ao acessar nossas informações. Por favor, tente novamente mais tarde.")

    # Método para lidar com a confirmação do serviço de reparo
    def handle_service_confirmation(self, confirmation):
        confirmation = confirmation.strip().upper()
        if confirmation in ['SIM', '✅']:
            self.send_message(self.chatID, "Obrigado! Seu serviço foi agendado. Nossa equipe entrará em contato para mais detalhes.")
            self.states[self.chatID]['state'] = 'FINISHED'
            self.states[self.chatID]['pause_start_time'] = time.time()
            save_states(self.states)
        elif confirmation in ['NÃO', 'NAO', '❌']:
            self.send_message(self.chatID, "Tudo bem! Se precisar de algo mais, estamos à disposição.")
            self.states[self.chatID]['state'] = 'FINISHED'
            self.states[self.chatID]['pause_start_time'] = time.time()
            save_states(self.states)
        else:
            self.send_message(self.chatID, "Desculpe, não entendi. Por favor, responda com 'Sim' ou 'Não'.")
    
    # Método para lidar com a descrição de outro problema
    def handle_problem_description(self, description):
        # Aqui você pode salvar a descrição em algum lugar ou enviar para sua equipe
        self.send_message(self.chatID, "Obrigado por nos informar. Nossa equipe técnica irá analisar e entraremos em contato com o orçamento em breve.")
        self.states[self.chatID]['state'] = 'FINISHED'
        self.states[self.chatID]['pause_start_time'] = time.time()
        save_states(self.states)

    def handle_talk_to_agent(self):
        message = "Um de nossos atendentes entrará em contato com você em breve."
        self.send_message(self.chatID, message)
        # Atualiza o estado para 'WAITING_FOR_AGENT' e define 'pause_start_time'
        self.states[self.chatID]['state'] = 'WAITING_FOR_AGENT'
        self.states[self.chatID]['pause_start_time'] = time.time()
        save_states(self.states)

        
    # Método para processar as mensagens recebidas
    def Processing_incoming_messages(self):
        user_message = self.message.get('body', '').strip()
        if not user_message:
            self.send_message(self.chatID, "Desculpe, não entendi sua mensagem.")
            return

        if self.chatID not in self.states:
            self.greet_and_ask_options()
            return

        state_info = self.states[self.chatID]
        state = state_info.get('state')

        if state == 'ASKED_OPTION':
            if user_message == '1':
                self.handle_buy_device()
            elif user_message == '2':
                self.handle_technical_assistance_options()
            elif user_message == '3':
                self.handle_talk_to_agent()
            elif user_message == '4':
                self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
                self.states[self.chatID]['state'] = 'FINISHED'
                self.states[self.chatID]['pause_start_time'] = time.time()
                save_states(self.states)
            else:
                self.send_message(self.chatID, "Opção inválida. Por favor, selecione uma das opções enviadas.")

        elif state == 'ASKED_MODEL_NAME':
            self.handle_model_search(user_message)

        elif state == 'ASKED_MODEL_NUMBER':
            self.handle_model_number_choice(user_message)

        elif state == 'CONFIRM_PURCHASE':
            self.handle_confirm_purchase(user_message)

        elif state == 'ASKED_TECH_OPTION':
            self.handle_tech_option_choice(user_message)

        elif state == 'ASKED_PHONE_MODEL':
            self.handle_phone_model(user_message)

        elif state == 'ASKED_SERVICE_CONFIRMATION':
            self.handle_service_confirmation(user_message)

        elif state == 'ASKED_PROBLEM_DESCRIPTION':
            self.handle_problem_description(user_message)

        elif state == 'WAITING_FOR_AGENT':
            self.send_message(self.chatID, "Por favor, aguarde. Um atendente entrará em contato em breve.")

        elif state == 'FINISHED':
            # Reinicia a conversa ao receber uma nova mensagem
            self.send_message(self.chatID, "Olá novamente! Como podemos te ajudar?")
            self.send_options()
            self.states[self.chatID]['state'] = 'ASKED_OPTION'
            self.states[self.chatID]['last_interaction'] = time.time()
            save_states(self.states)
        else:
            self.send_message(self.chatID, "Desculpe, ocorreu um erro. Vamos começar novamente.")
            self.greet_and_ask_options()