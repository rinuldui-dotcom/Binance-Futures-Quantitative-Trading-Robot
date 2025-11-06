import aiohttp
import json
import logging
from typing import Dict
from .base_ai_client import BaseAIClient

class OpenAIClient(BaseAIClient):
    """OpenAI兼容客户端"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.api_key = config['api_key']
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
    async def get_trading_signal(self, market_data: Dict, portfolio: Dict) -> Dict:
        """获取OpenAI交易信号"""
        prompt = self._build_trading_prompt(market_data, portfolio)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "response_format": {"type": "json_object"}
                }
                
                url = f"{self.base_url}/chat/completions"
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        ai_response = data['choices'][0]['message']['content']
                        return self.parse_trading_signal(ai_response, market_data)
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI API错误: {response.status} - {error_text}")
                        return self._get_fallback_signal()
                        
        except Exception as e:
            self.logger.error(f"OpenAI请求失败: {e}")
            return self._get_fallback_signal()
            
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的加密货币量化交易AI助手。请基于技术分析和风险管理给出交易建议。

始终以JSON格式返回，包含:
- action: "BUY", "SELL", "HOLD"
- confidence: 0.0-1.0
- position_size: 0.0-1.0
- leverage: 1-20
- stop_loss: 价格或百分比
- take_profit: 价格或百分比
- reasoning: 交易逻辑"""
    
    def _build_trading_prompt(self, market_data: Dict, portfolio: Dict) -> str:
        """构建交易提示词"""
        # 类似GLM4的实现
        symbol = market_data.get('symbol', 'Unknown')
        price = market_data.get('current_price', 0)
        indicators = market_data.get('indicators', {})
        
        prompt = f"""
分析 {symbol} 交易对:

价格: ${price:,.2f}
24h变化: {market_data.get('price_change_24h', 0):.2f}%

技术指标:
- RSI(14): {indicators.get('rsi', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')}
- 移动平均线: MA20={indicators.get('ma20', 'N/A')}
- 布林带: 上{indicators.get('bb_upper', 'N/A')} 中{indicators.get('bb_middle', 'N/A')} 下{indicators.get('bb_lower', 'N/A')}

当前持仓: {portfolio.get('position_side', '无')}
仓位大小: {portfolio.get('position_size', 0):.4f}

请给出交易建议。
"""
        return prompt
        
    def parse_trading_signal(self, ai_response: str, market_data: Dict) -> Dict:
        """解析交易信号"""
        try:
            signal = json.loads(ai_response)
            
            # 验证必需字段
            required_fields = ['action', 'confidence', 'position_size']
            for field in required_fields:
                if field not in signal:
                    signal[field] = self._get_default_value(field)
                    
            # 数据清理
            signal['confidence'] = max(0.0, min(1.0, float(signal['confidence'])))
            signal['position_size'] = max(0.0, min(1.0, float(signal['position_size'])))
            signal['leverage'] = max(1, min(20, int(signal.get('leverage', 1))))
            signal['source'] = 'openai'
            
            return signal
            
        except json.JSONDecodeError as e:
            self.logger.error(f"OpenAI响应JSON解析错误: {e}")
            return self._get_fallback_signal()
            
    def _get_default_value(self, field: str):
        """获取字段默认值"""
        defaults = {
            'action': 'HOLD',
            'confidence': 0.5,
            'position_size': 0.0,
            'leverage': 1
        }
        return defaults.get(field, None)
        
    def _get_fallback_signal(self) -> Dict:
        """获取降级信号"""
        return {
            "action": "HOLD",
            "confidence": 0.3,
            "position_size": 0.0,
            "leverage": 1,
            "stop_loss": None,
            "take_profit": None,
            "reasoning": "OpenAI服务暂时不可用",
            "source": "fallback"
        }
        
    async def analyze_market(self, symbol: str, indicators: Dict) -> Dict:
        """分析市场 - 简化实现"""
        return {"analysis": "OpenAI市场分析功能", "symbol": symbol}
        
    async def get_position_recommendation(self, symbol: str, current_position: Dict) -> Dict:
        """仓位建议 - 简化实现"""
        return {"recommendation": "OpenAI仓位建议", "symbol": symbol}
