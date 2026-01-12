FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖 (如果需要浏览器，这里可以安装 Chrome，但目前逻辑优先使用 httpx)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖并安装
COPY MissAvPuser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY MissAvPuser/ .

# 创建数据目录
RUN mkdir -p /app/data

# 设置环境变量
ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1

# 运行命令
CMD ["python", "bot.py"]
