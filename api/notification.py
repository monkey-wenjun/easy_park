from requests import get
from typing import Optional

class NotificationService:
    """通知服务类，用于处理各种通知消息"""
    
    def __init__(self, bark_key: str = "jszYkyQV7bnp3xRU63jcHF"):
        """
        初始化通知服务
        :param bark_key: Bark 应用的 API key
        """
        self.bark_key = bark_key
        self.bark_base_url = "https://api.day.app"

    def send_bark_notification(self, message: str, title: Optional[str] = None) -> bool:
        """
        发送 Bark 通知
        :param message: 通知消息内容
        :param title: 通知标题（可选）
        :return: 发送是否成功
        """
        try:
            url = f"{self.bark_base_url}/{self.bark_key}/"
            if title:
                url += f"{title}/"
            url += message
            
            response = get(url)
            if response.status_code == 200:
                print(f"通知发送成功: {message}")
                return True
            else:
                print(f"通知发送失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"通知发送出错: {str(e)}")
            return False 
