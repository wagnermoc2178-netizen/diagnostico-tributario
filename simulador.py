import streamlit as st
from datetime import datetime
from pathlib import Path
import base64

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Diagnóstico Tributário Inteligente")

# ================= CABEÇALHO =================
col1, col2 = st.columns([1, 5])

with col1:
    if Path("logo.png").exists():
        st.image("logo.png", width=80)

with col2:
    st.markdown("## Diagnóstico Tributário Inteligente")
    st.markdown("📞 Contato: 38 98808 9755")

st.markdown("---")

# ================= ENTRADAS =================
nome_cliente = st.text_input("Nome do cliente")

faturamento_total = st.number_input("Faturamento total", min_value=0.0)
faturamento_tributado = st.number_input("Faturamento tributado", min_value=0.0)
faturamento_st = st.number_input("Faturamento ST", min_value=0.0)

icms_credito = st.number_input("Crédito ICMS", min_value=0.0)

folha = st.number_input("Folha", min_value=0.0)
margem = st.number_input("Margem (%)", value=20.0) / 100

atividade = st.selectbox("Atividade", ["Serviço", "Comércio", "Indústria"])

if faturamento_total == 0:
    st.stop()

# ================= ICMS =================
icms_debito = faturamento_tributado * 0.18
credito_aproveitado = min(icms_debito, icms_credito)
saldo_credito = max(icms_credito - icms_debito, 0)
icms_a_pagar = max(icms_debito - icms_credito, 0)

# ================= SIMPLES =================
rbt12 = faturamento_total * 12

if atividade == "Serviço":
    if rbt12 <= 180000:
        aliquota = 0.06; deducao = 0
    elif rbt12 <= 360000:
        aliquota = 0.112; deducao = 9360
    elif rbt12 <= 720000:
        aliquota = 0.135; deducao = 17640
    elif rbt12 <= 1800000:
        aliquota = 0.16; deducao = 35640
    elif rbt12 <= 3600000:
        aliquota = 0.21; deducao = 125640
    else:
        aliquota = 0.33; deducao = 648000
else:
    if rbt12 <= 180000:
        aliquota = 0.04; deducao = 0
    elif rbt12 <= 360000:
        aliquota = 0.073; deducao = 5940
    elif rbt12 <= 720000:
        aliquota = 0.095; deducao = 13860
    elif rbt12 <= 1800000:
        aliquota = 0.107; deducao = 22500
    elif rbt12 <= 3600000:
        aliquota = 0.143; deducao = 87300
    else:
        aliquota = 0.19; deducao = 378000

aliquota_efetiva = ((rbt12 * aliquota) - deducao) / rbt12
imposto_simples = faturamento_total * aliquota_efetiva

# ================= PRESUMIDO =================
presuncao = 0.32 if atividade == "Serviço" else 0.08
base = faturamento_total * presuncao

pis = faturamento_total * 0.0065
cofins = faturamento_total * 0.03
irpj = base * 0.15
csll = base * 0.09
inss_patronal = folha * 0.20

imposto_lp = pis + cofins + irpj + csll + icms_a_pagar + inss_patronal

# ================= REAL =================
lucro = faturamento_total * margem

pis_lr = faturamento_total * 0.0165
cofins_lr = faturamento_total * 0.076
irpj_lr = lucro * 0.15
csll_lr = lucro * 0.09

imposto_lr = pis_lr + cofins_lr + irpj_lr + csll_lr + icms_a_pagar

# ================= COMPARAÇÃO =================
menor = min(imposto_simples, imposto_lp, imposto_lr)

if menor == imposto_simples:
    melhor = "Simples Nacional"
elif menor == imposto_lp:
    melhor = "Lucro Presumido"
else:
    melhor = "Lucro Real"

economia = max(imposto_simples, imposto_lp, imposto_lr) - menor

# ================= RESULTADO =================
st.subheader("Resultado")

st.write(f"Simples: R$ {imposto_simples:,.2f}")
st.write(f"Presumido: R$ {imposto_lp:,.2f}")
st.write(f"Real: R$ {imposto_lr:,.2f}")

st.success(f"Melhor regime: {melhor}")
st.write(f"Economia: R$ {economia:,.2f}")

# ================= PDF =================
def gerar_pdf():

    doc = SimpleDocTemplate("relatorio.pdf")
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Diagnóstico Tributário", styles["Title"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Cliente: {nome_cliente}", styles["Normal"]))
    elementos.append(Paragraph(f"Faturamento: R$ {faturamento_total:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("ICMS", styles["Heading2"]))
    elementos.append(Paragraph(f"Débito: R$ {icms_debito:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Crédito: R$ {icms_credito:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"A pagar: R$ {icms_a_pagar:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Comparativo Tributário", styles["Heading2"]))
    elementos.append(Paragraph(f"Simples: R$ {imposto_simples:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Presumido: R$ {imposto_lp:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Real: R$ {imposto_lr:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Conclusão", styles["Heading2"]))
    elementos.append(Paragraph(f"Melhor regime: {melhor}", styles["Normal"]))
    elementos.append(Paragraph(f"Economia: R$ {economia:,.2f}", styles["Normal"]))

    doc.build(elementos)

    with open("relatorio.pdf", "rb") as f:
        st.download_button("📄 Baixar PDF", f, "relatorio.pdf")

# ================= BOTÃO =================
if st.button("Gerar PDF"):
    gerar_pdf()
