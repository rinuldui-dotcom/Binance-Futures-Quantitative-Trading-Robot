import asyncio
import logging
from typing import Dict
from .base_strategy import BaseStrategy
from ai.ai_manager import AIManager

class AITradingStrategy(BaseStrategy):
    """AI交易策略"""
    
    def __init__(self, config, binance_client, position_manager, risk_manager, database, ai_manager: AIManager):
        super().__init__(config, binance_client, position_manager, risk_manager, database)
        self.ai_manager = ai_manager
        self.logger = logging.getLogger(__name__)
        
        # AI策略配置
        self.ai_config = config.get('trading_ai', {})
        self.decision_interval = self.ai_config.get('decision_interval', 300)
        self.last_decision_time = 0
        
    async def execute(self, symbol: str):
        """执行AI交易策略"""
        current_time = asyncio.get_event_loop().time()
        
        # 检查决策间隔
        if current_time - self.last_decision_time < self.decision_interval:
            return
            
        try:
            # 获取市场数据
            market_data = await self.get_market_data(symbol)
            if not market_data:
                return
                
            # 获取当前持仓
            portfolio = await self.get_portfolio_data(symbol)
            
            # 获取AI交易信号
            ai_signal = await self.ai_manager.get_trading_signal(symbol, market_data, portfolio)
            
            # 执行AI信号
            await self.execute_ai_signal(symbol, ai_signal, portfolio)
            
            self.last_decision_time = current_time
            
        except Exception as e:
            self.logger.error(f"AI策略执行失败 {symbol}: {e}")
            
    async def get_market_data(self, symbol: str) -> Dict:
        """获取市场数据"""
        try:
            # 获取K线数据
            ohlcv = self.binance_client.get_ohlcv(symbol, '1h', 100)
            if not ohlcv:
                return {}
                
            # 获取ticker数据
            ticker = self.binance_client.get_ticker(symbol)
            
            return {
                'current_price': ticker.get('last', 0),
                'high_24h': ticker.get('high', 0),
                'low_24h': ticker.get('low', 0),
                'volume_24h': ticker.get('baseVolume', 0),
                'price_change_24h': ticker.get('percentage', 0),
                'ohlcv': ohlcv
            }
            
        except Exception as e:
            self.logger.error(f"获取市场数据失败 {symbol}: {e}")
            return {}
            
    async def get_portfolio_data(self, symbol: str) -> Dict:
        """获取持仓数据"""
        try:
            position = self.position_manager.get_position(symbol)
            balance = self.binance_client.get_balance()
            
            return {
                'position_side': position.get('side', 'none'),
                'position_size': position.get('size', 0),
                'entry_price': position.get('entry_price', 0),
                'unrealized_pnl': position.get('unrealized_pnl', 0),
                'available_balance': balance.get('free', {}).get('USDT', 0)
            }
        except Exception as e:
            self.logger.error(f"获取持仓数据失败 {symbol}: {e}")
            return {}
            
    async def execute_ai_signal(self, symbol: str, ai_signal: Dict, portfolio: Dict):
        """执行AI信号"""
        action = ai_signal.get('action', 'HOLD')
        confidence = ai_signal.get('confidence', 0)
        position_size = ai_signal.get('position_size', 0)
        
        self.logger.info(f"AI信号 {symbol}: {action} (置信度: {confidence:.2f}, 仓位: {position_size:.2f})")
        
        if action == 'HOLD':
            return
            
        current_position = portfolio.get('position_side', 'none')
        current_size = portfolio.get('position_size', 0)
        
        try:
            if action == 'BUY':
                await self.execute_buy_signal(symbol, ai_signal, current_position, current_size)
            elif action == 'SELL':
                await self.execute_sell_signal(symbol, ai_signal, current_position, current_size)
                
        except Exception as e:
            self.logger.error(f"执行AI信号失败 {symbol}: {e}")
            
    async def execute_buy_signal(self, symbol: str, ai_signal: Dict, current_position: str, current_size: float):
        """执行买入信号"""
        position_size = ai_signal.get('position_size', 0)
        leverage = ai_signal.get('leverage', 1)
        
        if current_position == 'long':
            # 已有做多仓位，考虑加仓
            if position_size > current_size:
                # 加仓
                additional_size = position_size - current_size
                if await self.risk_manager.can_open_position(symbol, 'long'):
                    await self.position_manager.increase_position(
                        symbol, 'long', additional_size, leverage
                    )
                    self.logger.info(f"AI加仓 {symbol}: +{additional_size:.4f}")
                    
        elif current_position == 'short':
            # 平空仓并开多仓
            if current_size > 0:
                await self.position_manager.close_position(symbol)
                self.logger.info(f"AI平空开多 {symbol}")
                
            if await self.risk_manager.can_open_position(symbol, 'long'):
                await self.position_manager.open_position(
                    symbol, 'long', position_size, leverage
                )
                self.logger.info(f"AI开多仓 {symbol}: {position_size:.4f}")
                
        else:
            # 开新多仓
            if await self.risk_manager.can_open_position(symbol, 'long'):
                await self.position_manager.open_position(
                    symbol, 'long', position_size, leverage
                )
                self.logger.info(f"AI开多仓 {symbol}: {position_size:.4f}")
                
        # 设置止损止盈
        await self.set_stop_loss_take_profit(symbol, ai_signal, 'long')
        
    async def execute_sell_signal(self, symbol: str, ai_signal: Dict, current_position: str, current_size: float):
        """执行卖出信号"""
        position_size = ai_signal.get('position_size', 0)
        leverage = ai_signal.get('leverage', 1)
        
        if current_position == 'short':
            # 已有做空仓位，考虑加仓
            if position_size > current_size:
                # 加仓
                additional_size = position_size - current_size
                if await self.risk_manager.can_open_position(symbol, 'short'):
                    await self.position_manager.increase_position(
                        symbol, 'short', additional_size, leverage
                    )
                    self.logger.info(f"AI加仓 {symbol}: +{additional_size:.4f}")
                    
        elif current_position == 'long':
            # 平多仓并开空仓
            if current_size > 0:
                await self.position_manager.close_position(symbol)
                self.logger.info(f"AI平多开空 {symbol}")
                
            if await self.risk_manager.can_open_position(symbol, 'short'):
                await self.position_manager.open_position(
                    symbol, 'short', position_size, leverage
                )
                self.logger.info(f"AI开空仓 {symbol}: {position_size:.4f}")
                
        else:
            # 开新空仓
            if await self.risk_manager.can_open_position(symbol, 'short'):
                await self.position_manager.open_position(
                    symbol, 'short', position_size, leverage
                )
                self.logger.info(f"AI开空仓 {symbol}: {position_size:.4f}")
                
        # 设置止损止盈
        await self.set_stop_loss_take_profit(symbol, ai_signal, 'short')
        
    async def set_stop_loss_take_profit(self, symbol: str, ai_signal: Dict, side: str):
        """设置止损止盈"""
        stop_loss = ai_signal.get('stop_loss')
        take_profit = ai_signal.get('take_profit')
        
        if stop_loss:
            try:
                await self.position_manager.set_stop_loss(symbol, stop_loss)
                self.logger.info(f"AI设置止损 {symbol}: {stop_loss}")
            except Exception as e:
                self.logger.error(f"设置止损失败 {symbol}: {e}")
                
        if take_profit:
            try:
                await self.position_manager.set_take_profit(symbol, take_profit)
                self.logger.info(f"AI设置止盈 {symbol}: {take_profit}")
            except Exception as e:
                self.logger.error(f"设置止盈失败 {symbol}: {e}")
                
    def get_interval(self) -> int:
        """获取策略执行间隔"""
        return self.decision_interval
