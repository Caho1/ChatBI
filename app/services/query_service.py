from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit

# 从同级目录导入我们已经实例化的对象
from .llm_clients import sql_llm, interpretation_llm
from .database import db

# 1. 应用启动时，一次性获取数据库的完整结构信息
#DB_SCHEMA_INFO = db.get_table_info()
DB_SCHEMA_INFO = '''

erDiagram
    experts {
        int id PK "主键"
        varchar(255) name "姓名"
        varchar(64) phone "电话"
        varchar(255) email "邮箱"
        text resume "简历"
        varchar(64) account "账号"
        datetime operation_time "最后操作时间"
        datetime create_time "创建时间"
        int highest_degree_id FK "外键: lkp_degrees.id"
        int status_id FK "外键: lkp_statuses.id"
        int organization_id FK "外键: lkp_organizations.id"
        int title_id FK "外键: lkp_titles.id"
        int research_direction_id FK "外键: lkp_research_directions.id"
        int research_area_id FK "外键: lkp_research_areas.id"
        int data_source_id FK "外键: lkp_data_sources.id"
        int country_region_id FK "外键: lkp_countries_regions.id"
        int level_id FK "外键: lkp_levels.id"
        int channel_id FK "外键: lkp_channels.id"
        int developer_id FK "外键: staff.id"
        int contact_id FK "外键: staff.id"
        int creator_id FK "外键: staff.id"
    }

    staff {
        int id PK "主键ID"
        varchar(64) name "员工姓名"
        varchar(64) role "员工角色"
        datetime create_time "创建时间"
    }
    
    expert_followups {
        int id PK "关系ID"
        int expert_id FK "专家ID"
        int staff_id FK "跟进人ID"
        datetime assignment_date "分配时间"
        varchar(50) followup_role "跟进角色"
    }

    lkp_degrees { int id PK; varchar(64) name "学历名称"; }
    lkp_statuses { int id PK; varchar(64) name "状态名称"; }
    lkp_organizations { int id PK; varchar(255) name "单位名称"; }
    lkp_titles { int id PK; varchar(64) name "职称名称"; }
    lkp_research_directions { int id PK; varchar(255) name "研究方向"; }
    lkp_research_areas { int id PK; varchar(255) name "研究领域"; }
    lkp_data_sources { int id PK; varchar(64) name "数据来源"; }
    lkp_countries_regions { int id PK; varchar(64) name "国家/地区"; }
    lkp_levels { int id PK; varchar(16) name "等级"; }
    lkp_channels { int id PK; varchar(64) name "来源渠道"; }

    experts }|--|| lkp_degrees : "关联"
    experts }|--|| lkp_statuses : "关联"
    experts }|--|| lkp_organizations : "关联"
    experts }|--|| lkp_titles : "关联"
    experts }|--o{ expert_followups : "有多个跟进记录"
    staff }|--o{ expert_followups : "是跟进人"

'''

# 2. 从 toolkit 中获取工具列表
toolkit = SQLDatabaseToolkit(db=db, llm=sql_llm)
tools = [t for t in toolkit.get_tools() if t.name != "sql_db_query_checker"]

# 3. 创建一个全新的、注入了数据库结构的Prompt模板
SYSTEM_PROMPT = '''
你是一个专家级的MySQL数据分析AI助手，尤其擅长处理复杂的多表关联查询。

你的目标是帮助用户通过自然语言与数据库进行交互。请严格遵循以下工作流程：

# 数据库结构信息 (你的永久记忆):
你将操作的数据库的表结构如下，其中包含了清晰的主外键关联注释，这是你构建JOIN查询的唯一依据：

{db_schema}

# 工作流程:
1.  **分析问题**: 仔细分析用户的提问 `{input}`，拆解出用户想要查询的目标信息和筛选条件。

2.  **参考结构**: 你必须首先参考上面提供的"数据库结构信息"来构建SQL，而不是优先使用工具去勘查。只有在极度困惑时才允许使用 `sql_db_schema` 工具。

3.  **构建SQL (核心步骤)**:
    - **第一步：规划查询路径 (Query Planning)**
        a. **识别目标信息**: 明确用户最终想看到的数据在哪张表、哪个列？(例如: 专家姓名 -> `experts`.`name`)
        b. **识别筛选条件**: 明确用户给出的筛选条件在哪张表、哪个列？(例如: 等级是'L3' -> `lkp_levels`.`name`)
        c. **规划连接路径(JOIN Path)**: 这是最关键的一步。要从"筛选条件的表"连接到"目标信息的表"，你必须依赖"数据库结构信息"里提供的外键关系。
            - **示例**: 如果要根据`lkp_levels`的`name`筛选，并显示`experts`的`name`，你需要找到连接这两张表的"桥梁"。
            - **查找桥梁**: 查看结构信息，你会发现 `experts` 表的 `level_id` 注释为 `外键, 指向 lkp_levels.id`。
            - **确定JOIN条件**: 这意味着连接条件是 `experts.level_id = lkp_levels.id`。
            - **多表路径**: 如果需要跨越多个表，你需要规划一条完整的连接链条，例如 `table_A JOIN table_B ON ... JOIN table_C ON ...`。

    - **第二步：编写SQL语句**
        - **使用JOIN**: 基于你的规划，优先使用 `INNER JOIN`。只有当用户的问题暗示可能存在不匹配的数据也需要显示时（例如"列出所有专家及其跟进人，没有跟进人的也要列出"），才使用 `LEFT JOIN`。
        - **安全和效率**: 绝对不要使用 `SELECT *`，只选择你需要的列。如果只需要几条示例数据，请使用 `LIMIT`。
        - **语法**: 所有表名和列名都必须用反引号 (`) 包裹，以避免关键字冲突和兼容性问题。

4.  **执行SQL**: 使用 `sql_db_query` 工具来执行查询。

5.  **解读结果 (至关重要!)**:
    - 你必须仔细分析 `sql_db_query` 工具返回的结果。
    - **如果结果是一个空列表 `[]`**: 这意味着数据库中没有找到符合条件的数据，请明确告知用户。
    - **如果结果只有一个条目/一行**: 这就是最终的、确切的答案！请直接根据这一行数据形成你的结论。
    - **如果结果有多行**: 请进行总结，并可以挑选前几条作为示例展示。

6.  **最终回答**: 基于你对结果的分析，用通俗、友好、清晰的中文文本回答用户的问题,不需要向用户展示你的思考过程,也不要输出markdown格式的标点符合如"**"。
'''

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

prompt = prompt.partial(db_schema=DB_SCHEMA_INFO)

# 创建Agent和执行器
agent = create_openai_tools_agent(
    llm=sql_llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
)


# ----------------- 解读部分 -----------------

interpretation_prompt = PromptTemplate.from_template(
    """
    基于以下信息，请为用户生成一段通俗易懂的中文总结。

    原始问题: {question}
    SQL查询结果: {sql_result}

    你的任务:
    1. 用自然的语言复述查询结果的关键信息。 
    2. 不要暴露SQL查询语句或数据库的列名（如`姓名`, `工作单位`）。 
    3. 如果结果是一个列表，清晰地列出关键项。 
    4. 如果结果为空或没有信息，请友好地告知用户"根据数据，没有找到相关信息"。 
    5. 总结应该简洁明了，直接回答用户的问题。 

    生成的总结:
    """
)

interpretation_chain = interpretation_prompt | interpretation_llm


import ast
import decimal
from typing import Any

def _make_serializable(obj: Any):
    """递归把 tuple→list、Decimal→float，确保 jsonify 不报错"""
    if isinstance(obj, decimal.Decimal):
        return float(obj)           # 或 str(obj) 保留两位小数
    if isinstance(obj, tuple):
        return [_make_serializable(x) for x in obj]
    if isinstance(obj, list):
        return [_make_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    return obj

async def process_natural_language_query(question: str) -> dict:
    summary   = ""
    sql_query = "未能提取 SQL"
    raw_data  = []
    error     = None

    try:
        agent_response = await agent_executor.ainvoke({"input": question})
        summary = agent_response.get("output", "").strip()

        # ---- 提取 SQL & 原始数据 --------------------------------------------------
        for action, obs in agent_response.get("intermediate_steps", []):
            if action.tool == "sql_db_query":
                sql_query = (
                    action.tool_input.get("query")
                    if isinstance(action.tool_input, dict)
                    else action.tool_input
                )
                raw_data = obs
                break

        # 若 raw_data 被转成了字符串，尝试反序列化
        if isinstance(raw_data, str):
            try:
                raw_data = ast.literal_eval(raw_data)
            except Exception:
                raw_data = []


        # ---- 如果需要，重新生成自然语言摘要 --------------------------------------
        need_rewrite = (
            not summary or
            "max iteration" in summary.lower() or
            "未找到" in summary
        )
        if need_rewrite:
            interp = await interpretation_chain.ainvoke({
                "question": question,
                "sql_result": str(raw_data)
            })
            summary = interp.content.strip()

    except Exception as exc:
        error   = f"处理查询时发生错误: {exc}"
        summary = "抱歉，我在处理您的问题时遇到了一个内部错误。"
        print(error)

    return {
        "question": question,
        "summary" : summary,
        "sql_query": sql_query,
        "raw_data" : _make_serializable(raw_data),  # ✅ 保证可被 jsonify
        "error"    : error,
    }

