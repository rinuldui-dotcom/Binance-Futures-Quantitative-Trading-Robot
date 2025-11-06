import aiohttp
import json
import logging
from typing import Dict
from .base_ai_client import BaseAIClient

class AnthropicClient(BaseAIClient):
    """Anthropic Claude客户端"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.api_key = config['api_key']
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 30)
        
    async def get_trading_signal(self, market_data: Dict, portfolio: Dict) -> Dict:
        """获取Claude交易信号"""
        prompt = self._build_trading_prompt(market_data, portfolio)
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
                
                payload = {
                    "model": self.model_name,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "system": self._get_system_prompt(),
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
                
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        ai_response = data['content'][0]['text']
                        return self.parse_trading_signal(ai_response, market_data)
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Anthropic API错误: {response.status} - {error_text}")
                        return self._get_fallback_signal()
                        
        except Exception as e:
            self.logger.error(f"Anthropic请求失败: {e}")
            return self._get_fallback_signal()
            
    # 其他方法类似OpenAIClient的实现
    def _get_system_prompt(self) -> str:
        return "你是一个专业的加密货币交易AI。以JSON格式返回交易建议。"
        
    def _build_trading_prompt(self, market_data: Dict, portfolio: Dict) -> str:
        # 实现提示词构建
        return "交易分析请求..."
        
    def parse_trading_signal(self, ai_response: str, market_data: Dict) -> Dict:
        # 实现信号解析
        return self._get_fallback_signal()
        
    def _get_fallback_signal(self) -> Dict:
        return {
            "action": "HOLD", 
            "confidence": 0.3,
            "position_size": 0.0,
            "leverage": 1,
            "reasoning": "Claude服务暂时不可用",
            "source": "fallback"
        }
