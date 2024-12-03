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

    def handle_technical_assistance(self):
        message = "Para assistência técnica, por favor descreva o problema que está enfrentando."
        self.send_message(self.chatID, message)
        # Você pode definir um novo estado para assistência técnica, se necessário
        self.states[self.chatID]['state'] = 'TECH_ASSISTANCE'
        self.states[self.chatID]['last_interaction'] = time.time()
        save_states(self.states)

    def handle_talk_to_agent(self):
        message = "Um de nossos atendentes entrará em contato com você em breve."
        self.send_message(self.chatID, message)
        # Atualiza o estado para 'WAITING_FOR_AGENT' e define 'pause_start_time'
        self.states[self.chatID]['state'] = 'WAITING_FOR_AGENT'
        self.states[self.chatID]['pause_start_time'] = time.time()
        save_states(self.states)

    def Processing_incoming_messages(self):
        message = self.message
        if message:
            if 'body' in message and 'from' in message:
                text = message['body'].strip().upper()  # Captura o texto e padroniza para maiúsculas
                logging.info(f"Mensagem recebida de {self.chatID}: '{text}'")
                if not message.get('fromMe', False):  # Ignora mensagens enviadas pelo bot
                    if self.chatID not in self.states:
                        self.states[self.chatID] = {'state': 'INITIAL', 'last_interaction': time.time()}
                        save_states(self.states)
                    else:
                        state = self.states[self.chatID]['state']
                        logging.info(f"Estado atual de {self.chatID}: {state}")
                        if state not in ['WAITING_FOR_AGENT', 'FINISHED', 'SESSION_ENDED']:
                            self.states[self.chatID]['last_interaction'] = time.time()
                        # Verifica se já se passaram 10 minutos de inatividade para resetar o estado
                        last_interaction = self.states[self.chatID].get('last_interaction', time.time())
                        if time.time() - last_interaction > 10 * 60 and state != 'SESSION_ENDED':
                            self.states[self.chatID]['state'] = 'SESSION_ENDED'
                            save_states(self.states)
                            self.send_message(self.chatID, "Sua sessão foi encerrada por inatividade. Se precisar de algo, por favor, envie uma nova mensagem para iniciar um novo atendimento.")

                    state = self.states[self.chatID]['state']

                    if state == 'SESSION_ENDED':
                        # Reinicia a conversa
                        self.states[self.chatID]['state'] = 'INITIAL'
                        self.states[self.chatID]['last_interaction'] = time.time()
                        save_states(self.states)
                        self.send_greeting()
                        self.send_options()
                        return 'Session restarted after inactivity'

                    if state == 'INITIAL':
                        self.send_greeting()
                        self.send_options()
                        self.states[self.chatID]['state'] = 'ASKED_OPTION'
                        self.states[self.chatID]['last_interaction'] = time.time()
                        save_states(self.states)
                        logging.info(f"Estado atualizado para 'ASKED_OPTION' para {self.chatID}")
                        return 'Greeted and asked for options'

                    elif state == 'ASKED_OPTION':
                        # Processa a escolha do usuário
                        if text in ['1', '1️⃣']:
                            self.handle_buy_device()
                            return 'Client chose to buy a device'
                        elif text in ['2', '2️⃣']:
                            self.handle_technical_assistance()
                            return 'Client chose technical assistance'
                        elif text in ['3', '3️⃣']:
                            self.handle_talk_to_agent()
                            return 'Client chose to talk to an agent'
                        elif text in ['4', '4️⃣', 'S', 'E']:
                            self.send_message(self.chatID, "Obrigado pelo contato. Se precisar de algo, estamos à disposição!")
                            self.states[self.chatID]['state'] = 'FINISHED'
                            self.states[self.chatID]['pause_start_time'] = time.time()
                            save_states(self.states)
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
                        # Aqui você pode processar a mensagem do cliente relacionada à assistência técnica
                        issue_description = text
                        self.send_message(self.chatID, "Obrigado por nos informar. Nossa equipe de suporte entrará em contato em breve.")
                        self.states[self.chatID]['state'] = 'FINISHED'
                        # Define o início da pausa
                        self.states[self.chatID]['pause_start_time'] = time.time()
                        save_states(self.states)
                        return 'Handled technical assistance'

                    elif state == 'WAITING_FOR_AGENT' or state == 'FINISHED':
                        # Verifica se já se passou 1 hora desde o início da pausa
                        pause_duration = time.time() - self.states[self.chatID].get('pause_start_time', 0)
                        if pause_duration >= 3600:
                            # Mais de 1 hora se passou, o bot retoma o atendimento
                            self.send_message(self.chatID, "Desculpe pela espera. Posso ajudar em algo?")
                            self.send_options()
                            self.states[self.chatID]['state'] = 'ASKED_OPTION'
                            self.states[self.chatID].pop('pause_start_time', None)  # Remove o timestamp de pausa
                            save_states(self.states)
                            return 'Re-engaged after 1 hour pause'
                        else:
                            # Não responde durante a pausa
                            return 'Paused, waiting for agent'

                    else:
                        # Estado desconhecido, resetar para 'INITIAL'
                        self.states[self.chatID]['state'] = 'INITIAL'
                        self.states[self.chatID].pop('pause_start_time', None)
                        save_states(self.states)
                        self.greet_and_ask_options()
                        return 'Reset state and greeted with options'
                else:
                    return 'No action for messages sent by bot'
            else:
                logging.error("Faltando 'body' ou 'from' nos dados da mensagem.")
                return 'Erro: Dados da mensagem incompletos'
        else:
            return 'Nenhuma mensagem para processar'
