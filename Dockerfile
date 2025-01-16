FROM python:3.11-slim
LABEL maintainer="hi@awen.me"

ENV TZ=Asia/Shanghai
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 使用清华镜像源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn\/debian-security/g' /etc/apt/sources.list.d/debian.sources

WORKDIR /code

# 复制依赖文件
COPY requirements.txt .

# 安装依赖，完成后清理缓存
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tzdata \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libzbar0 \
        gcc \
        python3-dev \
        libffi-dev \
    && ln -sf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && pip install --no-cache-dir --upgrade pip \
    && pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf ~/.cache/pip/*

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p parking/code parking/output_file static \
    && chmod -R 777 parking static \
    && ls -la api/ \
    && python -m compileall api/

CMD ["gunicorn", "run_api:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]