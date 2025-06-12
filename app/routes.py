import asyncio
from flask import Blueprint, request, jsonify
from .services.query_service import process_natural_language_query

# 创建一个蓝图
api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/query', methods=['POST'])
def handle_query():
    """
    处理来自前端的自然语言查询请求
    """
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "请求体中必须包含 'question' 字段"}), 400

    question = data['question']

    try:
        # 因为我们的服务函数是异步的，所以需要用这种方式在同步的Flask路由中运行它
        result = asyncio.run(process_natural_language_query(question))
        return jsonify(result)
    except Exception as e:
        print(f"Error in handle_query: {e}")
        return jsonify({"error": "处理请求时发生内部错误", "details": str(e)}), 500