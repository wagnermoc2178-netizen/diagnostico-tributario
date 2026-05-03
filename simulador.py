import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Diagnóstico Tributário Inteligente", layout="centered")
st.text_input("38 98808 9755")
st.title("💼 Diagnóstico Tributário Inteligente")
st.write("Simples Nacional x Lucro Presumido x Lucro Real")

# ----------------------------
# CONEXÃO GOOGLE SHEETS
# ----------------------------
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]

        creds_dict = dict(st.secrets["gcp_service_account"])

        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        # 🔥 USE SEU LINK AQUI
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1sQQVdXBJkIioUrryurAmjEb3TA3CYoP5KigmUcoX0PI/edit?pli=1&gid=0#gid=0").sheet1

        return sheet

    except Exception as e:
        st.error("Erro ao conectar com Google Sheets")
        st.write(e)
        return None

sheet = conectar_planilha()

# ----------------------------
# ENTRADA DE DADOS
# ----------------------------
nome_cliente = st.text_input("Nome do cliente")

faturamento = st.number_input("Faturamento mensal (R$)", min_value=0.0, value=10000.0)
folha = st.number_input("Folha de pagamento (R$)", min_value=0.0, value=3000.0)
margem = st.number_input("Margem de lucro (%)", value=20.0) / 100

atividade = st.selectbox("Tipo de atividade", ["Serviço", "Comércio", "Indústria"])

# ----------------------------
# CÁLCULOS
# ----------------------------
rbt12 = faturamento * 12
fator_r = folha / faturamento if faturamento > 0 else 0

# Simples (simplificado)
imposto_simples = faturamento * 0.06

# Lucro Presumido
if atividade == "Serviço":
    presuncao = 0.32
    iss = faturamento * 0.05
else:
    presuncao = 0.08
    iss = 0

base = faturamento * presuncao

imposto_lp = (
    base * 0.15 +
    base * 0.09 +
    faturamento * 0.0065 +
    faturamento * 0.03 +
    iss
)

# Lucro Real
lucro = faturamento * margem

irpj_lr = lucro * 0.15
if lucro > 20000:
    irpj_lr += (lucro - 20000) * 0.10

imposto_lr = (
    irpj_lr +
    lucro * 0.09 +
    faturamento * 0.0165 +
    faturamento * 0.076
)

# Melhor opção
menor = min(imposto_simples, imposto_lp, imposto_lr)

if menor == imposto_simples:
    melhor = "Simples Nacional"
elif menor == imposto_lp:
    melhor = "Lucro Presumido"
else:
    melhor = "Lucro Real"

# ----------------------------
# RESULTADO
# ----------------------------
st.subheader("Resultado")

st.write(f"Fator R: {fator_r:.2%}")
st.write(f"Simples: R$ {imposto_simples:,.2f}")
st.write(f"Presumido: R$ {imposto_lp:,.2f}")
st.write(f"Lucro Real: R$ {imposto_lr:,.2f}")

st.success(f"Melhor regime: {melhor}")

# ----------------------------
# SALVAR DADOS
# ----------------------------
if st.button("💾 Salvar análise"):
    if sheet:
        try:
            sheet.append_row([
                nome_cliente,
                atividade,
                faturamento,
                imposto_simples,
                imposto_lp,
                imposto_lr,
                melhor,
                datetime.now().strftime("%d/%m/%Y %H:%M")
            ])
            st.success("Cliente salvo com sucesso!")
        except Exception as e:
            st.error("Erro ao salvar na planilha")
            st.write(e)
    else:
        st.warning("Planilha não conectada")
