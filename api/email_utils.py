import smtplib
import yaml
import os
from email.mime.text import MIMEText
from email.header import Header
import random
import string
from datetime import datetime, timedelta

class EmailSender:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config = self._load_config()
            self.smtp_server = self.config['smtp_server']
            self.smtp_port = self.config['smtp_port']
            self.sender = self.config['sender']
            self.password = self.config['password']
            self.initialized = True
    
    def _load_config(self):
        """加载邮箱配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config['email']
    
    def send_verification_code(self, to_email: str, code: str, type_str: str):
        """
        发送验证码邮件
        :param to_email: 收件人邮箱
        :param code: 验证码
        :param type_str: 验证码类型(register/reset)
        :return: 是否发送成功
        """
        try:
            # 根据类型设置不同的主题和内容
            if type_str == 'register':
                subject = '注册验证码'
                content = f'您的注册验证码是：{code}，有效期5分钟。请勿将验证码泄露给他人。'
            else:
                subject = '重置密码验证码'
                content = f'您的重置密码验证码是：{code}，有效期5分钟。请勿将验证码泄露给他人。'
            
            message = MIMEText(content, 'plain', 'utf-8')
            message['From'] = Header(self.sender)
            message['To'] = Header(to_email)
            message['Subject'] = Header(subject)
            
            # 连接SMTP服务器并发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender, self.password)
                server.sendmail(self.sender, [to_email], message.as_string())
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False

    @staticmethod
    def generate_verification_code():
        """生成6位数字验证码"""
        return ''.join(random.choices(string.digits, k=6)) 