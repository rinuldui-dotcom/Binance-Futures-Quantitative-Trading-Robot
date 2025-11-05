#!/bin/bash

set -e

echo "🚀 开始部署币安量化交易应用..."

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "❌ 找不到 .env 文件，请从 .env.example 复制并配置"
    exit 1
fi

# 停止现有容器
echo "停止现有容器..."
docker-compose down

# 拉取最新代码
echo "拉取最新代码..."
git pull

# 构建新镜像
echo "构建Docker镜像..."
docker-compose build --no-cache

# 启动服务
echo "启动服务..."
docker-compose up -d

# 健康检查
echo "等待服务启动..."
sleep 30

# 检查服务状态
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ 部署成功！"
    echo "📊 Web UI: http://localhost:8081"
    echo "📈 Grafana: http://localhost:3000"
else
    echo "❌ 部署失败，请检查日志"
    docker-compose logs quant-trading
    exit 1
fi
