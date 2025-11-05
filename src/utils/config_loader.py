import yaml
import os
from typing import Dict, Any
import logging

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
        """加载和验证配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                
            # 环境变量替换
            config = ConfigLoader._replace_env_vars(config)
            
            # 验证必要配置
            ConfigLoader._validate_config(config)
            
            logging.info("配置加载成功")
            return config
            
        except Exception as e:
            logging.error(f"配置加载失败: {e}")
            raise
            
    @staticmethod
    def _replace_env_vars(config: Dict) -> Dict:
        """递归替换环境变量"""
        if isinstance(config, dict):
            return {k: ConfigLoader._replace_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [ConfigLoader._replace_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]
            default = None
            if ":-" in env_var:
                env_var, default = env_var.split(":-")
            return os.getenv(env_var, default)
        else:
            return config
            
    @staticmethod
    def _validate_config(config: Dict):
        """验证配置完整性"""
        required_keys = [
            'binance.api_key',
            'binance.secret_key',
            'trading.symbols',
            'trading.total_capital'
        ]
        
        for key_path in required_keys:
            keys = key_path.split('.')
            current = config
            for key in keys:
                if key not in current:
                    raise ValueError(f"缺少必要配置: {key_path}")
                current = current[key]
