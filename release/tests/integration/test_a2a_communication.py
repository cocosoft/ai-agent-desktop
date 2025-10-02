"""
A2A通信集成测试
测试A2A服务器和客户端之间的通信功能，包括压力测试、消息序列化、错误处理等
"""

import pytest
import asyncio
import json
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from src.a2a.enhanced_server import EnhancedA2AServer
from src.a2a.enhanced_client import EnhancedA2AClient, ConnectionStatus, MessagePriority
from src.core.agent_communication import AgentMessage, MessageType, CollaborationType, CollaborationRequest
from src.core.task_router import Task, TaskPriority
from src.utils.logger import get_log_manager


class TestA2ACommunication:
    """A2A通信集成测试"""
    
    @pytest.fixture
    async def a2a_server(self):
        """创建A2A服务器实例"""
        server = EnhancedA2AServer()
        await server.start()
        yield server
        await server.stop()
    
    @pytest.fixture
    async def a2a_client(self):
        """创建A2A客户端实例"""
        client = EnhancedA2AClient("http://localhost:8000")
        yield client
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_basic_communication(self, a2a_server, a2a_client):
        """测试基础通信功能"""
        # 1. 客户端连接
        success = await a2a_client.connect()
        assert success is True
        assert a2a_client.is_connected() is True
        
        # 2. 发送任务请求消息
        task_message = AgentMessage(
            message_id="test_task",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_client",
            receiver_id="test_server",
            payload={
                "task": {
                    "task_id": "test_task_001",
                    "capability_id": "text_generation",
                    "input_data": {"text": "测试输入"},
                    "priority": TaskPriority.NORMAL.value
                }
            }
        )
        
        message_id = await a2a_client.send_message(task_message, MessagePriority.NORMAL)
        assert message_id == "test_task"
        
        # 3. 验证消息已发送
        stats = a2a_client.get_connection_stats()
        assert stats.total_messages_sent == 1
        
        # 4. 断开连接
        await a2a_client.disconnect()
        assert a2a_client.is_connected() is False
    
    @pytest.mark.asyncio
    async def test_message_priority_handling(self, a2a_server, a2a_client):
        """测试消息优先级处理"""
        # 1. 客户端连接
        await a2a_client.connect()
        
        # 2. 发送不同优先级的消息
        low_priority_message = AgentMessage(
            message_id="low_priority",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_client",
            receiver_id="test_server",
            payload={"task": {"task_id": "low_task"}}
        )
        
        high_priority_message = AgentMessage(
            message_id="high_priority",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_client",
            receiver_id="test_server",
            payload={"task": {"task_id": "high_task"}}
        )
        
        # 先发送低优先级消息
        await a2a_client.send_message(low_priority_message, MessagePriority.LOW)
        
        # 然后发送高优先级消息
        await a2a_client.send_message(high_priority_message, MessagePriority.HIGH)
        
        # 3. 验证队列中有2条消息
        assert a2a_client.get_queue_size() == 2
        
        # 4. 断开连接
        await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_recovery(self, a2a_server, a2a_client):
        """测试连接恢复功能"""
        # 1. 客户端连接
        await a2a_client.connect()
        assert a2a_client.is_connected() is True
        
        # 2. 模拟连接断开
        await a2a_client.disconnect()
        assert a2a_client.is_connected() is False
        
        # 3. 重新连接
        success = await a2a_client.connect()
        assert success is True
        assert a2a_client.is_connected() is True
        
        # 4. 验证连接统计
        stats = a2a_client.get_connection_stats()
        assert stats.connection_attempts == 2
        assert stats.successful_connections == 2
        
        # 5. 断开连接
        await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_heartbeat_mechanism(self, a2a_server, a2a_client):
        """测试心跳机制"""
        # 1. 客户端连接
        await a2a_client.connect()
        
        # 2. 等待一段时间让心跳机制运行
        await asyncio.sleep(35)  # 超过30秒心跳间隔
        
        # 3. 验证心跳消息已发送
        stats = a2a_client.get_connection_stats()
        # 至少应该发送了一次心跳消息
        assert stats.total_messages_sent >= 1
        
        # 4. 断开连接
        await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_collaboration_workflow(self, a2a_server, a2a_client):
        """测试协作工作流"""
        # 1. 客户端连接
        await a2a_client.connect()
        
        # 2. 创建协作请求
        collaboration_request = CollaborationRequest(
            request_id="test_collab",
            collaboration_type=CollaborationType.SEQUENTIAL,
            task_description="测试协作任务",
            required_capabilities=["text_generation", "code_generation"],
            input_data={"text": "测试输入"},
            timeout=60
        )
        
        # 3. 发送协作请求消息
        collab_message = AgentMessage(
            message_id="collab_request",
            message_type=MessageType.COLLABORATION_REQUEST,
            sender_id="test_client",
            receiver_id="test_server",
            payload={"collaboration_request": collaboration_request.__dict__}
        )
        
        await a2a_client.send_message(collab_message, MessagePriority.HIGH)
        
        # 4. 验证消息已发送
        stats = a2a_client.get_connection_stats()
        assert stats.total_messages_sent == 1
        
        # 5. 断开连接
        await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, a2a_server, a2a_client):
        """测试错误处理"""
        # 1. 尝试发送消息到未连接的客户端
        task_message = AgentMessage(
            message_id="test_error",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_client",
            receiver_id="test_server"
        )
        
        # 2. 验证未连接时发送消息会抛出异常
        with pytest.raises(Exception, match="客户端未连接"):
            await a2a_client.send_message(task_message)
        
        # 3. 连接客户端
        await a2a_client.connect()
        
        # 4. 发送错误消息
        error_message = AgentMessage(
            message_id="error_msg",
            message_type=MessageType.ERROR,
            sender_id="test_client",
            receiver_id="test_server",
            payload={"error": {"message": "测试错误", "code": "TEST_ERROR"}}
        )
        
        await a2a_client.send_message(error_message, MessagePriority.HIGH)
        
        # 5. 断开连接
        await a2a_client.disconnect()


class TestMessageSerialization:
    """消息序列化测试"""
    
    def test_agent_message_serialization(self):
        """测试代理消息序列化"""
        # 1. 创建消息
        message = AgentMessage(
            message_id="test_serialization",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver",
            payload={"task": {"task_id": "test_task"}},
            priority=TaskPriority.NORMAL
        )
        
        # 2. 序列化为JSON
        json_str = json.dumps(message.__dict__, default=str)
        
        # 3. 反序列化
        data = json.loads(json_str)
        reconstructed_message = AgentMessage(**data)
        
        # 4. 验证消息内容
        assert reconstructed_message.message_id == message.message_id
        assert reconstructed_message.message_type == message.message_type
        assert reconstructed_message.sender_id == message.sender_id
        assert reconstructed_message.receiver_id == message.receiver_id
        assert reconstructed_message.payload == message.payload
    
    def test_collaboration_request_serialization(self):
        """测试协作请求序列化"""
        # 1. 创建协作请求
        collab_request = CollaborationRequest(
            request_id="test_collab",
            collaboration_type=CollaborationType.SEQUENTIAL,
            task_description="测试任务",
            required_capabilities=["text_generation"],
            input_data={"text": "测试输入"},
            timeout=60
        )
        
        # 2. 序列化为JSON
        json_str = json.dumps(collab_request.__dict__, default=str)
        
        # 3. 反序列化
        data = json.loads(json_str)
        
        # 4. 验证协作请求内容
        assert data["request_id"] == collab_request.request_id
        assert data["collaboration_type"] == collab_request.collaboration_type.value
        assert data["task_description"] == collab_request.task_description
        assert data["required_capabilities"] == collab_request.required_capabilities


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_message_throughput(self, a2a_server, a2a_client):
        """测试消息吞吐量"""
        # 1. 客户端连接
        await a2a_client.connect()
        
        # 2. 发送多个消息
        num_messages = 10
        start_time = time.time()
        
        for i in range(num_messages):
            message = AgentMessage(
                message_id=f"test_message_{i}",
                message_type=MessageType.TASK_REQUEST,
                sender_id="test_client",
                receiver_id="test_server",
                payload={"task": {"task_id": f"task_{i}"}}
            )
            await a2a_client.send_message(message, MessagePriority.NORMAL)
        
        end_time = time.time()
        
        # 3. 计算吞吐量
        total_time = end_time - start_time
        throughput = num_messages / total_time
        
        # 4. 验证性能指标
        assert throughput > 1  # 至少每秒1条消息
        assert a2a_client.get_queue_size() == num_messages
        
        # 5. 断开连接
        await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_latency(self, a2a_server, a2a_client):
        """测试连接延迟"""
        # 1. 测量连接时间
        start_time = time.time()
        success = await a2a_client.connect()
        end_time = time.time()
        
        # 2. 验证连接成功
        assert success is True
        
        # 3. 计算连接延迟
        connection_time = end_time - start_time
        
        # 4. 验证延迟在合理范围内
        assert connection_time < 1.0  # 连接时间应小于1秒
        
        # 5. 断开连接
        await a2a_client.disconnect()


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_connection_failure(self):
        """测试连接失败处理"""
        # 1. 创建连接到无效服务器的客户端
        client = EnhancedA2AClient("http://invalid-server:9999")
        
        # 2. 尝试连接（应该失败）
        success = await client.connect()
        
        # 3. 验证连接失败
        assert success is False
        assert client.get_connection_status() == ConnectionStatus.ERROR
        
        # 4. 验证错误统计
        stats = client.get_connection_stats()
        assert stats.connection_attempts == 1
        assert stats.successful_connections == 0
        assert stats.last_error is not None
        
        # 5. 断开连接
        await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_message_retry_mechanism(self, a2a_server, a2a_client):
        """测试消息重试机制"""
        # 1. 客户端连接
        await a2a_client.connect()
        
        # 2. 创建消息
        message = AgentMessage(
            message_id="test_retry",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_client",
            receiver_id="test_server"
        )
        
        # 3. 模拟消息发送失败（通过Mock）
        with patch.object(a2a_client, '_process_message_queue_item', 
                         side_effect=Exception("模拟发送失败")):
            # 发送消息
            await a2a_client.send_message(message, MessagePriority.NORMAL)
            
            # 等待一段时间让重试机制运行
            await asyncio.sleep(0.1)
        
        # 4. 验证重试统计
        # 注意：实际重试逻辑需要进一步验证
        
        # 5. 断开连接
        await a2a_client.disconnect()


class TestMonitoring:
    """监控测试"""
    
    @pytest.mark.asyncio
    async def test_connection_monitoring(self, a2a_server, a2a_client):
        """测试连接监控"""
        # 1. 客户端连接
        await a2a_client.connect()
        
        # 2. 验证连接状态
        assert a2a_client.is_connected() is True
        assert a2a_client.get_connection_status() == ConnectionStatus.CONNECTED
        
        # 3. 验证连接统计
        stats = a2a_client.get_connection_stats()
        assert stats.connection_attempts == 1
        assert stats.successful_connections == 1
        assert stats.last_connection_time is not None
        
        # 4. 验证队列监控
        queue_size = a2a_client.get_queue_size()
        assert queue_size == 0  # 初始队列应为空
        
        # 5. 断开连接
        await a2a_client.disconnect()
        
        # 6. 验证断开后的状态
        assert a2a_client.is_connected() is False
        assert a2a_client.get_connection_status() == ConnectionStatus.DISCONNECTED


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
