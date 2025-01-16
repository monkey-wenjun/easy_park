import jwt
import datetime
from functools import wraps
from flask import request, jsonify, make_response
import os

# 生成随机密钥
JWT_SECRET = os.environ.get('JWT_SECRET', os.urandom(24).hex())
JWT_ALGORITHM = 'HS256'
DEFAULT_EXPIRATION = datetime.timedelta(days=1)
REMEMBER_EXPIRATION = datetime.timedelta(days=30)

def generate_token(user_data, remember=False):
    """生成 JWT token"""
    payload = {
        'username': user_data['username'],
        'exp': datetime.datetime.utcnow() + (REMEMBER_EXPIRATION if remember else DEFAULT_EXPIRATION),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def token_required(f):
    """验证 JWT token 的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        
        print("Checking token:", token)
        
        if not token:
            print("No token found in cookies")
            return jsonify({
                'code': 1,
                'message': '未登录'
            }), 401

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            print("Token decoded successfully:", payload)
            request.current_user = payload['username']
        except jwt.ExpiredSignatureError:
            print("Token expired")
            response = make_response(jsonify({
                'code': 1,
                'message': 'token已过期'
            }))
            response.delete_cookie('token')
            return response, 401
        except jwt.InvalidTokenError:
            print("Invalid token")
            response = make_response(jsonify({
                'code': 1,
                'message': '无效的token'
            }))
            response.delete_cookie('token')
            return response, 401
        except Exception as e:
            print(f"Unexpected error decoding token: {str(e)}")
            return jsonify({
                'code': 1,
                'message': '认证失败'
            }), 401

        return f(*args, **kwargs)
    return decorated 