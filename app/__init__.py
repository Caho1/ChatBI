from flask import Flask
from flask_cors import CORS
from .routes import api_bp

def create_app():
    """Flask application factory."""
    app = Flask(__name__)

    # 设置CORS，允许来自任何源的请求，这对于前端开发很方便
    # 在生产环境中，您可能希望将其限制为您的前端域名
    CORS(app)

    # 注册API蓝图
    app.register_blueprint(api_bp, url_prefix='/api')

    return app