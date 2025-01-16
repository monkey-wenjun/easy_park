import pymysql
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
import pytz
import time
import json
import threading
import traceback
from werkzeug.security import generate_password_hash


class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.connection = None
            self.config = self._load_config()
            self.connect()
            self.initialized = True

    def _load_config(self) -> dict:
        """加载数据库配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config['database']

    def connect(self):
        """建立数据库连接"""
        max_retries = 30
        retry_interval = 2

        for attempt in range(max_retries):
            try:
                print(f"尝试连接数据库 (attempt {attempt + 1}/{max_retries})...")

                self.connection = pymysql.connect(
                    host=os.environ.get('MYSQL_HOST', self.config['host']),
                    port=int(os.environ.get('MYSQL_PORT', self.config['port'])),
                    user=self.config['user'],
                    password=self.config['password'],
                    database=self.config['database'],
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )

                print("数据库连接成功")
                return True

            except Exception as e:
                print(f"连接失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
                else:
                    raise Exception("无法连接到数据库")

    def _get_current_time(self) -> datetime:
        """获取当前北京时间"""
        tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(tz).replace(tzinfo=None)

    def add_record(self, code_id, code_no, business_name=None, code_start_time=None, code_end_time=None, used_by=None):
        """添加记录"""
        try:
            with self.connection.cursor() as cursor:
                current_time = self._get_current_time()
                sql = """
                INSERT INTO code_records 
                (code_id, code_no, business_name, code_start_time, code_end_time, used_by, created_at, updated_at)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM code_records 
                    WHERE code_id = %s AND code_no = %s AND is_deleted = 0
                )
                """
                cursor.execute(sql, (
                    code_id, code_no, business_name, code_start_time, code_end_time,
                    used_by, current_time, current_time, code_id, code_no
                ))
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"添加记录失败: {str(e)}")
            return False

    def query_records_with_pagination(self, username,
                                      start_time: Optional[datetime] = None,
                                      end_time: Optional[datetime] = None,
                                      status: Optional[int] = None,
                                      page: int = 1,
                                      page_size: int = 5) -> Tuple[int, List[Dict]]:
        """分页查询记录"""
        try:
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                # 使用 %% 来转义 MySQL 的 % 符号
                base_sql = """
                    SELECT 
                        id,
                        code_id, 
                        code_no, 
                        business_name,
                        DATE_FORMAT(code_start_time, '%%Y-%%m-%%d %%H:%%i:%%s') as code_start_time,
                        DATE_FORMAT(code_end_time, '%%Y-%%m-%%d %%H:%%i:%%s') as code_end_time,
                        status,
                        used_by,
                        DATE_FORMAT(used_time, '%%Y-%%m-%%d %%H:%%i:%%s') as used_time,
                        DATE_FORMAT(verification_time, '%%Y-%%m-%%d %%H:%%i:%%s') as verification_time,
                        DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at,
                        is_deleted
                    FROM code_records 
                    WHERE is_deleted = 0 AND used_by = %s
                """
                
                # 修改计数 SQL
                count_sql = """
                    SELECT COUNT(*) as total 
                    FROM code_records 
                    WHERE is_deleted = 0 AND used_by = %s
                """
                params = [username]

                # 添加条件
                if start_time:
                    base_sql += " AND created_at >= %s"
                    count_sql += " AND created_at >= %s"
                    params.append(start_time)

                if end_time:
                    base_sql += " AND created_at <= %s"
                    count_sql += " AND created_at <= %s"
                    params.append(end_time)

                if status is not None:
                    base_sql += " AND status = %s"
                    count_sql += " AND status = %s"
                    params.append(status)

                # 获取总记录数
                cursor.execute(count_sql, params)
                total = cursor.fetchone()['total']

                # 添加分页和排序
                base_sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([page_size, (page - 1) * page_size])

                # 获取分页数据
                cursor.execute(base_sql, params)
                records = cursor.fetchall()

                return total, records

        except Exception as e:
            print(f"分页查询记录失败: {str(e)}")
            print(f"错误类型: {type(e)}")
            print(f"错误详情: {str(e)}")
            return 0, []

    def update_status(self, code_id: str, status: int) -> bool:
        """更新记录状态"""
        try:
            with self.connection.cursor() as cursor:
                current_time = self._get_current_time()
                sql = """
                UPDATE code_records 
                SET status = %s, 
                    updated_at = %s,
                    verification_time = %s,
                    used_by = %s,
                    used_time = %s
                WHERE code_id = %s AND is_deleted = 0
                """
                cursor.execute(sql, (
                    status,
                    current_time,
                    current_time if status == 1 else None,
                    'system' if status == 1 else None,
                    current_time if status == 1 else None,
                    code_id
                ))
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新状态失败: {str(e)}")
            return False

    def add_user(self, username: str, password: str, license_plate: str, user_no: str, openid: str) -> bool:
        """添加新用户"""
        print(username, password, license_plate, user_no, openid)
        try:
            with self.connection.cursor() as cursor:
                sql = """
                INSERT INTO user_vehicle_records 
                (username, password, license_plate, user_no, openid)
                VALUES (%s, %s, %s, %s, %s)
                """
                params = (
                    username,
                    password,
                    license_plate,
                    user_no,
                    openid
                )
                print(sql, params)
                cursor.execute(sql, params)
                self.connection.commit()
                return True
        except Exception as e:
            print(f"添加用户失败: {str(e)}")
            return False

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户信息"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT 
                        username,
                        password,
                        license_plate,
                        user_no,
                        openid,
                        email,
                        created_at
                    FROM user_vehicle_records 
                    WHERE username = %s 
                    AND is_deleted = 0
                """
                cursor.execute(sql, (username,))
                return cursor.fetchone()
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return None

    def get_record_by_id(self, record_id: int, username: str) -> Optional[Dict]:
        """通过 ID 获取记录"""
        try:
            with self.connection.cursor() as cursor:
                # 先检查记录是否存在（不考虑 is_deleted 状态）
                check_sql = f"""
                SELECT id, is_deleted 
                FROM code_records 
                WHERE id = %s and used_by ='{username}'
                """
                print(f"检查记录是否存在: {check_sql}")
                cursor.execute(check_sql, (record_id,))
                check_result = cursor.fetchone()
                print(f"检查结果: {check_result}")

                if not check_result:
                    print(f"记录 {record_id} 不存在")
                    return None

                if check_result['is_deleted'] == 1:
                    print(f"记录 {record_id} 已被删除")
                    return None

                # 获取完整记录
                sql = """
                SELECT * FROM code_records 
                WHERE id = %s
                """
                cursor.execute(sql, (record_id,))
                result = cursor.fetchone()
                print(f"完整记录: {result}")
                return result

        except Exception as e:
            print(f"查询记录失败: {str(e)}")
            print(f"错误类型: {type(e)}")
            print(f"错误详情: {str(e)}")
            return None

    def soft_delete_by_id(self, record_id: int, username: str) -> bool:
        """通过 ID 软删除记录"""
        try:
            with self.connection.cursor() as cursor:
                # 开始事务
                self.connection.begin()

                try:
                    # 先检查记录状态
                    check_sql = """
                    SELECT id, is_deleted 
                    FROM code_records 
                    WHERE id = %s and used_by = %s
                    FOR UPDATE  /* 添加行锁 */
                    """
                    cursor.execute(check_sql, (record_id, username))
                    record = cursor.fetchone()

                    if not record:
                        print(f"记录 {record_id} 不存在")
                        self.connection.rollback()
                        return False

                    if record['is_deleted'] == 1:
                        print(f"记录 {record_id} 已被删除")
                        self.connection.rollback()
                        return False

                    # 执行软删除
                    current_time = self._get_current_time()
                    update_sql = """
                    UPDATE code_records 
                    SET is_deleted = 1, 
                        updated_at = %s
                    WHERE id = %s and used_by = %s
                    """
                    print(f"执行软删除: {update_sql}")
                    print(f"参数: time={current_time}, id={record_id}")
                    cursor.execute(update_sql, (current_time, record_id, username))
                    affected_rows = cursor.rowcount
                    print(f"影响的行数: {affected_rows}")

                    # 提交事务
                    self.connection.commit()
                    print(f"事务已提交")
                    return affected_rows > 0

                except Exception as e:
                    # 发生错误时回滚事务
                    self.connection.rollback()
                    print(f"事务已回滚: {str(e)}")
                    raise

        except Exception as e:
            print(f"软删除记录失败: {str(e)}")
            print(f"SQL执行错误: {e.__class__.__name__}")
            print(f"错误详情: {str(e)}")
            return False

        finally:
            # 确保连接可用
            if not self.connection.open:
                self.connect()

    def __del__(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        """实现上下文管理器的进入方法"""
        if not self.connection or self.connection.open == False:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """实现上下文管理器的退出方法"""
        if self.connection and self.connection.open:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
            self.connection.close()
            self.connection = None

    def get_user_info(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT 
                        username,
                        license_plate,
                        user_no,
                        openid,
                        email,
                        created_at
                    FROM user_vehicle_records 
                    WHERE username = %s 
                    AND is_deleted = 0
                """
                cursor.execute(sql, (username,))
                result = cursor.fetchone()
                if result:
                    # 在 Python 中格式化日期
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S') if result['created_at'] else None
                return result
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return None

    def update_user_info(self, username: str, license_plate: str, user_no: str, openid: str) -> bool:
        """更新用户信息"""
        try:
            update_fields = []
            params = []

            if license_plate is not None:
                update_fields.append("license_plate = %s")
                params.append(license_plate)

            if user_no is not None:
                update_fields.append("user_no = %s")
                params.append(user_no)
            if openid is not None:
                update_fields.append("openid = %s")
                params.append(openid)


            if not update_fields:
                return True

            update_fields.append("updated_at = %s")
            params.append(self._get_current_time())
            params.append(username)

            sql = f"""
            UPDATE user_vehicle_records 
            SET {', '.join(update_fields)}
            WHERE username = %s
            """

            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                self.connection.commit()
                return cursor.rowcount > 0

        except Exception as e:
            print(f"更新用户信息失败: {str(e)}")
            return False

    def get_unused_codes(self, username) -> List[Dict]:
        """获取指定用户的未使用券码"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT code_id, code_no
                    FROM code_records
                    WHERE used_by = %s 
                    AND status = 0 
                    AND is_deleted = 0
                    AND code_end_time > NOW() 
                    ORDER BY created_at ASC LIMIT 1
                """
                cursor.execute(sql, (username,))
                return cursor.fetchall()
        except Exception as e:
            print(f"获取未使用券码失败: {str(e)}")
            return []

    def get_schedules(self, username: str) -> List[Dict]:
        """获取用户的定时任务列表"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT 
                    id,
                    hour,
                    minute,
                    weekdays,
                    status,
                    auto_collect,
                    auto_pay,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at,
                    DATE_FORMAT(updated_at, '%%Y-%%m-%%d %%H:%%i:%%s') as updated_at
                FROM schedule_tasks 
                WHERE username = %s AND status = 1
                ORDER BY created_at DESC
                """
                cursor.execute(sql, (username,))
                return cursor.fetchall()
        except Exception as e:
            print(f"获取定时任务失败: {str(e)}")
            return []

    def create_schedule(self, username: str, hour: int, minute: int, weekdays: str, auto_collect: int = 0,
                        auto_pay: int = 0) -> bool:
        """
        创建定时任务
        :param username: 用户名
        :param hour: 小时
        :param minute: 分钟
        :param weekdays: 星期几，逗号分隔的字符串
        :param auto_collect: 自动领取开关(0:关闭,1:开启)
        :param auto_pay: 自动支付开关(0:关闭,1:开启)
        :return: 是否成功
        """
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO schedule_tasks 
                    (username, hour, minute, weekdays, auto_collect, auto_pay)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (username, hour, minute, weekdays, auto_collect, auto_pay))
                self.connection.commit()
                return True
        except Exception as e:
            print(f"创建定时任务失败: {str(e)}")
            return False

    def delete_schedule(self, username: str, task_id: int) -> bool:
        """删除定时任务"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                UPDATE schedule_tasks 
                SET status = 0 
                WHERE id = %s AND username = %s
                """
                cursor.execute(sql, (task_id, username))
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除定时任务失败: {str(e)}")
            return False

    def get_active_schedules(self) -> List[Dict]:
        """获取活动的定时任务"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT id, username, hour, minute, weekdays, auto_collect, auto_pay
                    FROM schedule_tasks
                    WHERE status = 1 AND is_deleted = 0
                """
                cursor.execute(sql)
                return cursor.fetchall()
        except Exception as e:
            print(f"获取活动定时任务失败: {str(e)}")
            return []

    def check_task_executed_today(self, task_id: int) -> bool:
        """检查任务今天是否已经执行过"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT COUNT(*) as count
                FROM schedule_execution_logs
                WHERE task_id = %s and status=1
                AND DATE(execution_date) = CURDATE()
                """
                cursor.execute(sql, (task_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            print(f"检查任务执行状态失败: {str(e)}")
            return False

    def log_task_execution(self, task_id: int, status: bool = True, error_message: str = None) -> bool:
        """记录任务执行"""
        try:
            with self.connection.cursor() as cursor:
                current_time = self._get_current_time()
                sql = """
                INSERT INTO schedule_execution_logs 
                (task_id, execution_date, execution_time, status, error_message)
                VALUES (%s, CURDATE(), %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                execution_time = VALUES(execution_time),
                status = VALUES(status),
                error_message = VALUES(error_message)
                """
                cursor.execute(sql, (task_id, current_time, 1 if status else 0, error_message))
                self.connection.commit()
                return True
        except Exception as e:
            print(f"记录任务执行失败: {str(e)}")
            return False

    def get_task_execution_history(self, task_id: int) -> List[Dict]:
        """获取任务的执行历史"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT 
                    id,
                    task_id,
                    DATE_FORMAT(execution_date, '%%Y-%%m-%%d') as execution_date,
                    DATE_FORMAT(execution_time, '%%Y-%%m-%%d %%H:%%i:%%s') as execution_time,
                    status,
                    error_message,
                    DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at
                FROM schedule_execution_logs
                WHERE task_id = %s
                ORDER BY execution_date DESC, execution_time DESC
                LIMIT 10
                """
                cursor.execute(sql, (task_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"获取任务执行历史失败: {str(e)}")
            return []

    def update_schedule(self, username: str, task_id: int, hour: int, minute: int, weekdays: str,
                        auto_collect: bool = True, auto_pay: bool = False) -> bool:
        """更新定时任务"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                UPDATE schedule_tasks 
                SET hour = %s, minute = %s, weekdays = %s, auto_collect = %s, auto_pay = %s
                WHERE id = %s AND username = %s AND status = 1
                """
                cursor.execute(sql, (hour, minute, weekdays,
                                     1 if auto_collect else 0,
                                     1 if auto_pay else 0,
                                     task_id, username))
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新定时任务失败: {str(e)}")
            return False

    def get_execution_logs(self, username: str, page: int = 1, page_size: int = 10,
                           start_date: str = None, end_date: str = None, status: str = None) -> Tuple[List[Dict], int]:
        """获取核销记录"""
        try:
            with self.connection.cursor() as cursor:
                # 构建基础查询
                sql = """
                SELECT 
                    sel.id,
                    sel.task_id,
                    DATE_FORMAT(sel.execution_date, '%%Y-%%m-%%d') as execution_date,
                    DATE_FORMAT(sel.execution_time, '%%Y-%%m-%%d %%H:%%i:%%s') as execution_time,
                    sel.status,
                    sel.error_message
                FROM schedule_execution_logs sel
                JOIN schedule_tasks st ON sel.task_id = st.id
                WHERE st.username = %s
                """
                params = [username]

                # 添加过滤条件
                if start_date:
                    sql += " AND sel.execution_date >= %s"
                    params.append(start_date)
                if end_date:
                    sql += " AND sel.execution_date <= %s"
                    params.append(end_date)
                if status is not None:
                    sql += " AND sel.status = %s"
                    params.append(int(status))

                # 获取总记录数
                count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as t"
                cursor.execute(count_sql, params)
                total = cursor.fetchone()['total']

                # 添加排序和分页
                sql += " ORDER BY sel.execution_date DESC, sel.execution_time DESC LIMIT %s OFFSET %s"
                params.extend([(page_size), (page - 1) * page_size])

                cursor.execute(sql, params)
                logs = cursor.fetchall()

                return logs, total

        except Exception as e:
            print(f"获取核销记录失败: {str(e)}")
            return [], 0

    def execute_update(self, sql: str, params: tuple = None) -> int:
        """执行更新操作，返回影响的行数"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"执行更新失败: {str(e)}")
            self.connection.rollback()
            return 0

    def save_task_status(self, task_id, status, message=None, results=None, username=None):
        """保存任务状态"""
        try:
            # 确保连接可用
            if not self.connection.open:
                self.connect()

            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO task_status (task_id, status, message, results, username)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    message = VALUES(message),
                    results = VALUES(results),
                    updated_at = CURRENT_TIMESTAMP
                """
                print(f"执行 SQL: {sql}")
                print(
                    f"参数: task_id={task_id}, status={status}, message={message}, results={results}, username={username}")

                cursor.execute(sql, (task_id, status, message, json.dumps(results) if results else None, username))
                self.connection.commit()

                # 验证更新是否成功
                cursor.execute("SELECT * FROM task_status WHERE task_id = %s", (task_id,))
                result = cursor.fetchone()
                print(f"更新后的状态: {result}")

                return True
        except Exception as e:
            print(f"保存任务状态失败: {str(e)}")
            # 如果出错，尝试重新连接
            try:
                self.connect()
            except:
                pass
            return False

    def get_task_status(self, task_id, username):
        """获取任务状态"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = """
                    SELECT task_id, status, message, results, created_at, updated_at
                    FROM task_status
                    WHERE task_id = %s AND username = %s
                    LIMIT 1
                """
                cursor.execute(sql, (task_id, username))
                task = cursor.fetchone()

                # 如果找到任务，刷新连接以确保数据是最新的
                if task:
                    self.connection.ping(reconnect=True)

                return task
        except Exception as e:
            print(f"获取任务状态失败: {str(e)}")
            traceback.print_exc()
            return None

    def clean_old_tasks(self, days=7):
        """清理旧任务"""
        try:
            with self.connection.cursor() as cursor:
                sql = "DELETE FROM task_status WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)"
                cursor.execute(sql, (days,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"清理旧任务失败: {str(e)}")
            return False

    def log_login(self, username, ip_address, status, fail_reason=None, user_agent=None):
        """记录登录日志"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    INSERT INTO login_logs 
                    (username, ip_address, status, fail_reason, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (username, ip_address, status, fail_reason, user_agent))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"记录登录日志失败: {str(e)}")
            return False

    def update_code_owner(self, code_ids, username):
        """更新券码所有者
        
        Args:
            code_ids: 单个券码ID或券码ID列表
            username: 新的所有者用户名
        """
        try:
            with self.connection.cursor() as cursor:
                # 如果是单个ID，转换为列表
                if isinstance(code_ids, str):
                    code_ids = [code_ids]

                # 构建 SQL IN 语句
                placeholders = ','.join(['%s'] * len(code_ids))
                sql = f"""
                    UPDATE code_records 
                    SET used_by = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE code_id IN ({placeholders})
                    AND status = 0  # 只更新未核销的券码
                """

                # 组合参数：username 在前，followed by code_ids
                params = [username] + code_ids

                # 执行更新
                cursor.execute(sql, params)
                self.connection.commit()

                # 获取实际更新的行数
                rows_affected = cursor.rowcount

                # 记录日志
                print(f"更新券码所有者: username={username}, code_ids={code_ids}, affected={rows_affected}")

                return rows_affected > 0

        except Exception as e:
            print(f"更新券码所有者失败: {str(e)}")
            return False

    def verify_user_license(self, username: str, license_plate: str) -> dict:
        """
        验证用户名和车牌号是否匹配
        :param username: 用户名
        :param license_plate: 车牌号
        :return: 用户信息或None
        """
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    SELECT * FROM user_vehicle_records 
                    WHERE username = %s AND license_plate = %s
                """
                cursor.execute(sql, (username, license_plate))
                return cursor.fetchone()
        except Exception as e:
            print(f"验证用户信息失败: {str(e)}")
            return None

    def update_password(self, username: str, new_password: str) -> bool:
        """更新用户密码"""
        try:
            with self.connection.cursor() as cursor:
                # 对新密码进行哈希处理
                hashed_password = generate_password_hash(new_password)
                
                sql = """
                    UPDATE user_vehicle_records 
                    SET password = %s 
                    WHERE username = %s 
                    AND is_deleted = 0
                """
                cursor.execute(sql, (hashed_password, username))
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新密码失败: {str(e)}")
            return False

    def add_share_record(self, from_username: str, to_username: str, code_ids: list) -> bool:
        """添加分享记录"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                INSERT INTO share_records 
                (from_username, to_username, code_ids)
                VALUES (%s, %s, %s)
                """
                # 将 code_ids 列表转换为 JSON 字符串存储
                code_ids_json = json.dumps(code_ids)
                cursor.execute(sql, (from_username, to_username, code_ids_json))
                self.connection.commit()
                return True
        except Exception as e:
            print(f"添加分享记录失败: {str(e)}")
            return False

    def get_share_records(self, username: str, page: int = 1, page_size: int = 10) -> Tuple[int, List[Dict]]:
        """获取分享记录"""
        try:
            with self.connection.cursor() as cursor:
                # 获取总记录数
                count_sql = """
                SELECT COUNT(*) as total 
                FROM share_records 
                WHERE (from_username = %s OR to_username = %s)
                AND is_deleted = 0
                """
                cursor.execute(count_sql, (username, username))
                total = cursor.fetchone()['total']
                
                # 获取分页数据
                sql = """
                SELECT 
                    id,
                    from_username,
                    to_username,
                    JSON_LENGTH(code_ids) as share_count,
                    share_time,
                    created_at,
                    updated_at
                FROM share_records 
                WHERE (from_username = %s OR to_username = %s)
                AND is_deleted = 0
                ORDER BY share_time DESC
                LIMIT %s OFFSET %s
                """
                offset = (page - 1) * page_size
                cursor.execute(sql, (username, username, page_size, offset))
                records = cursor.fetchall()
                
                # 格式化时间
                for record in records:
                    record['share_time'] = record['share_time'].strftime('%Y-%m-%d %H:%M:%S')
                    record['created_at'] = record['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    record['updated_at'] = record['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                return total, records
        except Exception as e:
            print(f"获取分享记录失败: {str(e)}")
            return 0, []

    def add_verification_code(self, email: str, code: str, type_str: str) -> bool:
        """添加验证码记录"""
        try:
            with self.connection.cursor() as cursor:
                # 设置验证码有效期为5分钟
                expire_time = datetime.now() + timedelta(minutes=5)
                sql = """
                INSERT INTO verification_codes 
                (email, code, type, expire_time)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (email, code, type_str, expire_time))
                self.connection.commit()
                return True
        except Exception as e:
            print(f"添加验证码记录失败: {str(e)}")
            return False

    def verify_code(self, email: str, code: str, type_str: str) -> bool:
        """验证验证码"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT * FROM verification_codes 
                WHERE email = %s AND code = %s AND type = %s 
                AND expire_time > NOW() AND used = 0
                ORDER BY created_at DESC LIMIT 1
                """
                cursor.execute(sql, (email, code, type_str))
                result = cursor.fetchone()
                
                if result:
                    # 标记验证码为已使用
                    update_sql = """
                    UPDATE verification_codes 
                    SET used = 1 
                    WHERE id = %s
                    """
                    cursor.execute(update_sql, (result['id'],))
                    self.connection.commit()
                    return True
                return False
        except Exception as e:
            print(f"验证验证码失败: {str(e)}")
            return False

    def check_email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT COUNT(*) as count FROM user_vehicle_records WHERE email = %s"
                cursor.execute(sql, (email,))
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            print(f"检查邮箱是否存在失败: {str(e)}")
            return False

    def register_user(self, data: dict) -> bool:
        """
        注册新用户
        :param data: 包含用户信息的字典
        :return: 是否注册成功
        """
        try:
            with self.connection.cursor() as cursor:
                # 检查用户名是否已存在
                if self.get_user_by_username(data['username']):
                    print("用户名已存在")
                    return False
                    
                # 对密码进行哈希处理
                hashed_password = generate_password_hash(data['password'])
                
                # 插入用户记录
                sql = """
                INSERT INTO user_vehicle_records 
                (username, password, license_plate, user_no, openid, email, email_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    data['username'],
                    hashed_password,
                    data['license_plate'],
                    data.get('user_no', ''),# user_no 可能为空
                    data.get('openid', ''),  # openid可能为空
                    data['email'],
                    1  # 邮箱已验证
                ))
                self.connection.commit()
                return True
        except Exception as e:
            print(f"注册用户失败: {str(e)}")
            return False

    def update_user_profile(self, username: str, license_plate: str, user_no: str, openid: str, email: str) -> bool:
        """更新用户个人信息"""
        try:
            with self.connection.cursor() as cursor:
                sql = """
                    UPDATE user_vehicle_records 
                    SET license_plate = %s,
                        user_no = %s,
                        openid = %s,
                        email = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE username = %s 
                    AND is_deleted = 0
                """
                cursor.execute(sql, (license_plate, user_no, openid, email, username))
                self.connection.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"更新用户信息失败: {str(e)}")
            return False
