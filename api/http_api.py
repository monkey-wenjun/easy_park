from random import randint, choice
import string
from requests import post, get
import os
import yaml

class ParkingAPI:
    """停车场 API 接口类，用于处理所有与停车场服务器的 HTTP 请求"""
    
    def __init__(self, app_id=None, headers=None, car_no=None, user_no=None, openid=None):
        """
        初始化停车场 API 客户端
        :param app_id: 微信小程序的 APP ID
        :param headers: HTTP 请求头
        :param car_no: 车牌号码
        :param user_no: 用户编号
        :param openid: 微信开放平台 ID
        """
        # 从配置文件加载默认值
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            wechat_config = config.get('wechat', {})
            
        self.app_id = app_id or wechat_config.get('app_id')
        self.headers = headers or wechat_config.get('headers', {})
        self.car_no = car_no
        self.user_no = user_no
        self.openid = openid

    @staticmethod
    def generate_random_float():
        """
        生成随机浮点数
        :return: 17位精度的随机浮点数字符串
        """
        num1 = randint(1, 10)
        num2 = randint(1, 99)
        result = num1 / num2
        formatted_result = "{:.17f}".format(result)
        return formatted_result

    @staticmethod
    def generate_random_string(length):
        """
        生成指定长度的随机字符串
        :param length: 需要生成的字符串长度
        :return: 包含数字和字母的随机字符串
        """
        all_characters = string.digits + string.ascii_uppercase + string.ascii_lowercase
        random_list = [choice(all_characters) for _ in range(length)]
        random_string = ''.join(random_list)
        return random_string

    def login(self):
        """
        登录接口
        :return: 成功返回登录响应信息，失败返回 False
        """
        t_value = self.generate_random_float()
        url = f"https://parkingczsmall.ymlot.cn/OAuth/InitConfig?t={t_value}"
        data = {"appid": self.app_id}
        response = post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            resp_json = response.json()
            print(resp_json)
            if resp_json.get("msg") == "ok":
                return resp_json
        return False

    def create_code(self, token, park_no, code_no):
        """
        领取停车优惠券
        :param token: 登录令牌
        :param park_no: 停车场编号
        :param code_no: 优惠券编号
        :return: 成功返回优惠券信息，失败返回 False
        """
        t_value = self.generate_random_float()
        url = f"https://parkingczsmall.ymlot.cn/Business/CollectCoupon?t={t_value}"
        data = {
            "parkno": park_no,
            "carno": self.car_no,
            "solutionno": code_no,
            "token": token,
            "t": "3",
            "openid": self.openid,
            "appid": self.app_id,
            "usersno": self.user_no,
            "phone": ""
        }
        response = post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            resp_json = response.json()
            print(resp_json)
            if resp_json.get("msg") == "ok":
                return resp_json
        return False

    def get_user_coupon_list(self):
        t_value = self.generate_random_float()
        url = f"https://parkingczsmall.ymlot.cn/Order/GetUserCouponList?t={t_value}"
        data = {
                "status": "",
                "pageIndex": 1,
                "pageSize": 10,
                "appid": self.app_id,
                "usersno": self.user_no,
                "phone": ""
            }
        response = post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("msg") == "ok":
                return resp_json
        return False

    def query_code(self, code_id):
        """
        查询优惠券使用状态
        :param code_id: 优惠券 ID
        :return: 成功返回优惠券状态信息，失败返回 False
        """
        t_value = self.generate_random_float()
        generate_random_string_code = self.generate_random_string(32)
        url = f"https://parkingczsmall.ymlot.cn/Business/GetCouponSolutionByQrCode?t={t_value}"
        data = {
            "d": code_id,
            "code": generate_random_string_code,
            "appid": self.app_id,
            "usersno": self.user_no,
            "phone": "",
        }
        response = post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("msg") == "ok":
                return resp_json
        return False

    def get_order(self):
        """
        获取车辆订单信息
        :return: 成功返回订单信息，失败返回 False
        """
        t_value = self.generate_random_float()
        url = f"https://parkingczsmall.ymlot.cn/Pay/GetOrderCarNo?t={t_value}"
        data = {
            "parkno": "",
            "carno": self.car_no,
            "appid": self.app_id,
            "usersno": self.user_no,
            "phone": ""
        }
        print(f"query_code {data}")
        response = post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            resp_json = response.json()
            print(resp_json)
            if resp_json.get("msg") == "ok":
                return resp_json
        return False

    def get_park_order(self, park_no, order_no):
        """
        获取停车场订单详细信息
        :param park_no: 停车场编号
        :param order_no: 订单编号
        :return: 成功返回订单详细信息，失败返回 False
        """
        t_value = self.generate_random_float()
        url = f"https://parkingczsmall.ymlot.cn/Pay/GetParkOrder?t={t_value}"
        data = {
            "parkno": park_no,
            "orderno": order_no,
            "appid": self.app_id,
            "usersno": self.user_no,
            "phone": ""
        }
        response = post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("msg") == "ok":
                print(resp_json)
                return resp_json
        return False

    def get_pay_pirce(self, park_no, order_no, code_no):
        """
        获取支付金额信息
        :param park_no: 停车场编号
        :param order_no: 订单编号
        :param code_no: 优惠券编号
        :return: 成功返回支付金额信息，失败返回 False
        """
        t_value = self.generate_random_float()
        url = f"https://parkingczsmall.ymlot.cn/Pay/GetPayPirce?t={t_value}"
        data = {
            "parkno": park_no,
            "orderno": order_no,
            "coupons": f"[\"{code_no}\"]",
            "appid": self.app_id,
            "usersno": self.user_no,
            "phone": ""
        }
        print(f"query_code {data}")
        response = post(url, headers=self.headers, json=data)

        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("msg") == "ok":
                print(resp_json)
                return resp_json
        return False

    def on_pay_transactions(self, park_no, order_no, code_no):
        """
        执行支付交易
        :param park_no: 停车场编号
        :param order_no: 订单编号
        :param code_no: 优惠券编号
        :return: 成功返回支付结果，失败返回 False
        """
        t_value = self.generate_random_float()
        url = f"https://parkingczsmall.ymlot.cn/Pay/OnPayTransactions?t={t_value}"
        data = {
            "parkno": park_no,
            "passwayno": "",
            "orderno": order_no,
            "coupons": f"[\"{code_no}\"]",
            "qforderno": "[]",
            "appid": self.app_id,
            "usersno": self.user_no,
            "phone": ""
        }
        print(f"query_code {data}")
        response = post(url, headers=self.headers, json=data)
        print(response.json())
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("msg") == "支付成功":
                return True
        return False