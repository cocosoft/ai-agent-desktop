"""
代理数据模型单元测试
测试代理配置、实例、模板等核心数据结构
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.agent_model import (
    AgentStatus, AgentType, AgentPriority, AgentCapabilityMapping,
    AgentConfig, AgentInstance, AgentTemplate, AgentRegistry,
    create_sample_agents
)


class TestAgentModel:
    """代理数据模型测试类"""
    
    def test_agent_status_enum(self):
        """测试代理状态枚举"""
        assert AgentStatus.STOPPED.value == "stopped"
        assert AgentStatus.STARTING.value == "starting"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.STOPPING.value == "stopping"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.OFFLINE.value == "offline"
    
    def test_agent_type_enum(self):
        """测试代理类型枚举"""
        assert AgentType.TEXT_GENERATION.value == "text_generation"
        assert AgentType.CODE_GENERATION.value == "code_generation"
        assert AgentType.TEXT_SUMMARIZATION.value == "text_summarization"
        assert AgentType.TRANSLATION.value == "translation"
        assert AgentType.QUESTION_ANSWERING.value == "question_answering"
        assert AgentType.MULTI_MODAL.value == "multi_modal"
        assert AgentType.CUSTOM.value == "custom"
    
    def test_agent_priority_enum(self):
        """测试代理优先级枚举"""
        assert AgentPriority.LOW.value == "low"
        assert AgentPriority.NORMAL.value == "normal"
        assert AgentPriority.HIGH.value == "high"
        assert AgentPriority.CRITICAL.value == "critical"
    
    def test_agent_capability_mapping(self):
        """测试代理能力映射"""
        mapping = AgentCapabilityMapping(
            capability_id="text_generation",
            model_id="gpt-3.5-turbo",
            priority=1,
            enabled=True,
            fallback_models=["gpt-4", "claude-3-sonnet"],
            max_retries=3,
            timeout=30
        )
        
        assert mapping.capability_id == "text_generation"
        assert mapping.model_id == "gpt-3.5-turbo"
        assert mapping.priority == 1
        assert mapping.enabled is True
        assert mapping.fallback_models == ["gpt-4", "claude-3-sonnet"]
        assert mapping.max_retries == 3
        assert mapping.timeout == 30
    
    def test_agent_config_creation(self):
        """测试代理配置创建"""
        capabilities = [
            AgentCapabilityMapping(
                capability_id="text_generation",
                model_id="gpt-3.5-turbo",
                priority=1,
                enabled=True
            )
        ]
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=capabilities,
            priority=AgentPriority.NORMAL,
            max_concurrent_tasks=5,
            auto_start=True,
            health_check_interval=30,
            max_restart_attempts=3,
            restart_delay=5,
            resource_limits={"memory": "1GB"},
            metadata={"version": "1.0"}
        )
        
        assert agent_config.agent_id == "test_agent_1"
        assert agent_config.name == "测试代理"
        assert agent_config.description == "这是一个测试代理"
        assert agent_config.agent_type == AgentType.TEXT_GENERATION
        assert len(agent_config.capabilities) == 1
        assert agent_config.capabilities[0].capability_id == "text_generation"
        assert agent_config.priority == AgentPriority.NORMAL
        assert agent_config.max_concurrent_tasks == 5
        assert agent_config.auto_start is True
        assert agent_config.health_check_interval == 30
        assert agent_config.max_restart_attempts == 3
        assert agent_config.restart_delay == 5
        assert agent_config.resource_limits == {"memory": "1GB"}
        assert agent_config.metadata == {"version": "1.0"}
        assert isinstance(agent_config.created_at, datetime)
        assert isinstance(agent_config.updated_at, datetime)
    
    def test_agent_config_to_dict(self):
        """测试代理配置转换为字典"""
        capabilities = [
            AgentCapabilityMapping(
                capability_id="text_generation",
                model_id="gpt-3.5-turbo",
                priority=1,
                enabled=True
            )
        ]
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=capabilities
        )
        
        data = agent_config.to_dict()
        
        assert data["agent_id"] == "test_agent_1"
        assert data["name"] == "测试代理"
        assert data["description"] == "这是一个测试代理"
        assert data["agent_type"] == "text_generation"
        assert len(data["capabilities"]) == 1
        assert data["capabilities"][0]["capability_id"] == "text_generation"
        assert data["capabilities"][0]["model_id"] == "gpt-3.5-turbo"
        assert data["priority"] == "normal"
        assert data["max_concurrent_tasks"] == 5
        assert data["auto_start"] is False
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_agent_config_from_dict(self):
        """测试从字典创建代理配置"""
        data = {
            "agent_id": "test_agent_1",
            "name": "测试代理",
            "description": "这是一个测试代理",
            "agent_type": "text_generation",
            "capabilities": [
                {
                    "capability_id": "text_generation",
                    "model_id": "gpt-3.5-turbo",
                    "priority": 1,
                    "enabled": True,
                    "fallback_models": ["gpt-4"],
                    "max_retries": 3,
                    "timeout": 30
                }
            ],
            "priority": "high",
            "max_concurrent_tasks": 3,
            "auto_start": True,
            "health_check_interval": 60,
            "max_restart_attempts": 5,
            "restart_delay": 10,
            "resource_limits": {"memory": "2GB"},
            "metadata": {"version": "2.0"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        agent_config = AgentConfig.from_dict(data)
        
        assert agent_config.agent_id == "test_agent_1"
        assert agent_config.name == "测试代理"
        assert agent_config.description == "这是一个测试代理"
        assert agent_config.agent_type == AgentType.TEXT_GENERATION
        assert len(agent_config.capabilities) == 1
        assert agent_config.capabilities[0].capability_id == "text_generation"
        assert agent_config.capabilities[0].model_id == "gpt-3.5-turbo"
        assert agent_config.capabilities[0].fallback_models == ["gpt-4"]
        assert agent_config.priority == AgentPriority.HIGH
        assert agent_config.max_concurrent_tasks == 3
        assert agent_config.auto_start is True
        assert agent_config.health_check_interval == 60
        assert agent_config.max_restart_attempts == 5
        assert agent_config.restart_delay == 10
        assert agent_config.resource_limits == {"memory": "2GB"}
        assert agent_config.metadata == {"version": "2.0"}
    
    def test_agent_instance_creation(self):
        """测试代理实例创建"""
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        instance = AgentInstance(
            instance_id="test_instance_1",
            agent_config=agent_config,
            status=AgentStatus.RUNNING,
            current_tasks=2,
            total_tasks=100,
            successful_tasks=95,
            failed_tasks=5,
            avg_response_time=1500.0,
            last_health_check=datetime.now(),
            last_error="连接超时",
            restart_count=1,
            start_time=datetime.now(),
            resource_usage={"cpu": "50%", "memory": "1GB"},
            performance_metrics={"success_rate": 0.95}
        )
        
        assert instance.instance_id == "test_instance_1"
        assert instance.agent_config.agent_id == "test_agent_1"
        assert instance.status == AgentStatus.RUNNING
        assert instance.current_tasks == 2
        assert instance.total_tasks == 100
        assert instance.successful_tasks == 95
        assert instance.failed_tasks == 5
        assert instance.avg_response_time == 1500.0
        assert instance.last_error == "连接超时"
        assert instance.restart_count == 1
        assert instance.resource_usage == {"cpu": "50%", "memory": "1GB"}
        assert instance.performance_metrics == {"success_rate": 0.95}
    
    def test_agent_instance_to_dict(self):
        """测试代理实例转换为字典"""
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        instance = AgentInstance(
            instance_id="test_instance_1",
            agent_config=agent_config,
            status=AgentStatus.RUNNING
        )
        
        data = instance.to_dict()
        
        assert data["instance_id"] == "test_instance_1"
        assert data["agent_config"]["agent_id"] == "test_agent_1"
        assert data["status"] == "running"
        assert data["current_tasks"] == 0
        assert data["total_tasks"] == 0
        assert data["successful_tasks"] == 0
        assert data["failed_tasks"] == 0
        assert data["avg_response_time"] == 0.0
        assert data["restart_count"] == 0
        assert "resource_usage" in data
        assert "performance_metrics" in data
    
    def test_agent_template_creation(self):
        """测试代理模板创建"""
        template = AgentTemplate(
            template_id="test_template_1",
            name="测试模板",
            description="这是一个测试模板",
            agent_type=AgentType.TEXT_GENERATION,
            base_capabilities=["text_generation", "text_summarization"],
            recommended_models={
                "text_generation": ["gpt-3.5-turbo", "gpt-4"],
                "text_summarization": ["gpt-3.5-turbo"]
            },
            default_settings={
                "max_concurrent_tasks": 3,
                "auto_start": True
            },
            category="text",
            tags=["test", "text"]
        )
        
        assert template.template_id == "test_template_1"
        assert template.name == "测试模板"
        assert template.description == "这是一个测试模板"
        assert template.agent_type == AgentType.TEXT_GENERATION
        assert template.base_capabilities == ["text_generation", "text_summarization"]
        assert template.recommended_models["text_generation"] == ["gpt-3.5-turbo", "gpt-4"]
        assert template.default_settings["max_concurrent_tasks"] == 3
        assert template.category == "text"
        assert template.tags == ["test", "text"]
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)
    
    def test_agent_template_to_dict(self):
        """测试代理模板转换为字典"""
        template = AgentTemplate(
            template_id="test_template_1",
            name="测试模板",
            description="这是一个测试模板",
            agent_type=AgentType.TEXT_GENERATION,
            base_capabilities=["text_generation"],
            recommended_models={"text_generation": ["gpt-3.5-turbo"]},
            default_settings={"max_concurrent_tasks": 3}
        )
        
        data = template.to_dict()
        
        assert data["template_id"] == "test_template_1"
        assert data["name"] == "测试模板"
        assert data["description"] == "这是一个测试模板"
        assert data["agent_type"] == "text_generation"
        assert data["base_capabilities"] == ["text_generation"]
        assert data["recommended_models"]["text_generation"] == ["gpt-3.5-turbo"]
        assert data["default_settings"]["max_concurrent_tasks"] == 3
        assert data["category"] == "general"
        assert data["tags"] == []
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_agent_template_from_dict(self):
        """测试从字典创建代理模板"""
        data = {
            "template_id": "test_template_1",
            "name": "测试模板",
            "description": "这是一个测试模板",
            "agent_type": "text_generation",
            "base_capabilities": ["text_generation"],
            "recommended_models": {"text_generation": ["gpt-3.5-turbo"]},
            "default_settings": {"max_concurrent_tasks": 3},
            "category": "text",
            "tags": ["test", "text"],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        template = AgentTemplate.from_dict(data)
        
        assert template.template_id == "test_template_1"
        assert template.name == "测试模板"
        assert template.description == "这是一个测试模板"
        assert template.agent_type == AgentType.TEXT_GENERATION
        assert template.base_capabilities == ["text_generation"]
        assert template.recommended_models["text_generation"] == ["gpt-3.5-turbo"]
        assert template.default_settings["max_concurrent_tasks"] == 3
        assert template.category == "text"
        assert template.tags == ["test", "text"]


class TestAgentRegistry:
    """代理注册表测试类"""
    
    def test_agent_registry_initialization(self):
        """测试代理注册表初始化"""
        registry = AgentRegistry()
        
        assert registry.agents == {}
        assert registry.instances == {}
        assert len(registry.templates) > 0  # 应该包含默认模板
    
    def test_register_agent(self):
        """测试注册代理"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        result = registry.register_agent(agent_config)
        
        assert result is True
        assert "test_agent_1" in registry.agents
        assert registry.agents["test_agent_1"] == agent_config
    
    def test_register_duplicate_agent(self):
        """测试注册重复代理"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent_config)
        result = registry.register_agent(agent_config)  # 重复注册
        
        assert result is False
    
    def test_unregister_agent(self):
        """测试注销代理"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent_config)
        result = registry.unregister_agent("test_agent_1")
        
        assert result is True
        assert "test_agent_1" not in registry.agents
    
    def test_unregister_nonexistent_agent(self):
        """测试注销不存在的代理"""
        registry = AgentRegistry()
        
        result = registry.unregister_agent("nonexistent_agent")
        
        assert result is False
    
    def test_get_agent(self):
        """测试获取代理"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent_config)
        retrieved_agent = registry.get_agent("test_agent_1")
        
        assert retrieved_agent == agent_config
    
    def test_get_nonexistent_agent(self):
        """测试获取不存在的代理"""
        registry = AgentRegistry()
        
        retrieved_agent = registry.get_agent("nonexistent_agent")
        
        assert retrieved_agent is None
    
    def test_list_agents(self):
        """测试列出代理"""
        registry = AgentRegistry()
        
        agent1 = AgentConfig(
            agent_id="agent_1",
            name="代理1",
            description="代理1描述",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        agent2 = AgentConfig(
            agent_id="agent_2",
            name="代理2",
            description="代理2描述",
            agent_type=AgentType.CODE_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        agents = registry.list_agents()
        
        assert len(agents) == 2
        assert agent1 in agents
        assert agent2 in agents
    
    def test_search_agents(self):
        """测试搜索代理"""
        registry = AgentRegistry()
        
        agent1 = AgentConfig(
            agent_id="agent_1",
            name="文本生成代理",
            description="用于文本生成",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        agent2 = AgentConfig(
            agent_id="agent_2",
            name="代码生成代理",
            description="用于代码生成",
            agent_type=AgentType.CODE_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        # 按名称搜索
        results = registry.search_agents("文本")
        assert len(results) == 1
        assert results[0].agent_id == "agent_1"
        
        # 按描述搜索
        results = registry.search_agents("代码")
        assert len(results) == 1
        assert results[0].agent_id == "agent_2"
        
        # 按类型筛选
        results = registry.search_agents("生成", AgentType.TEXT_GENERATION)
        assert len(results) == 1
        assert results[0].agent_id == "agent_1"
    
    def test_create_instance(self):
        """测试创建代理实例"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent_config)
        instance = registry.create_instance("test_agent_1")
        
        assert instance is not None
        assert instance.agent_config.agent_id == "test_agent_1"
        assert instance.status == AgentStatus.STOPPED
        assert instance.instance_id in registry.instances
    
    def test_create_instance_nonexistent_agent(self):
        """测试为不存在的代理创建实例"""
        registry = AgentRegistry()
        
        instance = registry.create_instance("nonexistent_agent")
        
        assert instance is None
    
    def test_get_instance(self):
        """测试获取代理实例"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent_config)
        instance = registry.create_instance("test_agent_1")
        
        retrieved_instance = registry.get_instance(instance.instance_id)
        
        assert retrieved_instance == instance
    
    def test_get_nonexistent_instance(self):
        """测试获取不存在的代理实例"""
        registry = AgentRegistry()
        
        retrieved_instance = registry.get_instance("nonexistent_instance")
        
        assert retrieved_instance is None
    
    def test_list_instances(self):
        """测试列出代理实例"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent_config)
        instance1 = registry.create_instance("test_agent_1")
        instance2 = registry.create_instance("test_agent_1")
        
        instances = registry.list_instances()
        
        assert len(instances) == 2
        assert instance1 in instances
        assert instance2 in instances
    
    def test_get_agent_instances(self):
        """测试获取指定代理的所有实例"""
        registry = AgentRegistry()
        
        agent1 = AgentConfig(
            agent_id="agent_1",
            name="代理1",
            description="代理1描述",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        agent2 = AgentConfig(
            agent_id="agent_2",
            name="代理2",
            description="代理2描述",
            agent_type=AgentType.CODE_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        instance1 = registry.create_instance("agent_1")
        instance2 = registry.create_instance("agent_1")
        instance3 = registry.create_instance("agent_2")
        
        agent1_instances = registry.get_agent_instances("agent_1")
        agent2_instances = registry.get_agent_instances("agent_2")
        
        assert len(agent1_instances) == 2
        assert instance1 in agent1_instances
        assert instance2 in agent1_instances
        assert instance3 not in agent1_instances
        
        assert len(agent2_instances) == 1
        assert instance3 in agent2_instances
    
    def test_remove_instance(self):
        """测试移除代理实例"""
        registry = AgentRegistry()
        
        agent_config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="这是一个测试代理",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[]
        )
        
        registry.register_agent(agent_config)
        instance = registry.create_instance("test_agent_1")
        
        result = registry.remove_instance(instance.instance_id)
        
        assert result is True
        assert instance.instance_id not in registry.instances
    
    def test_remove_nonexistent_instance(self):
        """测试移除不存在的代理实例"""
        registry = AgentRegistry()
        
        result = registry.remove_instance("nonexistent_instance")
        
        assert result is False
    
    def test_get_template(self):
        """测试获取代理模板"""
        registry = AgentRegistry()
        
        template = registry.get_template("text_generation_basic")
        
        assert template is not None
        assert template.template_id == "text_generation_basic"
        assert template.name == "基础文本生成代理"
    
    def test_get_nonexistent_template(self):
        """测试获取不存在的代理模板"""
        registry = AgentRegistry()
        
        template = registry.get_template("nonexistent_template")
        
        assert template is None
    
    def test_list_templates(self):
        """测试列出代理模板"""
        registry = AgentRegistry()
        
        templates = registry.list_templates()
        
        assert len(templates) >= 3  # 至少包含3个默认模板
        template_ids = [template.template_id for template in templates]
        assert "text_generation_basic" in template_ids
        assert "code_generation_basic" in template_ids
        assert "multi_capability_advanced" in template_ids
    
    def test_search_templates(self):
        """测试搜索代理模板"""
        registry = AgentRegistry()
        
        # 按名称搜索
        results = registry.search_templates("文本")
        assert len(results) >= 1
        assert any("文本" in template.name for template in results)
        
        # 按描述搜索
        results = registry.search_templates("代码")
        assert len(results) >= 1
        assert any("代码" in template.description for template in results)
        
        # 按分类筛选
        results = registry.search_templates("", "text")
        assert len(results) >= 1
        assert all(template.category == "text" for template in results)
    
    def test_create_agent_from_template(self):
        """测试从模板创建代理"""
        registry = AgentRegistry()
        
        agent_config = registry.create_agent_from_template(
            "text_generation_basic",
            "我的文本代理",
            "自定义文本生成代理"
        )
        
        assert agent_config is not None
        assert agent_config.name == "我的文本代理"
        assert agent_config.description == "自定义文本生成代理"
        assert agent_config.agent_type == AgentType.TEXT_GENERATION
        assert len(agent_config.capabilities) >= 1
        assert agent_config.agent_id in registry.agents
    
    def test_create_agent_from_nonexistent_template(self):
        """测试从不存在的模板创建代理"""
        registry = AgentRegistry()
        
        agent_config = registry.create_agent_from_template(
            "nonexistent_template",
            "我的代理",
            "自定义代理"
        )
        
        assert agent_config is None
    
    def test_create_sample_agents(self):
        """测试创建示例代理"""
        registry = create_sample_agents()
        
        agents = registry.list_agents()
        
        assert len(agents) >= 3  # 至少包含3个示例代理
        agent_ids = [agent.agent_id for agent in agents]
        assert "text_agent_1" in agent_ids
        assert "code_agent_1" in agent_ids
        assert "multi_agent_1" in agent_ids


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
