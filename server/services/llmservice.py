from langchain.chat_models import init_chat_model
# from langchain_groq import ChatGroq
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# chat_model = ChatGroq(
#     model_name="llama-3.3-70b-versatile",
#     temperature=0.7,
# )

chat_model = init_chat_model(
    model="openai/gpt-oss-120b",
    model_provider="groq",
    temperature=0,
)

def get_groq_llama_3_8b():
    return chat_model

