import schedule
import time
from datetime import datetime
from db import DatabaseManager
from api.easy_park import EasyPark

def check_and_execute_tasks():
    """检查并执行定时任务"""
    current_time = datetime.now()
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_weekday = str(current_time.weekday())  # 0-6 表示周一到周日

    db = DatabaseManager()
    active_schedules = db.get_active_schedules()

    for task in active_schedules:
        try:
            # 检查是否到达执行时间
            if (task['hour'] == current_hour and 
                task['minute'] == current_minute and 
                current_weekday in task['weekdays'].split(',')):
                # 检查今天是否已经执行过
                if db.check_task_executed_today(task['id']):
                    print(f"任务 {task['id']} 今天已经执行过")
                    db.log_task_execution(task['id'], False, f"任务 {task['id']} 今天已经执行过")
                    continue
                
                try:
                    # 初始化 EasyPark 实例
                    easy_park = EasyPark()
                    # 执行核销任务
                    if easy_park.process_unused_coupons():
                        # 记录成功执行
                        db.log_task_execution(task['id'], True)
                except Exception as e:
                    error_msg = str(e)
                    print(f"执行任务失败: {error_msg}")
                    # 记录执行失败
                    db.log_task_execution(task['id'], False, error_msg)
        except Exception as e:
            print(f"处理任务 {task.get('id')} 失败: {str(e)}")

def run_scheduler():
    """运行调度器"""
    # 每分钟检查一次
    schedule.every().minute.do(check_and_execute_tasks)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler() 