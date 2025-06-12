import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取API配置
api_base = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL_NAME")

if not all([api_base, api_key, model_name]):
    raise ValueError("一个或多个OpenAI环境变量未设置 (OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL_NAME)。")

# LLM for SQL Generation (Agent)
# 用于SQL生成的LLM，温度设置为0以保证稳定和精确
sql_llm = ChatOpenAI(
    model=model_name,
    temperature=0,
    openai_api_base=api_base,
    openai_api_key=api_key
)

# LLM for Interpretation
# 用于结果解读的LLM，可以有略高的温度以产生更自然的语言
interpretation_llm = ChatOpenAI(
    model=model_name,
    temperature=0.7,
    openai_api_base=api_base,
    openai_api_key=api_key
)