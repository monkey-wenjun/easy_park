# 停车票管理系统

一个基于 Flask + Vue + MySQL 的停车票管理系统，支持停车券的扫描、管理、分享和自动使用。

## 项目结构
```
parking-system/
├── api/ # 后端 API 实现
│ ├── app.py # Flask 主应用
│ ├── auth.py # 认证相关
│ ├── http_api.py # HTTP 请求封装
│ ├── ocr_class.py # 二维码处理
│ └── easy_park.py # 停车场业务逻辑
├── config/ # 配置文件
│ └── config.yml # 主配置文件
├── db/ # 数据库相关文件
│ ├── init.sql # 数据库初始化脚本
│ └── mysql.cnf # MySQL 配置
├── frontend/ # 前端文件
│ ├── index.html # 主页面
│ ├── login.html # 登录页面
│ └── register.html # 注册页面
├── scripts/ # 工具脚本
├── docker compose.yml # Docker 编排配置
├── Dockerfile # Docker 构建文件
├── run_api.py # 应用启动脚本
└── requirements.txt # Python 依赖
``` 

## 功能特点

- 🎫 停车券管理：支持扫描、存储和管理停车券
- 📱 自动核销：支持定时自动领取和使用停车券
- 🔄 批量处理：支持批量上传和处理停车券图片
- 👥 分享功能：支持将停车券分享给其他用户
- 🔍 查询功能：支持按时间、状态等条件查询停车券
- 👤 用户管理：支持用户注册、登录、找回密码等功能
- 📊 数据统计：提供停车券使用情况的统计信息

## 系统要求

- Python 3.11+
- MySQL 8.0+
- Docker & Docker Compose
- Node.js 14+ (仅开发环境需要)

## 快速开始

### 1. 克隆项目 
```
bash
git clone https://github.com/yourusername/parking-system.git
cd parking-system
```
### 3. 使用 Docker Compose 部署

1. 构建并启动服务： 
```

2. 创建并配置 `config/config.yml`：
```yaml
wechat:
  app_id: "你的小程序APPID"
  wx_open_id: "微信OpenID"
  headers:
    User-Agent: "Mozilla/5.0..."
    # 其他必要的请求头
```

### 3. 使用 Docker Compose 部署

1. 构建并启动服务：
```bash
docker compose up -d --build
```

2. 检查服务状态：
```bash
docker compose ps
```

3. 查看日志：
```bash
docker compose logs -f
```

### 本地调试

1. 修改 `config/config.yml` 中的 `host` 为 `127.0.0.1`
2. 修改 `run_api.py` 中的 `app.run(host='0.0.0.0', port=8000, debug=False)` 为 `app.run(host='0.0.0.0', port=8000, debug=True)`
3. 执行 python3 run_api.py

### 4. 访问系统

- Web 界面：`http://localhost:8000`
- API 文档：`http://localhost:8000/api/docs`

## 开发指南

### 本地开发环境设置

1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动开发服务器：
```bash
python run_api.py
```

### 系统监控

1. 检查系统状态：
```bash
docker compose ps
```

2. 监控资源使用：
```bash
docker stats
```

### 更新部署

1. 拉取最新代码：
```bash
git pull origin main
```

2. 重新构建并启动：
```bash
docker compose down
docker compose up -d --build
```

## 常见问题

1. **Q: 容器启动失败怎么办？**
   A: 检查日志 `docker compose logs`，确认配置文件是否正确。

2. **Q: 如何修改端口号？**
   A: 修改 `docker compose.yml` 中的端口映射。

3. **Q: 数据库连接失败？**
   A: 检查 MySQL 容器状态和配置文件中的数据库连接信息。

## 安全注意事项

1. 确保修改默认的数据库密码
2. 定期更新系统和依赖包
3. 及时备份重要数据
4. 使用 HTTPS 进行安全传输
5. 定期检查系统日志

## 许可证

MIT License

## 联系方式

- 作者：阿文
- Email：hsweib@gmail.com
- 项目地址：[GitHub 仓库地址](https://github.com/monkey-wenjun/easy_park)