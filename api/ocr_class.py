import cv2
import os
import glob
import re
import numpy as np
from pyzbar import pyzbar
import qrcode

class QRCodeProcessor:
    """二维码处理类，用于处理图像识别和二维码相关操作"""
    
    def __init__(self, config_path=None):
        """
        初始化二维码处理器
        :param config_path: 配置文件路径
        """
        if config_path is None:
            # 使用项目根目录下的 config 路径
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, 'config')
            
        # 确保配置文件存在
        self.depro = os.path.join(config_path, 'detect.prototxt')
        self.decaf = os.path.join(config_path, 'detect.caffemodel')
        self.srpro = os.path.join(config_path, 'sr.prototxt')
        self.srcaf = os.path.join(config_path, 'sr.caffemodel')

        # 检查文件是否存在
        required_files = [
            (self.depro, 'detect.prototxt'),
            (self.decaf, 'detect.caffemodel'),
            (self.srpro, 'sr.prototxt'),
            (self.srcaf, 'sr.caffemodel')
        ]
        
        for file_path, file_name in required_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"找不到必要的配置文件: {file_name}")

    def detect_and_decode_qrcodes(self, image_path_list):
        """
        检测和解码图片中的二维码
        :param image_path_list: 图片路径列表
        :return: 识别到的二维码列表
        """
        qrcodes_list = []
        for image_path in image_path_list:
            # 加载原始图像
            image = cv2.imread(image_path)
            file_name = str(image_path).split("/")[-1]
            all_qr_codes = []
            marked_image = image.copy()  # 创建原始图像的副本用于标记
            
            # 1. 增加更多的缩放比例
            scale_factors = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5]
            
            # 2. 添加图像预处理步骤
            for scale in scale_factors:
                resized_image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                
                # 增加对比度
                lab = cv2.cvtColor(resized_image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                cl = clahe.apply(l)
                enhanced_image = cv2.merge((cl,a,b))
                enhanced_image = cv2.cvtColor(enhanced_image, cv2.COLOR_LAB2BGR)
                
                # 使用不同的阈值进行二值化处理
                gray = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2GRAY)
                thresholds = [cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV]
                for threshold in thresholds:
                    _, binary = cv2.threshold(gray, 127, 255, threshold)
                    
                    # 3. 尝试多种解码方法
                    # 使用pyzbar
                    decoded_pyzbar = pyzbar.decode(binary)
                    for obj in decoded_pyzbar:
                        qr_data = obj.data.decode('utf-8')
                        if qr_data not in all_qr_codes:
                            all_qr_codes.append(qr_data)
                            # 在原始大小的图像上标记
                            rect_points = obj.rect
                            x, y = rect_points.left, rect_points.top
                            w, h = rect_points.width, rect_points.height
                            # 根据缩放比例调整坐标
                            x, y = int(x/scale), int(y/scale)
                            w, h = int(w/scale), int(h/scale)
                            cv2.rectangle(marked_image, (x, y), (x + w, y + h), (0, 0, 255), 5)
                            cv2.putText(marked_image, f"#{len(all_qr_codes)}", 
                                      (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 
                                      1, (0, 0, 255), 2)
                    
                    # 使用WeChatQRCode检测器
                    detector = cv2.wechat_qrcode.WeChatQRCode(self.depro, self.decaf, self.srpro, self.srcaf)

                    # 尝试不同的图像处理方法
                    processing_methods = [
                        lambda img: img,  # 原始图像
                        lambda img: cv2.convertScaleAbs(img, alpha=1.2, beta=10),  # 增加亮度
                        lambda img: cv2.convertScaleAbs(img, alpha=0.8, beta=-10),  # 降低亮度
                        lambda img: cv2.filter2D(img, -1, np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])),  # 锐化
                        lambda img: cv2.GaussianBlur(img, (3, 3), 0),  # 高斯模糊
                    ]

                    for process in processing_methods:
                        try:
                            processed_img = process(binary)
                            if len(processed_img.shape) == 2:  # 如果是灰度图
                                processed_img = cv2.cvtColor(processed_img, cv2.COLOR_GRAY2BGR)
                            
                            res, points = detector.detectAndDecode(processed_img)
                            for i, qr_data in enumerate(res):
                                if qr_data not in all_qr_codes:
                                    all_qr_codes.append(qr_data)
                                    if points is not None and len(points) > i:
                                        point = points[i]
                                        x = int(min(point[:, 0])/scale)
                                        y = int(min(point[:, 1])/scale)
                                        w = int(max(point[:, 0])/scale - x)
                                        h = int(max(point[:, 1])/scale - y)
                                        cv2.rectangle(marked_image, (x, y), (x + w, y + h), (0, 0, 255), 5)
                                        text = f"#{len(all_qr_codes)}"
                                        cv2.putText(marked_image, text, 
                                                  (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 
                                                  1, (0, 0, 255), 2)
                        except Exception as e:
                            print(f"处理方法出错: {str(e)}")
                            continue
            
            # 确保输出目录存在
            output_dir = '../parking/output_file'
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存标记后的图像
            output_image_path = os.path.join(output_dir, f'marked_{file_name}')
            cv2.imwrite(output_image_path, marked_image)
            
            print(f"标记后的图像已保存到: {output_image_path}")
            print("识别到的二维码内容:")
            for idx, code in enumerate(all_qr_codes, 1):
                print(f"二维码 {idx}: {code}")
                qrcodes_list.append(code)
                
        return qrcodes_list

    def singe_detect_and_decode_qrcodes(self, image_path_list):
        """
        单独检测和解码图片中的二维码
        :param image_path_list: 图片路径列表
        :return: 识别到的二维码列表
        """
        qrcodes_list = []
        for image_path in image_path_list:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            detector = cv2.wechat_qrcode.WeChatQRCode(self.depro, self.decaf, self.srpro, self.srcaf)
            res, points = detector.detectAndDecode(gray)
            for pos in points:
                color = (0, 0, 255)
                thick = 3
                for p in [(0, 1), (1, 2), (2, 3), (3, 0)]:
                    start = int(pos[p[0]][0]), int(pos[p[0]][1])
                    end = int(pos[p[1]][0]), int(pos[p[1]][1])
                    cv2.line(img, start, end, color, thick)
            for i in res:
                qrcodes_list.append(str(i))
        return qrcodes_list

    @staticmethod
    def get_image_list(directory):
        """
        获取目录下的所有图片文件
        :param directory: 目录路径
        :return: 图片文件路径列表
        """
        image_types = ['jpg', 'jpeg', 'png']
        image_list = []
        image_list_suffix = []
        for image_type in image_types:
            pattern = os.path.join(directory, f'*.{image_type}')
            image_list.extend(glob.glob(pattern))
        for img in image_list:
            if not re.search("_", os.path.basename(img)):
                image_list_suffix.append(img)
        return image_list_suffix

    def process_parking_images(self, parking_directory):
        """
        处理停车场图片并生成二维码
        :param parking_directory: 停车场图片目录
        :return: 处理后的二维码ID列表
        """
        get_image_list = self.get_image_list(parking_directory)
        return self.detect_and_decode_qrcodes(get_image_list)

    @staticmethod
    def save_qrcode(code_id, file_path):
        """
        保存二维码图片
        :param code_id: 二维码内容
        :param file_path: 保存路径
        """
        img = qrcode.make(data=code_id)
        with open(file_path, 'wb') as f:
            img.save(f) 
