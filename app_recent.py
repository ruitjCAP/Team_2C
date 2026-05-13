import streamlit as st
from datetime import datetime
from  processing import processBPMN as BPMN
from datetime import datetime
import tempfile
from reasoning_LangGraph import build_compliance_graph,print_stream2
from dotenv import load_dotenv
import os

# Load env vars
load_dotenv()
# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Compliance Alignment Review",
    page_icon="📂",
    initial_sidebar_state="expanded" 
    ,layout="wide"
)

# =========================
# Custom CSS
# =========================
st.markdown(
    """
    <style>
        .main {
            background-color: #f6f8fb;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1100px;
        }

        .hero {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            padding: 2.2rem;
            border-radius: 24px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 12px 30px rgba(37, 99, 235, 0.25);
        }

        .hero h1 {
            font-size: 2.4rem;
            margin-bottom: 0.4rem;
        }

        .hero p {
            font-size: 1.05rem;
            opacity: 0.95;
            margin-bottom: 0;
        }

        .section-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 20px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            margin-bottom: 1.2rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.3rem;
        }

        .section-subtitle {
            color: #6b7280;
            font-size: 0.95rem;
            margin-bottom: 1rem;
        }

        .required {
            color: #ef4444;
            font-weight: 700;
        }

        .success-card {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            color: #065f46;
            padding: 1.2rem;
            border-radius: 18px;
            margin-top: 1rem;
        }

        .summary-card {
            background-color: #00008B;
            border-radius: 20px;
            padding: 1.4rem;
            border: 1px solid #e5e7eb;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }

        .file-pill {
            display: inline-block;
            background: #eef2ff;
            color: #3730a3;
            padding: 0.35rem 0.7rem;
            margin: 0.2rem 0.2rem 0.2rem 0;
            border-radius: 999px;
            font-size: 0.9rem;
            font-weight: 500;
        }

        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            border: none;
            border-radius: 14px;
            padding: 0.75rem 1.2rem;
            font-weight: 700;
            width: 100%;
            transition: 0.2s ease;
        }

        div.stButton > button:first-child:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.25);
        }

        [data-testid="stSidebar"] {
            background-color: #111827;
        }

        [data-testid="stSidebar"] * {
            color: white;
        }

        .sidebar-box {
            background: rgba(255, 255, 255, 0.08);
            padding: 1rem;
            border-radius: 16px;
            margin-bottom: 1rem;
        }

        .small-muted {
            color: #9ca3af;
            font-size: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("## 📂 Compliance Alignment Review")
    st.markdown(
        """
        <div class="sidebar-box">
            <strong>Estado</strong><br>
            <span class="small-muted">Plataforma para submissão de casos.</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Checklist")
    st.markdown("- Título do caso")
    st.markdown("- Ficheiro do processo")
    st.markdown("- Documentos de suporte opcionais")
    st.markdown("---")
    st.caption("Versão beta · Streamlit")

# =========================
# Hero
# =========================
st.markdown(
    """
    <div class="hero">
        <h1>📂 Compliance Alignment Review</h1>
        <p>Submete ficheiros de processo e metadados básicos de forma simples, clara e organizada.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# Form
# =========================
with st.form("submission_form", clear_on_submit=False):
    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Informação do caso</div>
                <div class="section-subtitle">Preenche os dados principais da submissão.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        case_title = st.text_input(
            "Título do caso *",
            placeholder="Ex.: Otimização do processo de aprovação"
        )

        case_description = st.text_area(
            "Descrição",
            placeholder="Descreve brevemente o objetivo, contexto ou notas relevantes...",
            height=150
        )

        priority = st.selectbox(
            "Prioridade",
            ["Baixa", "Média", "Alta"],
            index=1
        )

    with col2:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Upload de ficheiros</div>
                <div class="section-subtitle">Adiciona o processo proposto e documentos adicionais.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        proposed_file = st.file_uploader(
            "Ficheiro do processo proposto *",
            type=["bpmn", "xml", "pdf", "docx", "txt"],
            help="Formatos aceites: BPMN, XML, PDF, DOCX, TXT"
        )

        support_files = st.file_uploader(
            "Documentos de suporte",
            type=["pdf", "docx", "xlsx", "xls", "csv", "txt", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Podes anexar vários documentos de suporte."
        )

        print(proposed_file)
        if proposed_file:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(proposed_file.getbuffer())
                temp_path = tmp.name
           

    st.markdown("")

    submitted = st.form_submit_button("Submeter caso")

# =========================
# Validation and result
# =========================
if submitted:
    errors = []

    if not case_title.strip():
        errors.append("O título do caso é obrigatório.")

    if proposed_file is None:
        errors.append("O ficheiro do processo proposto é obrigatório.")

    if errors:
        st.error("Existem campos obrigatórios por preencher.")
        for error in errors:
            st.warning(error)

    else:
        submission_id = datetime.now().strftime("SUB-%Y%m%d-%H%M%S")

        st.markdown(
            """
            <div class="success-card">
                <h3>✅ Submissão criada com sucesso</h3>
                <p>O caso foi registado e está pronto para análise.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### Identificador da submissão")
        st.code(submission_id, language="text")

        st.markdown("### Resumo da submissão")

        summary_col1, summary_col2 = st.columns(2, gap="large")

        with summary_col1:
            st.markdown(
                f"""
                <div class="summary-card">
                    <h4>📌 Dados do caso</h4>
                    <p><strong>Título:</strong><br>{case_title}</p>
                    <p><strong>Descrição:</strong><br>{case_description or '-'}</p>
                    <p><strong>Prioridade:</strong><br>{priority}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with summary_col2:
            support_files_html = ""

            if support_files:
                for file in support_files:
                    support_files_html += f'<span class="file-pill">📎 {file.name}</span>'
            else:
                support_files_html = "<p>-</p>"

            st.markdown(
                f"""
                <div class="summary-card">
                    <h4>📁 Ficheiros</h4>
                    <p><strong>Processo proposto:</strong><br>
                    <span class="file-pill">📄 {proposed_file.name}</span></p>

                    
                </div>
                """,
                unsafe_allow_html=True
            )
        
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"BPMN_Analytics_{timestamp}.json"

        BPMN.export_bpmn_analytics_json(temp_path,filename)

        graph = build_compliance_graph()
        os.putenv("JSON_FILE",filename)
        report = print_stream2(graph.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Is my BPMN process is compliant regarding the order of each task?",
                }
            ],
            "user_question": "Is my process compliant?"
        },stream_mode="values"
    ))
        os.remove(filename)

        st.markdown(
            f"""
            <div class="summary-card">
                <h4>📋 Relatório de Compliance BPMN</h4>
                    {report}
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================
# Footer
# =========================
st.markdown("---")
st.caption("AI TRACE · 2026")
