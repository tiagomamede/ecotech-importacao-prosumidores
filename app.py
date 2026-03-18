import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Debug de Merge", layout="wide")

COLUNAS_PADRAO = [
    "NumeroInstalacaoUsina", "DistribuidoraNome", "PromotorNome", "Nome", "Email", 
    "Documento", "RgNumero", "Telefone", "NumeroInstalacao", "NumeroCliente", 
    "Fornecimento", "ModalidadeCompensacao", "KwhContratado", "TarifaDesconto", 
    "Endereco", "EnderecoNumero", "EnderecoComplemento", "EnderecoCidade", 
    "EnderecoCep", "EnderecoUf", "EnderecoBairro", "DataNascimento", 
    "DataAssinaturaContrato", "Observacao", "ValidacaoInfosDistribuidora", 
    "DescricaoValidacaoInfosDistribuidora", "WhatsappNotificacao", 
    "DevolucaoPisCofins", "DevolucaoFioB", "DevolucaoIcms", "CreditoResidual"
]

# --- KEYS PARA MERGE DAS PLANILHAS ---
CHAVE_A = "Número da Instalação"
CHAVE_B = "UC"

# Mapeamento de colunas destino e origem da tabela A e B
MAPEAMENTO_A = {
    "NumeroInstalacaoUsina": "Número de Instalação do Gerador",
    "DistribuidoraNome": "Distribuidora_A",
    "PromotorNome": "Parceiro",
    "Nome": "Titular",
    "Email": "E-mails do Consumidor Final",
    "Documento": "Documento do Consumidor Final (CPF ou CNPJ da Matriz)",
    "Telefone": "Telefones do Consumidor Final",
    "NumeroInstalacao": "Número da Instalação",
    "NumeroCliente": "Número do Cliente",
    "ModalidadeCompensacao": "Modalidade de Compensação",
    "KwhContratado": "kWh Contratado",
    "TarifaDesconto": "Desconto na Tarifa(%)",
    "Endereco": "Endereço_A",
    "EnderecoNumero": "Número (Endereço)",
    "EnderecoComplemento": "Complemento_A",
    "EnderecoCidade": "Cidade_A",
    "EnderecoCep": "CEP_A",
    "EnderecoUf": "UF",
    "EnderecoBairro": "Bairro_A",
    "DataNascimento": "Data de Nascimento_A",
    "DataAssinaturaContrato": "Data de Assinatura", 
    "Observacao": "Observações da Instalação", 
    "ValidacaoInfosDistribuidora": "Status da Validação das Credenciais da Distribuidora", 
    "DescricaoValidacaoInfosDistribuidora": "Informação da Validação das Credenciais da Distribuidora",
    "WhatsappNotificacao": "Envio de fatura via Whatsapp habilitado?", 
    "DevolucaoPisCofins": "Restituir Impostos",
    "DevolucaoFioB": "Restituir Fio B",
    # "DevolucaoIcms": "Restituir Impostos",
    # "CreditoResidual": ""
}

MAPEAMENTO_B = {
    "RgNumero": "NÚMERO DO RG",
    "Fornecimento": "TIPO DE LIGAÇÃO",
}

st.title("📑 Cadastro em massa Ecotech")

# --- BLOCO DE EXPLICAÇÃO ---
st.markdown("""
Esta ferramenta automatiza a unificação de dados entre a planilha de **Prosumidores (Digital Grid)** e a de **Negócios (Bitrix)**. 
O objetivo é gerar um arquivo padronizado para o sistema de cadastro em massa de prosumidores, na Ecotech.

**Como funciona:**
1. **Upload:** Faça o upload da planilha A (Prosumidores DG), planilha B (Negócios Bitrix em Cobrança) e planilha C (Negócios Bitrix em Follow-Up).
> Lembre-se de filtrar apenas os que deseja cadastrar e ativar todas as colunas no Bitrix antes de exportar o CSV.
2. **Cruzamento:** O sistema busca a correspondência entre o *Número da Instalação* (DG) e a *UC* (Bitrix).
3. **Prioridade:** Mantemos todos os registros da **planilha B (Bitrix)** e buscamos os dados complementares na DG.
4. **Download:** O resultado é um arquivo CSV pronto, seguindo o layout oficial de colunas da Ecotech.
5. **Conferência:** Por fim, confira os dados gerados e preencha os faltantes, caso hajam, antes de importar na Ecotech.
---
""")
# -------------------------------

col1, col2, col3 = st.columns(3)
with col1:
    file_a = st.file_uploader("Planilha A (Prosumidores DG)", type=["csv", "xlsx"])
with col2:
    file_b = st.file_uploader("Planilha B (Negócios Bitrix Cobrança)", type=["csv"])
with col3:
    file_c = st.file_uploader("Planilha C (Negócios Bitrix Follow-Up)", type=["csv"])

if file_a and file_b and file_c:
    try:
        # Leitura das planilhas
        df_a = pd.read_excel(file_a) if file_a.name.endswith('.xlsx') else pd.read_csv(file_a, sep=None, engine='python')
        df_b = pd.read_csv(file_b, sep=None, engine='python')
        df_c = pd.read_csv(file_c, sep=None, engine='python')

        # Adicionar registros de C em B (evitando o header e possíveis duplicações)
        df_b = pd.concat([df_b, df_c], ignore_index=True)

        # --- BLOCO DE SEGURANÇA: NORMALIZAÇÃO ---
        # Força os IDs a serem strings, remove espaços e converte para número (se possível) para igualar formatos
        def limpar_id(serie):
            return serie.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        df_a[CHAVE_A] = limpar_id(df_a[CHAVE_A])
        df_b[CHAVE_B] = limpar_id(df_b[CHAVE_B])

        # --- DEBUG DE COLUNAS ---
        # with st.expander("🕵️ Clique para ver os nomes das colunas encontradas"):
        #     st.write("**Colunas na Planilha A:**", df_a.columns.tolist())
        #     st.write("**Colunas na Planilha B:**", df_b.columns.tolist())

        # MERGE
        df_unificado = pd.merge(df_a,
                                df_b,
                                left_on=CHAVE_A,
                                right_on=CHAVE_B,
                                how='right',
                                suffixes=('_A', '_B'), # Colunas repetidas ganharão estes sufixos
                                indicator=True)

        # --- RELATÓRIO DE ERROS ---
        matches = df_unificado[df_unificado['_merge'] == 'both']
        falhas = df_unificado[df_unificado['_merge'] == 'right_only']

        # Armazena as chaves das ocorrências que não deram certo
        chaves_que_falharam = falhas[CHAVE_B].unique().tolist()

        st.subheader("📊 Resultado do Cruzamento")
        col1, col2 = st.columns(2)
        col1.metric("Sucesso (Bitrix x DG)", len(matches))
        col2.metric("Falha (Não encontrados dados correspondentes na DG)", len(falhas))

        # Exibe as chaves das falhas no front
        if len(falhas) > 0:
            with st.expander("⚠️ Ver UCs não encontrados na DG"):
                st.write(f"Os seguintes IDs da coluna '{CHAVE_B}' não possuem correspondência:")
                st.write(chaves_que_falharam)

        if len(matches) > 0:
            st.write("✅ **Exemplo de dados que deram certo:**")
            # Mostra a chave e as colunas que você quer puxar da A
            cols_to_show = [CHAVE_B] + [v for v in MAPEAMENTO_A.values() if v in df_unificado.columns]
            st.dataframe(matches[cols_to_show].head(5))
        else:
            st.error("🚨 NENHUM MATCH ENCONTRADO! Os IDs da Planilha A não batem com os da B.")
            st.write("Compare os IDs abaixo:")
            st.write(f"IDs na A (exemplo): {df_a[CHAVE_A].head(3).tolist()}")
            st.write(f"IDs na B (exemplo): {df_b[CHAVE_B].head(3).tolist()}")

        if st.button("Gerar Arquivo Final"):
            # FILTRO: Mantém apenas as linhas que existem em AMBAS as planilhas
            df_unificado_filtrado = df_unificado[df_unificado['_merge'] == 'both'].copy()

            # Cria o DataFrame vazio com o cabeçalho padrão
            df_final = pd.DataFrame(columns=COLUNAS_PADRAO)
            
            # IMPORTANTE: Agora usamos o df_unificado_filtrado para preencher os dados
            df_final["NumeroCliente"] = df_unificado_filtrado[CHAVE_B]

            # Preenchimento Planilha A
            for col_f, col_o in MAPEAMENTO_A.items():
                if col_o in df_unificado_filtrado.columns:
                    df_final[col_f] = df_unificado_filtrado[col_o]
                else:
                    st.warning(f"Coluna de origem '{col_o}' (Planilha A) não encontrada.")

            # Preenchimento Planilha B
            for col_f, col_o in MAPEAMENTO_B.items():
                if col_o in df_unificado.columns:
                    df_final[col_f] = df_unificado[col_o]
                else:
                    st.warning(f"Coluna de origem '{col_o}' (Planilha B) não encontrada.")

            # CORREÇÃO PARA COLUNAS DUPLICADAS (Mesma origem para destinos diferentes)
            # Atribuímos manualmente para evitar o erro de "Duplicate column names"
            if "DevolucaoPisCofins" in df_final.columns:
                df_final["DevolucaoIcms"] = df_final["DevolucaoPisCofins"]

            # Limpezas e Formatações Finais
            if "Documento" in df_final.columns:
                df_final["Documento"] = df_final["Documento"].astype(str).str.replace(r'\D', '', regex=True)
            
            for col_data in ["DataNascimento", "DataAssinaturaContrato"]:
                if col_data in df_final.columns:
                    df_final[col_data] = pd.to_datetime(df_final[col_data], errors='coerce').dt.strftime('%d/%m/%Y')

            # --- ETAPA DE TRANSFORMAÇÃO DE DADOS ---
            # 1. Mapeamento Sim/Não para TRUE/FALSE
            mapa_bool = {"Sim": True, "Não": False, "SIM": True, "NÃO": False, "nao": False, "sim": True}

            cols_booleanas = [
                "WhatsappNotificacao", 
                "DevolucaoPisCofins", 
                "DevolucaoFioB", 
                "DevolucaoIcms",
                "CreditoResidual"
            ]

            for col in cols_booleanas:
                if col in df_final.columns:
                    # Aplica o mapeamento e garante que valores vazios ou diferentes fiquem como False
                    df_final[col] = df_final[col].map(mapa_bool).fillna(False)

            # 2. Forçar Valor Fixo para Validação
            df_final["ValidacaoInfosDistribuidora"] = False

            # 3. Formatação de Datas (DD/MM/AAAA -> AAAA-MM-DD)
            cols_datas = ["DataNascimento", "DataAssinaturaContrato"]

            for col in cols_datas:
                if col in df_final.columns:
                    # Converte para datetime e depois formata como string ISO (AAAA-MM-DD)
                    df_final[col] = pd.to_datetime(df_final[col], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
                    # Caso a data seja inválida na origem, o resultado será 'NaN' ou string vazia
                    df_final[col] = df_final[col].fillna("")

            # 4. Formatação de KwhContratado (Ex: 799,99999 -> 799.99)
            if "KwhContratado" in df_final.columns:
                # Garante que é string, troca vírgula por ponto
                df_final["KwhContratado"] = df_final["KwhContratado"].astype(str).str.replace(',', '.')
                
                # Converte para numérico (coerce transforma erros em NaN)
                df_final["KwhContratado"] = pd.to_numeric(df_final["KwhContratado"], errors='coerce')
                
                # Arredonda para 2 casas decimais e preenche vazios com 0.00
                df_final["KwhContratado"] = df_final["KwhContratado"].round(2).fillna(0.00)

            # 5. Formatação de Documento (Ex: 12312312312 -> 123123123-12)
            if "Documento" in df_final.columns:
                # Primeiro, limpamos tudo que não é número e garantimos que é string
                df_final["Documento"] = df_final["Documento"].astype(str).str.replace(r'\D', '', regex=True)
                
                # Aplicamos a máscara: tudo até o penúltimo caractere + '-' + dois últimos caracteres
                # Apenas se o campo não estiver vazio
                df_final["Documento"] = df_final["Documento"].apply(
                    lambda x: f"{x[:-2]}-{x[-2:]}" if len(x) > 2 else x
                )

            # 6. Limpeza de NumeroInstalacao (Ex: 1234-cancel -> 1234)
            if "NumeroInstalacao" in df_final.columns:
                # Garante que é string e remove tudo que não for dígito (\D)
                df_final["NumeroInstalacao"] = df_final["NumeroInstalacao"].astype(str).str.replace(r'\D', '', regex=True)
                
                # Opcional: Se o campo ficar vazio após a limpeza (ex: era apenas texto), 
                # você pode preencher com vazio ou um valor padrão
                df_final["NumeroInstalacao"] = df_final["NumeroInstalacao"].replace('', '0')

            # 7. Formatacao de Multiplos Emails (Ex: email1, email2 -> "email1;email2")
            if "Email" in df_final.columns:
                # Garante que é string e remove espaços extras
                df_final["Email"] = df_final["Email"].astype(str).str.replace(r'\s+', '', regex=True)
                
                # Substitui vírgulas por ponto e vírgula para melhor legibilidade
                df_final["Email"] = df_final["Email"].str.replace(',', '; ')

                # Adiciona entre aspas duplas se houver mais de um email para evitar problemas na leitura do CSV
                df_final["Email"] = df_final["Email"].apply(lambda x: f'"{x}"' if ';' in x else x)

            # 8. Formatação de Multiplos Telefones (Ex: 11999999999, 11988888888 -> "11999999999;11988888888")
            if "Telefone" in df_final.columns:
                # Garante que é string e remove espaços extras
                df_final["Telefone"] = df_final["Telefone"].astype(str).str.replace(r'\s+', '', regex=True)
                
                # Substitui vírgulas por ponto e vírgula para melhor legibilidade
                df_final["Telefone"] = df_final["Telefone"].str.replace(',', '; ')

                # Adiciona entre aspas duplas se houver mais de um telefone para evitar problemas na leitura do CSV
                df_final["Telefone"] = df_final["Telefone"].apply(lambda x: f'"{x}"' if ';' in x else x)
            # ---------------------------------------

            # Exportação
            st.success("Tabela final gerada com sucesso! Baixe para obter todos os dados.")
            st.dataframe(df_final.head()) # Preview final para conferência

            output = BytesIO()
            df_final.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
            st.download_button("📥 Baixar CSV", output.getvalue(), "resultado.csv", "text/csv")

    except Exception as e:
        st.error(f"Erro crítico: {e}")