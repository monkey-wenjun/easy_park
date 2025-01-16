from flask import Flask, request, jsonify, send_file, make_response
from flask.helpers import send_from_directory
from datetime import datetime
from db import DatabaseManager
import traceback
from werkzeug.security import generate_password_hash, check_password_hash
from api.auth import generate_token, token_required
import os
from werkzeug.utils import secure_filename
from api.ocr_class import QRCodeProcessor
from api.http_api import ParkingAPI
import uuid
import yaml
import time
from threading import Thread
import json
from io import BytesIO
from PIL import Image, ImageDraw
import random
import string
import math
from api.email_utils import EmailSender

app = Flask(__name__, static_folder='../frontend')

db = DatabaseManager()

# 确保目录存在
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parking', 'code')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'parking', 'output_file')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

email_sender = EmailSender()

def process_image_task(task_id, filepath, username):
    """异步处理图片的任务"""
    print(f"开始处理任务 {task_id}, 用户: {username}")
    db_manager = None
    try:
        # 初始化数据库连接
        db_manager = DatabaseManager()
        
        # 更新初始状态
        print("更新初始状态为处理中...")
        db_manager.save_task_status(
            task_id=task_id,
            status='processing',
            message='正在处理中...',
            username=username
        )

        # 获取用户信息
        user_info = db_manager.get_user_info(username)
        print(f"获取到用户信息: {user_info}")
        if not user_info:
            raise Exception("用户信息不存在")

        # 加载配置
        config_path = os.path.join(BASE_DIR, 'config', 'config.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # 初始化处理器
        print("初始化 QR 处理器...")
        qr_config_path = os.path.join(BASE_DIR, 'config')
        qr_processor = QRCodeProcessor(config_path=qr_config_path)
        
        # 使用配置和用户信息初始化API
        print("初始化停车 API...")
        api = ParkingAPI(
            app_id=config['wechat']['app_id'],
            headers=config['wechat']['headers'],
            car_no=user_info['license_plate'],
            user_no=user_info['user_no'],
            openid=user_info['openid']
        )

        # 处理图片
        print(f"开始处理图片: {filepath}")
        code_id_list = qr_processor.detect_and_decode_qrcodes([filepath])
        print(f"检测到的二维码列表: {code_id_list}")
        results = []
        
        # 获取标记后的图片路径
        filename = os.path.basename(filepath)
        marked_filename = f'marked_{filename}'
        marked_filepath = os.path.join(OUTPUT_FOLDER, marked_filename)
        
        # 检查标记后的图片是否存在
        if os.path.exists(marked_filepath):
            marked_image_url = f'/static/output_file/{marked_filename}'
            print(f"找到标记后的图片: {marked_image_url}")
        else:
            marked_image_url = None
            print("未找到标记后的图片")

        for code_id in code_id_list:
            try:
                code_id = str(code_id).split("=")[1]
                print(f"处理二维码: {code_id}")
                query_code = api.query_code(code_id)
                print(f"查询结果: {query_code}")

                if query_code is False:
                    results.append({
                        'code_id': code_id,
                        'status': 'invalid',
                        'message': '券已核销'
                    })
                    continue

                data = query_code.get("data", {})
                code_no = data.get("no")
                business_name = data.get("park", {}).get("Parking_Name")
                code_start_time = data.get("model", {}).get("CouponSolution_StartTime")
                code_end_time = data.get("model", {}).get("CouponSolution_EndTime")

                if not code_no:
                    results.append({
                        'code_id': code_id,
                        'status': 'invalid',
                        'message': '获取券码编号失败'
                    })
                    continue
                
                # 添加到数据库
                success = db_manager.add_record(
                    code_id=code_id,
                    code_no=code_no,
                    business_name=business_name,
                    code_start_time=code_start_time,
                    code_end_time=code_end_time,
                    used_by=username
                )
                print(f"添加记录结果: {success}")
                
                results.append({
                    'code_id': code_id,
                    'code_no': code_no,
                    'business_name': business_name,
                    'code_start_time': code_start_time,
                    'code_end_time': code_end_time,
                    'status': 'success' if success else 'failed',
                    'message': '添加成功' if success else '添加失败'
                })
            except Exception as e:
                print(f"处理二维码出错: {str(e)}")
                results.append({
                    'code_id': code_id if 'code_id' in locals() else 'unknown',
                    'status': 'error',
                    'message': f'处理失败: {str(e)}'
                })

        # 更新任务状态为完成
        print(f"处理完成，更新任务状态，结果: {results}")
        success = db_manager.save_task_status(
            task_id=task_id,
            status='completed',
            message='处理完成',
            results=results,
            username=username
        )
        print(f"状态更新结果: {success}")

    except Exception as e:
        error_msg = f"任务 {task_id} 处理失败: {str(e)}"
        print(error_msg)
        if db_manager:
            db_manager.save_task_status(
                task_id=task_id,
                status='error',
                message=error_msg,
                username=username
            )
    finally:
        # 清理临时文件
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"清理临时文件: {filepath}")
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 添加路由来服务前端文件
@app.route('/')
def index():
    """提供前端首页"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """提供其他静态文件"""
    return send_from_directory(app.static_folder, path)

@app.route("/api/records", methods=['GET'])
@token_required
def get_records():
    """获取停车券记录"""
    try:
        username = request.current_user
        if not username:
            return jsonify({
                'code': 1,
                'message': '未提供用户名'
            }), 401

        # 获取查询参数
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        status = request.args.get('status', type=int)

        # 转换时间字符串为 datetime 对象
        start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') if start_time else None
        end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') if end_time else None

        # 查询记录
        total, records = db.query_records_with_pagination(
            username=username,
            start_time=start_datetime,
            end_time=end_datetime,
            status=status,
            page=page,
            page_size=page_size
        )

        # 由于数据库已经格式化了时间，这里不需要再处理
        return jsonify({
            'code': 0,
            'data': {
                'total': total,
                'records': records
            }
        })

    except Exception as e:
        print(f"Error in get_records: {traceback.format_exc()}")
        return jsonify({
            'code': 1,
            'message': '服务器内部错误',
            'error': str(e)
        }), 500

@app.route("/api/records", methods=['POST'])
@token_required
def add_record():
    """添加记录"""
    username = request.current_user
    data = request.get_json()
    code_id = data.get('code_id')
    code_no = data.get('code_no')
    
    if not code_id or not code_no:
        return jsonify({"code": 1, "message": "参数错误"})
    
    success = db.add_record(code_id, code_no,username)
    return jsonify({"code": 0 if success else 1, "message": "添加成功" if success else "添加失败"})

@app.route("/api/records/<code_id>/status", methods=['PUT'])
def update_record_status(code_id):
    """更新记录状态"""
    data = request.get_json()
    status = data.get('status')
    
    if status is None:
        return jsonify({"code": 1, "message": "参数错误"})
    
    success = db.update_status(code_id, status)
    return jsonify({"code": 0 if success else 1, "message": "更新成功" if success else "更新失败"})

@app.route("/api/records/<int:record_id>", methods=['DELETE'])
@token_required
def delete_record(record_id):
    """删除记录"""
    username = request.current_user
    try:
        print(f"删除记录 ID: {record_id}")
        with DatabaseManager() as db_con:
            # 先查询记录是否存在
            record = db_con.get_record_by_id(record_id, username)
            if not record:
                return jsonify({
                    "code": 1,
                    "message": "删除失败：记录不存在",
                    "error": "记录未找到"
                })
            
            success = db_con.soft_delete_by_id(record_id, username)
            print(f"删除操作结果: {success}")
            
            if success:
                return jsonify({
                    "code": 0,
                    "message": "删除成功"
                })
            else:
                return jsonify({
                    "code": 1,
                    "message": "删除失败：记录状态异常",
                    "error": "记录状态异常"
                })
            
    except Exception as e:
        error_msg = f"删除记录失败: {str(e)}"
        print(error_msg)
        print(f"错误类型: {type(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            "code": 1,
            "message": "删除失败",
            "error": str(e)
        }), 500

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # 验证邮箱验证码
        if not db.verify_code(data['email'], data['verificationCode'], 'register'):
            return jsonify({
                'code': 1,
                'message': '验证码错误或已过期'
            })
        
        # 检查邮箱是否已存在
        if db.check_email_exists(data['email']):
            return jsonify({
                'code': 1,
                'message': '该邮箱已被注册'
            })
        
        # 继续原有的注册逻辑...
        success = db.register_user(data)
        if success:
            return jsonify({
                'code': 0,
                'message': '注册成功'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '注册失败'
            })
    except Exception as e:
        print(f"注册失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '注册失败',
            'error': str(e)
        }), 500

@app.route('/login')
@app.route('/login.html')
def login_page():
    """提供登录页面"""
    return send_from_directory(app.static_folder, 'login.html')

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file():
    try:
        username = request.current_user
        if not username:
            return jsonify({
                'code': 1,
                'message': '未登录'
            }), 401

        if 'file' not in request.files:
            return jsonify({
                'code': 1,
                'message': '没有文件'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'code': 1,
                'message': '没有选择文件'
            }), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{int(time.time())}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            task_id = str(uuid.uuid4())
            
            # 初始化任务状态
            db.save_task_status(
                task_id=task_id,
                status='processing',
                message='正在处理中...',
                username=username
            )

            # 启动异步处理
            thread = Thread(target=process_image_task, args=(task_id, filepath, username))
            thread.daemon = True
            thread.start()

            return jsonify({
                'code': 0,
                'data': {
                    'task_id': task_id
                }
            })

    except Exception as e:
        print(f"上传文件失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '上传失败',
            'error': str(e)
        }), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
@token_required
def get_task_status(task_id):
    try:
        username = request.current_user
        if not username:
            return jsonify({
                'code': 1,
                'message': '未提供用户名'
            }), 401

        # 获取任务状态
        task = db.get_task_status(task_id, username)
        if not task:
            return jsonify({
                'code': 1,
                'message': '任务不存在'
            }), 404

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'status': task['status'],
                'message': task['message'],
                'results': json.loads(task['results']) if task['results'] else None
            }
        })
    except Exception as e:
        print(f"获取任务状态失败: {str(e)}")
        traceback.print_exc()  # 打印详细错误信息
        return jsonify({
            'code': 1,
            'message': '服务器内部错误'
        }), 500

# 添加错误处理器
@app.errorhandler(500)
def handle_500_error(e):
    return jsonify({
        "code": 1,
        "message": "服务器内部错误",
        "error": str(e)
    }), 500

# 修改静态文件路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    # 获取项目根目录的绝对路径
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    parts = filename.split('/')
    if len(parts) > 1:
        subdir = parts[0]
        filename = '/'.join(parts[1:])
        # 使用绝对路径
        directory = os.path.join(root_dir, 'parking', subdir)
        print(f"Directory: {directory}")
        print(f"Filename: {filename}")
        print(f"Full path: {os.path.join(directory, filename)}")
        print(f"File exists: {os.path.exists(os.path.join(directory, filename))}")
        return send_from_directory(directory, filename)
    else:
        # 使用绝对路径
        directory = os.path.join(root_dir, 'parking')
        print(f"Directory: {directory}")
        print(f"Filename: {filename}")
        print(f"Full path: {os.path.join(directory, filename)}")
        print(f"File exists: {os.path.exists(os.path.join(directory, filename))}")
        return send_from_directory(directory, filename)

@app.route('/api/user/profile', methods=['GET'])
@token_required
def get_user_profile():
    """获取用户个人信息"""
    try:
        username = request.current_user
        user_info = db.get_user_info(username)
        
        if not user_info:
            return jsonify({
                'code': 1,
                'message': '用户信息不存在'
            }), 404
        print(f"获取用户信息 {user_info}")
        return jsonify({
            'code': 0,
            'data': {
                'username': user_info['username'],
                'license_plate': user_info['license_plate'],
                'user_no': user_info['user_no'],
                'openid': user_info['openid'],
                'email': user_info['email'],
                'created_at': user_info['created_at']
            }
        })
        
    except Exception as e:
        print(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取用户信息失败',
            'error': str(e)
        }), 500

@app.route('/api/user/profile', methods=['PUT'])
@token_required
def update_user_profile():
    """更新用户个人信息"""
    try:
        username = request.current_user
        data = request.get_json()
        
        # 验证数据
        required_fields = ['license_plate', 'user_no', 'openid', 'email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 1,
                    'message': f'缺少必要字段: {field}'
                })
        
        # 更新用户信息
        success = db.update_user_profile(
            username=username,
            license_plate=data['license_plate'],
            user_no=data['user_no'],
            openid=data['openid'],
            email=data['email']
        )
        
        if success:
            return jsonify({
                'code': 0,
                'message': '更新成功'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '更新失败'
            })
            
    except Exception as e:
        print(f"更新用户信息失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '更新失败',
            'error': str(e)
        }), 500

# 获取定时任务列表
@app.route('/api/schedules', methods=['GET'])
@token_required
def get_schedules():
    try:
        username = request.current_user
        if not username:
            return jsonify({
                'code': 1,
                'message': '未登录'
            }), 401

        schedules = db.get_schedules(username)
        return jsonify({
            'code': 0,
            'data': schedules
        })

    except Exception as e:
        print(f"获取定时任务失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取定时任务失败',
            'error': str(e)
        }), 500

# 创建定时任务
@app.route('/api/schedules', methods=['POST'])
@token_required
def create_schedule():
    """创建定时任务"""
    try:
        username = request.current_user
        
        # 检查用户信息
        user_info = db.get_user_info(username)
        if not user_info:
            return jsonify({
                'code': 1,
                'message': '用户信息不存在'
            }), 404
            
        # 检查必要信息是否完整
        if not user_info.get('openid') or not user_info.get('user_no'):
            return jsonify({
                'code': 1,
                'message': '请先完善微信 OpenID 和用户编号信息'
            }), 400
            
        data = request.get_json()
        
        # 将布尔值转换为整数
        auto_collect = 1 if data.get('auto_collect') else 0
        auto_pay = 1 if data.get('auto_pay') else 0
        
        success = db.create_schedule(
            username=username,
            hour=data.get('hour'),
            minute=data.get('minute'),
            weekdays=data.get('weekdays'),
            auto_collect=auto_collect,
            auto_pay=auto_pay
        )
        
        if success:
            return jsonify({
                'code': 0,
                'message': '创建成功'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '创建失败'
            })
            
    except Exception as e:
        print(f"创建定时任务失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '创建定时任务失败',
            'error': str(e)
        }), 500

# 删除定时任务
@app.route('/api/schedules/<int:task_id>', methods=['DELETE'])
@token_required
def delete_schedule(task_id):
    try:
        username = request.headers.get('X-Username')
        if not username:
            return jsonify({
                'code': 1,
                'message': '未登录'
            }), 401

        success = db.delete_schedule(username, task_id)
        if success:
            return jsonify({
                'code': 0,
                'message': '删除成功'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '删除失败'
            }), 500

    except Exception as e:
        print(f"删除定时任务失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '删除定时任务失败',
            'error': str(e)
        }), 500

# 获取任务执行历史
@app.route('/api/schedules/<int:task_id>/history', methods=['GET'])
@token_required
def get_schedule_history(task_id):
    try:
        username = request.current_user
        if not username:
            return jsonify({
                'code': 1,
                'message': '未登录'
            }), 401

        history = db.get_task_execution_history(task_id)
        return jsonify({
            'code': 0,
            'data': history
        })

    except Exception as e:
        print(f"获取任务执行历史失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取任务执行历史失败',
            'error': str(e)
        }), 500

# 更新定时任务
@app.route('/api/schedules/<int:task_id>', methods=['PUT'])
@token_required
def update_schedule(task_id):
    try:
        username = request.current_user
        if not username:
            return jsonify({
                'code': 1,
                'message': '未登录'
            }), 401

        data = request.get_json()
        hour = int(data.get('hour', 0))
        minute = int(data.get('minute', 0))
        weekdays = data.get('weekdays', '')
        auto_collect = data.get('auto_collect', True)  # 添加自动领券字段，默认为 True
        auto_pay = data.get('auto_pay', False)        # 添加自动核销字段，默认为 False

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return jsonify({
                'code': 1,
                'message': '无效的时间'
            }), 400

        if not weekdays:
            return jsonify({
                'code': 1,
                'message': '请选择执行日期'
            }), 400

        success = db.update_schedule(
            username=username,
            task_id=task_id,
            hour=hour,
            minute=minute,
            weekdays=weekdays,
            auto_collect=auto_collect,
            auto_pay=auto_pay
        )

        if success:
            return jsonify({
                'code': 0,
                'message': '更新成功'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '更新失败'
            }), 500

    except Exception as e:
        print(f"更新定时任务失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '更新定时任务失败',
            'error': str(e)
        }), 500

# 获取核销记录
@app.route('/api/execution-logs', methods=['GET'])
@token_required
def get_execution_logs():
    try:
        username = request.current_user
        if not username:
            return jsonify({
                'code': 1,
                'message': '未登录'
            }), 401

        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')

        logs, total = db.get_execution_logs(
            username=username,
            page=page,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date,
            status=status
        )

        return jsonify({
            'code': 0,
            'data': {
                'logs': logs,
                'total': total
            }
        })

    except Exception as e:
        print(f"获取核销记录失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取核销记录失败',
            'error': str(e)
        }), 500

@app.route('/styles.css')
def styles():
    return send_from_directory(app.static_folder, 'styles.css')

@app.route('/app.js')
def app_js():
    return send_from_directory(app.static_folder, 'app.js')

@app.route('/register')
def register_page():
    """提供注册页面"""
    return send_from_directory(app.static_folder, 'register.html')

@app.route('/register.html')
def register_html():
    """提供注册页面（兼容 .html 后缀）"""
    return send_from_directory(app.static_folder, 'register.html')

# 生成验证码
def generate_captcha():
    """生成验证码 - 平衡可读性和安全性"""
    width = 160
    height = 60
    # 使用容易识别的字符（去掉容易混淆的字符）
    chars = ''.join(random.choices('23456789ABCDEFGHJKLMNPQRSTUVWXYZ', k=4))
    
    # 创建图像，使用白色背景
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 添加背景干扰点（颜色淡一些）
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point([x, y], fill=(
            random.randint(210, 240),
            random.randint(210, 240),
            random.randint(210, 240)
        ))
    
    # 添加干扰线（颜色淡一些，数量适中）
    for _ in range(3):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        line_color = (
            random.randint(180, 220),
            random.randint(180, 220),
            random.randint(180, 220)
        )
        draw.line([start, end], fill=line_color, width=1)
    
    # 添加文字
    for i, char in enumerate(chars):
        # 使用深色文字
        color = (random.randint(0, 30), random.randint(0, 30), random.randint(0, 30))
        
        # 位置有轻微随机偏移
        x = 30 + i * 30 + random.randint(-2, 2)
        y = random.randint(10, 20)
        
        # 轻微的旋转角度
        angle = random.randint(-15, 15)
        
        # 绘制字符
        draw.text((x, y), char, fill=color, font=None, font_size=38)
    
    # 添加轻微的波浪扭曲
    pixels = image.load()
    for i in range(width):
        for j in range(height):
            offset_x = int(math.sin(j * 0.3) * 1.3)
            if 0 <= i + offset_x < width:
                pixels[i, j] = pixels[(i + offset_x) % width, j]
    
    # 保存到内存
    buffer = BytesIO()
    image.save(buffer, format='PNG', quality=95)
    return chars, buffer.getvalue()

@app.route('/api/captcha', methods=['GET'])
def get_captcha():
    """获取验证码"""
    try:
        chars, image_data = generate_captcha()
        
        # 生成一个临时的验证码 token
        captcha_token = os.urandom(16).hex()
        # 将验证码存储在内存中，设置5分钟过期
        app.config[f'captcha_{captcha_token}'] = chars
        # 5分钟后自动删除
        def delete_captcha():
            time.sleep(300)
            app.config.pop(f'captcha_{captcha_token}', None)
        Thread(target=delete_captcha, daemon=True).start()
        
        print(f"Generated captcha: {chars}")
        
        # 将图片数据转换为字节流
        image_stream = BytesIO(image_data)
        response = send_file(
            image_stream,
            mimetype='image/png'
        )
        
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.set_cookie('captcha_token', captcha_token, max_age=300, httponly=True)
        
        return response

    except Exception as e:
        print(f"生成验证码失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': '生成验证码失败'
        }), 500

def verify_captcha(captcha):
    """验证验证码"""
    if not captcha:
        return False
    
    captcha_token = request.cookies.get('captcha_token')
    if not captcha_token:
        return False
    
    stored_captcha = app.config.get(f'captcha_{captcha_token}')
    if not stored_captcha:
        return False
    
    print(f"Stored captcha: {stored_captcha}, Received captcha: {captcha}")
    
    # 验证成功后删除验证码
    if captcha.upper() == stored_captcha.upper():
        app.config.pop(f'captcha_{captcha_token}', None)
        return True
    return False

# 修改为 api_login
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        captcha = data.get('captcha')
        
        # 获取请求信息
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        print(f"Login attempt for user: {username}")

        # 验证验证码
        if not verify_captcha(captcha):
            print("Captcha verification failed")
            # 记录失败的登录
            db.log_login(
                username=username,
                ip_address=ip_address,
                status=0,  # 0 表示失败
                fail_reason='验证码错误',
                user_agent=user_agent
            )
            return jsonify({
                'code': 1,
                'message': '验证码错误'
            })

        # 验证用户名和密码
        user = db.get_user_by_username(username)
        if not user or not check_password_hash(user['password'], password):
            print("Invalid username or password")
            # 记录失败的登录
            db.log_login(
                username=username,
                ip_address=ip_address,
                status=0,  # 0 表示失败
                fail_reason='用户名或密码错误',
                user_agent=user_agent
            )
            return jsonify({
                'code': 1,
                'message': '用户名或密码错误'
            })

        # 生成 token
        token = generate_token({'username': username})
        print(f"Generated token for user {username}")
        
        # 记录成功的登录
        db.log_login(
            username=username,
            ip_address=ip_address,
            status=1,  # 1 表示成功
            user_agent=user_agent
        )
        
        # 创建响应
        response = make_response(jsonify({
            'code': 0,
            'message': '登录成功',
            'data': {
                'username': username,
                'license_plate': user.get('license_plate'),
                'user_no': user.get('user_no')
            }
        }))
        
        # 设置 token cookie
        cookie_domain = None  # 或者设置为你的域名，比如 '.awen.me'
        response.set_cookie(
            'token',
            token,
            httponly=True,
            secure=True,  # 如果是 HTTPS 则设为 True
            samesite='Lax',
            max_age=86400,  # 24小时
            domain=cookie_domain
        )
        print("Cookie set successfully")
        
        return response

    except Exception as e:
        print(f"登录失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '登录失败'
        })

@app.route('/api/share-code', methods=['POST'])
@token_required
def share_code():
    try:
        username = request.current_user
        data = request.get_json()
        code_ids = data.get('code_ids')
        to_username = data.get('username')

        if username == to_username:
            return jsonify({
                'code': 1,
                'message': '不能分享给自己'
            }), 400

        # 验证参数
        if not code_ids or not to_username:
            return jsonify({
                'code': 1,
                'message': '参数错误'
            }), 400
            
        # 验证用户是否存在
        user = db.get_user_by_username(to_username)
        if not user:
            return jsonify({
                'code': 1,
                'message': '用户不存在'
            }), 404
            
        # 更新券码所有者
        success = db.update_code_owner(code_ids, to_username)
        if success:
            # 添加分享记录
            if isinstance(code_ids, str):
                code_ids = [code_ids]
            share_success = db.add_share_record(username, to_username, code_ids)
            if not share_success:
                print("添加分享记录失败")
                
            # 获取实际分享的数量
            shared_count = len(code_ids)
                
            return jsonify({
                'code': 0,
                'message': f'分享成功，共分享 {shared_count} 张券码',
                'data': {
                    'shared_count': shared_count
                }
            })
        else:
            return jsonify({
                'code': 1,
                'message': '分享失败，可能券码已被核销或不存在'
            }), 500
            
    except Exception as e:
        print(f"分享券码失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'code': 1,
            'message': '服务器内部错误'
        }), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        print(f"收到重置密码请求: {data}")  # 添加日志
        
        # 验证必要字段是否存在
        required_fields = ['username', 'email', 'verificationCode', 'new_password']
        for field in required_fields:
            if field not in data:
                print(f"缺少字段: {field}")  # 添加日志
                return jsonify({
                    'code': 1,
                    'message': f'缺少必要字段: {field}'
                })
        
        # 验证用户名是否存在
        user = db.get_user_by_username(data['username'])
        print(f"查询到的用户信息: {user}")  # 添加日志
        
        if not user:
            return jsonify({
                'code': 1,
                'message': '用户名不存在'
            })
        
        # 验证邮箱是否匹配
        if user['email'] != data['email']:
            print(f"邮箱不匹配: 期望 {user['email']}, 实际 {data['email']}")  # 添加日志
            return jsonify({
                'code': 1,
                'message': '邮箱地址不匹配'
            })
        
        # 验证邮箱验证码
        if not db.verify_code(data['email'], data['verificationCode'], 'reset'):
            print("验证码验证失败")  # 添加日志
            return jsonify({
                'code': 1,
                'message': '验证码错误或已过期'
            })
        
        # 更新密码
        success = db.update_password(data['username'], data['new_password'])
        print(f"密码更新结果: {success}")  # 添加日志
        
        if success:
            return jsonify({
                'code': 0,
                'message': '密码重置成功'
            })
        else:
            return jsonify({
                'code': 1,
                'message': '密码重置失败'
            })
    except Exception as e:
        print(f"重置密码失败: {str(e)}")
        print(f"错误类型: {type(e)}")
        print(f"错误详情: {traceback.format_exc()}")  # 添加完整的错误堆栈
        return jsonify({
            'code': 1,
            'message': '重置密码失败',
            'error': str(e)
        }), 500

@app.route('/api/share-records', methods=['GET'])
@token_required
def get_share_records():
    """获取分享记录"""
    try:
        username = request.current_user
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        
        total, records = db.get_share_records(username, page, page_size)
        
        return jsonify({
            'code': 0,
            'data': {
                'total': total,
                'records': records
            }
        })
    except Exception as e:
        print(f"获取分享记录失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '获取分享记录失败'
        }), 500

@app.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    """发送验证码"""
    try:
        data = request.get_json()
        email = data.get('email')
        type_str = data.get('type')  # register 或 reset
        
        if not email or not type_str:
            return jsonify({
                'code': 1,
                'message': '参数错误'
            })
        
        # 生成验证码
        code = EmailSender.generate_verification_code()
        
        # 发送验证码邮件
        if email_sender.send_verification_code(email, code, type_str):
            # 保存验证码记录
            if db.add_verification_code(email, code, type_str):
                return jsonify({
                    'code': 0,
                    'message': '验证码已发送'
                })
        
        return jsonify({
            'code': 1,
            'message': '发送验证码失败'
        })
    except Exception as e:
        print(f"发送验证码失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '发送验证码失败'
        }), 500

# 添加静态文件路由
@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('../frontend/js', filename)

@app.route('/api/check-email', methods=['POST'])
def check_email():
    """检查邮箱是否已被注册"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({
                'code': 1,
                'message': '参数错误'
            })
        
        # 检查邮箱是否已存在
        if db.check_email_exists(email):
            return jsonify({
                'code': 1,
                'message': '该邮箱已被注册'
            })
        
        return jsonify({
            'code': 0,
            'message': '邮箱可用'
        })
    except Exception as e:
        print(f"检查邮箱失败: {str(e)}")
        return jsonify({
            'code': 1,
            'message': '检查邮箱失败'
        }), 500
