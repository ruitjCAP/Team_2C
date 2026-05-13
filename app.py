import streamlit as st
from datetime import datetime

st.set_page_config(page_title="AI Trace", page_icon="📂", layout="centered")

st.title("AI Trace - Compliance Alignment Review")

with st.form("submission_form"):
    st.subheader("Informação do caso")
    case_title = st.text_input("Título do caso *")
    
    case_description = st.text_area("Descrição", height=120)

    st.subheader("Upload de ficheiros")

    proposed_file = st.file_uploader(
        "Ficheiro do processo proposto *",
        type=["bpmn", "xml", "pdf", "docx", "txt"],
    )
    support_files = st.file_uploader(
        "Documentos de suporte",
        type=["pdf", "docx", "xlsx", "xls", "csv", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    submitted = st.form_submit_button("Submeter")

if submitted:
    errors = []
    if not case_title.strip():
        errors.append("O título do caso é obrigatório.")

    if proposed_file is None:
        errors.append("O ficheiro do processo proposto é obrigatório.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        submission_id = datetime.now().strftime("SUB-%Y%m%d-%H%M%S")

        st.success("Submissão criada com sucesso.")
        st.code(submission_id, language="text")

        st.markdown("### Resumo da submissão")
        st.write(f"**Título do caso:** {case_title}")
        
        st.write(f"**Descrição:** {case_description or '-'}")
        
        st.write(f"**Processo proposto:** {proposed_file.name}")

        if support_files:
            st.write("**Documentos de suporte:**")
            for file in support_files:
                st.write(f"- {file.name}")
        else:
            st.write("**Documentos de suporte:** -")

st.markdown("---")
st.caption("Protótipo básico da Submission Layer em Streamlit.")