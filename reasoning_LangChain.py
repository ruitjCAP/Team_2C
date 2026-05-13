from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import ModelInference

import DB.question as q
import os
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
from langchain_core.tools import tool
import warnings
import json
from langchain_ibm import ChatWatsonx
warnings.filterwarnings("ignore")
load_dotenv()


model = ChatWatsonx(
        model_id="meta-llama/llama-3-3-70b-instruct",
        url=os.getenv("WATSON_ENDPOINT"),
        apikey=os.getenv("WATSON_API_KEY"),
        project_id=os.getenv("WATSON_PROJECT_ID"),
        params={
            "temperature": 0.9,
            "max_tokens": 1500,
        },
    )




def load_process(path="./json_processed/bpmn_analytics_dataStore.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
    


@tool
def compliance_check(question: str) -> str:
    """
    Check whether the BPMN business process is compliant with the relevant legal
    and regulatory framework.

    Use this tool when the user asks whether a process is compliant, non-compliant,
    risky, legally acceptable, or needs regulatory improvements.
    """

    process_data = load_process()

    retrieval_query = f"""
    Legal and regulatory requirements, obligations, controls, risks, and compliance rules
    relevant to the following process compliance question:

    {question}
    """

    

    legal_framework = q.rag(retrieval_query)

    print("LEGAL FRAMEWORK:")
    print(legal_framework)

    audit_prompt = f"""
        You are a compliance auditor.

        Check the business process against the legal framework.

        Rules:
        - Do not invent legal requirements.
        - Use only the provided legal framework.
        - Use evidence from the process JSON.
        - If information is missing, say "Unknown".
        - Be specific and practical.

        Legal framework:
        {legal_framework}

        Business process JSON:
        { process_data}

        Question:
        {question}

        Return a compliance report with:
        1. Overall compliance status
        2. Relevant legal requirements
        3. Evidence from the process
        4. Compliance gaps
        5. Risk level
        6. Recommendations
        """

    
    response = model.invoke(audit_prompt)

    return response.content


def ask_agent(user_question: str) -> str:

    

    tools = [compliance_check]
    tools_by_name = {tool.name: tool for tool in tools}

    # This gives the model knowledge of the available tool schema.
    llm_with_tools = model.bind_tools(tools)

    messages = [
        SystemMessage(
            content="""
            You are a compliance assistant.

            If the user asks about process compliance, use the compliance_check tool.
            After receiving the tool result, provide a clear final answer.

            Do not output fake TOOL_CALL text.
            Use actual tool calls only.
            """
        ),
        HumanMessage(content=user_question),
    ]

    first_response = llm_with_tools.invoke(messages)
    messages.append(first_response)

    # If the model requested tool calls, execute them.
    if first_response.tool_calls:
        for tool_call in first_response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            selected_tool = tools_by_name[tool_name]
            tool_result = selected_tool.invoke(tool_args)

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )

        # Ask the model for the final user-facing answer after tool execution.
        final_response = model.invoke(
            messages
            + [
                HumanMessage(
                    content="""
                    Using the tool result above, give the final compliance answer.
                    Do not call another tool.
                    Do not output TOOL_CALL.
                    """
                )
            ]
        )
        with open("trace.txt", "w+") as f:
            for i in messages:
                f.write(str(i))
        return final_response.content



    # If no tool call was needed, return the model's direct response.
    
    return first_response.content



result = ask_agent("Is my process compliant?")
print(result)

