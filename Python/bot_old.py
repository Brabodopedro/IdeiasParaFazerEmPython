from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd

app = Flask(__name__)

# Carrega os dados da planilha Excel
df = pd.read_excel('iPhone_Models.xlsx')

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'iphone' in incoming_msg:
        # Filtra os modelos de iPhone disponíveis
        modelos_novos = df[(df['Modelo'].str.contains('iPhone', case=False)) & (df['Condição'] == 'Novo')]
        if not modelos_novos.empty:
            resposta = 'Temos os seguintes iPhones novos disponíveis:\n'
            for index, row in modelos_novos.iterrows():
                resposta += f"{row['Modelo']} - R${row['Preço']}\n"
            resposta += 'Você gostaria de algum desses, ou prefere ver os iPhones usados?'
            msg.body(resposta)
        else:
            msg.body('Desculpe, não temos iPhones novos disponíveis no momento. Gostaria de ver os modelos usados?')
    elif 'usado' in incoming_msg or 'usados' in incoming_msg:
        # Filtra os modelos de iPhone usados
        modelos_usados = df[(df['Modelo'].str.contains('iPhone', case=False)) & (df['Condição'] == 'Usado')]
        if not modelos_usados.empty:
            resposta = 'Aqui estão os iPhones usados disponíveis:\n'
            for index, row in modelos_usados.iterrows():
                resposta += f"{row['Modelo']} - R${row['Preço']}\n"
            msg.body(resposta)
        else:
            msg.body('Desculpe, não temos iPhones usados disponíveis no momento.')
    else:
        msg.body('Olá! Qual modelo de celular você está procurando?')

    return str(resp)

if __name__ == '__main__':
    app.run()
