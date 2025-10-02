"""
A2A客户端单元测试
测试A2A客户端的基础功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

from src.a2a.a2a_client import (
    A2AClient, A2AAgentInfo, A2ATask, A2ATaskResult, A2AMessage,
    A2AConnectionStatus, A2AMessageType
)


class TestA2AClient:
    """A2A客户端测试类"""
    
    @pytest.fixture
    def client(self):
        """创建A2A客户端实例"""
        return A2AClient("http://localhost:8000", "test_client")
    
    @pytest.fixture
    def mock_agent_info(self):
        """创建模拟代理信息"""
        return A2AAgentInfo(
            agent_id="test_agent_1",
            name="测试代理",
            capabilities=["text_generation", "code_generation"]
        )
    
    @pytest.fixture
    def mock_task(self):
        """创建模拟任务"""
        return A2ATask(
            task_id="test_task_1",
            agent_id="test_agent_1",
            capability="text_generation",
            input_data={"prompt": "你好，请介绍一下自己"}
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, client):
        """测试初始化"""
        assert client.server_url == "http://localhost:8000"
        assert client.client_id == "test_client"
        assert client.status == A2AConnectionStatus.DISCONNECTED
        assert len(client.agents) == 0
        assert len(client.pending_tasks) == 0
        assert len(client.task_callbacks) == 0
    
    @pytest.mark.asyncio
    async def test_connect_success(self, client):
        """测试成功连接"""
        mock_response = Mock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            result = await client.connect()
            
            assert result is True
            assert client.status == A2AConnectionStatus.CONNECTED
            assert client.heartbeat_task is not None
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """测试连接失败"""
        mock_response = Mock()
        mock_response.status = 500
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            result = await client.connect()
            
            assert result is False
            assert client.status == A2AConnectionStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_connect_exception(self, client):
        """测试连接异常"""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.side_effect = Exception("连接错误")
            
            result = await client.connect()
            
            assert result is False
            assert client.status == A2AConnectionStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """测试断开连接"""
        # 先连接
        mock_response = Mock()
        mock_response.status = 200
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            await client.connect()
        
        # 测试断开连接
        await client.disconnect()
        
        assert client.status == A2AConnectionStatus.DISCONNECTED
        assert client.session is None
        assert client.heartbeat_task is None
    
    @pytest.mark.asyncio
    async def test_register_agent_success(self, client, mock_agent_info):
        """测试成功注册代理"""
        # 模拟连接状态
        client.status = A2AConnectionStatus.CONNECTED
        mock_session = AsyncMock()
        client.session = mock_session
        
        mock_response = Mock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch('src.a2a.a2a_client.AdapterFactory.create_adapter') as mock_factory:
            mock_factory.return_value = AsyncMock()
            
            result = await client.register_agent(mock_agent_info)
            
            assert result is True
            assert mock_agent_info.agent_id in client.agents
            assert client.agents[mock_agent_info.agent_id] == mock_agent_info
    
    @pytest.mark.asyncio
    async def test_register_agent_not_connected(self, client, mock_agent_info):
        """测试未连接时注册代理"""
        result = await client.register_agent(mock_agent_info)
        
        assert result is False
        assert mock_agent_info.agent_id not in client.agents
    
    @pytest.mark.asyncio
    async def test_unregister_agent_success(self, client, mock_agent_info):
        """测试成功注销代理"""
        # 先注册代理
        client.agents[mock_agent_info.agent_id] = mock_agent_info
        client.status = A2AConnectionStatus.CONNECTED
        mock_session = AsyncMock()
        client.session = mock_session
        
        mock_response = Mock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await client.unregister_agent(mock_agent_info.agent_id)
        
        assert result is True
        assert mock_agent_info.agent_id not in client.agents
    
    @pytest.mark.asyncio
    async def test_send_task_success(self, client, mock_task):
        """测试成功发送任务"""
        client.status = A2AConnectionStatus.CONNECTED
        mock_session = AsyncMock()
        client.session = mock_session
        
        mock_response = Mock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        callback_called = False
        
        def task_callback(result):
            nonlocal callback_called
            callback_called = True
        
        result = await client.send_task(mock_task, task_callback)
        
        assert result is True
        assert mock_task.task_id in client.pending_tasks
        assert mock_task.task_id in client.task_callbacks
        assert not callback_called  # 回调尚未调用
    
    @pytest.mark.asyncio
    async def test_send_task_not_connected(self, client, mock_task):
        """测试未连接时发送任务"""
        result = await client.send_task(mock_task)
        
        assert result is False
        assert mock_task.task_id not in client.pending_tasks
    
    @pytest.mark.asyncio
    async def test_get_available_agents_success(self, client):
        """测试成功获取可用代理列表"""
        client.status = A2AConnectionStatus.CONNECTED
        mock_session = AsyncMock()
        client.session = mock_session
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "agents": [
                {
                    "agent_id": "agent1",
                    "name": "代理1",
                    "capabilities": ["text_generation"],
                    "status": "idle",
                    "load": 0,
                    "metadata": {}
                }
            ]
        }
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        agents = await client.get_available_agents()
        
        assert len(agents) == 1
        assert agents[0].agent_id == "agent1"
        assert agents[0].name == "代理1"
    
    @pytest.mark.asyncio
    async def test_process_message_task_result(self, client, mock_task):
        """测试处理任务结果消息"""
        # 先注册任务和回调
        client.pending_tasks[mock_task.task_id] = mock_task
        callback_called = False
        
        def task_callback(result):
            nonlocal callback_called
            callback_called = True
            assert result.task_id == mock_task.task_id
            assert result.success is True
        
        client.task_callbacks[mock_task.task_id] = task_callback
        
        # 创建任务结果消息
        message_data = {
            "message_id": "msg1",
            "message_type": "task_result",
            "sender_id": "server",
            "payload": {
                "task_id": mock_task.task_id,
                "agent_id": mock_task.agent_id,
                "success": True,
                "output_data": {"response": "测试回复"},
                "execution_time": 1.5
            },
            "timestamp": 1234567890.0
        }
        
        await client.process_message(message_data)
        
        assert callback_called is True
        assert mock_task.task_id not in client.pending_tasks
        assert mock_task.task_id not in client.task_callbacks
    
    @pytest.mark.asyncio
    async def test_process_message_status_update(self, client, mock_agent_info):
        """测试处理状态更新消息"""
        # 先注册代理
        client.agents[mock_agent_info.agent_id] = mock_agent_info
        
        # 创建状态更新消息
        message_data = {
            "message_id": "msg2",
            "message_type": "status_update",
            "sender_id": "server",
            "payload": {
                "agent_id": mock_agent_info.agent_id,
                "status": "busy",
                "load": 80
            },
            "timestamp": 1234567890.0
        }
        
        await client.process_message(message_data)
        
        assert client.agents[mock_agent_info.agent_id].status == "busy"
        assert client.agents[mock_agent_info.agent_id].load == 80
    
    @pytest.mark.asyncio
    async def test_process_message_error(self, client):
        """测试处理错误消息"""
        message_data = {
            "message_id": "msg3",
            "message_type": "error",
            "sender_id": "server",
            "payload": {
                "error_type": "connection_error",
                "error_message": "连接超时"
            },
            "timestamp": 1234567890.0
        }
        
        await client.process_message(message_data)
        
        # 错误消息应该被记录，但没有状态变化
    
    @pytest.mark.asyncio
    async def test_heartbeat_loop(self, client):
        """测试心跳循环"""
        client.status = A2AConnectionStatus.CONNECTED
        mock_session = AsyncMock()
        client.session = mock_session
        
        mock_response = Mock()
        mock_response.status = 200
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # 添加一个代理
        agent_info = A2AAgentInfo(
            agent_id="test_agent",
            name="测试代理",
            capabilities=["text_generation"]
        )
        client.agents[agent_info.agent_id] = agent_info
        
        # 发送一次心跳
        await client._send_heartbeat()
        
        # 验证代理的最后心跳时间已更新
        assert agent_info.last_heartbeat > 0
    
    @pytest.mark.asyncio
    async def test_reconnect_loop(self, client):
        """测试重连循环"""
        client.status = A2AConnectionStatus.ERROR
        
        # 模拟重连成功
        with patch.object(client, 'connect', return_value=True):
            await client._reconnect_loop()
            
            assert client.status == A2AConnectionStatus.CONNECTED
    
    def test_message_conversion(self, client):
        """测试消息转换"""
        original_message = A2AMessage(
            message_id="test_msg",
            message_type=A2AMessageType.TASK_REQUEST,
            sender_id="client1",
            receiver_id="server1",
            payload={"key": "value"},
            timestamp=1234567890.0
        )
        
        # 转换为字典
        message_dict = client._message_to_dict(original_message)
        
        # 转换回消息对象
        converted_message = client._dict_to_message(message_dict)
        
        assert converted_message.message_id == original_message.message_id
        assert converted_message.message_type == original_message.message_type
        assert converted_message.sender_id == original_message.sender_id
        assert converted_message.receiver_id == original_message.receiver_id
        assert converted_message.payload == original_message.payload
        assert converted_message.timestamp == original_message.timestamp
    
    def test_get_status(self, client):
        """测试获取状态"""
        client.status = A2AConnectionStatus.CONNECTED
        client.agents["agent1"] = A2AAgentInfo("agent1", "代理1", ["cap1"])
        client.pending_tasks["task1"] = A2ATask("task1", "agent1", "cap1", {})
        
        status = client.get_status()
        
        assert status["client_id"] == "test_client"
        assert status["server_url"] == "http://localhost:8000"
        assert status["status"] == "connected"
        assert status["connected_agents"] == 1
        assert status["pending_tasks"] == 1


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
