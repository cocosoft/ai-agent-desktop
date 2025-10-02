"""
模型配置数据模型
定义模型配置相关的数据结构和验证逻辑
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# 配置基类
class BaseConfig:
    """配置基类"""
    pass


class ModelProvider(Enum):
    """模型提供商枚举"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    CUSTOM = "custom"


class ModelCapability(Enum):
    """模型能力枚举"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    IMAGE_GENERATION = "image_generation"
    AUDIO_PROCESSING = "audio_processing"
    MULTIMODAL = "multimodal"


@dataclass
class ModelParameterConfig:
    """模型参数配置"""
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int = 4096
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    custom_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'temperature': self.temperature,
            'top_p': self.top_p,
            'max_tokens': self.max_tokens,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'stop_sequences': self.stop_sequences,
            'custom_parameters': self.custom_parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelParameterConfig':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class ModelConnectionConfig:
    """模型连接配置"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True
    proxy_url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'base_url': self.base_url,
            'api_key': self.api_key,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'verify_ssl': self.verify_ssl,
            'proxy_url': self.proxy_url,
            'headers': self.headers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConnectionConfig':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class ModelPerformanceConfig:
    """模型性能配置"""
    enable_caching: bool = True
    cache_ttl: int = 3600  # 缓存过期时间（秒）
    enable_streaming: bool = True
    batch_size: int = 1
    concurrent_requests: int = 1
    rate_limit: Optional[int] = None  # 每分钟请求限制
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'enable_caching': self.enable_caching,
            'cache_ttl': self.cache_ttl,
            'enable_streaming': self.enable_streaming,
            'batch_size': self.batch_size,
            'concurrent_requests': self.concurrent_requests,
            'rate_limit': self.rate_limit
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelPerformanceConfig':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class ModelConfig(BaseConfig):
    """模型配置主类"""
    
    # 基本信息
    name: str
    provider: ModelProvider
    model_id: str
    version: str = "1.0.0"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    capabilities: List[ModelCapability] = field(default_factory=list)
    
    # 配置部分
    parameters: ModelParameterConfig = field(default_factory=ModelParameterConfig)
    connection: ModelConnectionConfig = field(default_factory=lambda: ModelConnectionConfig(base_url=""))
    performance: ModelPerformanceConfig = field(default_factory=ModelPerformanceConfig)
    
    # 元数据
    is_enabled: bool = True
    priority: int = 1  # 优先级，数值越小优先级越高
    cost_per_token: Optional[float] = None
    max_context_length: int = 4096
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.connection.base_url:
            # 设置默认基础URL
            self.connection.base_url = self._get_default_base_url()
    
    def _get_default_base_url(self) -> str:
        """获取默认基础URL"""
        defaults = {
            ModelProvider.OLLAMA: "http://localhost:11434",
            ModelProvider.OPENAI: "https://api.openai.com/v1",
            ModelProvider.ANTHROPIC: "https://api.anthropic.com",
            ModelProvider.AZURE_OPENAI: "https://{resource}.openai.azure.com",
            ModelProvider.GOOGLE: "https://generativelanguage.googleapis.com"
        }
        return defaults.get(self.provider, "")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'provider': self.provider.value,
            'model_id': self.model_id,
            'version': self.version,
            'description': self.description,
            'tags': self.tags,
            'capabilities': [cap.value for cap in self.capabilities],
            'parameters': self.parameters.to_dict(),
            'connection': self.connection.to_dict(),
            'performance': self.performance.to_dict(),
            'is_enabled': self.is_enabled,
            'priority': self.priority,
            'cost_per_token': self.cost_per_token,
            'max_context_length': self.max_context_length
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """从字典创建实例"""
        data = data.copy()
        
        # 转换枚举类型
        data['provider'] = ModelProvider(data['provider'])
        data['capabilities'] = [ModelCapability(cap) for cap in data.get('capabilities', [])]
        
        # 创建嵌套配置对象
        if 'parameters' in data:
            data['parameters'] = ModelParameterConfig.from_dict(data['parameters'])
        else:
            data['parameters'] = ModelParameterConfig()
        
        if 'connection' in data:
            data['connection'] = ModelConnectionConfig.from_dict(data['connection'])
        else:
            data['connection'] = ModelConnectionConfig(base_url="")
        
        if 'performance' in data:
            data['performance'] = ModelPerformanceConfig.from_dict(data['performance'])
        else:
            data['performance'] = ModelPerformanceConfig()
        
        return cls(**data)
    
    def validate(self) -> Dict[str, Any]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 验证基本信息
        if not self.name.strip():
            errors.append("模型名称不能为空")
        
        if not self.model_id.strip():
            errors.append("模型ID不能为空")
        
        # 验证连接配置
        if not self.connection.base_url.strip():
            errors.append("基础URL不能为空")
        elif not self.connection.base_url.startswith(('http://', 'https://')):
            warnings.append("基础URL应该以 http:// 或 https:// 开头")
        
        if self.connection.timeout <= 0:
            errors.append("超时时间必须大于0")
        
        if self.connection.max_retries < 0:
            errors.append("最大重试次数不能为负数")
        
        # 验证参数配置
        if self.parameters.temperature < 0 or self.parameters.temperature > 2:
            warnings.append("温度参数应该在0-2范围内")
        
        if self.parameters.max_tokens <= 0:
            errors.append("最大令牌数必须大于0")
        
        if self.parameters.top_p < 0 or self.parameters.top_p > 1:
            errors.append("top_p参数应该在0-1范围内")
        
        # 验证性能配置
        if self.performance.cache_ttl < 0:
            errors.append("缓存TTL不能为负数")
        
        if self.performance.batch_size <= 0:
            errors.append("批处理大小必须大于0")
        
        if self.performance.concurrent_requests <= 0:
            errors.append("并发请求数必须大于0")
        
        # 验证元数据
        if self.priority <= 0:
            errors.append("优先级必须大于0")
        
        if self.max_context_length <= 0:
            errors.append("最大上下文长度必须大于0")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_cost_estimate(self, tokens: int) -> Optional[float]:
        """估算成本"""
        if self.cost_per_token is None:
            return None
        return self.cost_per_token * tokens
    
    def get_capability_display_names(self) -> List[str]:
        """获取能力显示名称"""
        display_names = {
            ModelCapability.TEXT_GENERATION: "文本生成",
            ModelCapability.CODE_GENERATION: "代码生成",
            ModelCapability.TRANSLATION: "翻译",
            ModelCapability.SUMMARIZATION: "摘要",
            ModelCapability.QUESTION_ANSWERING: "问答",
            ModelCapability.SENTIMENT_ANALYSIS: "情感分析",
            ModelCapability.IMAGE_GENERATION: "图像生成",
            ModelCapability.AUDIO_PROCESSING: "音频处理",
            ModelCapability.MULTIMODAL: "多模态"
        }
        return [display_names.get(cap, cap.value) for cap in self.capabilities]
    
    def get_provider_display_name(self) -> str:
        """获取提供商显示名称"""
        display_names = {
            ModelProvider.OLLAMA: "Ollama",
            ModelProvider.OPENAI: "OpenAI",
            ModelProvider.ANTHROPIC: "Anthropic",
            ModelProvider.AZURE_OPENAI: "Azure OpenAI",
            ModelProvider.GOOGLE: "Google",
            ModelProvider.CUSTOM: "自定义"
        }
        return display_names.get(self.provider, self.provider.value)


class ModelConfigManager:
    """模型配置管理器"""
    
    def __init__(self, config_dir: Path):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录路径
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._configs: Dict[str, ModelConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """加载所有配置"""
        config_files = self.config_dir.glob("*.json")
        
        for config_file in config_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                config = ModelConfig.from_dict(config_data)
                self._configs[config.name] = config
                
            except Exception as e:
                print(f"加载模型配置失败 {config_file}: {e}")
    
    def get_config(self, name: str) -> Optional[ModelConfig]:
        """获取配置"""
        return self._configs.get(name)
    
    def get_all_configs(self) -> List[ModelConfig]:
        """获取所有配置"""
        return list(self._configs.values())
    
    def get_enabled_configs(self) -> List[ModelConfig]:
        """获取启用的配置"""
        return [config for config in self._configs.values() if config.is_enabled]
    
    def save_config(self, config: ModelConfig) -> bool:
        """
        保存配置
        
        Args:
            config: 模型配置
            
        Returns:
            保存是否成功
        """
        try:
            # 验证配置
            validation = config.validate()
            if not validation['valid']:
                print(f"配置验证失败: {validation['errors']}")
                return False
            
            # 保存到文件
            config_file = self.config_dir / f"{config.name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            
            # 更新内存中的配置
            self._configs[config.name] = config
            return True
            
        except Exception as e:
            print(f"保存模型配置失败: {e}")
            return False
    
    def delete_config(self, name: str) -> bool:
        """
        删除配置
        
        Args:
            name: 配置名称
            
        Returns:
            删除是否成功
        """
        try:
            config_file = self.config_dir / f"{name}.json"
            if config_file.exists():
                config_file.unlink()
            
            if name in self._configs:
                del self._configs[name]
            
            return True
            
        except Exception as e:
            print(f"删除模型配置失败: {e}")
            return False
    
    def create_default_configs(self):
        """创建默认配置"""
        default_configs = [
            ModelConfig(
                name="ollama-llama3",
                provider=ModelProvider.OLLAMA,
                model_id="llama3",
                description="Ollama本地运行的Llama 3模型",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
                connection=ModelConnectionConfig(base_url="http://localhost:11434")
            ),
            ModelConfig(
                name="openai-gpt-4",
                provider=ModelProvider.OPENAI,
                model_id="gpt-4",
                description="OpenAI GPT-4模型",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
                connection=ModelConnectionConfig(base_url="https://api.openai.com/v1")
            )
        ]
        
        for config in default_configs:
            if config.name not in self._configs:
                self.save_config(config)


# 便捷函数
def create_model_config(
    name: str,
    provider: ModelProvider,
    model_id: str,
    base_url: str,
    **kwargs
) -> ModelConfig:
    """
    创建模型配置的便捷函数
    
    Args:
        name: 模型名称
        provider: 模型提供商
        model_id: 模型ID
        base_url: 基础URL
        **kwargs: 其他参数
        
    Returns:
        模型配置实例
    """
    connection_config = ModelConnectionConfig(base_url=base_url)
    return ModelConfig(
        name=name,
        provider=provider,
        model_id=model_id,
        connection=connection_config,
        **kwargs
    )


# 测试函数
def test_model_config():
    """测试模型配置功能"""
    try:
        # 创建测试配置
        config = create_model_config(
            name="test-model",
            provider=ModelProvider.OLLAMA,
            model_id="test",
            base_url="http://localhost:8080",
            description="测试模型配置"
        )
        
        # 测试验证
        validation = config.validate()
        print(f"配置验证结果: {validation}")
        
        # 测试序列化
        config_dict = config.to_dict()
        print(f"配置字典: {config_dict}")
        
        # 测试反序列化
        config_restored = ModelConfig.from_dict(config_dict)
        print(f"恢复的配置名称: {config_restored.name}")
        
        print("✓ 模型配置测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 模型配置测试失败: {e}")
        return False


if __name__ == "__main__":
    test_model_config()
