import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Diagnóstico Tributário Inteligente", layout="centered")

st.title("💼 Diagnóstico Tributário Inteligente")
st.write("Simples Nacional x Lucro Presumido x Lucro Real")
st.markdown("📞 Contato: 38 98808 9755")
st.markdown("---")

# ----------------------------
# CONEXÃO GOOGLE SHEETS
# ----------------------------
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]

        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

        client = gspread.authorize(creds)

        sheet = client.open_by_url(
            "https://docs.google.com/spreadsheets/d/1sQQVdXBJkIioUrryurAmjEb3TA3CYoP5KigmUcoX0PI/edit?pli=1&gid=0#gid=0"
        ).sheet1

        return sheet

    except Exception as e:
        st.error("Erro ao conectar com Google Sheets")
        st.write(e)
        return None

sheet = conectar_planilha()

# ----------------------------
# ENTRADAS
# ----------------------------
st.subheader("📥 Dados da Empresa")

nome_cliente = st.text_input("Nome do cliente")

faturamento_total = st.number_input("Faturamento total (R$)", min_value=0.0, value=0.0)

st.subheader("📤 Saídas")

faturamento_tributado = st.number_input("Faturamento tributado (R$)", min_value=0.0, value=0.0)
faturamento_st = st.number_input("Faturamento com ST (R$)", min_value=0.0, value=0.0)

st.subheader("📥 Entradas")

icms_entrada = st.number_input("Crédito ICMS (R$)", min_value=0.0, value=0.0)

folha = st.number_input("Folha de pagamento (R$)", min_value=0.0, value=0.0)
margem = st.number_input("Margem de lucro (%)", value=20.0) / 100

atividade = st.selectbox("Tipo de atividade", ["Serviço", "Comércio", "Indústria"])

# ----------------------------
# CÁLCULOS
# ----------------------------

# Simples
imposto_simples = faturamento_total * 0.06

# ICMS
aliquota_icms = 0.18
icms_saida = faturamento_tributado * aliquota_icms
icms_a_pagar = max(icms_saida - icms_entrada, 0)

# Presumido
if atividade == "Serviço":
    presuncao = 0.32
    iss = faturamento_total * 0.05
else:
    presuncao = 0.08
    iss = 0

base = faturamento_total * presuncao

imposto_lp = (
    base * 0.15 +
    base * 0.09 +
    faturamento_total * 0.0065 +
    faturamento_total * 0.03 +
    icms_a_pagar +
    iss
)

# Lucro Real
lucro = faturamento_total * margem

irpj_lr = lucro * 0.15
if lucro > 20000:
    irpj_lr += (lucro - 20000) * 0.10

imposto_lr = (
    irpj_lr +
    lucro * 0.09 +
    faturamento_total * 0.0165 +
    faturamento_total * 0.076 +
    icms_a_pagar
)

# Melhor
menor = min(imposto_simples, imposto_lp, imposto_lr)

if menor == imposto_simples:
    melhor = "Simples Nacional"
elif menor == imposto_lp:
    melhor = "Lucro Presumido"
else:
    melhor = "Lucro Real"

economia = max(imposto_simples, imposto_lp, imposto_lr) - menor

# ----------------------------
# RESULTADO
# ----------------------------
st.subheader("📊 Resultado")

st.write(f"Simples: R$ {imposto_simples:,.2f}")
st.write(f"Presumido: R$ {imposto_lp:,.2f}")
st.write(f"Lucro Real: R$ {imposto_lr:,.2f}")

st.success(f"💡 Melhor regime: {melhor}")
st.write(f"💰 Economia: R$ {economia:,.2f}")

st.subheader("📊 ICMS")
st.write(f"Débito ICMS: R$ {icms_saida:,.2f}")
st.write(f"Crédito ICMS: R$ {icms_entrada:,.2f}")
st.write(f"ICMS a pagar: R$ {icms_a_pagar:,.2f}")

# ----------------------------
# PDF
# ----------------------------
def gerar_pdf():
    doc = SimpleDocTemplate("relatorio_tributario.pdf")
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Diagnóstico Tributário", styles["Title"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Cliente: {nome_cliente}", styles["Normal"]))
    elementos.append(Paragraph(f"Faturamento: R$ {faturamento_total:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("ICMS", styles["Heading2"]))
    elementos.append(Paragraph(f"Débito: R$ {icms_saida:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Crédito: R$ {icms_entrada:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"A pagar: R$ {icms_a_pagar:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Comparativo", styles["Heading2"]))
    elementos.append(Paragraph(f"Simples: R$ {imposto_simples:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Presumido: R$ {imposto_lp:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Real: R$ {imposto_lr:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Melhor regime: {melhor}", styles["Normal"]))
    elementos.append(Paragraph(f"Economia: R$ {economia:,.2f}", styles["Normal"]))

    doc.build(elementos)

# 👉 POSIÇÃO CORRETA DO BOTÃO PDF
if st.button("📄 Gerar Relatório em PDF"):
    gerar_pdf()
    with open("relatorio_tributario.pdf", "rb") as file:
        st.download_button(
            "⬇️ Baixar PDF",
            data=file,
            file_name="relatorio_tributario.pdf"
        )

# ----------------------------
# SALVAR
# ----------------------------
if st.button("💾 Salvar análise"):
    if sheet:
        try:
            sheet.append_row([
                nome_cliente,
                faturamento_total,
                faturamento_tributado,
                faturamento_st,
                icms_entrada,
                imposto_simples,
                imposto_lp,
                imposto_lr,
                melhor,
                economia,
                datetime.now().strftime("%d/%m/%Y %H:%M")
            ])
            st.success("Salvo com sucesso!")
        except Exception as e:
            st.error(e)
