"""
简化的A2A通信集成测试
专注于核心通信功能的验证，避免复杂的异步fixture问题
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch

from src.a2a.enhanced_client import EnhancedA2AClient, ConnectionStatus, MessagePriority
from src.core.agent_communication import AgentMessage, MessageType
from src.core.task_router import TaskPriority


class TestSimpleCommunication:
    """简化通信测试"""
    
    @pytest.fixture
    def a2a_client(self):
        """创建A2A客户端实例"""
        return EnhancedA2AClient("http://localhost:8000")
    
    @pytest.mark.asyncio
    async def test_client_creation(self, a2a_client):
        """测试客户端创建"""
        assert a2a_client is not None
        assert a2a_client.server_url == "http://localhost:8000"
        assert a2a_client.connection_status == ConnectionStatus.DISCONNECTED
        assert a2a_client.connection_stats is not None
        assert a2a_client.message_queue is not None
    
    @pytest.mark.asyncio
    async def test_connection_simulation(self, a2a_client):
        """测试连接模拟"""
        # 使用Mock模拟连接成功
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            success = await a2a_client.connect()
            assert success is True
            assert a2a_client.connection_status == ConnectionStatus.CONNECTED
            
            # 断开连接
            await a2a_client.disconnect()
            assert a2a_client.connection_status == ConnectionStatus.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_message_sending_simulation(self, a2a_client):
        """测试消息发送模拟"""
        # 模拟连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            await a2a_client.connect()
            
            # 发送消息
            message = AgentMessage(
                message_id="test_message",
                message_type=MessageType.TASK_REQUEST,
                sender_id="test_client",
                receiver_id="test_server",
                payload={"task": {"task_id": "test_task"}}
            )
            
            message_id = await a2a_client.send_message(message, MessagePriority.NORMAL)
            assert message_id == "test_message"
            assert a2a_client.get_queue_size() == 1
            
            # 断开连接
            await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_priority_message_handling(self, a2a_client):
        """测试优先级消息处理"""
        # 模拟连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            await a2a_client.connect()
            
            # 发送不同优先级的消息
            low_priority_message = AgentMessage(
                message_id="low_priority",
                message_type=MessageType.TASK_REQUEST,
                sender_id="test_client",
                receiver_id="test_server"
            )
            
            high_priority_message = AgentMessage(
                message_id="high_priority",
                message_type=MessageType.TASK_REQUEST,
                sender_id="test_client",
                receiver_id="test_server"
            )
            
            await a2a_client.send_message(low_priority_message, MessagePriority.LOW)
            await a2a_client.send_message(high_priority_message, MessagePriority.HIGH)
            
            # 验证队列中有2条消息
            assert a2a_client.get_queue_size() == 2
            
            # 断开连接
            await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_recovery_simulation(self, a2a_client):
        """测试连接恢复模拟"""
        # 模拟连接和断开
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            # 第一次连接
            await a2a_client.connect()
            assert a2a_client.connection_status == ConnectionStatus.CONNECTED
            
            # 断开连接
            await a2a_client.disconnect()
            assert a2a_client.connection_status == ConnectionStatus.DISCONNECTED
            
            # 重新连接
            await a2a_client.connect()
            assert a2a_client.connection_status == ConnectionStatus.CONNECTED
            
            # 验证连接统计
            stats = a2a_client.get_connection_stats()
            assert stats.connection_attempts == 2
            assert stats.successful_connections == 2
            
            # 断开连接
            await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_handling_simulation(self, a2a_client):
        """测试错误处理模拟"""
        # 测试未连接时发送消息
        message = AgentMessage(
            message_id="test_error",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_client",
            receiver_id="test_server"
        )
        
        # 验证未连接时发送消息会抛出异常
        with pytest.raises(Exception, match="客户端未连接"):
            await a2a_client.send_message(message)
        
        # 模拟连接后发送错误消息
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            await a2a_client.connect()
            
            error_message = AgentMessage(
                message_id="error_msg",
                message_type=MessageType.ERROR,
                sender_id="test_client",
                receiver_id="test_server",
                payload={"error": {"message": "测试错误", "code": "TEST_ERROR"}}
            )
            
            await a2a_client.send_message(error_message, MessagePriority.HIGH)
            
            # 断开连接
            await a2a_client.disconnect()


class TestMessageSerialization:
    """消息序列化测试"""
    
    def test_agent_message_serialization(self):
        """测试代理消息序列化"""
        # 创建消息
        message = AgentMessage(
            message_id="test_serialization",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver",
            payload={"task": {"task_id": "test_task"}},
            priority=TaskPriority.NORMAL
        )
        
        # 序列化为JSON
        json_str = json.dumps(message.__dict__, default=str)
        
        # 反序列化
        data = json.loads(json_str)
        
        # 验证消息内容
        assert data["message_id"] == message.message_id
        assert data["message_type"] == message.message_type.value  # 使用value进行比较
        assert data["sender_id"] == message.sender_id
        assert data["receiver_id"] == message.receiver_id
        assert data["payload"] == message.payload
    
    def test_message_priority_serialization(self):
        """测试消息优先级序列化"""
        # 创建不同优先级的消息
        low_priority_message = AgentMessage(
            message_id="low_priority",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver",
            priority=TaskPriority.LOW
        )
        
        high_priority_message = AgentMessage(
            message_id="high_priority",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver",
            priority=TaskPriority.HIGH
        )
        
        # 验证优先级值
        assert low_priority_message.priority == TaskPriority.LOW
        assert high_priority_message.priority == TaskPriority.HIGH


class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_message_throughput_simulation(self, a2a_client):
        """测试消息吞吐量模拟"""
        # 模拟连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            await a2a_client.connect()
            
            # 发送多个消息
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
            
            # 计算吞吐量
            total_time = end_time - start_time
            throughput = num_messages / total_time
            
            # 验证性能指标
            assert throughput > 1  # 至少每秒1条消息
            assert a2a_client.get_queue_size() == num_messages
            
            # 断开连接
            await a2a_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_connection_latency_simulation(self, a2a_client):
        """测试连接延迟模拟"""
        # 测量连接时间
        start_time = time.time()
        
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            success = await a2a_client.connect()
            end_time = time.time()
            
            # 验证连接成功
            assert success is True
            
            # 计算连接延迟
            connection_time = end_time - start_time
            
            # 验证延迟在合理范围内
            assert connection_time < 1.0  # 连接时间应小于1秒
            
            # 断开连接
            await a2a_client.disconnect()


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_connection_failure_simulation(self):
        """测试连接失败处理模拟"""
        # 创建连接到无效服务器的客户端
        client = EnhancedA2AClient("http://invalid-server:9999")
        
        # 模拟连接失败
        with patch('asyncio.sleep', side_effect=Exception("连接失败")):
            success = await client.connect()
            
            # 验证连接失败
            assert success is False
            assert client.get_connection_status() == ConnectionStatus.ERROR
            
            # 验证错误统计
            stats = client.get_connection_stats()
            assert stats.connection_attempts == 1
            assert stats.successful_connections == 0
            assert stats.last_error == "连接失败"
            
            # 断开连接
            await client.disconnect()


class TestMonitoring:
    """监控测试"""
    
    @pytest.mark.asyncio
    async def test_connection_monitoring_simulation(self, a2a_client):
        """测试连接监控模拟"""
        # 模拟连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            
            await a2a_client.connect()
            
            # 验证连接状态
            assert a2a_client.is_connected() is True
            assert a2a_client.get_connection_status() == ConnectionStatus.CONNECTED
            
            # 验证连接统计
            stats = a2a_client.get_connection_stats()
            assert stats.connection_attempts == 1
            assert stats.successful_connections == 1
            assert stats.last_connection_time is not None
            
            # 验证队列监控
            queue_size = a2a_client.get_queue_size()
            assert queue_size == 0  # 初始队列应为空
            
            # 断开连接
            await a2a_client.disconnect()
            
            # 验证断开后的状态
            assert a2a_client.is_connected() is False
            assert a2a_client.get_connection_status() == ConnectionStatus.DISCONNECTED


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
