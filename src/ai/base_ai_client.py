import abc
import logging
from typing import Dict, List, Optional, Any
import json

class BaseAIClient(abc.ABC):
    """AI客户端基类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model_name = config.get('model_name', 'default')
        
    @abc.abstractmethod
    async def get_trading_signal(self, market_data: Dict, portfolio: Dict) -> Dict:
        """获取交易信号"""
        pass
        
    @abc.abstractmethod
    async def analyze_market(self, symbol: str, indicators: Dict) -> Dict:
        """分析市场"""
        pass
        
    @abc.abstractmethod
    async def get_position_recommendation(self, symbol: str, current_position: Dict) -> Dict:
        """获取仓位调整建议"""
        pass
        
    def parse_ai_response(self, response: str) -> Dict:
        """解析AI响应"""
        try:
            # 尝试解析JSON响应
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
                
            # 如果无法解析JSON，返回原始响应
            self.logger.warning(f"无法解析AI响应为JSON: {response}")
            return {"raw_response": response, "confidence": 0.5}
            
        except json.JSONDecodeError as e:
            self.logger.error(f"AI响应JSON解析错误: {e}")
            return {"error": str(e), "raw_response": response, "confidence": 0.3}
