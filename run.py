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
    # 生产环境配置
    # app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    # 开发环境配置
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False,  # 避免重复加载
        threaded=True  # 启用多线程
    )