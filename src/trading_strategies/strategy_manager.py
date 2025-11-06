import asyncio
import logging
from typing import Dict, List
import importlib

from .base_strategy import BaseStrategy
from .rsi_strategy import RSIStrategy
from .ma_crossover_strategy import MACrossoverStrategy
from .bollinger_bands_strategy import BollingerBandsStrategy
from .ai_trading_strategy import AITradingStrategy  # 新增导入

class StrategyManager:
    def __init__(self, config, binance_client, position_manager, risk_manager, database, ai_manager):  # 新增ai_manager参数
        self.config = config
        self.binance_client = binance_client
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.database = database
        self.ai_manager = ai_manager  # 新增
        self.logger = logging.getLogger(__name__)
        
        self.strategies: Dict[str, BaseStrategy] = {}
        self.running = False
        
    async def load_strategy(self, strategy_name: str):
        """加载策略"""
        try:
            if strategy_name == 'ai_trading':
                strategy_class = AITradingStrategy
            else:
                strategy_class = self.get_strategy_class(strategy_name)
                
            if not strategy_class:
                self.logger.error(f"未知策略: {strategy_name}")
                return
                
            strategy_config = self.config['strategies'].get(strategy_name, {})
            
            if strategy_name == 'ai_trading':
                strategy = strategy_class(
                    strategy_config,
                    self.binance_client,
                    self.position_manager,
                    self.risk_manager,
                    self.database,
                    self.ai_manager  # 传入AI管理器
                )
            else:
                strategy = strategy_class(
                    strategy_config,
                    self.binance_client,
                    self.position_manager,
                    self.risk_manager,
                    self.database
                )
            
            self.strategies[strategy_name] = strategy
            self.logger.info(f"策略加载成功: {strategy_name}")
            
        except Exception as e:
            self.logger.error(f"加载策略 {strategy_name} 失败: {e}")
            
    def get_strategy_class(self, strategy_name: str):
        """获取策略类"""
        strategy_map = {
            'rsi_strategy': RSIStrategy,
            'ma_crossover': MACrossoverStrategy,
            'bollinger_bands': BollingerBandsStrategy,
            'ai_trading': AITradingStrategy  # 新增
        }
        return strategy_map.get(strategy_name)

class StrategyManager:
    def __init__(self, config, binance_client, position_manager, risk_manager, database):
        self.config = config
        self.binance_client = binance_client
        self.position_manager = position_manager
        self.risk_manager = risk_manager
        self.database = database
        self.logger = logging.getLogger(__name__)
        
        self.strategies: Dict[str, BaseStrategy] = {}
        self.running = False
        
    async def start(self):
        """启动所有策略"""
        self.logger.info("启动交易策略管理器...")
        self.running = True
        
        # 加载启用的策略
        enabled_strategies = self.config['strategies']['enabled']
        for strategy_name in enabled_strategies:
            await self.load_strategy(strategy_name)
            
        # 启动策略任务
        tasks = []
        for symbol in self.config['trading']['symbols']:
            for strategy in self.strategies.values():
                task = asyncio.create_task(
                    self.run_strategy_for_symbol(strategy, symbol)
                )
                tasks.append(task)
                
        self.logger.info(f"启动 {len(tasks)} 个策略任务")
        
    async def load_strategy(self, strategy_name: str):
        """加载策略"""
        try:
            strategy_class = self.get_strategy_class(strategy_name)
            if not strategy_class:
                self.logger.error(f"未知策略: {strategy_name}")
                return
                
            strategy_config = self.config['strategies'].get(strategy_name, {})
            strategy = strategy_class(
                strategy_config,
                self.binance_client,
                self.position_manager,
                self.risk_manager,
                self.database
            )
            
            self.strategies[strategy_name] = strategy
            self.logger.info(f"策略加载成功: {strategy_name}")
            
        except Exception as e:
            self.logger.error(f"加载策略 {strategy_name} 失败: {e}")
            
    def get_strategy_class(self, strategy_name: str):
        """获取策略类"""
        strategy_map = {
            'rsi_strategy': RSIStrategy,
            'ma_crossover': MACrossoverStrategy,
            'bollinger_bands': BollingerBandsStrategy
        }
        return strategy_map.get(strategy_name)
        
    async def run_strategy_for_symbol(self, strategy: BaseStrategy, symbol: str):
        """为指定交易对运行策略"""
        self.logger.info(f"为 {symbol} 启动策略 {strategy.__class__.__name__}")
        
        while self.running:
            try:
                # 检查交易时间
                if not await self.is_trading_hours():
                    await asyncio.sleep(60)
                    continue
                    
                # 执行策略
                await strategy.execute(symbol)
                
                # 策略特定的间隔
                await asyncio.sleep(strategy.get_interval())
                
            except Exception as e:
                self.logger.error(f"{symbol} 策略执行错误: {e}")
                await asyncio.sleep(60)
                
    async def is_trading_hours(self) -> bool:
        """检查是否在交易时间内"""
        # 实现交易时间检查逻辑
        return True
        
    async def stop(self):
        """停止所有策略"""
        self.logger.info("停止策略管理器...")
        self.running = False
        
    async def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        # 实现性能统计逻辑
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0
        }
