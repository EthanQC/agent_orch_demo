from openai import OpenAI
from typing import Optional
import config


class QwenClient:
    """通义千问客户端单例"""
    
    _instance: Optional[OpenAI] = None
    
    @classmethod
    def get_client(cls) -> OpenAI:
        """获取或创建客户端实例"""
        if cls._instance is not None:
            return cls._instance
        
        if not config.DASHSCOPE_API_KEY:
            raise RuntimeError(
                "请先在环境变量中设置 DASHSCOPE_API_KEY (或 QWEN_API_KEY)"
            )
        
        cls._instance = OpenAI(
            api_key=config.DASHSCOPE_API_KEY,
            base_url=config.QWEN_BASE_URL,
        )
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置客户端实例(主要用于测试)"""
        cls._instance = None