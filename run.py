# -*- coding: utf-8 -*-
"""
启动脚本：python run.py
"""
import os
import sys

# 将当前目录加入Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    # Railway/生产环境：端口来自环境变量 PORT，本地默认 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,  # 避免重复加载
        threaded=True  # 启用多线程
    )