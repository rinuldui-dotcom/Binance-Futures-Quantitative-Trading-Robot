import aiohttp
import json
import logging
from typing import Dict, List, Optional
from .base_ai_client import BaseAIClient

class GLM4Client(BaseAIClient):
    """GLM4 AI客户端"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_endpoint = config['api_endpoint']
        self.api_key = config['api_key']
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
    async def get_trading_signal(self, market_data: Dict, portfolio: Dict) -> Dict:
        """获取GLM4交易信号"""
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
                    "temperature": self.temperature
                }
                
                async with session.post(
                    self.api_endpoint,
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
                        self.logger.error(f"GLM4 API错误: {response.status} - {error_text}")
                        return self._get_fallback_signal()
                        
        except Exception as e:
            self.logger.error(f"GLM4请求失败: {e}")
            return self._get_fallback_signal()
            
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的加密货币量化交易AI助手。请基于提供的市场数据和技术指标，给出专业的交易建议。

请始终以JSON格式返回响应，包含以下字段：
- action: "BUY", "SELL", 或 "HOLD"
- confidence: 0.0到1.0的置信度
- position_size: 建议仓位大小(0.0到1.0)
- leverage: 建议杠杆倍数(1-20)
- stop_loss: 止损价格或百分比
- take_profit: 止盈价格或百分比
- reasoning: 简要的交易逻辑说明

请基于技术分析、市场趋势和风险管理给出建议。"""
    
    def _build_trading_prompt(self, market_data: Dict, portfolio: Dict) -> str:
        """构建交易提示词"""
        symbol = market_data.get('symbol', 'Unknown')
        price = market_data.get('current_price', 0)
        indicators = market_data.get('indicators', {})
        
        prompt = f"""
交易对: {symbol}
当前价格: ${price:,.2f}

技术指标:
- RSI: {indicators.get('rsi', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')}
- 移动平均线(MA20): {indicators.get('ma20', 'N/A')}
- 布林带: 上轨={indicators.get('bb_upper', 'N/A')}, 中轨={indicators.get('bb_middle', 'N/A')}, 下轨={indicators.get('bb_lower', 'N/A')}
- 成交量: {indicators.get('volume', 'N/A')}

市场数据:
- 24小时变化: {market_data.get('price_change_24h', 0):.2f}%
- 24小时高点: ${market_data.get('high_24h', 0):,.2f}
- 24小时低点: ${market_data.get('low_24h', 0):,.2f}

当前持仓:
- 方向: {portfolio.get('position_side', '无持仓')}
- 仓位大小: {portfolio.get('position_size', 0):.4f}
- 入场价格: ${portfolio.get('entry_price', 0):,.2f}
- 当前盈亏: {portfolio.get('unrealized_pnl', 0):.4f}

请基于以上信息给出交易建议。
"""
        return prompt
        
    def parse_trading_signal(self, ai_response: str, market_data: Dict) -> Dict:
        """解析交易信号"""
        parsed = self.parse_ai_response(ai_response)
        
        # 默认信号
        default_signal = {
            "action": "HOLD",
            "confidence": 0.5,
            "position_size": 0.0,
            "leverage": 1,
            "stop_loss": None,
            "take_profit": None,
            "reasoning": "AI分析中...",
            "source": "glm4"
        }
        
        if "error" in parsed:
            default_signal["reasoning"] = f"AI解析错误: {parsed['error']}"
            return default_signal
            
        # 合并AI响应
        signal = {**default_signal, **parsed}
        
        # 验证和清理数据
        signal['confidence'] = max(0.0, min(1.0, float(signal.get('confidence', 0.5))))
        signal['position_size'] = max(0.0, min(1.0, float(signal.get('position_size', 0.0))))
        signal['leverage'] = max(1, min(20, int(signal.get('leverage', 1))))
        
        return signal
        
    def _get_fallback_signal(self) -> Dict:
        """获取降级信号"""
        return {
            "action": "HOLD",
            "confidence": 0.3,
            "position_size": 0.0,
            "leverage": 1,
            "stop_loss": None,
            "take_profit": None,
            "reasoning": "AI服务暂时不可用，采用保守策略",
            "source": "fallback"
        }
        
    async def analyze_market(self, symbol: str, indicators: Dict) -> Dict:
        """分析市场状况"""
        prompt = f"""
对交易对 {symbol} 进行全面的市场分析。

当前技术指标:
{json.dumps(indicators, indent=2)}

请分析:
1. 当前市场趋势
2. 关键支撑位和阻力位
3. 交易机会评估
4. 风险提示

以JSON格式返回分析结果。
"""
        # 实现类似get_trading_signal的逻辑
        return await self._get_analysis(prompt)
        
    async def get_position_recommendation(self, symbol: str, current_position: Dict) -> Dict:
        """获取仓位调整建议"""
        prompt = f"""
对交易对 {symbol} 的现有仓位给出调整建议。

当前仓位:
{json.dumps(current_position, indent=2)}

请建议:
1. 是否调整仓位(加仓/减仓/平仓)
2. 新的止损止盈设置
3. 杠杆调整建议

以JSON格式返回建议。
"""
        # 实现类似get_trading_signal的逻辑
        return await self._get_analysis(prompt)
        
    async def _get_analysis(self, prompt: str) -> Dict:
        """获取分析结果"""
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
                            "content": "你是一个专业的金融市场分析师。请提供详细的市场分析和交易建议。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
                
                async with session.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return self.parse_ai_response(data['choices'][0]['message']['content'])
                    else:
                        error_text = await response.text()
                        self.logger.error(f"GLM4分析请求失败: {response.status} - {error_text}")
                        return {"error": f"API错误: {response.status}"}
                        
        except Exception as e:
            self.logger.error(f"GLM4分析请求异常: {e}")
            return {"error": str(e)}
