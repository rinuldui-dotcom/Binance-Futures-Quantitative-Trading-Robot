# 🚀 币安合约量化交易机器人

一个功能完善、易于部署的币安合约量化交易应用。

## ✨ 特性

- 🎯 **多策略支持**: RSI、均线交叉、布林带等
- 🛡️ **完善风控**: 仓位管理、止损止盈、风险控制
- 📊 **实时监控**: Web UI 界面，实时查看交易状态
- 🔔 **智能通知**: Telegram、邮件通知
- 📈 **性能分析**: 交易统计、性能指标
- 🐳 **容器化部署**: Docker 一键部署
- 🔧 **可扩展架构**: 易于添加新策略

## 🚀 快速开始

### 1. 环境准备

```bash
git clone <repository>
cd binance-quant-trading
cp .env.example .env

目录结构

binance-quant-trading/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── .env.example
├── .dockerignore
├── config/
│   ├── config.yaml
│   ├── strategies.yaml
│   └── logging.yaml
├── src/
│   ├── main.py
│   ├── binance_client.py
│   ├── trading_strategies/
│   │   ├── __init__.py
│   │   ├── base_strategy.py
│   │   ├── rsi_strategy.py
│   │   ├── ma_crossover_strategy.py
│   │   └── bollinger_bands_strategy.py
│   ├── risk_manager.py
│   ├── position_manager.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── migrations/
│   ├── web_ui/
│   │   ├── app.py
│   │   └── templates/
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── telegram_notifier.py
│   │   └── email_notifier.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   ├── logger.py
│   │   └── helpers.py
│   └── tests/
├── scripts/
│   ├── deploy.sh
│   ├── backup_db.sh
│   └── health_check.sh
├── monitoring/
│   ├── prometheus.yml
│   └── alert_rules.yml
├── nginx/
│   └── nginx.conf
├── logs/
├── data/
└── README.md
