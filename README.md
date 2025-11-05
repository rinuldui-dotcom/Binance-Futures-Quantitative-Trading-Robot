# 🚀 币安合约量化交易机器人 （ 由喵哥提供技术支持）

一个功能完善、易于部署的币安合约量化交易应用，支持多种交易策略和风险管理。

## ✨ 特性

- 🎯 **多策略支持**: RSI、均线交叉、布林带等经典策略
- 🛡️ **完善风控**: 仓位管理、止损止盈、风险控制
- 📊 **实时监控**: Web UI 界面，实时查看交易状态
- 🔔 **智能通知**: Telegram、邮件实时通知
- 📈 **性能分析**: 完整的交易统计和性能指标
- 🐳 **容器化部署**: Docker 一键部署
- 🔧 **可扩展架构**: 易于添加新策略和功能
- 📱 **响应式界面**: 支持移动端访问的Web界面

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- 币安账户 (API Key 和 Secret Key)
- (可选) Telegram Bot (用于通知)

### 1. 克隆项目

```bash
git clone 本仓库
cd binance-quant-trading

环境配置
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
cp config/config.yaml.example config/config.yaml

编辑 .env 文件:

# 币安API配置 (必需)
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here

# 应用配置
ENVIRONMENT=development
TESTNET=true
SANDBOX_MODE=true

# 交易配置
TOTAL_CAPITAL=10000
RISK_PER_TRADE=0.02

# 通知配置 (可选)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Web界面认证
WEB_USERNAME=admin
WEB_PASSWORD=admin123

启动应用

# 开发环境
docker-compose up -d

# 或者带日志输出
docker-compose up

