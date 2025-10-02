"""
模型适配器基础框架
定义所有模型适配器的统一接口和基础功能
"""

import abc
import json
import time
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# 在测试模式下使用模拟函数
if __name__ == "__main__":
    def log_info(message: str):
        print(f"INFO: {message}")
    
    def log_warning(message: str):
        print(f"WARNING: {message}")
    
    def log_error(message: str, error: Exception = None):
        print(f"ERROR: {message}")
        if error:
            print(f"Error details: {error}")
    
    def log_performance(operation: str, duration_ms: float, details: str = ""):
        print(f"PERF: {operation} - {duration_ms:.2f}ms - {details}")
    
    def safe_execute(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(f"安全执行失败: {e}")
            return None
else:
    from ..utils.logger import log_info, log_warning, log_error, log_performance
    from ..utils.error_handler import safe_execute


class ModelType(Enum):
    """模型类型枚举"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class ModelStatus(Enum):
    """模型状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class ModelConfig:
    """模型配置数据类"""
    name: str
    model_type: ModelType
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    system_prompt: Optional[str] = None
    custom_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['model_type'] = self.model_type.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建实例"""
        data = data.copy()
        data['model_type'] = ModelType(data['model_type'])
        return cls(**data)


@dataclass
class ModelResponse:
    """模型响应数据类"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ModelMetrics:
    """模型性能指标数据类"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    average_response_time: float = 0.0
    last_response_time: float = 0.0
    last_error: Optional[str] = None
    
    def update_success(self, response_time: float, tokens: int):
        """更新成功请求指标"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_tokens += tokens
        self.last_response_time = response_time
        self.average_response_time = (
            (self.average_response_time * (self.total_requests - 1) + response_time) 
            / self.total_requests
        )
    
    def update_failure(self, error: str):
        """更新失败请求指标"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_error = error
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.get_success_rate(),
            'total_tokens': self.total_tokens,
            'average_response_time': self.average_response_time,
            'last_response_time': self.last_response_time,
            'last_error': self.last_error
        }


class BaseAdapter(abc.ABC):
    """模型适配器基类"""
    
    def __init__(self, config: ModelConfig):
        """
        初始化适配器
        
        Args:
            config: 模型配置
        """
        self.config = config
        self.status = ModelStatus.DISCONNECTED
        self.metrics = ModelMetrics()
        self.logger = logging.getLogger(f"adapter.{config.name}")
        self._connection_timeout = config.timeout
        self._last_health_check = 0
        self._health_check_interval = 60  # 健康检查间隔（秒）
        
        # 回调函数
        self._status_callbacks: List[Callable] = []
        self._metrics_callbacks: List[Callable] = []
    
    @abc.abstractmethod
    async def connect(self) -> bool:
        """
        连接到模型服务
        
        Returns:
            连接是否成功
        """
        pass
    
    @abc.abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abc.abstractmethod
    async def generate_text(
        self, 
        prompt: str, 
        **kwargs
    ) -> ModelResponse:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            模型响应
        """
        pass
    
    @abc.abstractmethod
    async def generate_stream(
        self, 
        prompt: str, 
        callback: Callable[[str], None],
        **kwargs
    ):
        """
        流式生成文本
        
        Args:
            prompt: 输入提示
            callback: 回调函数，接收生成的文本片段
            **kwargs: 额外参数
        """
        pass
    
    @abc.abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            模型服务是否健康
        """
        pass
    
    def update_status(self, new_status: ModelStatus, reason: str = ""):
        """
        更新模型状态
        
        Args:
            new_status: 新状态
            reason: 状态变更原因
        """
        old_status = self.status
        self.status = new_status
        
        if old_status != new_status:
            log_info(f"模型状态变更: {self.config.name} {old_status.value} -> {new_status.value} {reason}")
            
            # 调用状态回调函数
            for callback in self._status_callbacks:
                try:
                    callback(self, old_status, new_status, reason)
                except Exception as e:
                    log_error(f"状态回调函数执行失败: {e}")
    
    def register_status_callback(self, callback: Callable):
        """
        注册状态变更回调函数
        
        Args:
            callback: 回调函数，参数为(adapter, old_status, new_status, reason)
        """
        self._status_callbacks.append(callback)
    
    def register_metrics_callback(self, callback: Callable):
        """
        注册指标更新回调函数
        
        Args:
            callback: 回调函数，参数为(adapter, metrics)
        """
        self._metrics_callbacks.append(callback)
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取适配器信息
        
        Returns:
            适配器信息字典
        """
        return {
            'name': self.config.name,
            'type': self.config.model_type.value,
            'status': self.status.value,
            'config': self.config.to_dict(),
            'metrics': self.metrics.to_dict(),
            'connected': self.status == ModelStatus.CONNECTED
        }
    
    async def safe_generate_text(self, prompt: str, **kwargs) -> ModelResponse:
        """
        安全的文本生成（带错误处理）
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            模型响应，包含错误信息
        """
        start_time = time.time()
        
        try:
            response = await self.generate_text(prompt, **kwargs)
            response_time = time.time() - start_time
            
            # 更新指标
            self.metrics.update_success(response_time, response.usage.get('total_tokens', 0))
            log_performance(f"MODEL_GENERATE_{self.config.name}", response_time * 1000, 
                          f"tokens: {response.usage.get('total_tokens', 0)}")
            
            # 调用指标回调
            for callback in self._metrics_callbacks:
                try:
                    callback(self, self.metrics)
                except Exception as e:
                    log_error(f"指标回调函数执行失败: {e}")
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"文本生成失败: {str(e)}"
            
            # 更新指标
            self.metrics.update_failure(error_msg)
            log_error(f"模型 {self.config.name} 生成失败", e)
            
            # 更新状态
            self.update_status(ModelStatus.ERROR, error_msg)
            
            return ModelResponse(
                content="",
                model=self.config.name,
                usage={},
                finish_reason="error",
                response_time=response_time,
                error=error_msg
            )
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接
        
        Returns:
            测试结果字典
        """
        start_time = time.time()
        
        try:
            # 发送简单的测试提示
            test_prompt = "请回复'连接测试成功'"
            response = await self.safe_generate_text(test_prompt, max_tokens=10)
            
            test_time = time.time() - start_time
            
            result = {
                'success': response.error is None,
                'response_time': test_time,
                'error': response.error,
                'response_content': response.content,
                'model_used': response.model
            }
            
            if response.error is None:
                log_info(f"模型连接测试成功: {self.config.name} ({test_time:.2f}s)")
            else:
                log_error(f"模型连接测试失败: {self.config.name} - {response.error}")
            
            return result
            
        except Exception as e:
            test_time = time.time() - start_time
            error_msg = f"连接测试异常: {str(e)}"
            log_error(f"模型连接测试异常: {self.config.name}", e)
            
            return {
                'success': False,
                'response_time': test_time,
                'error': error_msg,
                'response_content': "",
                'model_used': self.config.name
            }


class AdapterFactory:
    """适配器工厂类"""
    
    _adapters: Dict[str, type] = {}
    
    @classmethod
    def register_adapter(cls, model_type: ModelType, adapter_class: type):
        """
        注册适配器类
        
        Args:
            model_type: 模型类型
            adapter_class: 适配器类
        """
        cls._adapters[model_type.value] = adapter_class
    
    @classmethod
    def create_adapter(cls, config: ModelConfig) -> BaseAdapter:
        """
        创建适配器实例
        
        Args:
            config: 模型配置
            
        Returns:
            适配器实例
            
        Raises:
            ValueError: 不支持的模型类型
        """
        if config.model_type.value not in cls._adapters:
            raise ValueError(f"不支持的模型类型: {config.model_type.value}")
        
        adapter_class = cls._adapters[config.model_type.value]
        return adapter_class(config)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """
        获取支持的模型类型
        
        Returns:
            支持的模型类型列表
        """
        return list(cls._adapters.keys())


# 便捷函数
def create_model_config(
    name: str,
    model_type: Union[ModelType, str],
    base_url: str,
    **kwargs
) -> ModelConfig:
    """
    创建模型配置的便捷函数
    
    Args:
        name: 模型名称
        model_type: 模型类型（枚举或字符串）
        base_url: 基础URL
        **kwargs: 其他配置参数
        
    Returns:
        模型配置实例
    """
    if isinstance(model_type, str):
        model_type = ModelType(model_type)
    
    return ModelConfig(name=name, model_type=model_type, base_url=base_url, **kwargs)


def validate_model_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证模型配置
    
    Args:
        config_dict: 配置字典
        
    Returns:
        验证结果字典
    """
    errors = []
    warnings = []
    
    # 检查必需字段
    required_fields = ['name', 'model_type', 'base_url']
    for field in required_fields:
        if field not in config_dict:
            errors.append(f"缺少必需字段: {field}")
    
    # 检查模型类型
    if 'model_type' in config_dict:
        try:
            ModelType(config_dict['model_type'])
        except ValueError:
            errors.append(f"不支持的模型类型: {config_dict['model_type']}")
    
    # 检查URL格式
    if 'base_url' in config_dict:
        url = config_dict['base_url']
        if not url.startswith(('http://', 'https://')):
            warnings.append("base_url 应该以 http:// 或 https:// 开头")
    
    # 检查数值范围
    if 'timeout' in config_dict and config_dict['timeout'] <= 0:
        errors.append("timeout 必须大于0")
    
    if 'temperature' in config_dict:
        temp = config_dict['temperature']
        if temp < 0 or temp > 2:
            warnings.append("temperature 应该在 0-2 范围内")
    
    if 'max_tokens' in config_dict and config_dict['max_tokens'] <= 0:
        errors.append("max_tokens 必须大于0")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


# 测试函数
async def test_base_adapter():
    """测试基础适配器功能"""
    try:
        # 创建测试配置
        config = create_model_config(
            name="test-model",
            model_type=ModelType.CUSTOM,
            base_url="http://localhost:8080"
        )
        
        # 测试配置验证
        validation = validate_model_config(config.to_dict())
        print(f"配置验证结果: {validation}")
        
        # 测试适配器工厂
        print(f"支持的模型类型: {AdapterFactory.get_supported_types()}")
        
        print("✓ 基础适配器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基础适配器测试失败: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_base_adapter())
