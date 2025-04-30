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

    # 3. Buscar todas as respostas de uma vez
    query_respostas = """
        SELECT 
            edi.cod_ticket,
            edi.cod_usuario,
            edi.cod_dado_formulario,
            edi.opcao_inscrito,
            ecfi.desc_dado_formulario
        FROM evento_dados_inscritos_ingresso edi
        JOIN evento_campo_formulario_ingresso ecfi 
            ON edi.cod_dado_formulario = ecfi.cod_dado_formulario
        WHERE edi.cod_evento = %s
    """
    df_respostas = pd.read_sql(query_respostas, conexao, params=(cod_evento,))

    # Pivotar respostas por cod_ticket + cod_usuario
    df_respostas_pivot = df_respostas.pivot_table(
        index=["cod_ticket", "cod_usuario"],
        columns="desc_dado_formulario",
        values="opcao_inscrito",
        aggfunc="first"
    ).reset_index()

    # Juntar com o DataFrame principal
    df_final = pd.merge(
        df_inscritos,
        df_respostas_pivot,
        on=["cod_ticket", "cod_usuario"],
        how="left"
    )

    # Exportar Excel
    df_final.to_excel(f'inscritos_detalhados_evento_{cod_evento}.xlsx', index=False)

# Executar
gerar_excel_detalhado()
