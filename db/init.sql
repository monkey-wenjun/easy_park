-- 创建并设置数据库
CREATE DATABASE IF NOT EXISTS parking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE parking;

-- 创建用户车辆记录表
CREATE TABLE IF NOT EXISTS user_vehicle_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    username VARCHAR(255) NOT NULL COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    license_plate VARCHAR(20) NOT NULL COMMENT '车牌号',
    user_no VARCHAR(50) COMMENT '用户编号',
    openid VARCHAR(50) COMMENT '用户编号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除(0:未删除,1:已删除)',
    email VARCHAR(255) COMMENT '邮箱地址',
    email_verified TINYINT(1) DEFAULT 0 COMMENT '邮箱是否验证(0:未验证,1:已验证)'
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '用户车辆记录表';

-- 创建券码记录表
CREATE TABLE IF NOT EXISTS code_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    code_id VARCHAR(255) NOT NULL COMMENT '券码ID',
    code_no VARCHAR(255) NOT NULL COMMENT '券码编号',
    business_name VARCHAR(255) DEFAULT NULL COMMENT '商家名称',
    code_start_time DATETIME DEFAULT NULL COMMENT '券码开始时间',
    code_end_time DATETIME DEFAULT NULL COMMENT '券码结束时间',
    status TINYINT DEFAULT 0 COMMENT '状态(0:正常,1:已核销)',
    used_by VARCHAR(255) DEFAULT NULL COMMENT '使用人',
    used_time DATETIME DEFAULT NULL COMMENT '使用时间',
    verification_time DATETIME DEFAULT NULL COMMENT '核销时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除'
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '券码记录表';

-- 创建定时任务表
CREATE TABLE IF NOT EXISTS schedule_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    hour INT NOT NULL,
    minute INT NOT NULL,
    weekdays VARCHAR(20) NOT NULL,
    status TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    auto_collect TINYINT(1) DEFAULT 0 COMMENT '自动领取开关(0:关闭,1:开启)',
    auto_pay TINYINT(1) DEFAULT 0 COMMENT '自动支付开关(0:关闭,1:开启)',
    is_deleted TINYINT(1) DEFAULT 0
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建任务执行记录表
CREATE TABLE IF NOT EXISTS schedule_execution_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    task_id INT NOT NULL COMMENT '任务ID',
    execution_date DATE NOT NULL COMMENT '执行日期',
    execution_time DATETIME NOT NULL COMMENT '执行时间',
    status TINYINT DEFAULT 1 COMMENT '执行状态(1:成功,0:失败)',
    error_message TEXT DEFAULT NULL COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_task_date (task_id, execution_date) COMMENT '确保每个任务每天只执行一次'
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '任务执行记录表';

-- 创建任务状态表
CREATE TABLE IF NOT EXISTS task_status (
    task_id VARCHAR(36) PRIMARY KEY COMMENT '任务ID',
    status VARCHAR(20) NOT NULL COMMENT '任务状态(processing/completed/error)',
    message TEXT COMMENT '任务消息',
    results JSON COMMENT '处理结果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    username VARCHAR(255) NOT NULL COMMENT '用户名'
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '任务状态表';

-- 创建登录记录表
CREATE TABLE IF NOT EXISTS login_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    username VARCHAR(255) NOT NULL COMMENT '用户名',
    ip_address VARCHAR(50) NOT NULL COMMENT '登录IP',
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
    status TINYINT(1) DEFAULT 1 COMMENT '登录状态(0:失败,1:成功)',
    fail_reason VARCHAR(255) DEFAULT NULL COMMENT '失败原因',
    user_agent VARCHAR(500) DEFAULT NULL COMMENT '浏览器信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '登录记录表';

-- 创建分享记录表
CREATE TABLE IF NOT EXISTS share_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    from_username VARCHAR(255) NOT NULL COMMENT '分享人用户名',
    to_username VARCHAR(255) NOT NULL COMMENT '被分享人用户名',
    code_ids TEXT NOT NULL COMMENT '分享的券码ID列表',
    share_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分享时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除(0:未删除,1:已删除)',
    INDEX idx_from_username (from_username),
    INDEX idx_to_username (to_username),
    INDEX idx_share_time (share_time)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '分享记录表';

-- 创建验证码表
CREATE TABLE IF NOT EXISTS verification_codes (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    email VARCHAR(255) NOT NULL COMMENT '邮箱地址',
    code VARCHAR(6) NOT NULL COMMENT '验证码',
    type VARCHAR(20) NOT NULL COMMENT '验证码类型(register:注册,reset:重置密码)',
    expire_time TIMESTAMP NOT NULL COMMENT '过期时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    used TINYINT(1) DEFAULT 0 COMMENT '是否已使用(0:未使用,1:已使用)',
    INDEX idx_email_type (email, type),
    INDEX idx_expire_time (expire_time)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '验证码表'; 