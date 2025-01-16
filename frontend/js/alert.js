class CustomAlert {
    constructor() {
        // 等待 DOM 加载完成后再初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    init() {
        if (document.querySelector('.custom-alert')) {
            return; // 已经初始化过，避免重复
        }

        // 创建弹窗容器
        this.alertBox = document.createElement('div');
        this.alertBox.className = 'custom-alert';
        this.alertBox.style.display = 'none';
        
        // 创建弹窗内容
        this.alertContent = document.createElement('div');
        this.alertContent.className = 'custom-alert-content';
        
        // 创建消息文本区域
        this.messageBox = document.createElement('div');
        this.messageBox.className = 'custom-alert-message';
        
        // 创建确认按钮
        this.confirmBtn = document.createElement('button');
        this.confirmBtn.className = 'custom-alert-button';
        this.confirmBtn.textContent = '确定';
        
        // 组装弹窗
        this.alertContent.appendChild(this.messageBox);
        this.alertContent.appendChild(this.confirmBtn);
        this.alertBox.appendChild(this.alertContent);
        
        // 添加到页面
        document.body.appendChild(this.alertBox);
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .custom-alert {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
            
            .custom-alert-content {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                min-width: 300px;
                max-width: 80%;
                text-align: center;
            }
            
            .custom-alert-message {
                margin-bottom: 20px;
                font-size: 16px;
                color: #333;
                line-height: 1.4;
            }
            
            .custom-alert-button {
                padding: 8px 30px;
                background-color: #409EFF;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.3s;
            }
            
            .custom-alert-button:hover {
                background-color: #66b1ff;
            }
            
            .custom-alert.show {
                display: flex;
                animation: fadeIn 0.3s;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    show(message) {
        this.messageBox.textContent = message;
        this.alertBox.style.display = 'flex';
        this.alertBox.classList.add('show');
        
        return new Promise((resolve) => {
            const handleClick = () => {
                this.hide();
                this.confirmBtn.removeEventListener('click', handleClick);
                resolve();
            };
            
            this.confirmBtn.addEventListener('click', handleClick);
        });
    }

    hide() {
        this.alertBox.style.display = 'none';
        this.alertBox.classList.remove('show');
    }

    showAutoClose(message, duration = 2000) {
        this.messageBox.textContent = message;
        this.alertBox.style.display = 'flex';
        this.alertBox.classList.add('show');
        this.confirmBtn.style.display = 'none'; // 隐藏确认按钮
        
        return new Promise((resolve) => {
            setTimeout(() => {
                this.hide();
                this.confirmBtn.style.display = 'block'; // 恢复确认按钮显示
                resolve();
            }, duration);
        });
    }
}

// 等待 DOM 加载完成后再创建实例和重写 alert
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomAlert);
} else {
    initCustomAlert();
}

function initCustomAlert() {
    // 创建全局实例
    window.customAlert = new CustomAlert();

    // 重写原生 alert，添加第二个参数用于控制是否自动关闭
    window.alert = function(message, autoClose = false) {
        if (autoClose) {
            return window.customAlert.showAutoClose(message);
        }
        return window.customAlert.show(message);
    };
} 