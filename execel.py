import mysql.connector
import pandas as pd

def gerar_excel_detalhado(cod_evento=300):
    conexao = mysql.connector.connect(
        host='op_ulb.vpshost2563.mysql.dbaas.com.br',
        user='op_ulb',
        password='A!tGc6sCZo#Biq',
        database='op_ulb'
    )

    # 1. Buscar inscritos
    query_inscritos = """
        SELECT
            eie.cod_ticket,
            eg.cod_evento,
            u.cod_usuario,
            ie.cod_inscricao,
            gp.protocolo,
            u.nome_usuario,
            u.camiseta,
            i.nome_igreja,
            i.cod_igreja,
            d.nome_distrito,
            YEAR(FROM_DAYS(TO_DAYS(NOW())-TO_DAYS(u.dt_nascimento))) AS idade,
            u.cpf,
            u.rg,
            DATE_FORMAT(u.dt_nascimento, '%d/%m/%Y') AS dt_nascimento,
            (CASE WHEN u.batizado = 'S' THEN 'Sim' ELSE 'Não' END) AS batizado,
            u.cel_usuario,
            u.email_usuario,
            u.end_usuario,
            u.num_usuario,
            u.bairro_usuario,
            u.complemento_usuario,
            u.cep,
            c.nome_cidade,
            e.sigla_estado as uf,
            DATE_FORMAT(ie.dt_inscricao, '%d/%m/%Y') AS dt_inscricao,
            ie.finalizado,
            ie.ativo,
            gp.confirmado,
            gtp.desc_tipo,
            gfp.desc_forma 
        FROM evento_ingressos_evento eie
        JOIN usuario u ON eie.cod_usuario = u.cod_usuario
        JOIN evento_inscritos_evento ie ON eie.cod_evento = ie.cod_evento 
            AND eie.cod_usuario = ie.cod_usuario 
            AND eie.cod_inscricao = ie.cod_inscricao
        JOIN igreja i ON ie.cod_igreja = i.cod_igreja
        JOIN distrito d ON i.cod_distrito = d.cod_distrito
        JOIN evento_global eg ON ie.cod_evento = eg.cod_evento
        JOIN global_pagamentos gp ON eg.cod_global = gp.cod_global 
            AND gp.protocolo = ie.protocolo
        LEFT JOIN global_tipo_pagto gtp ON gp.cod_tipo_pagto = gtp.cod_tipo_pagto
        LEFT JOIN global_formas_pagto gfp ON gp.cod_pagto = gfp.cod_pagto 
        LEFT JOIN cidades c ON c.cod_cidade = u.cod_cidade
        LEFT JOIN estados e ON e.cod_estado = c.cod_estado
        WHERE eie.cod_evento = %s
            AND ie.finalizado = 'S'
            AND ie.ativo = 'S'
            AND gp.confirmado = 'S'
            AND u.nome_usuario NOT LIKE '%Teste%'
        ORDER BY u.nome_usuario ASC
    """
    df_inscritos = pd.read_sql(query_inscritos, conexao, params=(cod_evento,))

    # 2. Buscar campos personalizados do evento
    query_campos = """
        SELECT cod_dado_formulario, desc_dado_formulario
        FROM evento_campo_formulario_ingresso
        WHERE cod_evento = %s AND ativo = 'S'
    """
    df_campos = pd.read_sql(query_campos, conexao, params=(cod_evento,))

    # 3. Para cada campo, buscar a resposta de cada inscrito
    cursor = conexao.cursor(buffered=True)
    colunas_adicionais = {}

    for idx, campo in df_campos.iterrows():
        cod_campo = campo["cod_dado_formulario"]
        nome_coluna = campo["desc_dado_formulario"]
        respostas = []

        for _, inscrito in df_inscritos.iterrows():
            query_resposta = """
                SELECT opcao_inscrito
                FROM evento_dados_inscritos_ingresso
                WHERE cod_ticket = %s
                AND cod_evento = %s
                AND cod_usuario = %s
                AND cod_dado_formulario = %s
            """
            cursor.execute(query_resposta, (
                inscrito["cod_ticket"],
                cod_evento,
                inscrito["cod_usuario"],
                cod_campo
            ))
            resultado = cursor.fetchone()
            respostas.append(resultado[0] if resultado else "")

        colunas_adicionais[nome_coluna] = respostas

    # Adicionar colunas novas ao DataFrame de inscritos
    for coluna, valores in colunas_adicionais.items():
        df_inscritos[coluna] = valores

    # Salvar Excel
    df_inscritos.to_excel(f'inscritos_detalhados_evento_{cod_evento}.xlsx', index=False)
    conexao.close()
    print(f"Excel gerado com sucesso: inscritos_detalhados_evento_{cod_evento}.xlsx")

# Executar
gerar_excel_detalhado()
