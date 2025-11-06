import os
import logging
import asyncio
import signal
import sys
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from utils.config_loader import ConfigLoader
from utils.logger import setup_logging
from binance_client import BinanceClient
from trading_strategies.strategy_manager import StrategyManager
from risk_manager import RiskManager
from position_manager import PositionManager
from database.database import Database
from notifications.notification_manager import NotificationManager
from web_ui.app import create_web_app
import uvicorn
# 在导入部分添加
from ai.ai_manager import AIManager

class QuantTradingApp:
    def __init__(self):
        self.config = ConfigLoader.load_config()
        self.logger = setup_logging(self.config)
        self.running = False
        self.start_time = None
        
        # 初始化组件
        self.components = {}
        self.setup_components()
        
    def setup_components(self):
        """初始化所有组件"""
        try:
            # 数据库
            self.components['database'] = Database(self.config)
            
            # AI管理器
            self.components['ai_manager'] = AIManager(self.config)
            
            # 通知管理器
            self.components['notifier'] = NotificationManager(self.config)
            
            # 币安客户端
            self.components['binance'] = BinanceClient(self.config, self.components['notifier'])
            
            # 风险管理器
            self.components['risk_manager'] = RiskManager(
                self.config, 
                self.components['database'],
                self.components['notifier']
            )
            
            # 仓位管理器
            self.components['position_manager'] = PositionManager(
                self.config,
                self.components['binance'],
                self.components['database'],
                self.components['risk_manager']
            )
            
            # 策略管理器 (传入AI管理器)
            self.components['strategy_manager'] = StrategyManager(
                self.config,
                self.components['binance'],
                self.components['position_manager'],
                self.components['risk_manager'],
                self.components['database'],
                self.components['ai_manager']  # 新增参数
            )
            
            self.logger.info("所有组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise

load_dotenv()

class QuantTradingApp:
    def __init__(self):
        self.config = ConfigLoader.load_config()
        self.logger = setup_logging(self.config)
        self.running = False
        self.start_time = None
        
        # 初始化组件
        self.components = {}
        self.setup_components()
        
    def setup_components(self):
        """初始化所有组件"""
        try:
            # 数据库
            self.components['database'] = Database(self.config)
            
            # 通知管理器
            self.components['notifier'] = NotificationManager(self.config)
            
            # 币安客户端
            self.components['binance'] = BinanceClient(self.config, self.components['notifier'])
            
            # 风险管理器
            self.components['risk_manager'] = RiskManager(
                self.config, 
                self.components['database'],
                self.components['notifier']
            )
            
            # 仓位管理器
            self.components['position_manager'] = PositionManager(
                self.config,
                self.components['binance'],
                self.components['database'],
                self.components['risk_manager']
            )
            
            # 策略管理器
            self.components['strategy_manager'] = StrategyManager(
                self.config,
                self.components['binance'],
                self.components['position_manager'],
                self.components['risk_manager'],
                self.components['database']
            )
            
            self.logger.info("所有组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
            
    async def start(self):
        """启动交易应用"""
        self.logger.info("🚀 启动币安量化交易应用...")
        self.start_time = time.time()
        self.running = True
        
        try:
            # 启动通知
            await self.components['notifier'].send_message("🔔 交易机器人启动")
            
            # 初始化数据库
            await self.components['database'].initialize()
            
            # 连接币安
            await self.components['binance'].initialize()
            
            # 启动策略管理器
            await self.components['strategy_manager'].start()
            
            # 启动Web UI (如果启用)
            if self.config['web_ui']['enabled']:
                await self.start_web_ui()
                
            # 主循环
            await self.main_loop()
            
        except Exception as e:
            self.logger.error(f"应用启动失败: {e}")
            await self.stop()
            
    async def start_web_ui(self):
        """启动Web UI"""
        try:
            app = create_web_app(self)
            config = uvicorn.Config(
                app, 
                host=self.config['web_ui']['host'],
                port=self.config['web_ui']['port'],
                log_level="info"
            )
            server = uvicorn.Server(config)
            # 在后台运行Web服务器
            asyncio.create_task(server.serve())
            self.logger.info(f"Web UI 启动在 {self.config['web_ui']['host']}:{self.config['web_ui']['port']}")
        except Exception as e:
            self.logger.error(f"Web UI 启动失败: {e}")
            
    async def main_loop(self):
        """主循环"""
        iteration = 0
        while self.running:
            try:
                # 定期健康检查
                if iteration % 30 == 0:  # 每30次循环检查一次
                    await self.health_check()
                    
                # 定期报告
                if iteration % 300 == 0:  # 每300次循环报告一次
                    await self.periodic_report()
                    
                iteration += 1
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"主循环错误: {e}")
                await asyncio.sleep(5)
                
    async def health_check(self):
        """健康检查"""
        try:
            # 检查币安连接
            balance = self.components['binance'].get_balance()
            if not balance:
                self.logger.warning("币安连接检查失败")
                
            # 检查数据库连接
            await self.components['database'].health_check()
            
            self.logger.debug("健康检查通过")
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            
    async def periodic_report(self):
        """定期报告"""
        try:
            stats = await self.components['strategy_manager'].get_performance_stats()
            self.logger.info(f"性能统计: {stats}")
            
            # 发送定期报告通知
            message = f"📊 定期报告\n交易次数: {stats['total_trades']}\n盈利比率: {stats['win_rate']:.2%}"
            await self.components['notifier'].send_message(message)
            
        except Exception as e:
            self.logger.error(f"定期报告生成失败: {e}")
            
    async def stop(self):
        """停止交易应用"""
        self.logger.info("🛑 停止交易应用...")
        self.running = False
        
        # 停止所有组件
        for name, component in reversed(self.components.items()):
            try:
                if hasattr(component, 'stop'):
                    await component.stop()
                self.logger.debug(f"组件 {name} 已停止")
            except Exception as e:
                self.logger.error(f"停止组件 {name} 时出错: {e}")
                
        # 发送停止通知
        try:
            runtime = time.time() - self.start_time
            await self.components['notifier'].send_message(
                f"🔴 交易机器人已停止\n运行时间: {runtime:.0f}秒"
            )
        except Exception as e:
            self.logger.error(f"发送停止通知失败: {e}")
            
    def get_status(self):
        """获取应用状态"""
        return {
            "running": self.running,
            "uptime": time.time() - self.start_time if self.start_time else 0,
            "components": {name: "active" for name in self.components.keys()}
        }

# 信号处理
def signal_handler(signum, frame):
    """处理系统信号"""
    asyncio.create_task(app.stop())

if __name__ == "__main__":
    app = QuantTradingApp()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动应用
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        asyncio.run(app.stop())
    except Exception as e:
        logging.error(f"应用运行失败: {e}")
        sys.exit(1)
