from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from save_trace import save_trace
from Client.llmClient import create_llm
from tools.signatures import (
    inspect_process,
    retrieve_legal_framework,
    extract_compliance_requirements,
    assess_process_against_requirements,
    generate_compliance_report,
    summarize_process_for_analysis
)
import warnings

from langgraph.graph import StateGraph, START, END

from typing import Optional
from typing_extensions import TypedDict



warnings.filterwarnings("ignore")

tools = [summarize_process_for_analysis,
    inspect_process,
    retrieve_legal_framework,
    extract_compliance_requirements,
    assess_process_against_requirements,
    generate_compliance_report,
]

llm = create_llm()
llm_with_tools = llm.bind_tools(tools)


SYSTEM_PROMPT = """
You are an autonomous compliance-checking agent.

Use tools to investigate compliance:
1. inspect_process
2. retrieve_legal_framework
3. extract_compliance_requirements
4. assess_process_against_requirements
5. generate_compliance_report
6. summarize_process_for_analysis


Start by making the summarization of the process to have the better context of it.
Then make the relevant use of tools to make inference and extract key information.
Do not output fake TOOL_CALL text.
Use actual tool calls only.
Do not invent legal requirements.
If process evidence is missing, say Missing or Unknown.
"""



class ComplianceState(TypedDict):
    user_question: str
    process_summary: Optional[str]
    legal_framework: Optional[str]
    compliance_requirements: Optional[str]
    compliance_assessment: Optional[str]
    final_report: Optional[str]


def summarize_node(state: ComplianceState):
    summary = summarize_process_for_analysis.invoke(
        {
            "focus": "full_process_context",
            "include_precedences": True,
            "include_decision_paths": True,
            "include_context": True,
            "output_style": "analysis_ready_summary",
        }
    )

    return {
        "process_summary": summary
    }

def retrieve_legal_node(state: ComplianceState):
    process_summary = state["process_summary"]
    user_question = state["user_question"]

    legal_framework = retrieve_legal_framework.invoke(
        {
            "process_summary": process_summary,
            "user_question": user_question,
            "query": (
                "Retrieve legal and regulatory requirements based on the actual process order. "
                "Focus on prerequisite checks, due diligence before onboarding, KYC/AML, "
                "identity verification before customer acceptance, risk assessment before activation, "
                "approval before service provision, and GDPR obligations during data collection."
            ),
        }
    )

    return {
        "legal_framework": legal_framework
    }

def extract_requirements_node(state: ComplianceState):
    requirements = extract_compliance_requirements.invoke(
        {
            "legal_framework": state["legal_framework"],
            "process_summary": state["process_summary"],
        }
    )

    return {
        "compliance_requirements": requirements
    }

def assess_node(state: ComplianceState):
    assessment = assess_process_against_requirements.invoke(
        {
            "process_summary": state["process_summary"],
            "legal_framework": state["legal_framework"],
            "requirements": state["compliance_requirements"],
            "focus": (
                "Assess the process itself, especially task order, precedences, "
                "due diligence before onboarding, controls before activation, "
                "evidence, missing steps, and compliance gaps."
            ),
        }
    )

    return {
        "compliance_assessment": assessment
    }

def report_node(state: ComplianceState):
    report = generate_compliance_report.invoke(
        {
            "assessment": state["compliance_assessment"],
            "audience": "business, compliance, and process stakeholders",
        }
    )

    return {
        "final_report": report
    }



def build_compliance_graph():
    graph = StateGraph(ComplianceState)

    graph.add_node("summarize_process", summarize_node)
    graph.add_node("retrieve_legal_framework", retrieve_legal_node)
    graph.add_node("extract_requirements", extract_requirements_node)
    graph.add_node("assess_process", assess_node)
    graph.add_node("generate_report", report_node)

    graph.add_edge(START, "summarize_process")
    graph.add_edge("summarize_process", "retrieve_legal_framework")
    graph.add_edge("retrieve_legal_framework", "extract_requirements")
    graph.add_edge("extract_requirements", "assess_process")
    graph.add_edge("assess_process", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()



def assistant_node(state: MessagesState):
    messages = state["messages"]

    response = llm_with_tools.invoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + messages
    )

    return {"messages": [response]}


def build_graph():
    graph_builder = StateGraph(MessagesState)

    graph_builder.add_node("assistant", assistant_node)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "assistant")

    graph_builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )

    graph_builder.add_edge("tools", "assistant")

    graph = graph_builder.compile()

    return graph
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

def print_stream2(stream, max_chars=2500):
    """
    Pretty print LangGraph stream output for ComplianceState graphs.

    Works with stream_mode='values', where each event is the full current state.
    Prints only fields that changed since the previous event.
    """

    previous_state = {}

    for step_number, state in enumerate(stream, start=1):
        print("\n" + "=" * 100)
        print(f"GRAPH STEP {step_number}")
        print("=" * 100)

        if not isinstance(state, dict):
            print(state)
            continue

        changed_keys = []

        for key, value in state.items():
            previous_value = previous_state.get(key)

            if value is not None and value != previous_value:
                changed_keys.append(key)

        if not changed_keys:
            print("No visible state changes.")
        else:
            for key in changed_keys:
                value = state[key]

                print("\n" + "-" * 100)
                print(f"UPDATED FIELD: {key}")
                print("-" * 100)

                if isinstance(value, str):
                    if len(value) > max_chars:
                        print(value)
                        
                    else:
                        print(value)
                    
                elif isinstance(value, list):
                    for item in value:
                        if hasattr(item, "pretty_print"):
                            item.pretty_print()
                        else:
                            print(item)

                elif isinstance(value, dict):
                    import json
                    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))

                else:
                    print(value)
                if key == 'final_report':
                    return value

        previous_state = dict(state)
if __name__ == "__main__":
    graph = build_compliance_graph()

    print_stream2(graph.stream(
        {

            "user_question": "Is my process compliant?"
        },stream_mode="values"
    ))
    
    #print(result["messages"][-1].content)


