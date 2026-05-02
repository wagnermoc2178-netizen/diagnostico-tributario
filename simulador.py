import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

st.set_page_config(page_title="Diagnóstico Tributário Inteligente", layout="centered")

st.title("💼 Diagnóstico Tributário Inteligente")
st.write("Consultoria Contábil Estratégica")

# ----------------------------
# ENTRADA DE DADOS
# ----------------------------
faturamento_mensal = st.number_input("Faturamento mensal (R$)", min_value=0.0, value=10000.0)
folha = st.number_input("Folha de pagamento mensal (R$)", min_value=0.0, value=3000.0)
margem_lucro = st.number_input("Margem de lucro (%)", min_value=0.0, value=20.0) / 100

atividade = st.selectbox("Tipo de atividade", ["Serviço", "Comércio", "Indústria"])

rbt12 = faturamento_mensal * 12
fator_r = folha / faturamento_mensal if faturamento_mensal > 0 else 0

# ----------------------------
# TABELAS SIMPLES
# ----------------------------
def tabela_anexo_I(rbt12):
    if rbt12 <= 180000: return 0.04, 0
    elif rbt12 <= 360000: return 0.073, 5940
    elif rbt12 <= 720000: return 0.095, 13860
    elif rbt12 <= 1800000: return 0.107, 22500
    elif rbt12 <= 3600000: return 0.143, 87300
    else: return 0.19, 378000

def tabela_anexo_II(rbt12):
    if rbt12 <= 180000: return 0.045, 0
    elif rbt12 <= 360000: return 0.078, 5940
    elif rbt12 <= 720000: return 0.10, 13860
    elif rbt12 <= 1800000: return 0.112, 22500
    elif rbt12 <= 3600000: return 0.147, 85500
    else: return 0.30, 720000

def tabela_anexo_III(rbt12):
    if rbt12 <= 180000: return 0.06, 0
    elif rbt12 <= 360000: return 0.112, 9360
    elif rbt12 <= 720000: return 0.135, 17640
    elif rbt12 <= 1800000: return 0.16, 35640
    elif rbt12 <= 3600000: return 0.21, 125640
    else: return 0.33, 648000

def tabela_anexo_V(rbt12):
    if rbt12 <= 180000: return 0.155, 0
    elif rbt12 <= 360000: return 0.18, 4500
    elif rbt12 <= 720000: return 0.195, 9900
    elif rbt12 <= 1800000: return 0.205, 17100
    elif rbt12 <= 3600000: return 0.23, 62100
    else: return 0.305, 540000

# ----------------------------
# SIMPLES
# ----------------------------
if atividade == "Serviço":
    if fator_r >= 0.28:
        anexo = "Anexo III"
        aliquota, deducao = tabela_anexo_III(rbt12)
    else:
        anexo = "Anexo V"
        aliquota, deducao = tabela_anexo_V(rbt12)
elif atividade == "Comércio":
    anexo = "Anexo I"
    aliquota, deducao = tabela_anexo_I(rbt12)
else:
    anexo = "Anexo II"
    aliquota, deducao = tabela_anexo_II(rbt12)

aliquota_efetiva = ((rbt12 * aliquota) - deducao) / rbt12
imposto_simples = faturamento_mensal * aliquota_efetiva

# ----------------------------
# LUCRO PRESUMIDO
# ----------------------------
if atividade == "Serviço":
    presuncao = 0.32
    iss = faturamento_mensal * 0.05
else:
    presuncao = 0.08
    iss = 0

base = faturamento_mensal * presuncao
imposto_lp = base*0.15 + base*0.09 + faturamento_mensal*0.0065 + faturamento_mensal*0.03 + iss

# ----------------------------
# LUCRO REAL
# ----------------------------
lucro = faturamento_mensal * margem_lucro

irpj_lr = lucro * 0.15
if lucro > 20000:
    irpj_lr += (lucro - 20000) * 0.10

imposto_lr = irpj_lr + (lucro*0.09) + (faturamento_mensal*0.0165) + (faturamento_mensal*0.076)

# ----------------------------
# RESULTADO
# ----------------------------
st.subheader("Resultado")

st.write(f"Fator R: {fator_r:.2%}")
st.write(f"Anexo: {anexo}")
st.write(f"Alíquota efetiva: {aliquota_efetiva:.2%}")

st.write(f"Simples: R$ {imposto_simples:,.2f}")
st.write(f"Presumido: R$ {imposto_lp:,.2f}")
st.write(f"Lucro Real: R$ {imposto_lr:,.2f}")

# Melhor opção
menor = min(imposto_simples, imposto_lp, imposto_lr)

if menor == imposto_simples:
    melhor = "Simples Nacional"
elif menor == imposto_lp:
    melhor = "Lucro Presumido"
else:
    melhor = "Lucro Real"

st.success(f"Melhor opção: {melhor}")

# ----------------------------
# GERAR PDF
# ----------------------------
def gerar_pdf():
    doc = SimpleDocTemplate("relatorio_tributario.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Diagnóstico Tributário", styles["Title"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Faturamento: R$ {faturamento_mensal:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Atividade: {atividade}", styles["Normal"]))
    elementos.append(Paragraph(f"Fator R: {fator_r:.2%}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Simples Nacional: R$ {imposto_simples:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Lucro Presumido: R$ {imposto_lp:,.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"Lucro Real: R$ {imposto_lr:,.2f}", styles["Normal"]))
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph(f"Melhor opção: {melhor}", styles["Normal"]))

    doc.build(elementos)

# Botão
if st.button("📄 Gerar Relatório em PDF"):
    gerar_pdf()
    with open("relatorio_tributario.pdf", "rb") as file:
        st.download_button("⬇️ Baixar PDF", file, file_name="relatorio_tributario.pdf")