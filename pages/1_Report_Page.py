
import streamlit as st

st.set_page_config(
    page_title="Relatório",
    page_icon="📊",
    layout="wide"
)


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

def risk_class(risk: str) -> str:
    r = (risk or "").upper()
    if "ALTO" in r:
        return "risk-high"
    if "MÉDIO" in r or "MEDIO" in r:
        return "risk-med"
    if "BAIXO" in r:
        return "risk-low"
    return "risk-unk"
 
st.markdown("""
<style>
.st-key-report_wrapper_low {
    border: 2px solid #22c55e;
    border-radius: 18px;
    padding: 18px;
    background-color: #f0fdf4;
}

.st-key-report_wrapper_default {
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 18px;
    background-color: #ffffff;
}

.st-key-report_wrapper_high {
    border: 1px solid #e5e7eb;
    border-radius: 22px;
    padding: 22px;
    margin-top: 18px;
    background-color: #fef2f2;
    box-shadow: 0 0 0 3px rgba(255,0, 0, 0.4);
}
.report-header {
    background: linear-gradient(90deg, #0b2d4a, #0f3a60);
    padding: 12px 14px;
    border-radius: 12px;
    color: white;
    font-weight: 900;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)


def is_low_risk(value: str) -> bool:
    return str(value).strip().lower() == "baixo"

def is_high_risk(value: str) -> bool:
    return str(value).strip().lower() == "alto"

def render_report_page(report: dict):
    
    resumo = report.get("resumo_do_caso", {}) or {}
    avaliacao = report.get("avaliacao_de_conformidade", {}) or {}
 
    tipo = resumo.get("tipo", "Unknown")
    risco = resumo.get("risco_preliminar", "Unknown")
    regs = resumo.get("regulamentacao_potencialmente_aplicavel", []) or []
    wrapper_key = "report_wrapper_low" if is_low_risk(risco) else "report_wrapper_high" if is_high_risk(risco) else "report_wrapper_default"



    st.markdown('<div class="report-header">RELATÓRIO DE AVALIAÇÃO </div>', unsafe_allow_html=True)
    

    with st.container(key=wrapper_key):

        # Resumo do caso
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📌 Resumo do caso</div>', unsafe_allow_html=True)
    
        
    
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






if "report" not in st.session_state:
    st.warning("Nenhum relatório encontrado. Volta à página inicial e submete um caso.")
    if st.button("⬅️ Voltar"):
        st.switch_page("app.py")
else:
    #st.title(st.session_state.get("case_title", "Relatório"))
    render_report_page(st.session_state.report)

    if st.button("⬅️ Voltar à submissão"):
        st.switch_page("Submit_Page.py")
