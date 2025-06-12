import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量中获取数据库连接URL
db_url = os.getenv("DB_URL")

if not db_url:
    raise ValueError("环境变量 DB_URL 未设置，请检查您的 .env 文件。")

# 创建SQLAlchemy引擎
engine = create_engine(db_url)

# 创建LangChain的SQLDatabase实例
# 这个实例会被Agent用来查询schema和执行SQL
db = SQLDatabase(engine=engine)