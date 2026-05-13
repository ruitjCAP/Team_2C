import os
from dotenv import load_dotenv
from langchain_ibm import ChatWatsonx
load_dotenv()

def create_llm():
    return ChatWatsonx(
        model_id="meta-llama/llama-3-3-70b-instruct",
        url=os.getenv("WATSON_ENDPOINT"),
        apikey=os.getenv("WATSON_API_KEY"),
        project_id=os.getenv("WATSON_PROJECT_ID"),
        params={
            "temperature": 0.9,
            "max_tokens": 1500,
        },
    )