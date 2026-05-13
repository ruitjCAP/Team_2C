
import json
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_ibm import ChatWatsonx
from langchain_core.tools import tool
import os
from dotenv import load_dotenv
from pathlib import Path
import DB.question as q
load_dotenv()

PROCESS_PATH = "./json_processed/bpmn_analytics.json"


import json
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from Client.llmClient import create_llm



class ProcessSummarizationInput(BaseModel):


    focus: Optional[str] = Field(
        default="full_process_context",
        description=(
            "Specific summarization focus. Examples: 'full_process_context', "
            "'task_order', 'precedence_relationships', 'decision_paths', "
            "'actors_and_responsibilities', 'data_flow', 'controls', "
            "'exceptions', 'compliance_context'."
        ),
    )

    include_precedences: bool = Field(
        default=True,
        description=(
            "Whether to explicitly describe which process steps happen before "
            "and after each other."
        ),
    )

    include_decision_paths: bool = Field(
        default=True,
        description=(
            "Whether to include gateways, branching logic, alternative paths, "
            "conditions, and exceptions."
        ),
    )

    include_context: bool = Field(
        default=True,
        description=(
            "Whether to include relevant context such as actors, systems, data objects, "
            "documents, controls, approvals, validations, and business meaning."
        ),
    )

    output_style: Optional[str] = Field(
        default="natural_language_structured",
        description=(
            "Desired summary style. Examples: 'natural_language_structured', "
            "'narrative', 'bullet_points', 'analysis_ready_summary'."
        ),
    )


@tool(args_schema=ProcessSummarizationInput)
def summarize_process_for_analysis(

    focus: Optional[str] = "full_process_context",
    include_precedences: bool = True,
    include_decision_paths: bool = True,
    include_context: bool = True,
    output_style: Optional[str] = "natural_language_structured",
) -> str:
    """
    Summarize a BPMN process in natural language for downstream analysis.

    Use this tool before compliance, legal, risk, or operational analysis.

    The summary should describe the actual process using human-readable names,
    not technical BPMN IDs. It should explain the order between steps,
    precedence relationships, decision paths, actors, tasks, data usage,
    controls, and missing context.
    """

    with open(PROCESS_PATH, encoding="utf-8") as f:
        process_data = json.load(f)

    llm = create_llm()

    prompt = f"""
You are a BPMN process analyst.

Your task is to transform the BPMN JSON into a natural-language summary that another LLM can use for deeper compliance, legal, risk, or operational analysis.

The summary must focus on the process itself.

Important instructions:
- Do not expose technical BPMN IDs.
- Do not refer to elements by internal identifiers.
- Use the actual human-readable names of tasks, events, gateways, data objects, lanes, pools, actors, and systems.
- If an element has no clear name, describe it naturally based on its type and surrounding context.
- Preserve the real order of the process.
- Explain which steps happen before and after other steps.
- Explain precedence relationships.
- Explain dependencies between activities.
- Include all relevant context that would help later analysis.
- Do not perform legal compliance analysis yet.
- Do not invent missing process information.
- If information is missing, say "Not specified in the process model".

Summarization focus:
{focus}

Include precedence relationships:
{include_precedences}

Include decision paths:
{include_decision_paths}

Include broader process context:
{include_context}

Output style:
{output_style}

BPMN process JSON:
{json.dumps(process_data, indent=2, ensure_ascii=False)}

Return the summary using this structure:

1. Process overview
   - Briefly explain what the process appears to do.
   - Mention the business purpose if inferable from the model.

2. Main process flow in natural order
   - Describe the process from start to end.
   - Use the actual step names, not IDs.
   - Explain the order between steps.
   - Use language like:
     "The process starts with..."
     "After that..."
     "Before this can happen..."
     "This step depends on..."
     "The process then continues to..."

3. Ordered step-by-step narrative
   For each relevant step, include:
   - Step name
   - What happens in the step
   - Who or what performs it, if known
   - What must happen before it
   - What happens after it
   - Inputs or data used
   - Outputs or data produced
   - Relevant controls, approvals, validations, or checks

4. Precedence and dependency summary
   - Explain important before/after relationships.
   - Identify tasks that depend on previous approvals, data collection, validations, or decisions.
   - Identify any parallel or alternative paths if present.

5. Decision points and alternative paths
   - Describe gateways and branching logic using natural language.
   - Explain what causes the process to follow each path.
   - Mention exception paths, rework loops, rejection flows, or escalation paths if present.

6. Actors, roles, systems, and responsibilities
   - Summarize who participates in the process.
   - Include lanes, pools, users, departments, systems, or external parties if present.
   - Describe handoffs between actors or systems.

7. Data, documents, and records used
   - Summarize data objects, data stores, documents, forms, records, or messages.
   - Explain where data is created, read, updated, transferred, approved, archived, or deleted if visible.

8. Controls and compliance-relevant context
   - Identify approvals, validations, audit logs, monitoring, segregation of duties, manual checks, automated checks, and review steps.
   - Do not judge compliance yet.
   - Only describe what the process model shows.

9. Missing or unclear process information
   - List relevant missing information that would affect later analysis.
   - Examples: unclear actor, missing data retention, missing approval criteria, missing exception handling, unclear data object, missing audit trail.

10. Analysis-ready condensed summary
   - Provide a concise paragraph that another LLM can use directly for legal, compliance, risk, or operational analysis.
   - This paragraph should mention the process purpose, key steps in order, actors, data handled, decision points, controls, and missing information.

Remember:
- Use natural language.
- Prefer actual element names.
- Avoid technical IDs completely.
- Do not make compliance conclusions.
"""

    response = llm.invoke(prompt)
    return response.content



class InspectProcessInput(BaseModel):
    focus: Optional[str] = Field(
        default="process_overview",
        description=(
            "Main inspection focus for the BPMN process. "
            "Use this to specify what part of the process should be analyzed, such as "
            "'process_overview', 'tasks', 'user_tasks', 'service_tasks', 'manual_tasks', "
            "'gateways', 'events', 'sequence_flows', 'actors_roles', 'data_objects', "
            "'systems', 'handoffs', 'controls', 'exceptions', 'risks', or 'compliance_gaps'. "
            "If no focus is provided, inspect the overall process structure first."
        ),
    )


@tool(args_schema=InspectProcessInput)
def inspect_process(focus: Optional[str] = None) -> str:
    """
    Inspect the BPMN process JSON and return a concise, compliance-oriented summary.
    Use this tool before assessing compliance, especially to understand tasks,
    actors, data objects, decisions, approvals, risks, controls, and missing evidence.
    """

    with open(PROCESS_PATH, encoding="utf-8") as f:
        process_data = json.load(f)

    llm = ChatWatsonx(
        model_id="meta-llama/llama-3-3-70b-instruct",
        url=os.getenv("WATSON_ENDPOINT"),
        apikey=os.getenv("WATSON_API_KEY"),
        project_id=os.getenv("WATSON_PROJECT_ID"),
        params={
            "temperature": 0.9,
            "max_tokens": 1500,
        },
    )

    prompt = f"""
    You are analyzing a BPMN process JSON for compliance.

    Focus:
    {focus or "General compliance analysis"}

    Process JSON:
    {json.dumps(process_data, indent=2, ensure_ascii=False)}

    Return:
    1. Process purpose
    2. Main actors or roles
    3. Main activities
    4. Data handled
    5. Decisions/gateways
    6. Existing controls
    7. Possible compliance-relevant gaps
    8. Short process summary for legal retrieval
    """

    response = llm.invoke(prompt)
    return response.content


class LegalRetrievalInput(BaseModel):
    
    process_summary: str = Field(
            description=(
                "Natural-language summary of the BPMN process, including ordered steps, "
                "precedence relationships, actors, data, controls, decisions, and missing information."
            )
        )

    query: str = Field(
        description="Search query for retrieving legal, regulatory, policy, or compliance requirements."
    )



@tool(args_schema=LegalRetrievalInput)
def retrieve_legal_framework(
    process_summary: str,
    query: str,

) -> str:
    """
    Retrieve legal and regulatory context relevant to a compliance question.
    Use this whenever legal obligations, regulatory requirements, controls,
    or compliance rules are needed.
    
    """

    retrieval_query = f"""
    Retrieve legal and regulatory requirements relevant to the following compliance analysis.

    This is the summary:
    {process_summary}

    Query:
    {query}

    Jurisdiction:
    EU



    Return obligations, controls, risks, articles, and requirements where available.
    """

    llm = create_llm()

    retrieval = llm.invoke(
        " Resume this prompt for a vector database:\n" + retrieval_query
    )

    return q.rag(retrieval.content)


class RequirementExtractionInput(BaseModel):
    legal_framework: str = Field(
        description="Retrieved legal or regulatory framework text."
    )
    process_summary: Optional[str] = Field(
        default=None,
        description="Summary of the process being checked."
    )


@tool(args_schema=RequirementExtractionInput)
def extract_compliance_requirements(
    legal_framework: str,
    process_summary: Optional[str] = None,
) -> str:
    """
    Extract concrete compliance requirements from legal framework text.
    Use this after retrieving legal context and before assessing the BPMN process.
    """

    llm = ChatWatsonx(
        model_id="meta-llama/llama-3-3-70b-instruct",
        url=os.getenv("WATSON_ENDPOINT"),
        apikey=os.getenv("WATSON_API_KEY"),
        project_id=os.getenv("WATSON_PROJECT_ID"),
        params={
            "temperature": 0.9,
            "max_tokens": 1500,
        },
    )


    prompt = f"""
You are a compliance analyst.

Extract concrete, checkable requirements from the legal framework.

Process summary:
{process_summary or "No process summary provided."}

Legal framework:
{legal_framework}

Return a numbered list of requirements.

For each requirement include:
- requirement_id
- legal_basis
- obligation
- evidence_needed_from_process
- risk_if_missing

Do not invent requirements.
If the legal framework is vague, say so.
"""

    response = llm.invoke(prompt)
    return response.content


class ComplianceAssessmentInput(BaseModel):
    requirements: str = Field(
        description="Concrete compliance requirements to check."
    )
    legal_framework: str = Field(
        description="Legal/regulatory context used for the assessment."
    )
    focus: Optional[str] = Field(
        default=None,
        description="Specific compliance focus, if any."
    )


@tool(args_schema=ComplianceAssessmentInput)
def assess_process_against_requirements(
    requirements: str,
    legal_framework: str,
    focus: Optional[str] = None,
) -> str:
    """
    Assess the BPMN process JSON against concrete compliance requirements.
    Use this after requirements have been extracted.
    """

    with open(PROCESS_PATH, encoding="utf-8") as f:
        process_data = json.load(f)

    llm = ChatWatsonx(
        model_id="meta-llama/llama-3-3-70b-instruct",
        url=os.getenv("WATSON_ENDPOINT"),
        apikey=os.getenv("WATSON_API_KEY"),
        project_id=os.getenv("WATSON_PROJECT_ID"),
        params={
            "temperature": 0.9,
            "max_tokens": 1500,
        },
    )

    prompt = f"""
You are a compliance auditor.

Assess the BPMN process against the compliance requirements.

Focus:
{focus or "Full compliance assessment"}

Legal framework:
{legal_framework}

Compliance requirements:
{requirements}

Process JSON:
{json.dumps(process_data, indent=2, ensure_ascii=False)}

Rules:
- Use only the provided legal framework and requirements.
- Do not invent laws.
- Use evidence from the process JSON.
- If evidence is missing, mark the requirement as Unknown or Non-compliant.
- Be strict but fair.
- Do not output fake TOOL_CALL text.

Return findings in this structure:

Overall status:
Compliant / Partially compliant / Non-compliant / Unknown

Findings:
For each requirement:
- Requirement ID
- Legal basis article (not the name of the pdf file)
- Status
- Evidence from process
- Gap
- Risk level
- Recommendation
"""

    response = llm.invoke(prompt)
    return response.content


class ReportGenerationInput(BaseModel):
    assessment: str = Field(
        description="Detailed compliance assessment findings."
    )
    audience: Optional[str] = Field(
        default="business and compliance stakeholders",
        description="Target audience for the report."
    )


@tool(args_schema=ReportGenerationInput)
def generate_compliance_report(
    assessment: str,
    audience: Optional[str] = "business and compliance stakeholders",
) -> str:
    """
    Generate a final compliance report from assessment findings.
    Use this as the last step before answering the user.
    """

    llm = ChatWatsonx(
        model_id="meta-llama/llama-3-3-70b-instruct",
        url=os.getenv("WATSON_ENDPOINT"),
        apikey=os.getenv("WATSON_API_KEY"),
        project_id=os.getenv("WATSON_PROJECT_ID"),
        params={
            "temperature": 0.9,
            "max_tokens": 1500,
        },
    )

    prompt = f"""
You are preparing a final compliance report for {audience}.

Assessment findings:
{assessment}

Never mention the JSON file, if you talk about Requirements in the report explicitly explain those requirements
Create a clear final report with:

1. Executive summary
2. Overall compliance status
3. Key compliant areas
4. Key gaps
5. Risk rating
6. Prioritized recommendations
7. Information missing from the BPMN/process model
8. Suggested next steps
9. Relevant regulation

Keep it practical and concise.
"""

    response = llm.invoke(prompt)
    return response.content