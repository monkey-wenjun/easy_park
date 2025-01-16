import os
import secrets

def generate_jwt_secret():
    """生成一个安全的 JWT 密钥"""
    return secrets.token_hex(32)

def create_env_file():
    """创建或更新 .env 文件"""
    jwt_secret = generate_jwt_secret()
    
    env_content = f"""JWT_SECRET={jwt_secret}
MYSQL_ROOT_PASSWORD=1ux2Dewk2xdrk5uqh.CMU
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("已生成新的 .env 文件")
    print(f"JWT_SECRET={jwt_secret}")

if __name__ == "__main__":
    create_env_file() 