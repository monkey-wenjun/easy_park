// 填充时间选择器选项
function initTimeSelectors() {
    const hourSelect = document.getElementById('scheduleHour');
    const minuteSelect = document.getElementById('scheduleMinute');
    
    // 填充小时选项 (0-23)
    for (let i = 0; i < 24; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.text = String(i).padStart(2, '0');
        hourSelect.appendChild(option);
    }
    
    // 填充分钟选项 (0-59)
    for (let i = 0; i < 60; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.text = String(i).padStart(2, '0');
        minuteSelect.appendChild(option);
    }
}

// 页面加载时的初始化
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM Content Loaded');
    
    // 先检查登录状态
    if (!checkLogin()) {
        return;
    }
    
    // 获取用户信息
    await getUserInfo();
    
    // 初始化所有事件监听器
    initTimeSelectors();
    initScheduleForms();
    initOtherEventListeners();
    initShareRecordsEvents();
    initEventListeners();
    
    // 修改导航菜单项的 data-content 属性
    const executionLogsNav = document.querySelector('[data-content="execution-logs"]');
    if (executionLogsNav) {
        executionLogsNav.setAttribute('data-content', 'executionLogs');
    }
    
    // 根据当前页面内容初始化相应的功能
    const currentContent = localStorage.getItem('currentContent') || 'records';
    console.log('Current content:', currentContent);
    showContent(currentContent);
});

// 初始化其他事件监听器
function initOtherEventListeners() {
    // 点击模态框外部关闭
    window.onclick = function(event) {
        const editModal = document.getElementById('editProfileModal');
        const scheduleModal = document.getElementById('editScheduleModal');
        const shareModal = document.getElementById('shareModal');
        
        if (event.target === editModal) {
            editModal.style.display = 'none';
        }
        if (event.target === scheduleModal) {
            scheduleModal.style.display = 'none';
        }
        if (event.target === shareModal) {
            shareModal.style.display = 'none';
        }
    }

    // 处理文件上传相关事件
    const qrcodeFileInput = document.getElementById('qrcodeFile');
    if (qrcodeFileInput) {
        qrcodeFileInput.addEventListener('change', handleFileSelect);
    }

    // 处理搜索表单
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(event) {
            event.preventDefault();
            searchRecords();
        });
    }

    // 处理核销记录搜索
    const searchLogsForm = document.getElementById('searchLogsForm');
    if (searchLogsForm) {
        searchLogsForm.addEventListener('submit', function(event) {
            event.preventDefault();
            loadExecutionLogs(1);
        });
    }

    // 处理全选框
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.record-checkbox:not(:disabled)');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBatchActionButtons();
        });
    }

    // 处理批量分享按钮
    const batchShareBtn = document.getElementById('batchShareBtn');
    if (batchShareBtn) {
        batchShareBtn.addEventListener('click', showBatchShareDialog);
    }

    // 初始化分享表单
    initShareForm();

    // 处理重置按钮
    const resetButton = document.getElementById('resetButton');
    if (resetButton) {
        resetButton.addEventListener('click', resetForm);
    }

    // 处理重置日志搜索按钮
    const resetLogButton = document.getElementById('resetLogButton');
    if (resetLogButton) {
        resetLogButton.addEventListener('click', resetLogSearch);
    }

    // 处理退出登录按钮
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // 处理重置搜索按钮
    const resetSearchButton = document.getElementById('resetSearchButton');
    if (resetSearchButton) {
        resetSearchButton.addEventListener('click', resetForm);
    }

    // 处理上传按钮
    const uploadButton = document.getElementById('uploadButton');
    if (uploadButton) {
        uploadButton.addEventListener('click', uploadFiles);
    }

    // 处理编辑个人信息按钮
    const editProfileButton = document.getElementById('editProfileButton');
    if (editProfileButton) {
        editProfileButton.addEventListener('click', editProfile);
    }

    // 处理关闭编辑模态框按钮
    const closeEditModalButton = document.getElementById('closeEditModalButton');
    if (closeEditModalButton) {
        closeEditModalButton.addEventListener('click', closeEditModal);
    }

    // 处理关闭编辑定时任务模态框按钮
    const closeEditScheduleModalButton = document.getElementById('closeEditScheduleModalButton');
    if (closeEditScheduleModalButton) {
        closeEditScheduleModalButton.addEventListener('click', closeEditScheduleModal);
    }

    // 处理分页按钮
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => changePage('prev'));
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', () => changePage('next'));
    }

    // 处理核销记录分页按钮
    const prevLogBtn = document.getElementById('prevLogBtn');
    const nextLogBtn = document.getElementById('nextLogBtn');
    if (prevLogBtn) {
        prevLogBtn.addEventListener('click', () => changeLogPage('prev'));
    }
    if (nextLogBtn) {
        nextLogBtn.addEventListener('click', () => changeLogPage('next'));
    }

    // 处理核销记录搜索按钮
    const searchLogsButton = document.getElementById('searchLogsButton');
    if (searchLogsButton) {
        searchLogsButton.addEventListener('click', searchExecutionLogs);
    }

    // 处理核销记录重置按钮
    const resetLogsButton = document.getElementById('resetLogsButton');
    if (resetLogsButton) {
        resetLogsButton.addEventListener('click', resetLogSearch);
    }

    // 处理导航菜单点击
    document.querySelectorAll('.nav-menu .nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const contentType = this.getAttribute('data-content');
            showContent(contentType);
        });
    });

    // 处理分享模态框关闭按钮
    const closeShareModalButton = document.getElementById('closeShareModalButton');
    if (closeShareModalButton) {
        closeShareModalButton.addEventListener('click', closeShareModal);
    }

    // 处理二维码模态框关闭按钮
    const closeQRCodeModalButton = document.getElementById('closeQRCodeModalButton');
    if (closeQRCodeModalButton) {
        closeQRCodeModalButton.addEventListener('click', closeQRCodeModal);
    }

    // 处理模态框外部点击关闭
    window.addEventListener('click', function(event) {
        const shareModal = document.getElementById('shareModal');
        const qrcodeModal = document.getElementById('qrcodeModal');
        
        if (event.target === shareModal) {
            shareModal.style.display = 'none';
        }
        if (event.target === qrcodeModal) {
            qrcodeModal.style.display = 'none';
        }
    });

    // 处理搜索按钮
    const searchButton = document.getElementById('searchButton');
    if (searchButton) {
        searchButton.addEventListener('click', () => searchRecords());
    }
}

// 初始化定时任务表单和事件监听
function initScheduleForms() {
    // 处理创建定时任务表单
    const scheduleForm = document.getElementById('scheduleForm');
    if (scheduleForm) {
        // 设置自动领取复选框的初始状态
        const autoCollectCheckbox = document.getElementById('autoCollect');
        if (autoCollectCheckbox) {
            autoCollectCheckbox.checked = true;  // 默认选中
            autoCollectCheckbox.disabled = true;  // 设置为禁用
        }
        
        scheduleForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            // 添加前端校验
            const user = JSON.parse(localStorage.getItem('user'));
            if (!user || !user.openid || !user.user_no) {
                alert('请先在个人中心完善微信 OpenID 和用户编号信息');
                return;
            }
            
            // 获取选中的星期
            const weekdays = [];
            document.querySelectorAll('.weekday-selector input[type="checkbox"]:checked').forEach(checkbox => {
                weekdays.push(checkbox.value);
            });
            
            if (weekdays.length === 0) {
                alert('请至少选择一个执行日期');
                return;
            }
            
            const hour = document.getElementById('scheduleHour').value;
            const minute = document.getElementById('scheduleMinute').value;
            
            // 获取自动化选项的状态
            const autoCollect = document.getElementById('autoCollect').checked;
            const autoPay = document.getElementById('autoPay').checked;
            
            try {
                const response = await fetch('/api/schedules', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Username': JSON.parse(localStorage.getItem('user')).username
                    },
                    body: JSON.stringify({
                        hour: parseInt(hour),
                        minute: parseInt(minute),
                        weekdays: weekdays.join(','),
                        auto_collect: autoCollect,
                        auto_pay: autoPay
                    })
                });
                
                const data = await response.json();
                if (data.code === 0) {
                    alert('创建成功');
                    loadSchedules();  // 重新加载任务列表
                } else {
                    alert(data.message || '创建失败');
                }
            } catch (error) {
                console.error('创建定时任务失败:', error);
                alert('创建失败');
            }
        });
    }

    // 处理编辑定时任务表单
    const editScheduleForm = document.getElementById('editScheduleForm');
    if (editScheduleForm) {
        editScheduleForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const taskId = document.getElementById('edit-schedule-id').value;
            const hour = document.getElementById('edit-schedule-hour').value;
            const minute = document.getElementById('edit-schedule-minute').value;
            
            // 获取选中的星期
            const weekdays = [];
            this.querySelectorAll('.weekday-selector input[type="checkbox"]:checked').forEach(checkbox => {
                weekdays.push(checkbox.value);
            });
            
            // 获取自动化选项的状态
            const autoCollect = document.getElementById('edit-autoCollect').checked;
            const autoPay = document.getElementById('edit-autoPay').checked;
            
            try {
                const response = await fetch(`/api/schedules/${taskId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Username': JSON.parse(localStorage.getItem('user')).username
                    },
                    body: JSON.stringify({
                        hour: parseInt(hour),
                        minute: parseInt(minute),
                        weekdays: weekdays.join(','),
                        auto_collect: autoCollect,
                        auto_pay: autoPay
                    })
                });
                
                const data = await response.json();
                if (data.code === 0) {
                    alert('更新成功');
                    closeEditScheduleModal();
                    loadSchedules();  // 重新加载任务列表
                } else {
                    alert(data.message || '更新失败');
                }
            } catch (error) {
                console.error('更新定时任务失败:', error);
                alert('更新失败');
            }
        });
    }
}

// 修改分页状态变量
let currentPage = 1;
const pageSize = 5;  // 改为 5 条每页
let totalRecords = 0;

// 核销记录相关变量
let currentLogPage = 1;
const logPageSize = 10;
let totalLogs = 0;

// 分享记录相关变量
let currentSharePage = 1;
const sharePageSize = 10;

// 检查登录状态
async function checkLogin() {
    try {
        const userStr = localStorage.getItem('user');
        if (!userStr) {
            window.location.href = '/login.html';
            return;
        }
        
        // 尝试解析用户信息
        try {
            const user = JSON.parse(userStr);
            if (!user || !user.username) {
                window.location.href = '/login.html';
                return;
            }
            // 更新顶部用户信息显示
            document.getElementById('userInfo').textContent = 
                `${user.username}${user.license_plate ? ` (${user.license_plate})` : ''}`;
        } catch (parseError) {
            console.error('解析用户信息失败:', parseError);
            localStorage.removeItem('user');  // 清除无效的用户信息
            window.location.href = '/login.html';
            return;
        }

        // 验证 token 是否有效
        const response = await fetch('/api/user/profile', {
            credentials: 'include'  // 包含 cookies
        });

        if (response.status === 401) {
            // token 无效或过期
            localStorage.removeItem('user');  // 清除用户信息
            window.location.href = '/login.html';
            return;
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
        localStorage.removeItem('user');  // 发生错误时清除用户信息
        window.location.href = '/login.html';
    }
}

// 查询记录
async function searchRecords(page = 1) {
    try {
        loading = true;
        const params = new URLSearchParams();
        params.append('page', page);
        params.append('page_size', pageSize);

        // 获取查询参数
        const startTime = document.getElementById('startTime').value;
        const endTime = document.getElementById('endTime').value;
        const status = document.getElementById('status').value;

        // 添加查询参数
        if (startTime) params.append('start_time', startTime);
        if (endTime) params.append('end_time', endTime);
        // 如果是初始加载且没有选择状态，默认查询正常状态
        if (status !== '') {
            params.append('status', status);
        } else if (!startTime && !endTime) {
            // 只有在没有其他查询条件时才使用默认状态
            params.append('status', '0');  // 默认查询正常状态
            document.getElementById('status').value = '0';  // 更新选择器显示
        }

        const response = await fetch(`/api/records?${params.toString()}`, {
            credentials: 'include'  // 添加认证信息
        });

        if (response.status === 401) {
            window.location.href = '/login.html';
            return;
        }

        const data = await response.json();
        
        if (data.code === 0) {
            const tbody = document.getElementById('recordsTable');
            tbody.innerHTML = '';
            
            data.data.records.forEach(record => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>
                        <input type="checkbox" class="record-checkbox" value="${record.code_id}" 
                            ${record.status === 1 ? 'disabled' : ''}>
                    </td>
                    <td>
                        <div class="qr-code" data-code="${record.code_id}">
                            ${renderQRCode(record.code_id)}
                        </div>
                    </td>
                    <td>${record.code_no}</td>
                    <td>${record.business_name || '-'}</td>
                    <td>${formatDateTime(record.code_start_time)}</td>
                    <td>${formatDateTime(record.code_end_time)}</td>
                    <td><span class="status-tag ${record.status === 0 ? 'status-normal' : 'status-used'}">${record.status === 0 ? '正常' : '已核销'}</span></td>
                    <td>${record.used_by || '-'}</td>
                    <td>${formatDateTime(record.verification_time)}</td>
                    <td>${formatDateTime(record.created_at)}</td>
                    <td>
                        <button class="btn btn-primary share-record" data-id="${record.code_id}" ${record.status === 1 ? 'disabled' : ''}>分享</button>
                    </td>
                `;
                tbody.appendChild(tr);

                // 为新添加的复选框添加事件监听器
                const checkbox = tr.querySelector('.record-checkbox');
                if (checkbox) {
                    checkbox.addEventListener('change', updateBatchActionButtons);
                }

                // 为删除和分享按钮添加事件监听器
                const deleteBtn = tr.querySelector('.delete-record');
                const shareBtn = tr.querySelector('.share-record');
                
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', function() {
                        deleteRecord(this.getAttribute('data-id'));
                    });
                }
                
                if (shareBtn) {
                    shareBtn.addEventListener('click', function() {
                        showShareDialog(this.getAttribute('data-id'));
                    });
                }

                // 为二维码添加点击事件
                const qrCode = tr.querySelector('.qr-code');
                if (qrCode) {
                    qrCode.addEventListener('click', function() {
                        const code = this.getAttribute('data-code');
                        showLargeQRCode(code);
                    });
                }
            });

            // 更新分页信息
            totalRecords = data.data.total;
            currentPage = page;
            document.getElementById('totalRecords').textContent = totalRecords;
            document.getElementById('currentPage').textContent = currentPage;
            
            // 更新按钮状态
            document.getElementById('prevBtn').disabled = currentPage === 1;
            document.getElementById('nextBtn').disabled = currentPage * pageSize >= totalRecords;
        } else {
            alert('加载记录失败：' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('加载记录失败');
    } finally {
        loading = false;
    }
}

// 添加分页控制函数
function changePage(direction) {
    if (direction === 'prev' && currentPage > 1) {
        searchRecords(currentPage - 1);
    } else if (direction === 'next' && currentPage * pageSize < totalRecords) {
        searchRecords(currentPage + 1);
    }
}

// 更新分页信息显示
function updatePagination() {
    document.getElementById('totalRecords').textContent = totalRecords;
    document.getElementById('currentPage').textContent = currentPage;
    
    // 更新按钮状态
    document.getElementById('prevBtn').disabled = currentPage <= 1;
    document.getElementById('nextBtn').disabled = currentPage * pageSize >= totalRecords;
}

// 修改重置表单函数
function resetForm() {
    document.getElementById('startTime').value = '';
    document.getElementById('endTime').value = '';
    document.getElementById('status').value = '0';  // 重置为正常状态而不是全部
    searchRecords(1);
}

// 修改渲染记录函数，移除 ID 列的显示
function renderRecords(records) {
    console.log('Records to render:', records);  // 保留调试日志
    const tbody = document.getElementById('recordsTable');
    tbody.innerHTML = '';

    if (!records || records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" style="text-align: center;">暂无数据</td></tr>';
        return;
    }

    records.forEach(record => {
        console.log('Record:', record);  // 保留调试日志
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div id="qrcode-${record.code_id}"></div>
            </td>
            <td>${record.code_no}</td>
            <td>${record.business_name || '-'}</td>
            <td>${formatDateTime(record.code_start_time)}</td>
            <td>${formatDateTime(record.code_end_time)}</td>
            <td>
                <span class="status-tag ${record.status === 0 ? 'status-normal' : 'status-used'}">
                    ${record.status === 0 ? '正常' : '已核销'}
                </span>
            </td>
            <td>${record.used_by || '-'}</td>
            <td>${formatDateTime(record.used_time)}</td>
            <td>${formatDateTime(record.verification_time)}</td>
            <td>${formatDateTime(record.created_at)}</td>
            <td>
                <button class="btn btn-danger" onclick="deleteRecord(${record.id})"
                        ${record.status === 1 ? 'disabled' : ''}>
                    删除
                </button>
            </td>
        `;
        tbody.appendChild(tr);

        // 生成二维码
        generateQRCode(record.code_id);
    });
}

// 生成二维码的函数
function generateQRCode(text) {
    try {
        // 生成完整的URL
        const qrUrl = `https://c.ymlot.cn/couponqrcode?d=${text}`;
        
        // 创建QR码对象
        const qr = qrcode(0, 'L');
        qr.addData(qrUrl);
        qr.make();
        
        // 生成较小的SVG格式二维码
        return qr.createSvgTag(2);  // 2是放大倍数
    } catch (error) {
        console.error('生成二维码失败:', error);
        return '';
    }
}

// 渲染二维码
function renderQRCode(code) {
    if (!code) return '';
    try {
        // 生成完整的URL
        const qrUrl = `https://c.ymlot.cn/couponqrcode?d=${code}`;
        
        // 创建QR码对象
        const qr = qrcode(0, 'L');
        qr.addData(qrUrl);
        qr.make();
        
        // 生成较小的SVG格式二维码
        return qr.createSvgTag(2);  // 2是放大倍数
    } catch (error) {
        console.error('生成二维码失败:', error);
        return '';
    }
}

// 添加记录
async function addRecord() {
    const codeId = document.getElementById('codeId').value;
    const codeNo = document.getElementById('codeNo').value;

    if (!codeId || !codeNo) {
        alert('请填写完整信息');
        return;
    }

    try {
        const response = await fetch('/api/records', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code_id: codeId,
                code_no: codeNo
            })
        });

        const data = await response.json();
        if (data.code === 0) {
            alert('添加成功');
            document.getElementById('codeId').value = '';
            document.getElementById('codeNo').value = '';
            showQueryPage();
            searchRecords();
        } else {
            alert('添加失败：' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('添加失败，请稍后重试');
    }
}

// 删除记录
async function deleteRecord(id) {
    if (!confirm('确定要删除这条记录吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/records/${id}`, {
            method: 'DELETE',
            credentials: 'include'  // 添加认证信息
        });

        if (response.status === 401) {
            window.location.href = '/login.html';
            return;
        }

        console.log('删除请求状态:', response.status);
        const data = await response.json();
        console.log('删除响应数据:', data);
        
        // 不管后端返回什么状态，都先刷新数据
        try {
            // 先获取当前页的记录数
            const params = new URLSearchParams();
            params.append('page', currentPage);
            params.append('page_size', pageSize);
            params.append('_t', new Date().getTime());
            
            const checkResponse = await fetch(`/api/records?${params.toString()}`, {
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });
            
            const checkData = await checkResponse.json();
            console.log('检查当前页数据:', checkData);
            
            // 如果当前页没有数据了，就跳转到前一页
            if (checkData.data.records.length === 0 && currentPage > 1) {
                currentPage--;
            }
            
            // 刷新数据
            await searchRecords(currentPage);
            
            // 更新总记录数和分页
            totalRecords = checkData.data.total;
            updatePagination();
            
            // 根据错误类型显示不同的消息
            if (data.code === 0) {
                alert('删除成功');
            } else if (data.error === '记录未找到' || data.message.includes('记录不存在')) {
                // 记录不存在，可能是已经被删除
                alert('记录已不存在，可能已被删除');
            } else {
                // 其他错误情况
                alert(`操作失败：${data.message}`);
            }
        } catch (error) {
            console.error('刷新数据失败:', error);
            // 如果刷新失败，也强制刷新一次
            await searchRecords(1);
            alert('操作完成，但刷新数据时出错');
        }
    } catch (error) {
        console.error('删除操作错误:', error);
        alert(`操作失败，请稍后重试\n错误信息：${error.message}`);
        // 发生错误时也刷新一次，确保显示最新状态
        await searchRecords(currentPage);
    }
}

// 显示查询页面
function showQueryPage() {
    document.getElementById('queryPage').style.display = 'block';
    document.getElementById('addPage').style.display = 'none';
    document.querySelector('.nav-item:nth-child(1)').classList.add('active');
    document.querySelector('.nav-item:nth-child(2)').classList.remove('active');
}

// 显示新增页面
function showAddPage() {
    document.getElementById('queryPage').style.display = 'none';
    document.getElementById('addPage').style.display = 'block';
    document.querySelector('.nav-item:nth-child(1)').classList.remove('active');
    document.querySelector('.nav-item:nth-child(2)').classList.add('active');
}

// 退出登录
function logout() {
    localStorage.removeItem('user');
    window.location.href = '/login.html';
}

// 文件上传相关函数
function handleFileSelect(event) {
    const files = event.target.files;
    const preview = document.getElementById('uploadPreview');
    preview.innerHTML = '';

    Array.from(files).forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const div = document.createElement('div');
            div.className = 'preview-item';
            div.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <button class="remove-btn" onclick="removeFile(${index})">×</button>
            `;
            preview.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

function removeFile(index) {
    const input = document.getElementById('qrcodeFile');
    const preview = document.getElementById('uploadPreview');
    
    const dt = new DataTransfer();
    const files = input.files;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }
    
    input.files = dt.files;
    preview.children[index].remove();
}

async function uploadFiles() {
    const files = document.getElementById('qrcodeFile').files;
    if (files.length === 0) {
        alert('请选择要上传的图片');
        return;
    }

    // 获取当前登录用户信息
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user || !user.username) {
        alert('请先登录');
        window.location.href = '/login.html';
        return;
    }

    const resultsDiv = document.getElementById('uploadResults');
    const markedImagePreview = document.getElementById('markedImagePreview');
    resultsDiv.innerHTML = '';
    markedImagePreview.innerHTML = '';

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('username', user.username);  // 添加用户名到表单数据

        try {
            // 上传文件
            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'X-Username': user.username  // 添加用户认证头
                },
                body: formData
            });

            const uploadData = await uploadResponse.json();
            
            if (uploadData.code === 0) {
                const taskId = uploadData.data.task_id;
                
                // 创建进度提示
                const progressDiv = document.createElement('div');
                progressDiv.className = 'upload-progress';
                progressDiv.innerHTML = `
                    <p>正在处理文件: ${file.name}</p>
                    <div class="progress-status">处理中...</div>
                `;
                resultsDiv.appendChild(progressDiv);

                // 轮询任务状态
                while (true) {
                    const statusResponse = await fetch(`/api/task-status/${taskId}`, {
                        headers: {
                            'X-Username': user.username  // 状态查询也添加用户认证头
                        }
                    });
                    const statusData = await statusResponse.json();

                    if (statusData.code !== 0) {
                        progressDiv.innerHTML = `<p class="error">处理失败: ${statusData.message}</p>`;
                        break;
                    }

                    const result = statusData.data;
                    if (result.status === 'completed') {
                        // 显示标记后的图片
                        if (result.marked_image) {
                            const markedImageDiv = document.createElement('div');
                            markedImageDiv.className = 'marked-image-container';
                            markedImageDiv.innerHTML = `
                                <div class="marked-image-title">识别结果图片</div>
                                <img src="${result.marked_image}" alt="标记后的图片">
                            `;
                            markedImagePreview.appendChild(markedImageDiv);
                        }

                        // 显示处理结果
                        progressDiv.remove();  // 移除进度提示
                        result.results.forEach(result => {
                            const resultDiv = document.createElement('div');
                            resultDiv.className = `result-item ${result.status === 'success' ? 'success' : 'error'}`;
                            resultDiv.innerHTML = `
                                <p>券码ID: ${result.code_id}</p>
                                ${result.code_no ? `<p>券码编号: ${result.code_no}</p>` : ''}
                                <p>状态: ${result.message}</p>
                            `;
                            resultsDiv.appendChild(resultDiv);
                        });
                        break;
                    } else if (result.status === 'error') {
                        progressDiv.innerHTML = `<p class="error">处理失败: ${result.error}</p>`;
                        break;
                    }

                    // 等待一段时间后再次查询
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            } else {
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result-item error';
                resultDiv.innerHTML = `<p>上传失败: ${uploadData.error || uploadData.message}</p>`;
                resultsDiv.appendChild(resultDiv);
            }
        } catch (error) {
            console.error('上传失败:', error);
            resultsDiv.innerHTML += `<p class="error">上传失败: ${error.message}</p>`;
        }
    }
}

// 添加统一的时间格式化函数
function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    try {
        const date = new Date(dateStr);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: 'Asia/Shanghai'  // 指定北京时区
        });
    } catch (e) {
        console.error('时间格式化错误:', e);
        return dateStr;
    }
}

// 修改显示内容区域的函数
function showContent(contentId) {
    console.log('Showing content:', contentId);
    
    // 隐藏所有内容
    document.querySelectorAll('.main-content > div').forEach(div => {
        div.style.display = 'none';
    });
    
    // 显示选中的内容
    const contentElement = document.getElementById(contentId + 'Page');
    if (contentElement) {
        contentElement.style.display = 'block';
    }
    
    // 更新导航菜单的激活状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.content === contentId) {
            item.classList.add('active');
        }
    });
    
    // 存储当前页面
    localStorage.setItem('currentContent', contentId);
    
    // 根据页面类型加载不同的数据
    switch (contentId) {
        case 'records':
            searchRecords();
            break;
        case 'executionLogs':
            loadExecutionLogs();
            break;
        case 'share-records':
            loadShareRecords(1);
            break;
        case 'schedule':
            loadSchedules();
            checkUserCanCreateTask();
            break;
        case 'profile':
            loadProfileData();
            break;
    }
}

// 加载个人信息
async function loadProfileData() {
    try {
        // 获取当前登录用户信息
        const user = JSON.parse(localStorage.getItem('user'));
        if (!user || !user.username) {
            alert('请先登录');
            window.location.href = '/login.html';
            return;
        }

        const response = await fetch('/api/user/profile', {
            headers: {
                'X-Username': user.username
            }
        });
        const data = await response.json();
        
        if (data.code === 0) {
            // 更新所有字段的显示
            document.getElementById('profile-username').textContent = data.data.username || '-';
            document.getElementById('profile-license').textContent = data.data.license_plate || '-';
            document.getElementById('profile-userno').textContent = data.data.user_no || '-';
            document.getElementById('profile-openid').textContent = data.data.openid || '-';
            document.getElementById('profile-email').textContent = data.data.email || '-';  // 添加邮箱显示
            
            // 格式化创建时间为北京时间
            const createdDate = new Date(data.data.created_at);
            const beijingTime = new Date(createdDate.getTime());  // 创建新的日期对象
            
            document.getElementById('profile-created').textContent = beijingTime.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                timeZone: 'Asia/Shanghai'  // 指定北京时区
            });
            
            // 更新本地存储的用户信息
            localStorage.setItem('user', JSON.stringify(data.data));
        } else {
            alert('获取个人信息失败：' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('获取个人信息失败');
    }
}

// 打开编辑模态框
function editProfile() {
    const modal = document.getElementById('editProfileModal');
    // 填充当前值
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        document.getElementById('edit-license').value = user.license_plate || '';
        document.getElementById('edit-userno').value = user.user_no || '';
        document.getElementById('edit-openid').value = user.openid || '';
        document.getElementById('edit-email').value = user.email || '';  // 添加邮箱值填充
    }
    modal.style.display = 'block';
}

// 关闭编辑模态框
function closeEditModal() {
    document.getElementById('editProfileModal').style.display = 'none';
}

// 生成时间选项
function generateTimeOptions() {
    const hourSelect = document.getElementById('scheduleHour');
    const minuteSelect = document.getElementById('scheduleMinute');

    // 生成小时选项 (0-23)
    for (let i = 0; i < 24; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i.toString().padStart(2, '0');
        hourSelect.appendChild(option);
    }

    // 生成分钟选项 (0-59)
    for (let i = 0; i < 60; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i.toString().padStart(2, '0');
        minuteSelect.appendChild(option);
    }
}

// 在任务列表项中添加执行历史显示
async function loadTaskExecutionHistory(taskId) {
    try {
        const response = await fetch(`/api/schedules/${taskId}/history`, {
            headers: {
                'X-Username': JSON.parse(localStorage.getItem('user')).username
            }
        });
        const data = await response.json();
        
        if (data.code === 0) {
            return data.data.map(log => `
                <div class="execution-log ${log.status ? 'success' : 'error'}">
                    <div class="log-time">${log.execution_time}</div>
                    <div class="log-status">${log.status ? '成功' : '失败'}</div>
                    ${log.error_message ? `<div class="log-error">${log.error_message}</div>` : ''}
                </div>
            `).join('');
        }
        return '';
    } catch (error) {
        console.error('Error:', error);
        return '';
    }
}

// 修改任务列表渲染代码
async function loadSchedules() {
    try {
        console.log('Loading schedules...'); // 添加日志
        const user = JSON.parse(localStorage.getItem('user'));
        if (!user || !user.username) {
            console.error('User not logged in');
            window.location.href = '/login.html';
            return;
        }

        const response = await fetch('/api/schedules', {
            headers: {
                'X-Username': user.username
            }
        });

        if (response.status === 401) {
            console.error('Unauthorized access');
            window.location.href = '/login.html';
            return;
        }

        const data = await response.json();
        console.log('Schedules response:', data); // 添加日志
        
        const scheduleList = document.getElementById('currentSchedules');
        if (!scheduleList) {
            console.error('Schedule list element not found');
            return;
        }

        scheduleList.innerHTML = '';
        
        if (data.code === 0 && data.data.length > 0) {
            for (const schedule of data.data) {
                const weekdays = schedule.weekdays.split(',').map(day => 
                    ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][parseInt(day)]
                ).join(', ');
                
                const div = document.createElement('div');
                div.className = 'schedule-item';
                div.innerHTML = `
                    <div class="schedule-info">
                        <div class="schedule-time">
                            ${String(schedule.hour).padStart(2, '0')}:${String(schedule.minute).padStart(2, '0')}
                        </div>
                        <div class="schedule-days">执行日期：${weekdays}</div>
                        <div class="schedule-options">
                            <span class="option-tag">自动领券</span>
                            ${schedule.auto_pay ? '<span class="option-tag">自动核销</span>' : ''}
                        </div>
                    </div>
                    <div class="schedule-actions">
                        <button class="edit-btn" data-schedule='${JSON.stringify(schedule)}'>编辑</button>
                        <button class="delete-btn" data-id="${schedule.id}">删除</button>
                    </div>
                `;
                scheduleList.appendChild(div);

                // 为按钮添加事件监听器
                const editBtn = div.querySelector('.edit-btn');
                const deleteBtn = div.querySelector('.delete-btn');
                
                if (editBtn) {
                    editBtn.addEventListener('click', () => {
                        const scheduleData = JSON.parse(editBtn.getAttribute('data-schedule'));
                        editSchedule(scheduleData);
                    });
                }
                
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', () => {
                        const id = deleteBtn.getAttribute('data-id');
                        deleteSchedule(id);
                    });
                }
            }
        } else {
            scheduleList.innerHTML = '<div class="no-data">暂无定时任务</div>';
        }
    } catch (error) {
        console.error('加载定时任务列表失败:', error);
        alert('加载定时任务列表失败');
    }
}

// 删除定时任务
async function deleteSchedule(id) {
    if (!confirm('确定要删除这个任务吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/schedules/${id}`, {
            method: 'DELETE',
            headers: {
                'X-Username': JSON.parse(localStorage.getItem('user')).username
            }
        });

        const data = await response.json();
        
        if (data.code === 0) {
            alert('删除任务成功');
            loadSchedules();
        } else {
            alert('删除任务失败：' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('删除任务失败');
    }
}

// 打开编辑定时任务的模态框
function editSchedule(schedule) {
    const modal = document.getElementById('editScheduleModal');
    const hourSelect = document.getElementById('edit-schedule-hour');
    const minuteSelect = document.getElementById('edit-schedule-minute');
    
    // 填充时间选项（如果还没有生成）
    if (hourSelect.children.length <= 1) {
        for (let i = 0; i < 24; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = i.toString().padStart(2, '0');
            hourSelect.appendChild(option);
        }
    }
    if (minuteSelect.children.length <= 1) {
        for (let i = 0; i < 60; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = i.toString().padStart(2, '0');
            minuteSelect.appendChild(option);
        }
    }
    
    // 设置当前值
    document.getElementById('edit-schedule-id').value = schedule.id;
    hourSelect.value = schedule.hour;
    minuteSelect.value = schedule.minute;
    
    // 设置星期选择
    const weekdays = schedule.weekdays.split(',');
    document.querySelectorAll('#editScheduleModal .weekday-selector input').forEach(checkbox => {
        checkbox.checked = weekdays.includes(checkbox.value);
    });
    
    // 设置自动化选项
    const autoCollectCheckbox = document.getElementById('edit-autoCollect');
    autoCollectCheckbox.checked = true;  // 始终设置为选中
    autoCollectCheckbox.disabled = true;  // 设置为禁用
    document.getElementById('edit-autoPay').checked = schedule.auto_pay === 1;
    
    modal.style.display = 'block';
}

// 关闭编辑模态框
function closeEditScheduleModal() {
    document.getElementById('editScheduleModal').style.display = 'none';
}

// 加载核销记录
async function loadExecutionLogs(page = 1) {
    try {
        const params = new URLSearchParams();
        params.append('page', page);
        params.append('page_size', logPageSize);

        const startDate = document.getElementById('logStartDate').value;
        const endDate = document.getElementById('logEndDate').value;
        const status = document.getElementById('logStatus').value;

        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (status !== '') params.append('status', status);

        const response = await fetch(`/api/execution-logs?${params.toString()}`, {
            headers: {
                'X-Username': JSON.parse(localStorage.getItem('user')).username
            }
        });

        const data = await response.json();
        
        if (data.code === 0) {
            const tbody = document.getElementById('executionLogsTable');
            tbody.innerHTML = '';

            data.data.logs.forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${log.task_id}</td>
                    <td>${log.execution_date}</td>
                    <td>${formatDateTime(log.execution_time)}</td>
                    <td><span class="log-status ${log.status ? 'success' : 'error'}">${log.status ? '成功' : '失败'}</span></td>
                    <td>${log.error_message ? `<div class="log-error-message" title="${log.error_message}">${log.error_message}</div>` : '-'}</td>
                `;
                tbody.appendChild(tr);
            });

            // 更新分页信息
            totalLogs = data.data.total;
            currentLogPage = page;
            document.getElementById('totalLogs').textContent = totalLogs;
            document.getElementById('currentLogPage').textContent = currentLogPage;
            
            // 更新按钮状态
            document.getElementById('prevLogBtn').disabled = currentLogPage === 1;
            document.getElementById('nextLogBtn').disabled = currentLogPage * logPageSize >= totalLogs;
        } else {
            alert('加载核销记录失败：' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('加载核销记录失败');
    }
}

// 搜索核销记录
function searchExecutionLogs() {
    loadExecutionLogs(1);
}

// 重置搜索条件
function resetLogSearch() {
    document.getElementById('logStartDate').value = '';
    document.getElementById('logEndDate').value = '';
    document.getElementById('logStatus').value = '';
    loadExecutionLogs(1);
}

// 切换页面
function changeLogPage(direction) {
    const newPage = direction === 'prev' ? currentLogPage - 1 : currentLogPage + 1;
    if (newPage > 0 && newPage * logPageSize <= totalLogs) {
        loadExecutionLogs(newPage);
    }
}

// 修改上传文件的方法
async function uploadFile() {
    // 检查用户是否登录
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user || !user.username) {
        alert('请先登录');
        window.location.href = '/login.html';
        return;
    }

    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file) {
        alert('请选择文件');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'X-Username': user.username  // 确保添加用户名到请求头
            },
            body: formData
        });

        const data = await response.json();
        
        if (data.code === 0) {
            // 开始轮询任务状态
            pollTaskStatus(data.data.task_id);
        } else {
            alert(data.message || '上传失败');
        }
    } catch (error) {
        console.error('上传失败:', error);
        alert('上传失败: ' + error.message);
    }
}

// 轮询任务状态
async function pollTaskStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const user = JSON.parse(localStorage.getItem('user'));
            const response = await fetch(`/api/task-status/${taskId}`, {
                headers: {
                    'X-Username': user.username  // 状态查询也添加用户名
                }
            });

            const data = await response.json();
            
            if (data.code === 0) {
                const result = data.data;
                if (result.status === 'completed') {
                    clearInterval(interval);
                    alert('处理完成');
                    // 刷新记录列表
                    loadRecords();
                } else if (result.status === 'error') {
                    clearInterval(interval);
                    alert(`处理失败: ${result.error}`);
                }
            } else {
                clearInterval(interval);
                alert('获取任务状态失败');
            }
        } catch (error) {
            clearInterval(interval);
            console.error('获取任务状态失败:', error);
            alert('获取任务状态失败');
        }
    }, 1000);  // 每秒轮询一次
}

// 显示分享对话框
function showShareDialog(codeId) {
    const selectedCount = 1;
    document.getElementById('share-code-id').value = codeId;
    document.getElementById('selectedCount').textContent = selectedCount;
    document.getElementById('shareModal').style.display = 'block';
}

// 关闭分享对话框
function closeShareModal() {
    document.getElementById('shareModal').style.display = 'none';
    document.getElementById('share-username').value = '';
    document.getElementById('selectedCount').textContent = '0';
}

// 处理分享表单提交
function initShareForm() {
    const shareForm = document.getElementById('shareForm');
    if (shareForm) {
        shareForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            const codeIds = document.getElementById('share-code-id').value.split(',');
            const username = document.getElementById('share-username').value;
            
            try {
                const response = await fetch('/api/share-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Username': JSON.parse(localStorage.getItem('user')).username
                    },
                    body: JSON.stringify({
                        code_ids: codeIds,
                        username: username
                    })
                });
                
                const data = await response.json();
                if (data.code === 0) {
                    alert('分享成功');
                    closeShareModal();
                    searchRecords();  // 刷新列表
                } else {
                    alert(data.message || '分享失败');
                }
            } catch (error) {
                console.error('分享失败:', error);
                alert('分享失败');
            }
        });
    }
}

// 切换全选
function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.record-checkbox:not(:disabled)');
    const selectAllCheckbox = document.getElementById('selectAll');
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
    updateBatchActionButtons();
}

// 更新批量操作按钮状态
function updateBatchActionButtons() {
    const selectedCount = document.querySelectorAll('.record-checkbox:checked').length;
    document.getElementById('batchShareBtn').disabled = selectedCount === 0;
    
    // 更新全选框状态
    const allCheckboxes = document.querySelectorAll('.record-checkbox:not(:disabled)');
    const checkedCheckboxes = document.querySelectorAll('.record-checkbox:checked');
    const selectAllCheckbox = document.getElementById('selectAll');
    
    if (allCheckboxes.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCheckboxes.length === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCheckboxes.length === allCheckboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

// 显示批量分享对话框
function showBatchShareDialog() {
    const selectedCodes = Array.from(document.querySelectorAll('.record-checkbox:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedCodes.length === 0) {
        alert('请选择要分享的券码');
        return;
    }
    
    document.getElementById('share-code-id').value = selectedCodes.join(',');
    document.getElementById('selectedCount').textContent = selectedCodes.length;
    document.getElementById('shareModal').style.display = 'block';
}

// 显示大二维码
function showLargeQRCode(code) {
    try {
        // 生成完整的URL
        const qrUrl = `https://c.ymlot.cn/couponqrcode?d=${code}`;
        
        // 创建QR码对象
        const qr = qrcode(0, 'L');
        qr.addData(qrUrl);
        qr.make();
        
        // 在模态框中显示大二维码
        document.getElementById('largeQRCode').innerHTML = qr.createSvgTag(8);  // 8是放大倍数
        document.getElementById('qrcodeModal').style.display = 'block';
    } catch (error) {
        console.error('生成大二维码失败:', error);
    }
}

// 关闭二维码模态框
function closeQRCodeModal() {
    document.getElementById('qrcodeModal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('qrcodeModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// 获取用户信息
async function getUserInfo() {
    try {
        const response = await fetch('/api/user/profile', {
            credentials: 'include'  // 添加这行以包含 cookies
        });
        
        if (response.status === 401) {
            window.location.href = '/login.html';
            return;
        }

        const data = await response.json();
        if (data.code === 0) {
            const userInfo = data.data;
            
            // 格式化创建时间为北京时间
            const createdDate = new Date(userInfo.created_at);
            const beijingTime = new Date(createdDate.getTime());  // 创建新的日期对象
            
            document.getElementById('profile-username').textContent = userInfo.username || '-';
            document.getElementById('profile-license').textContent = userInfo.license_plate || '-';
            document.getElementById('profile-userno').textContent = userInfo.user_no || '-';
            document.getElementById('profile-openid').textContent = userInfo.openid || '-';
            document.getElementById('profile-email').textContent = userInfo.email || '-';
            document.getElementById('profile-created').textContent = beijingTime.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                timeZone: 'Asia/Shanghai'  // 指定北京时区
            });
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
    }
}

// 加载分享记录
async function loadShareRecords(page = 1) {
    try {
        console.log('Loading share records for page:', page);
        
        // 确保分享记录页面是可见的
        const shareRecordsPage = document.getElementById('share-recordsPage');
        if (!shareRecordsPage) {
            console.error('Share records page element not found!');
            return;
        }
        
        const response = await fetch(`/api/share-records?page=${page}&page_size=${sharePageSize}`);
        const data = await response.json();
        console.log('Share records response:', data);
        
        if (data.code === 0) {
            const records = data.data.records;
            const total = data.data.total;
            
            console.log('Processing records:', records);
            
            // 更新分页信息
            const totalElement = document.getElementById('totalShares');
            const currentPageElement = document.getElementById('currentSharePage');
            
            if (!totalElement || !currentPageElement) {
                console.error('Pagination elements not found!');
                return;
            }
            
            totalElement.textContent = total;
            currentPageElement.textContent = page;
            currentSharePage = page;
            
            // 更新表格内容
            const tbody = document.getElementById('shareRecordsTable');
            if (!tbody) {
                console.error('Share records table body not found!');
                return;
            }
            
            tbody.innerHTML = '';
            
            records.forEach(record => {
                console.log('Processing record:', record);
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${record.share_time}</td>
                    <td class="share-direction">${record.from_username}</td>
                    <td class="share-count">${record.share_count}张</td>
                `;
                tbody.appendChild(tr);
            });
            
            // 更新分页按钮状态
            const prevBtn = document.getElementById('prevShareBtn');
            const nextBtn = document.getElementById('nextShareBtn');
            
            if (!prevBtn || !nextBtn) {
                console.error('Pagination buttons not found!');
                return;
            }
            
            prevBtn.disabled = page <= 1;
            nextBtn.disabled = page >= Math.ceil(total / sharePageSize);
            
        } else {
            console.error('Failed to load share records:', data.message);
            alert(data.message || '加载分享记录失败');
        }
    } catch (error) {
        console.error('加载分享记录失败:', error);
        alert('加载分享记录失败');
    }
}

// 初始化分享记录页面事件监听器
function initShareRecordsEvents() {
    console.log('Initializing share records events');
    
    // 分页按钮事件
    const prevBtn = document.getElementById('prevShareBtn');
    const nextBtn = document.getElementById('nextShareBtn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            console.log('Clicking prev button, current page:', currentSharePage);
            if (currentSharePage > 1) {
                loadShareRecords(currentSharePage - 1);
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            console.log('Clicking next button, current page:', currentSharePage);
            loadShareRecords(currentSharePage + 1);
        });
    }
    
    // 搜索和重置按钮事件
    const searchBtn = document.getElementById('searchShareButton');
    const resetBtn = document.getElementById('resetShareButton');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            console.log('Searching share records');
            loadShareRecords(1);
        });
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            console.log('Resetting share records search');
            document.getElementById('shareStartDate').value = '';
            document.getElementById('shareEndDate').value = '';
            loadShareRecords(1);
        });
    }
}

// 在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // ... 现有的初始化代码 ...
    
    // 初始化分享记录页面
    initShareRecordsEvents();
});

// 添加检查用户是否可以创建任务的函数
function checkUserCanCreateTask() {
    const user = JSON.parse(localStorage.getItem('user'));
    const schedulePage = document.getElementById('schedulePage');
    
    // 移除已存在的遮罩层（如果有）
    const existingOverlay = document.querySelector('.schedule-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    
    if (!user || !user.openid || !user.user_no) {
        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'schedule-overlay';
        
        overlay.innerHTML = `
            <div class="schedule-overlay-content">
                <div class="schedule-overlay-icon">⚠️</div>
                <div class="schedule-overlay-message">
                    请先在个人中心完善微信 OpenID 和用户编号信息，才能创建定时任务
                </div>
                <a href="#" class="schedule-overlay-link" onclick="showContent('profile')">
                    前往个人中心
                </a>
            </div>
        `;
        
        // 添加遮罩层到定时任务页面
        schedulePage.appendChild(overlay);
        
        // 禁用表单
        const scheduleForm = document.getElementById('scheduleForm');
        if (scheduleForm) {
            const inputs = scheduleForm.querySelectorAll('input, select, button');
            inputs.forEach(input => {
                input.disabled = true;
            });
        }
    } else {
        // 启用表单
        const scheduleForm = document.getElementById('scheduleForm');
        if (scheduleForm) {
            const inputs = scheduleForm.querySelectorAll('input, select, button');
            inputs.forEach(input => {
                if (input.id !== 'autoCollect') { // 保持自动领取复选框禁用
                    input.disabled = false;
                }
            });
        }
    }
}

// 初始化事件监听器
function initEventListeners() {
    // 处理编辑个人信息表单提交
    const editProfileForm = document.getElementById('editProfileForm');
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            try {
                const formData = {
                    license_plate: document.getElementById('edit-license').value.trim(),
                    user_no: document.getElementById('edit-userno').value.trim(),
                    openid: document.getElementById('edit-openid').value.trim(),
                    email: document.getElementById('edit-email').value.trim()
                };
                
                const response = await fetch('/api/user/profile', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Username': JSON.parse(localStorage.getItem('user')).username
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.code === 0) {
                    alert('更新成功');
                    // 关闭模态框
                    document.getElementById('editProfileModal').style.display = 'none';
                    // 重新加载个人信息
                    await loadProfileData();
                    // 更新本地存储的用户信息
                    const user = JSON.parse(localStorage.getItem('user'));
                    Object.assign(user, formData);
                    localStorage.setItem('user', JSON.stringify(user));
                } else {
                    alert(data.message || '更新失败');
                }
            } catch (error) {
                console.error('更新个人信息失败:', error);
                alert('更新失败');
            }
        });
    }

    // 处理编辑按钮点击
    const editProfileButton = document.getElementById('editProfileButton');
    if (editProfileButton) {
        editProfileButton.addEventListener('click', function() {
            // 填充当前值
            const user = JSON.parse(localStorage.getItem('user'));
            if (user) {
                document.getElementById('edit-license').value = user.license_plate || '';
                document.getElementById('edit-userno').value = user.user_no || '';
                document.getElementById('edit-openid').value = user.openid || '';
                document.getElementById('edit-email').value = user.email || '';
            }
            // 显示模态框
            document.getElementById('editProfileModal').style.display = 'block';
        });
    }

    // 处理关闭按钮点击
    const closeEditModalButton = document.getElementById('closeEditModalButton');
    if (closeEditModalButton) {
        closeEditModalButton.addEventListener('click', function() {
            document.getElementById('editProfileModal').style.display = 'none';
        });
    }
}