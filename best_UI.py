import os
import json
import glob
from datetime import datetime
import streamlit as st
from  processing import processBPMN as BPMN
from reasoning_LangGraph import build_compliance_graph,print_stream2
import tempfile
from dotenv import load_dotenv

PROCESS_PATH = "./json_processed/bpmn_analytics.json"
# Load env vars
load_dotenv()
# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Relatório de Avaliação – One-Shot Solution",
    page_icon="📄",
    initial_sidebar_state="expanded",
    layout="wide"
)
 
# DEBUG: garante que algo aparece
st.write("✅ APP A CORRER")
 
# =========================
# Paths / helpers
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
 
def list_reports(pattern: str):
    return sorted(glob.glob(os.path.join(REPORTS_DIR, pattern)), reverse=True)
 
def latest_report_path():
    reports = list_reports("compliance_report_*.json")
    return reports[0] if reports else None
 
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
 
def nice_name(path: str):
    name = os.path.basename(path)
    parts = name.replace(".json", "").split("_")
    if len(parts) >= 3:
        try:
            dt = datetime.strptime(parts[-2] + "_" + parts[-1], "%Y%m%d_%H%M%S")
            return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} — {name}"
        except Exception:
            return name
    return name
 
def risk_class(risk: str) -> str:
    r = (risk or "").upper()
    if "ALTO" in r:
        return "risk-high"
    if "MÉDIO" in r or "MEDIO" in r:
        return "risk-med"
    if "BAIXO" in r:
        return "risk-low"
    return "risk-unk"
 
def run_analysis(question_text: str) -> str:
    # IMPORT LAZY para evitar “white page” por bloqueio no import
    from llm_call import ask_agent
    return ask_agent(question_text)
 

def render_report(report: dict):
    resumo = report.get("resumo_do_caso", {}) or {}
    avaliacao = report.get("avaliacao_de_conformidade", {}) or {}
 
    st.markdown('<div class="report-header">RELATÓRIO DE AVALIAÇÃO </div>', unsafe_allow_html=True)
 
    # Resumo do caso
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📌 Resumo do caso</div>', unsafe_allow_html=True)
 
    tipo = resumo.get("tipo", "Unknown")
    risco = resumo.get("risco_preliminar", "Unknown")
    regs = resumo.get("regulamentacao_potencialmente_aplicavel", []) or []
 
    st.markdown(
        f"""
        <div class="kv"><div class="kv-label">Tipo:</div><div class="kv-value">{tipo}</div></div>
        <div class="kv"><div class="kv-label">Risco Preliminar:</div><div class="badge {risk_class(risco)}">{risco}</div></div>
        <div class="kv"><div class="kv-label">Regulamentação Potencialmente Aplicável:</div></div>
        """,
        unsafe_allow_html=True
    )
    for r in regs:
        st.markdown(f'<span class="chip">✅ {r}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
 
    # Áreas de Controlo
    areas = resumo.get("areas_de_controlo_impactadas", []) or []
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🛡️ Áreas de Controlo Impactadas</div>', unsafe_allow_html=True)
    if areas:
        for a in areas:
            st.markdown(f'<span class="chip">🟢 {a}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-item">✅ Nenhuma área indicada.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
 
    # Red Flags
    flags = resumo.get("red_flags_identificadas", []) or []
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🚩 Red Flags Identificadas</div>', unsafe_allow_html=True)
    if flags:
        for f in flags:
            st.markdown(f'<div class="flag-item">❗ {f}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-item">✅ Nenhuma red flag identificada.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
 
    # Avaliação
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📌 Avaliação de Conformidade</div>', unsafe_allow_html=True)
 
    estado = avaliacao.get("estado_geral", "Unknown")
    nivel_risco = avaliacao.get("nivel_de_risco", "Unknown")
 
    st.markdown(
        f"""
        <div class="kv"><div class="kv-label">Estado Geral:</div><div class="kv-value">{estado}</div></div>
        <div class="kv"><div class="kv-label">Nível de Risco:</div><div class="badge {risk_class(nivel_risco)}">{nivel_risco}</div></div>
        """,
        unsafe_allow_html=True
    )
 
    with st.expander("📚 Requisitos relevantes"):
        items = avaliacao.get("requisitos_relevantes") or []
        st.write("\n".join([f"- {x}" for x in items]) if items else "Unknown")
 
    with st.expander("🔎 Evidência no processo"):
        items = avaliacao.get("evidencia_no_processo") or []
        st.write("\n".join([f"- {x}" for x in items]) if items else "Unknown")
 
    with st.expander("🧩 Gaps / Lacunas"):
        items = avaliacao.get("gaps") or []
        st.write("\n".join([f"- {x}" for x in items]) if items else "Unknown")
 
    with st.expander("✅ Recomendações"):
        items = avaliacao.get("recomendacoes") or []
        st.write("\n".join([f"- {x}" for x in items]) if items else "Unknown")
 
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# Custom CSS
# =========================
st.markdown(
    """
    <style>
        .main { background-color: #f6f8fb; }
        .block-container { padding-top: 1.6rem; max-width: 1200px; }
 
        [data-testid="stSidebar"] { background-color: #0b1220; }
        [data-testid="stSidebar"] * { color: white; }
        .sidebar-box {
            background: rgba(255,255,255,0.08);
            padding: 1rem; border-radius: 16px; margin-bottom: 1rem;
        }
        .small-muted { color: #9ca3af; font-size: 0.85rem; }
 
        .hero {
            background: linear-gradient(135deg, #0b2d4a 0%, #0f3a60 55%, #1d4ed8 100%);
            padding: 1.6rem 1.8rem; border-radius: 18px; color: white;
            margin-bottom: 1.2rem;
            box-shadow: 0 12px 30px rgba(15, 58, 96, 0.18);
        }
        .hero h1 { font-size: 1.65rem; margin: 0 0 .35rem 0; font-weight: 900; }
        .hero p { margin:0; opacity:.95; }
 
        .report-header {
            background: linear-gradient(90deg, #0b2d4a, #0f3a60);
            padding: 12px 14px; border-radius: 12px;
            color: white; font-weight: 900; letter-spacing: .3px;
            margin: .2rem 0 1rem 0;
        }
 
        .section-card {
            background: white;
            padding: 1rem 1.1rem;
            border-radius: 16px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }
        .section-title {
            font-size: 1.05rem;
            font-weight: 900;
            color: #111827;
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .kv { display:flex; align-items:center; gap:10px; margin: 8px 0; }
        .kv-label { color:#6b7280; font-weight:800; min-width: 160px; }
        .kv-value { color:#111827; font-weight:800; }
 
        .chip {
            display:inline-flex; align-items:center; gap:6px;
            padding: 5px 10px;
            border-radius: 999px;
            margin: 4px 8px 0 0;
            font-size: 12px;
            border: 1px solid #d7e3ef;
            background: #f6fbff;
            color: #0f3a60;
            font-weight: 900;
        }
 
        .badge {
            display:inline-flex;
            align-items:center;
            padding: 5px 12px;
            border-radius: 999px;
            font-weight: 900;
            font-size: 12px;
            border: 1px solid transparent;
        }
        .risk-low  { background:#ecfdf5; color:#065f46; border-color:#a7f3d0; }
        .risk-med  { background:#fff7e6; color:#92400e; border-color:#fde68a; }
        .risk-high { background:#fdecec; color:#991b1b; border-color:#fecaca; }
        .risk-unk  { background:#f3f4f6; color:#374151; border-color:#e5e7eb; }
 
        .ok-item {
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid #d6efe0;
            background: #f2fff7;
            margin: 8px 0;
            font-weight: 800;
            color: #145a2a;
        }
        .flag-item {
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid #f0d6d6;
            background: #fff4f4;
            margin: 8px 0;
            font-weight: 900;
            color: #7a1b1b;
        }
 
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            border: none;
            border-radius: 14px;
            padding: 0.75rem 1.2rem;
            font-weight: 900;
            width: 100%;
            transition: 0.2s ease;
        }
    </style>
    """,
    unsafe_allow_html=True
)
 
# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("## 📄 AI TRACE")
    st.markdown(
        """
        <div class="sidebar-box">
            <strong>Estado</strong><br>
            <span class="small-muted">Gerar e consultar relatórios de avaliação.</span>
        </div>
        """,
        unsafe_allow_html=True
    )
 
    st.markdown("### Ações")
    generate_now = st.button("⚡ Gerar novo relatório")
    st.markdown("---")
 
    st.markdown("### Relatórios guardados")
    report_choice = None
    if os.path.exists(REPORTS_DIR):
        existing = list_reports("compliance_report_*.json")
        if existing:
            report_choice = st.selectbox("Selecionar", existing, format_func=nice_name)
        else:
            st.caption("Ainda não existem relatórios em ./reports")
    else:
        st.caption("A pasta ./reports ainda não existe.")
 
# =========================
# Hero
# =========================
st.markdown(
    """
    <div class="hero">
        <h1> Compliance Alignment Review </h1>
        <p> Geração automática de relatório a partir do produzido pelo LLM.</p>
    </div>
    """,
    unsafe_allow_html=True
)
 
# =========================
# Form
# =========================
with st.form("submission_form", clear_on_submit=False):
    col1, col2 = st.columns([1.15, 0.85], gap="large")
    with col1:
        st.markdown("### Informação do caso")
        case_title = st.text_input("Título do caso *", placeholder="Ex.: Simplificação do processo de onboarding")
        case_description = st.text_area("Descrição", placeholder="Contexto / objetivo / notas...", height=140)
        priority = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"], index=1)
 
    with col2:
        st.markdown("### Upload de ficheiros")
        proposed_file = st.file_uploader("Ficheiro do processo proposto *", type=["bpmn","xml","json","pdf","docx","txt"])
        support_files = st.file_uploader("Documentos de suporte", type=["pdf","docx","xlsx","csv","txt","png","jpg","jpeg"], accept_multiple_files=True)
 
    submitted = st.form_submit_button("✅ Submeter e gerar relatório")
 
# =========================
# Session state
# =========================
if "final_text" not in st.session_state:
    st.session_state.final_text = None
if "report_path" not in st.session_state:
    st.session_state.report_path = None
if "report" not in st.session_state:
    st.session_state.report=None
 
# Se escolheu na sidebar
if report_choice:
    st.session_state.report_path = report_choice
 
# Botão rápido
# if generate_now:
#     st.session_state.final_text = run_analysis("Is my process compliant?")
#     st.session_state.report_path = latest_report_path()
 
# Submit do form
if submitted:
    errors = []
    if not (case_title or "").strip():
        errors.append("O título do caso é obrigatório.")
    if proposed_file is None:
        errors.append("O ficheiro do processo proposto é obrigatório.")
    if errors:
        st.error("Existem campos obrigatórios por preencher.")
        for e in errors:
            st.warning(e)
    else:
        # RUN ANALYTICS LAYER
        #st.session_state.final_text = run_analysis(question)
        #st.session_state.report_path = latest_report_path()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(proposed_file.getbuffer())
                temp_path = tmp.name

        with st.spinner("A gerar relatório de compliance..."):
            BPMN.export_bpmn_analytics_json(temp_path,PROCESS_PATH)

            graph = build_compliance_graph()
            
            st.session_state.report = json.loads(print_stream2(graph.stream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Is my BPMN process is compliant regarding the order of each task?",
                        }
                    ],
                    "user_question": "Is my process compliant?"
                },stream_mode="values"
            )) )
            

        

 
# Mostrar resposta final e relatório
# if st.session_state.final_text:
#     st.markdown("### 🗣️ Resposta final (texto)")
#     st.write(st.session_state.final_text)
 
if st.session_state.report and submitted:
    try:
        
        render_report(st.session_state.report)
        st.caption(f"Relatório carregado de: {st.session_state.report_path}")
    except Exception as e:
        st.error("Não foi possível carregar/renderizar o relatório JSON.")
        st.exception(e)
else:
    st.info("Submete um caso, clica em 'Gerar novo relatório' ou seleciona um relatório na sidebar.")
 
st.markdown("---")
st.caption("AI TRACE · 2026")