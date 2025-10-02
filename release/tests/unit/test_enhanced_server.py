"""
增强A2A服务器单元测试
测试代理注册发现、心跳检测、状态同步等高级功能
"""

import pytest
import asyncio
import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.a2a.enhanced_server import (
    EnhancedA2AServer, EnhancedAgentExecutor, AgentConnectionStatus, 
    RegisteredAgent, get_enhanced_server, start_enhanced_server, stop_enhanced_server
)
from src.core.agent_model import AgentRegistry, AgentConfig, AgentType, AgentCapabilityMapping
from a2a.types import AgentCard, AgentCapabilities


class TestEnhancedA2AServer:
    """增强A2A服务器测试"""
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表"""
        return AgentRegistry()
    
    @pytest.fixture
    def enhanced_server(self, agent_registry):
        """创建增强A2A服务器"""
        return EnhancedA2AServer(agent_registry, host="localhost", port=8000)
    
    @pytest.fixture
    def sample_agent_card(self):
        """创建示例代理卡片"""
        return AgentCard(
            name="测试代理",
            version="1.0.0",
            description="测试代理描述",
            url="http://localhost:8001/",
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=True,
            ),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[
                {
                    "id": "test_skill",
                    "name": "测试技能",
                    "description": "测试技能描述",
                    "tags": ["test"]
                }
            ]
        )
    
    def test_enhanced_server_creation(self, enhanced_server):
        """测试增强服务器创建"""
        assert enhanced_server is not None
        assert enhanced_server.host == "localhost"
        assert enhanced_server.port == 8000
        assert enhanced_server.agent_registry is not None
        assert enhanced_server.logger is not None
        assert isinstance(enhanced_server.registered_agents, dict)
        assert enhanced_server.heartbeat_interval == 30
        assert enhanced_server.heartbeat_timeout == 60
        assert enhanced_server.running is False
    
    @pytest.mark.asyncio
    async def test_register_agent(self, enhanced_server, sample_agent_card):
        """测试代理注册"""
        agent_id = "test_agent_1"
        instance_id = "test_instance_1"
        capabilities = ["text_generation", "text_summarization"]
        metadata = {"priority": "high"}
        
        success = await enhanced_server.register_agent(
            agent_id, instance_id, sample_agent_card, capabilities, metadata
        )
        
        assert success is True
        assert agent_id in enhanced_server.registered_agents
        
        registered_agent = enhanced_server.registered_agents[agent_id]
        assert registered_agent.agent_id == agent_id
        assert registered_agent.instance_id == instance_id
        assert registered_agent.agent_card == sample_agent_card
        assert registered_agent.connection_status == AgentConnectionStatus.CONNECTED
        assert registered_agent.capabilities == capabilities
        assert registered_agent.metadata == metadata
    
    @pytest.mark.asyncio
    async def test_register_agent_duplicate(self, enhanced_server, sample_agent_card):
        """测试重复代理注册"""
        agent_id = "test_agent_2"
        
        # 第一次注册
        success1 = await enhanced_server.register_agent(
            agent_id, "instance_1", sample_agent_card, ["text_generation"]
        )
        assert success1 is True
        
        # 第二次注册相同ID
        success2 = await enhanced_server.register_agent(
            agent_id, "instance_2", sample_agent_card, ["code_generation"]
        )
        assert success2 is False
    
    @pytest.mark.asyncio
    async def test_unregister_agent(self, enhanced_server, sample_agent_card):
        """测试代理注销"""
        agent_id = "test_agent_3"
        
        # 先注册
        await enhanced_server.register_agent(
            agent_id, "instance_3", sample_agent_card, ["text_generation"]
        )
        assert agent_id in enhanced_server.registered_agents
        
        # 注销
        success = await enhanced_server.unregister_agent(agent_id)
        assert success is True
        assert agent_id not in enhanced_server.registered_agents
    
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_agent(self, enhanced_server):
        """测试注销不存在的代理"""
        success = await enhanced_server.unregister_agent("nonexistent_agent")
        assert success is False
    
    def test_get_connected_agents(self, enhanced_server, sample_agent_card):
        """测试获取已连接代理"""
        # 添加一些测试代理
        agent1 = RegisteredAgent(
            agent_id="agent1",
            instance_id="instance1",
            agent_card=sample_agent_card,
            connection_status=AgentConnectionStatus.CONNECTED,
            last_heartbeat=datetime.datetime.now(),
            capabilities=["text_generation"]
        )
        
        agent2 = RegisteredAgent(
            agent_id="agent2",
            instance_id="instance2",
            agent_card=sample_agent_card,
            connection_status=AgentConnectionStatus.DISCONNECTED,
            last_heartbeat=datetime.datetime.now(),
            capabilities=["code_generation"]
        )
        
        enhanced_server.registered_agents["agent1"] = agent1
        enhanced_server.registered_agents["agent2"] = agent2
        
        connected_agents = enhanced_server.get_connected_agents()
        assert len(connected_agents) == 1
        assert connected_agents[0].agent_id == "agent1"
    
    def test_get_agents_by_capability(self, enhanced_server, sample_agent_card):
        """测试根据能力获取代理"""
        # 添加一些测试代理
        agent1 = RegisteredAgent(
            agent_id="agent1",
            instance_id="instance1",
            agent_card=sample_agent_card,
            connection_status=AgentConnectionStatus.CONNECTED,
            last_heartbeat=datetime.datetime.now(),
            capabilities=["text_generation", "translation"]
        )
        
        agent2 = RegisteredAgent(
            agent_id="agent2",
            instance_id="instance2",
            agent_card=sample_agent_card,
            connection_status=AgentConnectionStatus.CONNECTED,
            last_heartbeat=datetime.datetime.now(),
            capabilities=["code_generation"]
        )
        
        enhanced_server.registered_agents["agent1"] = agent1
        enhanced_server.registered_agents["agent2"] = agent2
        
        # 测试文本生成能力
        text_generation_agents = enhanced_server.get_agents_by_capability("text_generation")
        assert len(text_generation_agents) == 1
        assert text_generation_agents[0].agent_id == "agent1"
        
        # 测试代码生成能力
        code_generation_agents = enhanced_server.get_agents_by_capability("code_generation")
        assert len(code_generation_agents) == 1
        assert code_generation_agents[0].agent_id == "agent2"
        
        # 测试不存在的能
        nonexistent_agents = enhanced_server.get_agents_by_capability("nonexistent")
        assert len(nonexistent_agents) == 0
    
    @pytest.mark.asyncio
    async def test_heartbeat_monitor(self, enhanced_server, sample_agent_card):
        """测试心跳检测监控"""
        # 添加一个代理
        agent_id = "heartbeat_test_agent"
        await enhanced_server.register_agent(
            agent_id, "heartbeat_instance", sample_agent_card, ["text_generation"]
        )
        
        # 启动心跳监控
        enhanced_server.running = True
        monitor_task = asyncio.create_task(enhanced_server._heartbeat_monitor())
        
        # 等待一小段时间让监控运行
        await asyncio.sleep(0.1)
        
        # 停止监控
        enhanced_server.running = False
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        # 验证代理状态
        agent = enhanced_server.registered_agents[agent_id]
        assert agent.connection_status == AgentConnectionStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_heartbeat_timeout(self, enhanced_server, sample_agent_card):
        """测试心跳超时"""
        agent_id = "timeout_test_agent"
        
        # 添加一个代理，设置很久以前的心跳时间
        old_time = datetime.datetime.now() - datetime.timedelta(seconds=120)  # 2分钟前
        agent = RegisteredAgent(
            agent_id=agent_id,
            instance_id="timeout_instance",
            agent_card=sample_agent_card,
            connection_status=AgentConnectionStatus.CONNECTED,
            last_heartbeat=old_time,
            capabilities=["text_generation"]
        )
        enhanced_server.registered_agents[agent_id] = agent
        
        # 运行一次心跳检查
        await enhanced_server.check_heartbeat_once()
        
        # 验证代理状态变为断开连接
        assert agent.connection_status == AgentConnectionStatus.DISCONNECTED


class TestEnhancedAgentExecutor:
    """增强代理执行器测试"""
    
    @pytest.fixture
    def enhanced_server(self):
        """创建增强服务器"""
        agent_registry = AgentRegistry()
        return EnhancedA2AServer(agent_registry)
    
    @pytest.fixture
    def agent_executor(self, enhanced_server):
        """创建增强代理执行器"""
        return EnhancedAgentExecutor(enhanced_server)
    
    @pytest.fixture
    def mock_context(self):
        """创建模拟请求上下文"""
        context = Mock()
        context.task_id = "test_task"
        context.context_id = "test_context"
        context.message = Mock()
        context.message.parts = []
        return context
    
    @pytest.fixture
    def mock_event_queue(self):
        """创建模拟事件队列"""
        return Mock()
    
    def test_agent_executor_creation(self, agent_executor):
        """测试代理执行器创建"""
        assert agent_executor is not None
        assert agent_executor.server is not None
        assert agent_executor.logger is not None
    
    @pytest.mark.asyncio
    async def test_handle_status_request(self, agent_executor):
        """测试处理状态请求"""
        # 添加一些测试代理
        agent_card = AgentCard(
            name="测试代理",
            version="1.0.0",
            description="测试代理描述",
            url="http://localhost:8001/",
            capabilities=AgentCapabilities(streaming=True, push_notifications=True),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[]
        )
        
        agent = RegisteredAgent(
            agent_id="status_test_agent",
            instance_id="status_instance",
            agent_card=agent_card,
            connection_status=AgentConnectionStatus.CONNECTED,
            last_heartbeat=datetime.datetime.now(),
            capabilities=["text_generation"]
        )
        agent_executor.server.registered_agents["status_test_agent"] = agent
        
        response = await agent_executor._handle_status_request()
        
        assert "系统状态:" in response
        assert "总代理数:" in response
        assert "已连接代理:" in response
        assert "测试代理" in response
    
    @pytest.mark.asyncio
    async def test_handle_agent_request(self, agent_executor):
        """测试处理代理请求"""
        # 添加一些测试代理
        agent_card = AgentCard(
            name="代理测试",
            version="1.0.0",
            description="代理测试描述",
            url="http://localhost:8001/",
            capabilities=AgentCapabilities(streaming=True, push_notifications=True),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[]
        )
        
        agent1 = RegisteredAgent(
            agent_id="agent_test_1",
            instance_id="instance_1",
            agent_card=agent_card,
            connection_status=AgentConnectionStatus.CONNECTED,
            last_heartbeat=datetime.datetime.now(),
            capabilities=["text_generation"]
        )
        
        agent2 = RegisteredAgent(
            agent_id="agent_test_2",
            instance_id="instance_2",
            agent_card=agent_card,
            connection_status=AgentConnectionStatus.DISCONNECTED,
            last_heartbeat=datetime.datetime.now(),
            capabilities=["code_generation"]
        )
        
        agent_executor.server.registered_agents["agent_test_1"] = agent1
        agent_executor.server.registered_agents["agent_test_2"] = agent2
        
        response = await agent_executor._handle_agent_request()
        
        assert "已注册代理:" in response
        assert "代理测试" in response
        assert "connected" in response
        assert "disconnected" in response
    
    def test_handle_help_request(self, agent_executor):
        """测试处理帮助请求"""
        response = agent_executor._handle_help_request()
        
        assert "增强A2A服务器帮助" in response
        assert "状态" in response
        assert "代理" in response
        assert "帮助" in response
        assert "代理注册发现" in response
        assert "心跳检测监控" in response
        assert "状态同步" in response


class TestGlobalFunctions:
    """全局函数测试"""
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表"""
        return AgentRegistry()
    
    def test_get_enhanced_server(self, agent_registry):
        """测试获取全局增强服务器"""
        server1 = get_enhanced_server(agent_registry)
        server2 = get_enhanced_server(agent_registry)
        
        assert server1 is not None
        assert server2 is not None
        assert server1 is server2  # 应该是同一个实例
    
    @pytest.mark.asyncio
    async def test_start_stop_enhanced_server(self, agent_registry):
        """测试启动和停止增强服务器"""
        # 使用Mock来避免实际启动服务器
        with patch('src.a2a.enhanced_server.EnhancedA2AServer.start') as mock_start, \
             patch('src.a2a.enhanced_server.EnhancedA2AServer.stop') as mock_stop:
            
            # 测试启动
            await start_enhanced_server(agent_registry)
            mock_start.assert_called_once()
            
            # 测试停止
            await stop_enhanced_server()
            mock_stop.assert_called_once()


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表"""
        return AgentRegistry()
    
    @pytest.fixture
    def enhanced_server(self, agent_registry):
        """创建增强服务器"""
        return EnhancedA2AServer(agent_registry)
    
    @pytest.mark.asyncio
    async def test_agent_registration_workflow(self, enhanced_server):
        """测试代理注册完整工作流"""
        # 创建代理卡片
        agent_card = AgentCard(
            name="工作流测试代理",
            version="1.0.0",
            description="工作流测试代理描述",
            url="http://localhost:8001/",
            capabilities=AgentCapabilities(streaming=True, push_notifications=True),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[{"id": "workflow", "name": "工作流", "description": "工作流测试", "tags": ["workflow"]}]
        )
        
        # 1. 注册代理
        success = await enhanced_server.register_agent(
            "workflow_agent", "workflow_instance", agent_card, 
            ["text_generation", "code_generation"],
            {"test": "metadata"}
        )
        assert success is True
        
        # 2. 验证代理已注册
        assert "workflow_agent" in enhanced_server.registered_agents
        agent = enhanced_server.registered_agents["workflow_agent"]
        assert agent.agent_card.name == "工作流测试代理"
        assert agent.connection_status == AgentConnectionStatus.CONNECTED
        assert "text_generation" in agent.capabilities
        assert "code_generation" in agent.capabilities
        
        # 3. 获取已连接代理
        connected_agents = enhanced_server.get_connected_agents()
        assert len(connected_agents) == 1
        assert connected_agents[0].agent_id == "workflow_agent"
        
        # 4. 根据能力获取代理
        text_agents = enhanced_server.get_agents_by_capability("text_generation")
        assert len(text_agents) == 1
        code_agents = enhanced_server.get_agents_by_capability("code_generation")
        assert len(code_agents) == 1
        
        # 5. 注销代理
        success = await enhanced_server.unregister_agent("workflow_agent")
        assert success is True
        assert "workflow_agent" not in enhanced_server.registered_agents


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
