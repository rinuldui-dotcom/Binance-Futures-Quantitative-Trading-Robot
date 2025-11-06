import logging
from typing import Dict, List, Optional
from .base_ai_client import BaseAIClient
from .glm4_client import GLM4Client
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient

class AIManager:
    """AI模型管理器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.clients: Dict[str, BaseAIClient] = {}
        self.active_client: Optional[BaseAIClient] = None
        
        self.setup_clients()
        
    def setup_clients(self):
        """设置AI客户端"""
        ai_config = self.config.get('ai_models', {})
        
        # GLM4客户端
        if ai_config.get('glm4', {}).get('enabled', False):
            try:
                self.clients['glm4'] = GLM4Client(ai_config['glm4'])
                self.active_client = self.clients['glm4']
                self.logger.info("GLM4客户端初始化成功")
            except Exception as e:
                self.logger.error(f"GLM4客户端初始化失败: {e}")
                
        # OpenAI客户端
        if ai_config.get('openai', {}).get('enabled', False):
            try:
                self.clients['openai'] = OpenAIClient(ai_config['openai'])
                if not self.active_client:
                    self.active_client = self.clients['openai']
                self.logger.info("OpenAI客户端初始化成功")
            except Exception as e:
                self.logger.error(f"OpenAI客户端初始化失败: {e}")
                
        # Anthropic客户端
        if ai_config.get('anthropic', {}).get('enabled', False):
            try:
                self.clients['anthropic'] = AnthropicClient(ai_config['anthropic'])
                if not self.active_client:
                    self.active_client = self.clients['anthropic']
                self.logger.info("Anthropic客户端初始化成功")
            except Exception as e:
                self.logger.error(f"Anthropic客户端初始化失败: {e}")
                
        if not self.active_client:
            self.logger.warning("没有可用的AI客户端，AI交易功能将不可用")
            
    def switch_client(self, client_name: str) -> bool:
        """切换AI客户端"""
        if client_name in self.clients:
            self.active_client = self.clients[client_name]
            self.logger.info(f"切换到AI客户端: {client_name}")
            return True
        else:
            self.logger.error(f"未知的AI客户端: {client_name}")
            return False
            
    async def get_trading_signal(self, symbol: str, market_data: Dict, portfolio: Dict) -> Dict:
        """获取交易信号"""
        if not self.active_client:
            return self._get_default_signal("无可用AI客户端")
            
        try:
            # 丰富市场数据
            enriched_data = await self._enrich_market_data(symbol, market_data)
            
            signal = await self.active_client.get_trading_signal(enriched_data, portfolio)
            
            # 应用风险调整
            adjusted_signal = self._apply_risk_adjustment(signal, portfolio)
            
            self.logger.info(f"AI交易信号: {symbol} - {adjusted_signal['action']} (置信度: {adjusted_signal['confidence']:.2f})")
            return adjusted_signal
            
        except Exception as e:
            self.logger.error(f"获取AI交易信号失败: {e}")
            return self._get_default_signal(f"AI信号获取失败: {str(e)}")
            
    async def _enrich_market_data(self, symbol: str, market_data: Dict) -> Dict:
        """丰富市场数据"""
        # 添加技术指标计算
        indicators = await self._calculate_technical_indicators(market_data)
        
        enriched_data = {
            **market_data,
            'symbol': symbol,
            'indicators': indicators
        }
        
        return enriched_data
        
    async def _calculate_technical_indicators(self, market_data: Dict) -> Dict:
        """计算技术指标"""
        # 这里可以集成TA-Lib等技术指标库
        # 简化实现，实际项目中应该计算真实的指标
        return {
            'rsi': 45.2,
            'macd': -12.5,
            'ma20': market_data.get('current_price', 0) * 0.98,
            'bb_upper': market_data.get('current_price', 0) * 1.02,
            'bb_middle': market_data.get('current_price', 0),
            'bb_lower': market_data.get('current_price', 0) * 0.98,
            'volume': market_data.get('volume_24h', 0)
        }
        
    def _apply_risk_adjustment(self, signal: Dict, portfolio: Dict) -> Dict:
        """应用风险调整"""
        trading_config = self.config.get('trading_ai', {})
        confidence_threshold = trading_config.get('confidence_threshold', 0.7)
        max_position = trading_config.get('max_ai_position_size', 0.3)
        
        # 如果置信度低于阈值，调整为HOLD
        if signal['confidence'] < confidence_threshold:
            signal['action'] = 'HOLD'
            signal['position_size'] = 0.0
            signal['reasoning'] += f" (置信度{signal['confidence']:.2f}低于阈值{confidence_threshold})"
            
        # 限制最大仓位
        if signal['position_size'] > max_position:
            signal['position_size'] = max_position
            signal['reasoning'] += f" (仓位限制为{max_position})"
            
        # 检查当前持仓，避免过度交易
        current_position = portfolio.get('position_size', 0)
        if current_position > 0 and signal['action'] == 'HOLD':
            # 如果有持仓但AI建议HOLD，可以考虑减仓
            if signal['confidence'] < 0.4:
                signal['action'] = 'SELL'
                signal['position_size'] = min(current_position, 0.5)  # 减仓50%
                signal['reasoning'] += " (低置信度，建议减仓)"
                
        return signal
        
    def _get_default_signal(self, reason: str) -> Dict:
        """获取默认信号"""
        return {
            "action": "HOLD",
            "confidence": 0.3,
            "position_size": 0.0,
            "leverage": 1,
            "stop_loss": None,
            "take_profit": None,
            "reasoning": reason,
            "source": "default"
        }
        
    async def analyze_market(self, symbol: str, market_data: Dict) -> Dict:
        """分析市场"""
        if not self.active_client:
            return {"error": "无可用AI客户端"}
            
        try:
            indicators = await self._calculate_technical_indicators(market_data)
            return await self.active_client.analyze_market(symbol, indicators)
        except Exception as e:
            self.logger.error(f"市场分析失败: {e}")
            return {"error": str(e)}
            
    async def get_position_recommendation(self, symbol: str, current_position: Dict) -> Dict:
        """获取仓位建议"""
        if not self.active_client:
            return {"error": "无可用AI客户端"}
            
        try:
            return await self.active_client.get_position_recommendation(symbol, current_position)
        except Exception as e:
            self.logger.error(f"仓位建议获取失败: {e}")
            return {"error": str(e)}
            
    def get_available_clients(self) -> List[str]:
        """获取可用的客户端列表"""
        return list(self.clients.keys())
        
    def get_active_client_info(self) -> Dict:
        """获取当前活跃客户端信息"""
        if not self.active_client:
            return {"active_client": None}
            
        return {
            "active_client": self.active_client.__class__.__name__,
            "model_name": self.active_client.model_name
        }
