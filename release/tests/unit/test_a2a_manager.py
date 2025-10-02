"""
A2A管理器单元测试
测试 A2AManager 类的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any

from src.a2a.a2a_manager import A2AManager
from src.a2a.a2a_client import A2AClient
from src.core.agent_model import AgentConfig, AgentInstance


class TestA2AManager:
    """测试A2A管理器类"""
    
    def test_a2a_manager_initialization(self):
        """测试A2A管理器初始化"""
        # 测试正常初始化
        a2a_manager = A2AManager()
        
        assert a2a_manager.clients == {}
        assert a2a_manager.connected_agents == {}
        assert a2a_manager.task_queue is not None
        assert a2a_manager.is_running is False
    
    def test_a2a_manager_client_management(self):
        """测试A2A客户端管理"""
        a2a_manager = A2AManager()
        
        # 测试添加客户端
        client1 = Mock(spec=A2AClient)
        client1.server_url = "http://localhost:8001"
        
        a2a_manager.add_client(client1)
        assert "http://localhost:8001" in a2a_manager.clients
        assert a2a_manager.clients["http://localhost:8001"] == client1
        
        # 测试添加重复客户端
        a2a_manager.add_client(client1)  # 应该不会重复添加
        assert len(a2a_manager.clients) == 1
        
        # 测试移除客户端
        a2a_manager.remove_client("http://localhost:8001")
        assert "http://localhost:8001" not in a2a_manager.clients
        
        # 测试移除不存在的客户端
        a2a_manager.remove_client("nonexistent")  # 应该不会报错
    
    def test_a2a_manager_agent_registration(self):
        """测试代理注册管理"""
        a2a_manager = A2AManager()
        
        # 创建模拟客户端
        client = Mock(spec=A2AClient)
        client.server_url = "http://localhost:8001"
        client.register_agent = AsyncMock(return_value=True)
        client.unregister_agent = AsyncMock(return_value=True)
        
        a2a_manager.add_client(client)
        
        # 创建模拟代理
        agent_config = Mock(spec=AgentConfig)
        agent_config.id = "agent-123"
        agent_config.name = "Test Agent"
        
        agent_instance = Mock(spec=AgentInstance)
        agent_instance.id = "instance-456"
        agent_instance.config = agent_config
        
        # 测试注册代理
        success = asyncio.run(a2a_manager.register_agent(agent_instance, "http://localhost:8001"))
        assert success is True
        
        # 验证代理已注册
        assert "agent-123" in a2a_manager.connected_agents
        assert a2a_manager.connected_agents["agent-123"] == {
            "instance": agent_instance,
            "client": client,
            "server_url": "http://localhost:8001"
        }
        
        # 测试注销代理
        success = asyncio.run(a2a_manager.unregister_agent("agent-123"))
        assert success is True
        assert "agent-123" not in a2a_manager.connected_agents
    
    @pytest.mark.asyncio
    async def test_a2a_manager_task_handling(self):
        """测试任务处理"""
        a2a_manager = A2AManager()
        
        # 创建模拟客户端和代理
        client = Mock(spec=A2AClient)
        client.server_url = "http://localhost:8001"
        client.send_task = AsyncMock(return_value={"task_id": "task-789", "status": "accepted"})
        
        agent_config = Mock(spec=AgentConfig)
        agent_config.id = "agent-123"
        
        agent_instance = Mock(spec=AgentInstance)
        agent_instance.id = "instance-456"
        agent_instance.config = agent_config
        
        # 注册代理
        a2a_manager.add_client(client)
        await a2a_manager.register_agent(agent_instance, "http://localhost:8001")
        
        # 测试发送任务
        task_data = {
            "type": "text_generation",
            "prompt": "Hello, world!",
            "parameters": {"max_tokens": 100}
        }
        
        result = await a2a_manager.send_task("agent-123", task_data)
        
        assert result == {"task_id": "task-789", "status": "accepted"}
        client.send_task.assert_called_once_with("agent-123", task_data)
    
    @pytest.mark.asyncio
    async def test_a2a_manager_agent_discovery(self):
        """测试代理发现"""
        a2a_manager = A2AManager()
        
        # 创建模拟客户端
        client1 = Mock(spec=A2AClient)
        client1.server_url = "http://localhost:8001"
        client1.get_available_agents = AsyncMock(return_value=[
            {"id": "agent-1", "name": "Agent 1", "capabilities": ["translation"]},
            {"id": "agent-2", "name": "Agent 2", "capabilities": ["summarization"]}
        ])
        
        client2 = Mock(spec=A2AClient)
        client2.server_url = "http://localhost:8002"
        client2.get_available_agents = AsyncMock(return_value=[
            {"id": "agent-3", "name": "Agent 3", "capabilities": ["qa"]}
        ])
        
        a2a_manager.add_client(client1)
        a2a_manager.add_client(client2)
        
        # 测试发现所有代理
        all_agents = await a2a_manager.discover_agents()
        
        assert len(all_agents) == 3
        assert any(agent["id"] == "agent-1" for agent in all_agents)
        assert any(agent["id"] == "agent-2" for agent in all_agents)
        assert any(agent["id"] == "agent-3" for agent in all_agents)
        
        # 测试按能力发现代理
        translation_agents = await a2a_manager.discover_agents(capability="translation")
        assert len(translation_agents) == 1
        assert translation_agents[0]["id"] == "agent-1"
    
    @pytest.mark.asyncio
    async def test_a2a_manager_error_handling(self):
        """测试错误处理"""
        a2a_manager = A2AManager()
        
        # 测试发送任务到未注册的代理
        with pytest.raises(ValueError):
            await a2a_manager.send_task("nonexistent-agent", {})
        
        # 测试注册代理到不存在的客户端
        agent_instance = Mock(spec=AgentInstance)
        agent_instance.id = "test-agent"
        agent_instance.config = Mock(spec=AgentConfig)
        agent_instance.config.id = "test-agent"
        
        success = await a2a_manager.register_agent(agent_instance, "nonexistent-server")
        assert success is False
        
        # 测试客户端连接失败
        client = Mock(spec=A2AClient)
        client.server_url = "http://localhost:8001"
        client.register_agent = AsyncMock(side_effect=ConnectionError("Connection failed"))
        
        a2a_manager.add_client(client)
        
        success = await a2a_manager.register_agent(agent_instance, "http://localhost:8001")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_a2a_manager_connection_management(self):
        """测试连接管理"""
        a2a_manager = A2AManager()
        
        # 创建模拟客户端
        client1 = Mock(spec=A2AClient)
        client1.server_url = "http://localhost:8001"
        client1.connect = AsyncMock(return_value=True)
        client1.disconnect = AsyncMock(return_value=True)
        client1.is_connected = Mock(return_value=True)
        
        client2 = Mock(spec=A2AClient)
        client2.server_url = "http://localhost:8002"
        client2.connect = AsyncMock(return_value=False)  # 连接失败
        client2.is_connected = Mock(return_value=False)
        
        a2a_manager.add_client(client1)
        a2a_manager.add_client(client2)
        
        # 测试连接所有客户端
        success_count = await a2a_manager.connect_all()
        assert success_count == 1  # 只有client1连接成功
        
        # 测试断开所有连接
        await a2a_manager.disconnect_all()
        client1.disconnect.assert_called_once()
    
    def test_a2a_manager_status_monitoring(self):
        """测试状态监控"""
        a2a_manager = A2AManager()
        
        # 创建模拟客户端
        client1 = Mock(spec=A2AClient)
        client1.server_url = "http://localhost:8001"
        client1.is_connected = Mock(return_value=True)
        client1.get_status = Mock(return_value={"status": "connected", "agents": 2})
        
        client2 = Mock(spec=A2AClient)
        client2.server_url = "http://localhost:8002"
        client2.is_connected = Mock(return_value=False)
        client2.get_status = Mock(return_value={"status": "disconnected"})
        
        a2a_manager.add_client(client1)
        a2a_manager.add_client(client2)
        
        # 测试获取状态
        status = a2a_manager.get_status()
        
        assert "clients" in status
        assert "connected_agents" in status
        assert "task_queue_size" in status
        
        assert len(status["clients"]) == 2
        assert status["clients"]["http://localhost:8001"]["connected"] is True
        assert status["clients"]["http://localhost:8002"]["connected"] is False


class TestA2AManagerIntegration:
    """测试A2A管理器集成功能"""
    
    @pytest.mark.asyncio
    async def test_a2a_manager_complete_workflow(self):
        """测试完整的A2A工作流程"""
        a2a_manager = A2AManager()
        
        # 创建模拟客户端
        client = Mock(spec=A2AClient)
        client.server_url = "http://localhost:8001"
        client.connect = AsyncMock(return_value=True)
        client.disconnect = AsyncMock(return_value=True)
        client.register_agent = AsyncMock(return_value=True)
        client.unregister_agent = AsyncMock(return_value=True)
        client.send_task = AsyncMock(return_value={"task_id": "task-123", "status": "accepted"})
        client.get_available_agents = AsyncMock(return_value=[])
        client.is_connected = Mock(return_value=True)
        client.get_status = Mock(return_value={"status": "connected"})
        
        a2a_manager.add_client(client)
        
        # 1. 连接客户端
        success_count = await a2a_manager.connect_all()
        assert success_count == 1
        
        # 2. 创建并注册代理
        agent_config = Mock(spec=AgentConfig)
        agent_config.id = "translation-agent"
        agent_config.name = "Translation Agent"
        
        agent_instance = Mock(spec=AgentInstance)
        agent_instance.id = "instance-1"
        agent_instance.config = agent_config
        
        success = await a2a_manager.register_agent(agent_instance, "http://localhost:8001")
        assert success is True
        
        # 3. 发送任务
        task_data = {
            "type": "translation",
            "source_language": "en",
            "target_language": "zh",
            "text": "Hello, world!"
        }
        
        result = await a2a_manager.send_task("translation-agent", task_data)
        assert result["task_id"] == "task-123"
        assert result["status"] == "accepted"
        
        # 4. 检查状态
        status = a2a_manager.get_status()
        assert status["clients"]["http://localhost:8001"]["connected"] is True
        assert "translation-agent" in status["connected_agents"]
        
        # 5. 注销代理并断开连接
        success = await a2a_manager.unregister_agent("translation-agent")
        assert success is True
        
        await a2a_manager.disconnect_all()
        client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_a2a_manager_multiple_clients(self):
        """测试多客户端管理"""
        a2a_manager = A2AManager()
        
        # 创建多个模拟客户端
        clients = []
        for i in range(3):
            client = Mock(spec=A2AClient)
            client.server_url = f"http://localhost:800{i+1}"
            client.connect = AsyncMock(return_value=True)
            client.disconnect = AsyncMock(return_value=True)
            client.register_agent = AsyncMock(return_value=True)
            client.get_available_agents = AsyncMock(return_value=[
                {"id": f"agent-{i}-1", "name": f"Agent {i}-1"},
                {"id": f"agent-{i}-2", "name": f"Agent {i}-2"}
            ])
            client.is_connected = Mock(return_value=True)
            
            a2a_manager.add_client(client)
            clients.append(client)
        
        # 连接所有客户端
        success_count = await a2a_manager.connect_all()
        assert success_count == 3
        
        # 注册代理到不同客户端
        for i, client in enumerate(clients):
            agent_config = Mock(spec=AgentConfig)
            agent_config.id = f"agent-{i}"
            
            agent_instance = Mock(spec=AgentInstance)
            agent_instance.id = f"instance-{i}"
            agent_instance.config = agent_config
            
            success = await a2a_manager.register_agent(agent_instance, client.server_url)
            assert success is True
        
        # 发现所有代理
        all_agents = await a2a_manager.discover_agents()
        assert len(all_agents) == 6  # 3个客户端 * 2个代理
        
        # 断开所有连接
        await a2a_manager.disconnect_all()
        for client in clients:
            client.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_a2a_manager_load_balancing(self):
        """测试负载均衡"""
        a2a_manager = A2AManager()
        
        # 创建多个模拟客户端
        clients = []
        task_counts = {}  # 跟踪每个客户端的任务数量
        
        for i in range(2):
            client = Mock(spec=A2AClient)
            client.server_url = f"http://localhost:800{i+1}"
            client.connect = AsyncMock(return_value=True)
            client.register_agent = AsyncMock(return_value=True)
            
            # 模拟任务发送，记录任务计数
            task_counts[client.server_url] = 0
            
            def make_send_task(server_url):
                async def send_task(agent_id, task_data):
                    task_counts[server_url] += 1
                    return {"task_id": f"task-{task_counts[server_url]}", "status": "accepted"}
                return send_task
            
            client.send_task = make_send_task(client.server_url)
            client.is_connected = Mock(return_value=True)
            
            a2a_manager.add_client(client)
            clients.append(client)
        
        # 连接客户端并注册代理
        await a2a_manager.connect_all()
        
        for i, client in enumerate(clients):
            agent_config = Mock(spec=AgentConfig)
            agent_config.id = f"agent-{i}"
            
            agent_instance = Mock(spec=AgentInstance)
            agent_instance.id = f"instance-{i}"
            agent_instance.config = agent_config
            
            await a2a_manager.register_agent(agent_instance, client.server_url)
        
        # 发送多个任务，应该均衡分配到不同客户端
        tasks = []
        for i in range(10):
            task_data = {"type": "test", "data": f"task-{i}"}
            # 交替使用两个代理
            agent_id = "agent-0" if i % 2 == 0 else "agent-1"
            task = a2a_manager.send_task(agent_id, task_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 验证任务分配
        assert len(results) == 10
        assert task_counts["http://localhost:8001"] == 5  # agent-0的任务
        assert task_counts["http://localhost:8002"] == 5  # agent-1的任务


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
