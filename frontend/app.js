const { createApp, ref, reactive, nextTick } = Vue;

// 确保 ElementPlus 和 ElementPlusLocaleZhCn 已定义
if (typeof ElementPlus === 'undefined') {
    throw new Error('ElementPlus is not loaded');
}
if (typeof ElementPlusLocaleZhCn === 'undefined') {
    throw new Error('ElementPlusLocaleZhCn is not loaded');
}

const app = createApp({
    setup() {
        const records = ref([]);
        const loading = ref(false);
        const currentPage = ref(1);
        const pageSize = ref(5);
        const total = ref(0);
        const searchForm = reactive({
            startTime: '',
            endTime: '',
            status: ''
        });

        // 添加时间选择器的选项
        const timeOptions = {
            hours: Array.from({ length: 24 }, (_, i) => ({
                value: i,
                label: String(i).padStart(2, '0')
            })),
            minutes: Array.from({ length: 60 }, (_, i) => ({
                value: i,
                label: String(i).padStart(2, '0')
            }))
        };

        // 格式化时间的函数
        const formatDateTime = (dateStr) => {
            if (!dateStr) return '';
            const date = new Date(dateStr + '+08:00');
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        };

        // 生成二维码
        const generateQRCodes = async () => {
            await nextTick();
            records.value.forEach((record, index) => {
                const container = document.getElementById(`qrcode-${index}`);
                if (container && !container.hasChildNodes()) {
                    container.innerHTML = ''; // 清除可能存在的旧二维码
                    new QRCode(container, {
                        text: record.code_id,
                        width: 128,
                        height: 128,
                        colorDark: "#000000",
                        colorLight: "#ffffff",
                        correctLevel: QRCode.CorrectLevel.H
                    });
                }
            });
        };

        // 状态选项
        const statusOptions = [
            { label: '正常', value: '0' },
            { label: '已核销', value: '1' }
        ];

        // 获取状态显示文本
        const getStatusLabel = (value) => {
            const option = statusOptions.find(opt => opt.value === value);
            return option ? option.label : '全部';
        };

        const searchRecords = async () => {
            loading.value = true;
            try {
                const params = new URLSearchParams();
                if (searchForm.startTime) {
                    params.append('start_time', searchForm.startTime);
                }
                if (searchForm.endTime) {
                    params.append('end_time', searchForm.endTime);
                }
                if (searchForm.status !== undefined && searchForm.status !== null && searchForm.status !== '') {
                    params.append('status', searchForm.status);
                }
                params.append('page', currentPage.value);
                params.append('page_size', pageSize.value);

                const response = await axios.get(`/api/records?${params.toString()}`);
                if (response.data.code === 0) {
                    records.value = response.data.data.records.map(record => ({
                        ...record,
                        created_at: formatDateTime(record.created_at),
                        updated_at: formatDateTime(record.updated_at)
                    }));
                    total.value = response.data.data.total;
                    await generateQRCodes();
                } else {
                    ElementPlus.ElMessage.error('查询失败');
                }
            } catch (error) {
                console.error('查询失败:', error);
                ElementPlus.ElMessage.error('查询失败');
            } finally {
                loading.value = false;
            }
        };

        const resetForm = () => {
            searchForm.startTime = '';
            searchForm.endTime = '';
            searchForm.status = undefined;
        };

        const handleDelete = async (codeId) => {
            try {
                const response = await axios.delete(`/api/records/${codeId}`);
                if (response.data.code === 0) {
                    ElementPlus.ElMessage.success('删除成功');
                    searchRecords(); // 重新加载数据
                } else {
                    ElementPlus.ElMessage.error('删除失败');
                }
            } catch (error) {
                console.error('删除失败:', error);
                ElementPlus.ElMessage.error('删除失败');
            }
        };

        // 处理每页显示数量变化
        const handleSizeChange = (val) => {
            pageSize.value = val;
            currentPage.value = 1; // 重置到第一页
            searchRecords();
        };

        // 处理页码变化
        const handleCurrentChange = (val) => {
            currentPage.value = val;
            searchRecords();
        };

        // 初始加载
        searchRecords();

        // 在上传文件的方法中添加轮询任务状态的逻辑
        const uploadFile = async (file) => {
            try {
                loading.value = true;
                const formData = new FormData();
                formData.append('file', file);

                // 上传文件
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    headers: {
                        'X-Username': localStorage.getItem('username')
                    },
                    body: formData
                });

                const result = await response.json();
                if (result.code === 0) {
                    // 开始轮询任务状态
                    const taskId = result.data.task_id;
                    await pollTaskStatus(taskId);
                } else {
                    ElMessage.error(result.message || '上传失败');
                }
            } catch (error) {
                console.error('上传失败:', error);
                ElMessage.error('上传失败');
            } finally {
                loading.value = false;
            }
        };

        // 轮询任务状态
        const pollTaskStatus = async (taskId) => {
            const maxAttempts = 30;
            const interval = 1000;
            let attempts = 0;

            while (attempts < maxAttempts) {
                try {
                    console.log(`正在获取任务 ${taskId} 的状态...`);
                    const response = await fetch(`/api/task-status/${taskId}`, {
                        headers: {
                            'X-Username': localStorage.getItem('username')
                        }
                    });
                    const result = await response.json();
                    console.log('API 返回结果:', result);  // 添加日志
                    
                    if (result.code === 0) {
                        const status = result.data;
                        console.log('解析后的任务状态:', status);  // 添加日志

                        if (status.status === 'completed') {
                            // 处理完成
                            console.log('任务完成，结果:', status.results);  // 添加日志
                            ElMessage.success(status.message || '处理完成');
                            // 显示处理结果
                            if (status.results && status.results.length > 0) {
                                const successCount = status.results.filter(r => r.status === 'success').length;
                                const failedCount = status.results.filter(r => r.status === 'failed').length;
                                const invalidCount = status.results.filter(r => r.status === 'invalid').length;
                                ElMessage.info(`处理完成: ${successCount}个成功, ${failedCount}个失败, ${invalidCount}个无效`);
                            }
                            // 刷新记录列表
                            await searchRecords();
                            return;
                        } else if (status.status === 'error') {
                            // 处理出错
                            console.log('任务出错:', status.message);  // 添加日志
                            ElMessage.error(status.message || '处理失败');
                            return;
                        } else {
                            console.log('任务处理中...');  // 添加日志
                        }
                    } else {
                        console.error('获取任务状态失败:', result.message);  // 添加日志
                        ElMessage.error(result.message || '获取任务状态失败');
                        return;
                    }
                } catch (error) {
                    console.error('轮询任务状态失败:', error);
                }

                attempts++;
                await new Promise(resolve => setTimeout(resolve, interval));
            }

            ElMessage.warning('任务处理超时');
        };

        // 添加新的响应式变量
        const shareDialogVisible = ref(false);
        const shareForm = reactive({
            username: '',
            codeId: ''
        });
        
        // 显示分享对话框
        const showShareDialog = (row) => {
            shareForm.codeId = row.code_id;
            shareDialogVisible.value = true;
        };
        
        // 处理分享
        const handleShare = async () => {
            try {
                if (!shareForm.username) {
                    ElementPlus.ElMessage.warning('请输入用户名');
                    return;
                }
                
                const response = await axios.post('/api/share-code', {
                    code_id: shareForm.codeId,
                    username: shareForm.username
                });
                
                if (response.data.code === 0) {
                    ElementPlus.ElMessage.success('分享成功');
                    shareDialogVisible.value = false;
                    searchRecords(); // 刷新列表
                } else {
                    ElementPlus.ElMessage.error(response.data.message || '分享失败');
                }
            } catch (error) {
                console.error('分享失败:', error);
                ElementPlus.ElMessage.error('分享失败');
            }
        };

        return {
            records,
            loading,
            searchForm,
            searchRecords,
            resetForm,
            handleDelete,
            statusOptions,
            getStatusLabel,
            currentPage,
            pageSize,
            total,
            handleSizeChange,
            handleCurrentChange,
            uploadFile,
            pollTaskStatus,
            shareDialogVisible,
            shareForm,
            showShareDialog,
            handleShare,
            timeOptions,  // 导出时间选项
            formatDateTime
        };
    }
});

app.use(ElementPlus, {
    locale: ElementPlusLocaleZhCn,
});
app.mount('#app'); 