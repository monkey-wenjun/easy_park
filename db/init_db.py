import os
import pymysql
import yaml
import time
import sys

def init_database():
    # 加载配置
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)['database']

    # 覆盖配置中的主机名
    host = os.environ.get('MYSQL_HOST', config['host'])
    port = int(os.environ.get('MYSQL_PORT', config['port']))

    max_retries = 30
    retry_interval = 2

    for attempt in range(max_retries):
        try:
            print(f"尝试连接数据库 (attempt {attempt + 1}/{max_retries})...")
            # 连接MySQL（不指定数据库）
            connection = pymysql.connect(
                host=host,
                port=port,
                user=config['user'],
                password=config['password']
            )

            try:
                with connection.cursor() as cursor:
                    # 创建数据库
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
                    print(f"数据库 {config['database']} 创建成功")

                    # 使用数据库
                    cursor.execute(f"USE {config['database']}")

                    # 读取并执行SQL文件
                    sql_path = os.path.join(os.path.dirname(__file__), 'init.sql')
                    with open(sql_path, 'r', encoding='utf-8') as f:
                        sql_commands = f.read().split(';')
                        for command in sql_commands:
                            if command.strip():
                                cursor.execute(command)
                                connection.commit()
                    
                    print("数据库表创建成功")
                    return  # 成功后退出函数

            except Exception as e:
                print(f"初始化数据库失败: {str(e)}")
                raise
            finally:
                connection.close()

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"连接失败: {str(e)}")
                print(f"等待 {retry_interval} 秒后重试...")
                time.sleep(retry_interval)
            else:
                print("达到最大重试次数，初始化失败")
                raise

if __name__ == '__main__':
    try:
        init_database()
        print("数据库初始化成功")
        sys.exit(0)
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        sys.exit(1) 