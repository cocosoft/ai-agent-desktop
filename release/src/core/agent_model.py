"""
代理数据模型
定义代理配置、实例、模板等核心数据结构
"""

from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
from datetime import datetime, timedelta

from .capability_model import Capability, CapabilityType, CapabilityRegistry
from .model_config import ModelConfig


class AgentStatus(Enum):
    """代理状态枚举"""
    STOPPED = "stopped"        # 已停止
    STARTING = "starting"      # 启动中
    RUNNING = "running"        # 运行中
    STOPPING = "stopping"      # 停止中
    ERROR = "error"            # 错误状态
    OFFLINE = "offline"        # 离线状态


class AgentType(Enum):
    """代理类型枚举"""
    TEXT_GENERATION = "text_generation"        # 文本生成代理
    CODE_GENERATION = "code_generation"        # 代码生成代理
    TEXT_SUMMARIZATION = "text_summarization"  # 文本摘要代理
    TRANSLATION = "translation"                # 翻译代理
    QUESTION_ANSWERING = "question_answering"  # 问答代理
    MULTI_MODAL = "multi_modal"                # 多模态代理
    CUSTOM = "custom"                          # 自定义代理


class AgentPriority(Enum):
    """代理优先级枚举"""
    LOW = "low"        # 低优先级
    NORMAL = "normal"  # 正常优先级
    HIGH = "high"      # 高优先级
    CRITICAL = "critical"  # 关键优先级


@dataclass
class AgentCapabilityMapping:
    """代理能力映射配置"""
    capability_id: str
    model_id: str
    priority: int = 1  # 1-10，数字越大优先级越高
    enabled: bool = True
    fallback_models: List[str] = field(default_factory=list)  # 备用模型列表
    max_retries: int = 3
    timeout: int = 30  # 秒


@dataclass
class AgentConfig:
    """代理配置"""
    agent_id: str
    name: str
    description: str
    agent_type: AgentType
    capabilities: List[AgentCapabilityMapping] = field(default_factory=list)
    priority: AgentPriority = AgentPriority.NORMAL
    max_concurrent_tasks: int = 5
    auto_start: bool = False
    health_check_interval: int = 30  # 秒
    max_restart_attempts: int = 3
    restart_delay: int = 5  # 秒
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "capabilities": [
                {
                    "capability_id": mapping.capability_id,
                    "model_id": mapping.model_id,
                    "priority": mapping.priority,
                    "enabled": mapping.enabled,
                    "fallback_models": mapping.fallback_models,
                    "max_retries": mapping.max_retries,
                    "timeout": mapping.timeout
                }
                for mapping in self.capabilities
            ],
            "priority": self.priority.value,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "auto_start": self.auto_start,
            "health_check_interval": self.health_check_interval,
            "max_restart_attempts": self.max_restart_attempts,
            "restart_delay": self.restart_delay,
            "resource_limits": self.resource_limits,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """从字典创建实例"""
        capabilities = [
            AgentCapabilityMapping(
                capability_id=mapping_data["capability_id"],
                model_id=mapping_data["model_id"],
                priority=mapping_data.get("priority", 1),
                enabled=mapping_data.get("enabled", True),
                fallback_models=mapping_data.get("fallback_models", []),
                max_retries=mapping_data.get("max_retries", 3),
                timeout=mapping_data.get("timeout", 30)
            )
            for mapping_data in data.get("capabilities", [])
        ]
        
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            description=data["description"],
            agent_type=AgentType(data["agent_type"]),
            capabilities=capabilities,
            priority=AgentPriority(data.get("priority", "normal")),
            max_concurrent_tasks=data.get("max_concurrent_tasks", 5),
            auto_start=data.get("auto_start", False),
            health_check_interval=data.get("health_check_interval", 30),
            max_restart_attempts=data.get("max_restart_attempts", 3),
            restart_delay=data.get("restart_delay", 5),
            resource_limits=data.get("resource_limits", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class AgentInstance:
    """代理实例"""
    instance_id: str
    agent_config: AgentConfig
    status: AgentStatus = AgentStatus.STOPPED
    current_tasks: int = 0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    last_error: Optional[str] = None
    restart_count: int = 0
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "instance_id": self.instance_id,
            "agent_config": self.agent_config.to_dict(),
            "status": self.status.value,
            "current_tasks": self.current_tasks,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_response_time": self.avg_response_time,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "last_error": self.last_error,
            "restart_count": self.restart_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stop_time": self.stop_time.isoformat() if self.stop_time else None,
            "resource_usage": self.resource_usage,
            "performance_metrics": self.performance_metrics
        }


@dataclass
class AgentTemplate:
    """代理模板"""
    template_id: str
    name: str
    description: str
    agent_type: AgentType
    base_capabilities: List[str] = field(default_factory=list)  # 基础能力ID列表
    recommended_models: Dict[str, List[str]] = field(default_factory=dict)  # 能力到推荐模型的映射
    default_settings: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "agent_type": self.agent_type.value,
            "base_capabilities": self.base_capabilities,
            "recommended_models": self.recommended_models,
            "default_settings": self.default_settings,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTemplate':
        """从字典创建实例"""
        return cls(
            template_id=data["template_id"],
            name=data["name"],
            description=data["description"],
            agent_type=AgentType(data["agent_type"]),
            base_capabilities=data.get("base_capabilities", []),
            recommended_models=data.get("recommended_models", {}),
            default_settings=data.get("default_settings", {}),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


class AgentRegistry:
    """代理注册表"""
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self.instances: Dict[str, AgentInstance] = {}
        self.templates: Dict[str, AgentTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """加载默认模板"""
        # 文本生成代理模板
        text_gen_template = AgentTemplate(
            template_id="text_generation_basic",
            name="基础文本生成代理",
            description="用于文本生成任务的基础代理模板",
            agent_type=AgentType.TEXT_GENERATION,
            base_capabilities=["text_generation"],
            recommended_models={
                "text_generation": ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet"]
            },
            default_settings={
                "max_concurrent_tasks": 3,
                "auto_start": True
            },
            category="text",
            tags=["text", "generation", "basic"]
        )
        self.templates[text_gen_template.template_id] = text_gen_template
        
        # 代码生成代理模板
        code_gen_template = AgentTemplate(
            template_id="code_generation_basic",
            name="基础代码生成代理",
            description="用于代码生成任务的基础代理模板",
            agent_type=AgentType.CODE_GENERATION,
            base_capabilities=["code_generation"],
            recommended_models={
                "code_generation": ["gpt-4", "claude-3-sonnet", "codellama"]
            },
            default_settings={
                "max_concurrent_tasks": 2,
                "auto_start": True
            },
            category="code",
            tags=["code", "generation", "basic"]
        )
        self.templates[code_gen_template.template_id] = code_gen_template
        
        # 多能力代理模板
        multi_cap_template = AgentTemplate(
            template_id="multi_capability_advanced",
            name="多能力高级代理",
            description="支持多种能力的综合代理模板",
            agent_type=AgentType.MULTI_MODAL,
            base_capabilities=["text_generation", "code_generation", "text_summarization"],
            recommended_models={
                "text_generation": ["gpt-4", "claude-3-sonnet"],
                "code_generation": ["gpt-4", "claude-3-sonnet"],
                "text_summarization": ["gpt-3.5-turbo", "claude-3-haiku"]
            },
            default_settings={
                "max_concurrent_tasks": 5,
                "auto_start": True,
                "priority": "high"
            },
            category="advanced",
            tags=["multi", "advanced", "comprehensive"]
        )
        self.templates[multi_cap_template.template_id] = multi_cap_template
    
    def register_agent(self, agent_config: AgentConfig) -> bool:
        """注册代理配置"""
        if agent_config.agent_id in self.agents:
            return False
        
        self.agents[agent_config.agent_id] = agent_config
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销代理配置"""
        if agent_id not in self.agents:
            return False
        
        # 检查是否有运行中的实例
        running_instances = [
            instance for instance in self.instances.values()
            if instance.agent_config.agent_id == agent_id and instance.status == AgentStatus.RUNNING
        ]
        
        if running_instances:
            return False  # 有运行中的实例，不能注销
        
        del self.agents[agent_id]
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """获取代理配置"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentConfig]:
        """列出所有代理配置"""
        return list(self.agents.values())
    
    def search_agents(self, query: str, agent_type: Optional[AgentType] = None) -> List[AgentConfig]:
        """搜索代理配置"""
        results = []
        for agent in self.agents.values():
            # 按名称和描述搜索
            if (query.lower() in agent.name.lower() or 
                query.lower() in agent.description.lower()):
                if agent_type is None or agent.agent_type == agent_type:
                    results.append(agent)
        return results
    
    def create_instance(self, agent_id: str) -> Optional[AgentInstance]:
        """创建代理实例"""
        agent_config = self.get_agent(agent_id)
        if not agent_config:
            return None
        
        instance_id = str(uuid.uuid4())
        instance = AgentInstance(
            instance_id=instance_id,
            agent_config=agent_config
        )
        
        self.instances[instance_id] = instance
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[AgentInstance]:
        """获取代理实例"""
        return self.instances.get(instance_id)
    
    def list_instances(self) -> List[AgentInstance]:
        """列出所有代理实例"""
        return list(self.instances.values())
    
    def get_agent_instances(self, agent_id: str) -> List[AgentInstance]:
        """获取指定代理的所有实例"""
        return [
            instance for instance in self.instances.values()
            if instance.agent_config.agent_id == agent_id
        ]
    
    def remove_instance(self, instance_id: str) -> bool:
        """移除代理实例"""
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        if instance.status == AgentStatus.RUNNING:
            return False  # 运行中的实例不能移除
        
        del self.instances[instance_id]
        return True
    
    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """获取代理模板"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[AgentTemplate]:
        """列出所有代理模板"""
        return list(self.templates.values())
    
    def search_templates(self, query: str, category: Optional[str] = None) -> List[AgentTemplate]:
        """搜索代理模板"""
        results = []
        for template in self.templates.values():
            # 按名称和描述搜索
            if (query.lower() in template.name.lower() or 
                query.lower() in template.description.lower()):
                if category is None or template.category == category:
                    results.append(template)
        return results
    
    def create_agent_from_template(self, template_id: str, name: str, description: str) -> Optional[AgentConfig]:
        """从模板创建代理配置"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        agent_id = str(uuid.uuid4())
        agent_config = AgentConfig(
            agent_id=agent_id,
            name=name,
            description=description,
            agent_type=template.agent_type,
            capabilities=[
                AgentCapabilityMapping(
                    capability_id=capability_id,
                    model_id=template.recommended_models.get(capability_id, [""])[0] if template.recommended_models.get(capability_id) else "",
                    priority=1,
                    enabled=True
                )
                for capability_id in template.base_capabilities
            ],
            **template.default_settings
        )
        
        self.register_agent(agent_config)
        return agent_config


# 预定义的代理配置示例
def create_sample_agents() -> AgentRegistry:
    """创建示例代理配置"""
    registry = AgentRegistry()
    
    # 文本生成代理
    text_agent = AgentConfig(
        agent_id="text_agent_1",
        name="文本生成助手",
        description="用于文本生成和创作的专业代理",
        agent_type=AgentType.TEXT_GENERATION,
        capabilities=[
            AgentCapabilityMapping(
                capability_id="text_generation",
                model_id="gpt-3.5-turbo",
                priority=1,
                enabled=True
            )
        ],
        auto_start=True,
        max_concurrent_tasks=3
    )
    registry.register_agent(text_agent)
    
    # 代码生成代理
    code_agent = AgentConfig(
        agent_id="code_agent_1",
        name="代码生成助手",
        description="用于代码生成和编程的专业代理",
        agent_type=AgentType.CODE_GENERATION,
        capabilities=[
            AgentCapabilityMapping(
                capability_id="code_generation",
                model_id="gpt-4",
                priority=1,
                enabled=True
            )
        ],
        auto_start=True,
        max_concurrent_tasks=2
    )
    registry.register_agent(code_agent)
    
    # 多能力代理
    multi_agent = AgentConfig(
        agent_id="multi_agent_1",
        name="多能力综合助手",
        description="支持多种能力的综合代理",
        agent_type=AgentType.MULTI_MODAL,
        capabilities=[
            AgentCapabilityMapping(
                capability_id="text_generation",
                model_id="gpt-3.5-turbo",
                priority=1,
                enabled=True
            ),
            AgentCapabilityMapping(
                capability_id="code_generation",
                model_id="gpt-4",
                priority=2,
                enabled=True
            ),
            AgentCapabilityMapping(
                capability_id="text_summarization",
                model_id="gpt-3.5-turbo",
                priority=3,
                enabled=True
            )
        ],
        auto_start=True,
        max_concurrent_tasks=5
    )
    registry.register_agent(multi_agent)
    
    return registry
