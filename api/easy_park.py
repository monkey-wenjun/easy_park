from time import sleep
from api.http_api import ParkingAPI
from api.ocr_class import QRCodeProcessor
from api.notification import NotificationService
import os
import yaml
from db import DatabaseManager
from datetime import datetime


class EasyPark:
    def __init__(self):
        # 加载配置文件
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yml')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.db = DatabaseManager()
        self.qr = QRCodeProcessor()
        self.notification = NotificationService()

    def update_coupon_status(self, code_id: str, transaction_result: bool):
        """
        更新优惠券状态
        :param code_id: 券码ID
        :param transaction_result: 交易结果
        """
        if transaction_result:
            try:
                self.db.update_status(code_id, 1)  # 1 表示已核销
            except Exception as e:
                print(f"更新券码状态失败: {str(e)}")

    def process_payment(self, api, code_id: str, parking_no: str, park_order_no: str, code_no: str, task: dict, coupons=None):
        """
        处理支付流程
        :param api:
        :param code_id: 券码ID
        :param parking_no: 停车场编号
        :param park_order_no: 订单编号
        :param code_no: 券码编号
        :param task: 当前执行的任务信息
        :param coupons: 是否已有优惠券
        :return: 使用的优惠券编号
        """
        if not coupons:
            # 领取优惠券
            api.create_code(code_id, parking_no, code_no)
            get_park_order = api.get_park_order(parking_no, park_order_no)
            coupons = get_park_order.get("data").get("coupons")
        else:
            print("有可用优惠券直接支付")
        use_code_no = coupons[0]["CouponRecord_No"]
        api.get_pay_pirce(parking_no, park_order_no, use_code_no)
        # 检查任务的 auto_pay 设置
        if task['auto_pay'] != 1:
            print("自动支付未开启，跳过支付步骤")
            return use_code_no
        
        transaction_result = api.on_pay_transactions(parking_no, park_order_no, use_code_no)
        print(f"transaction_result {transaction_result}")
        if transaction_result:
            self.update_coupon_status(code_id, transaction_result)
        return use_code_no

    def process_unused_coupons(self):
        """处理未使用的券码"""
        try:
            # 获取当前时间信息
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute
            current_weekday = str(now.weekday())  # 0-6 表示周一到周日
            # 从 schedule_tasks 表获取符合当前时间的任务
            active_tasks = self.db.get_active_schedules()
            print(f"active_tasks {active_tasks}")
            if not active_tasks:
                print("没有找到符合条件的定时任务")
                return False

            processed = False
            for task in active_tasks:
                # 检查时间是否匹配
                user_info = self.db.get_user_by_username(task['username'])
                if (task['hour'] == current_hour and
                        task['minute'] == current_minute and
                        current_weekday in task['weekdays'].split(',')):

                    # 获取任务用户的信息
                    user = self.db.get_user_by_username(task['username'])
                    if not user:
                        print(f"未找到用户信息: {task['username']}")
                        continue
                    api = ParkingAPI(
                        app_id=self.config['wechat']['app_id'],
                        headers=self.config['wechat']['headers'],
                        car_no=user_info['license_plate'],
                        user_no=user_info['user_no'],
                        openid=user_info['openid']
                    )
                    get_order = api.get_order()
                    if get_order is False or get_order.get("data") is None:
                        print("没有需要支付的订单")
                        self.db.log_task_execution(
                            task_id=task['id'],
                            status=processed,
                            error_message=None if processed else f"用户 {task['username']} 没有需要支付的订单"
                        )
                        return
                    print(get_order)
                    # 获取该用户未使用的券码
                    unused_codes = self.db.get_unused_codes(task['username'])
                    if not unused_codes:
                        print(f"用户 {task['username']} 没有未使用的券码")
                        self.db.log_task_execution(
                            task_id=task['id'],
                            status=processed,
                            error_message=None if processed else f"用户 {task['username']} 没有未使用的券码"
                        )
                        return
                    code = unused_codes[0]
                    code_id = code['code_id']
                    print(f"处理券码: {code_id}")
                    # 判断券是否已核销
                    query_code = api.query_code(code_id)
                    if query_code is False:
                        print(f"券码 {code_id} 已被领取")
                        # 更新数据库状态
                        self.db.update_status(code_id, 1)
                        return False
                    code_no = query_code.get("data", {}).get("no")
                    # 获取券码相关信息
                    parking_no = get_order.get("data").get("ParkOrder_ParkNo")

                    # 获取订单信息
                    park_order_no = get_order.get("data", {}).get("ParkOrder_No")
                    get_park_order = api.get_park_order(parking_no, park_order_no)
                    coupons = get_park_order.get("data", {}).get("coupons")
                    try:
                        # 处理支付
                        if coupons:
                            use_code_no = self.process_payment(api, code_id, parking_no, park_order_no, code_no, task, coupons=coupons)
                        else:
                            use_code_no = self.process_payment(api, code_id, parking_no, park_order_no, code_no, task)
                        # 发送通知
                        self.notification.send_bark_notification(f"停车券已领取并核销,券码{use_code_no}")
                        # 记录任务执行
                        processed = True
                        self.db.log_task_execution(
                            task_id=task['id'],
                            status=processed,
                            error_message=None if processed else "没有成功核销的券码"
                        )
                    except Exception as e:
                        print(f"处理券码 {code_id} 失败: {str(e)}")
                        self.db.log_task_execution(
                            task_id=task['id'],
                            status=processed,
                            error_message=None if processed else f"处理券码 {code_id} 失败: {str(e)}"
                        )
            return processed

        except Exception as e:
            print(f"处理未使用券码失败: {str(e)}")
            return False

    def main(self):
        self.process_unused_coupons()


if __name__ == '__main__':
    easy = EasyPark()
    easy.main()
