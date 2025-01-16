import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.app import app
from api.scheduler import run_scheduler
import threading

def init_scheduler():
    """初始化并启动调度器"""
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# 初始化调度器
init_scheduler()

if __name__ == '__main__':
    # 本地开发时使用
    app.run(host='0.0.0.0', port=8000, debug=False)