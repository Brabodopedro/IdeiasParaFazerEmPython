import mysql.connector
import pandas as pd

def gerar_excel_da_query():
    # Configurações de conexão
    conexao = mysql.connector.connect(
        host='',
        user='',
        password='',
        database=''
    )

    # A query completa com SUBSELECT, SUBSTRING_INDEX, etc.
    query = """
    SELECT 
        t.cod_evento,
        t.cod_usuario,
        t.cod_inscricao,
        t.protocolo,
        t.nome_usuario,
        t.camiseta,
        t.nome_igreja,
        t.nome_distrito,
        t.idade,
        t.cpf,
        t.rg,
        t.dt_nascimento,
        t.cel_usuario,
        t.email_usuario,
        t.dt_inscricao,
        t.end_usuario,
        t.num_usuario,
        t.bairro_usuario,
        t.complemento_usuario,
        t.cep,
        t.nome_cidade,
        t.uf,
        t.finalizado,
        t.ativo,
        t.confirmado,
        t.desc_tipo,
        t.desc_forma,
        SUBSTRING_INDEX(t.opcoes_inscrito, ';', 1) AS opcao1,
        SUBSTRING_INDEX(
            SUBSTRING_INDEX(t.opcoes_inscrito, ';', 2),
            ';',
            -1
        ) AS opcao2,
        SUBSTRING_INDEX(
            SUBSTRING_INDEX(t.opcoes_inscrito, ';', 3),
            ';',
            -1
        ) AS opcao3
    FROM
    (
        SELECT
            eg.cod_evento, 
            u.cod_usuario,
            ie.cod_inscricao,
            gp.protocolo,
            u.nome_usuario,
            u.camiseta,
            i.nome_igreja,
            d.nome_distrito,
            YEAR(FROM_DAYS(TO_DAYS(NOW()) - TO_DAYS(u.dt_nascimento))) AS idade,
            u.cpf,
            u.rg,
            DATE_FORMAT(u.dt_nascimento, '%d/%m/%Y') AS dt_nascimento,
            u.cel_usuario,
            u.email_usuario,
            DATE_FORMAT(ie.dt_inscricao, '%d/%m/%Y') AS dt_inscricao,
            u.end_usuario,
            u.num_usuario,
            u.bairro_usuario,
            u.complemento_usuario,
            u.cep,
            c.nome_cidade,
            e.sigla_estado AS uf,
            ie.finalizado,
            ie.ativo,
            gp.confirmado,
            gtp.desc_tipo,
            gfp.desc_forma,
            GROUP_CONCAT(DISTINCT edi.opcao_inscrito SEPARATOR ';') AS opcoes_inscrito
        FROM evento_inscritos_evento ie
             JOIN usuario u ON ie.cod_usuario = u.cod_usuario
             JOIN igreja i  ON ie.cod_igreja   = i.cod_igreja
             JOIN distrito d ON i.cod_distrito = d.cod_distrito
             JOIN evento_global eg ON ie.cod_evento = eg.cod_evento
             JOIN global_pagamentos gp 
                  ON eg.cod_global = gp.cod_global 
                 AND gp.protocolo  = ie.protocolo
             LEFT JOIN evento_palestra_inscrito epi 
                   ON ie.cod_inscricao = epi.cod_inscricao
             LEFT JOIN evento_palestras_usuario epu 
                   ON epi.cod_usuario_sub = epu.cod_usuario_sub
             LEFT JOIN evento_palestras_evento ep 
                   ON epu.cod_evento = ep.cod_evento
                  AND epu.cod_sub    = ep.cod_sub
             LEFT JOIN evento_palestras_agrupador ea 
                   ON ep.cod_agrupador = ea.cod_agrupador 
                  AND ep.cod_evento    = ea.cod_evento
             LEFT JOIN global_tipo_pagto gtp 
                   ON gp.cod_tipo_pagto = gtp.cod_tipo_pagto
             LEFT JOIN global_formas_pagto gfp 
                   ON gp.cod_pagto = gfp.cod_pagto
             LEFT JOIN cidades c 
                   ON c.cod_cidade = u.cod_cidade
             LEFT JOIN estados e 
                   ON e.cod_estado = c.cod_estado
             LEFT JOIN evento_dados_inscritos edi
                   ON edi.cod_evento  = ie.cod_evento
                  AND edi.cod_usuario = ie.cod_usuario
        WHERE
            ie.cod_evento = '309'
            AND ie.finalizado = 'S'
            AND ie.ativo      = 'S'
            AND gp.confirmado = 'S'
        GROUP BY
            ie.cod_inscricao,
            eg.cod_evento,
            u.cod_usuario,
            gp.protocolo,
            u.nome_usuario,
            i.nome_igreja,
            i.cod_igreja,
            d.nome_distrito,
            ie.idade,
            u.cpf,
            u.rg,
            u.dt_nascimento,
            u.cel_usuario,
            u.email_usuario,
            ie.dt_inscricao,
            ie.finalizado,
            ie.ativo,
            gp.confirmado,
            gtp.desc_tipo,
            gfp.desc_forma,
            gp.nsu_cielo,
            u.end_usuario,
            u.num_usuario,
            u.bairro_usuario,
            u.complemento_usuario,
            u.cep,
            c.nome_cidade,
            e.sigla_estado
    ) AS t
    ORDER BY t.nome_usuario ASC;
    """

    try:
        # Lê os dados diretamente em um DataFrame
        df = pd.read_sql(query, conexao)

        # Exporta o DataFrame para um arquivo Excel
        nome_arquivo = 'resultado_inscricoes.xlsx'
        df.to_excel(nome_arquivo, index=False)

        print(f"Arquivo '{nome_arquivo}' gerado com sucesso!")
    finally:
        conexao.close()

# Executa a função
if __name__ == "__main__":
    gerar_excel_da_query()

