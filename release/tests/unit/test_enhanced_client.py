"""
增强A2A客户端单元测试
测试A2A客户端连接、消息队列管理、异步消息处理等功能
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any
from datetime import datetime

from src.a2a.enhanced_client import (
    EnhancedA2AClient, ConnectionStatus, MessagePriority, MessageQueueItem,
    ConnectionStats, get_a2a_client, start_a2a_client, stop_a2a_client
)
from src.core.agent_communication import AgentMessage, MessageType


class TestEnhancedA2AClient:
    """增强A2A客户端测试"""
    
    @pytest.fixture
    def a2a_client(self):
        """创建A2A客户端实例"""
        return EnhancedA2AClient("http://localhost:8000")
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return AgentMessage(
            message_id="test_message",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver",
            payload={"task": {"task_id": "test_task"}}
        )
    
    def test_a2a_client_creation(self, a2a_client):
        """测试A2A客户端创建"""
        assert a2a_client is not None
        assert a2a_client.server_url == "http://localhost:8000"
        assert a2a_client.connection_status == ConnectionStatus.DISCONNECTED
        assert a2a_client.connection_stats is not None
        assert a2a_client.message_queue is not None
        assert len(a2a_client.message_handlers) == 6  # 6种消息类型
        assert a2a_client.reconnect_attempts == 0
    
    @pytest.mark.asyncio
    async def test_connect_success(self, a2a_client):
        """测试成功连接"""
        with patch.object(a2a_client, '_message_processing_loop') as mock_processing, \
             patch.object(a2a_client, '_heartbeat_loop') as mock_heartbeat:
            
            success = await a2a_client.connect()
            
            assert success is True
            assert a2a_client.connection_status == ConnectionStatus.CONNECTED
            assert a2a_client.connection_stats.connection_attempts == 1
            assert a2a_client.connection_stats.successful_connections == 1
            assert a2a_client.reconnect_attempts == 0
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, a2a_client):
        """测试连接失败"""
        with patch('asyncio.sleep', side_effect=Exception("连接失败")):
            success = await a2a_client.connect()
            
            assert success is False
            assert a2a_client.connection_status == ConnectionStatus.ERROR
            assert a2a_client.connection_stats.connection_attempts == 1
            assert a2a_client.connection_stats.successful_connections == 0
            assert a2a_client.connection_stats.last_error == "连接失败"
    
    @pytest.mark.asyncio
    async def test_disconnect(self, a2a_client):
        """测试断开连接"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 然后断开连接
        await a2a_client.disconnect()
        
        assert a2a_client.connection_status == ConnectionStatus.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_send_message(self, a2a_client, sample_message):
        """测试发送消息"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        message_id = await a2a_client.send_message(sample_message, MessagePriority.NORMAL)
        
        assert message_id == sample_message.message_id
        assert a2a_client.message_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, a2a_client, sample_message):
        """测试未连接时发送消息"""
        with pytest.raises(Exception, match="客户端未连接"):
            await a2a_client.send_message(sample_message)
    
    @pytest.mark.asyncio
    async def test_send_message_and_wait(self, a2a_client, sample_message):
        """测试发送消息并等待响应"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 模拟响应
        response_message = AgentMessage(
            message_id="response_message",
            message_type=MessageType.TASK_RESULT,
            sender_id="test_receiver",
            receiver_id="test_sender",
            correlation_id=sample_message.message_id,
            payload={"task_result": {"task_id": "test_task", "success": True}}
        )
        
        # 在后台设置响应
        async def set_response():
            await asyncio.sleep(0.1)
            await a2a_client.receive_message(response_message)
        
        asyncio.create_task(set_response())
        
        # 发送消息并等待响应
        response = await a2a_client.send_message_and_wait(sample_message, timeout=5)
        
        assert response is not None
        assert response.message_id == "response_message"
        assert response.message_type == MessageType.TASK_RESULT
    
    @pytest.mark.asyncio
    async def test_send_message_and_wait_timeout(self, a2a_client, sample_message):
        """测试发送消息并等待响应超时"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 发送消息并等待响应（应该超时）
        response = await a2a_client.send_message_and_wait(sample_message, timeout=0.1)
        
        assert response is None
    
    @pytest.mark.asyncio
    async def test_receive_message(self, a2a_client, sample_message):
        """测试接收消息"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 修改消息类型为任务结果
        sample_message.message_type = MessageType.TASK_RESULT
        
        await a2a_client.receive_message(sample_message)
        
        assert a2a_client.connection_stats.total_messages_received == 1
    
    @pytest.mark.asyncio
    async def test_receive_message_with_correlation(self, a2a_client):
        """测试接收关联消息"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 创建原始消息
        original_message = AgentMessage(
            message_id="original_message",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver"
        )
        
        # 创建响应消息
        response_message = AgentMessage(
            message_id="response_message",
            message_type=MessageType.TASK_RESULT,
            sender_id="test_receiver",
            receiver_id="test_sender",
            correlation_id="original_message"
        )
        
        # 设置pending response
        response_future = asyncio.Future()
        a2a_client.pending_responses["original_message"] = response_future
        
        # 接收响应消息
        await a2a_client.receive_message(response_message)
        
        # 验证future已完成
        assert response_future.done()
        assert response_future.result() == response_message
    
    @pytest.mark.asyncio
    async def test_message_processing_loop(self, a2a_client):
        """测试消息处理循环"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 添加消息到队列
        message = AgentMessage(
            message_id="test_message",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver"
        )
        
        queue_item = MessageQueueItem(
            message=message,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now()
        )
        
        await a2a_client.message_queue.put((MessagePriority.NORMAL.value, queue_item))
        
        # 处理消息
        await a2a_client._process_message_queue_item(queue_item)
        
        assert a2a_client.connection_stats.total_messages_sent == 1
    
    @pytest.mark.asyncio
    async def test_message_retry(self, a2a_client):
        """测试消息重试"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        message = AgentMessage(
            message_id="test_message",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver"
        )
        
        queue_item = MessageQueueItem(
            message=message,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            retry_count=0,
            max_retries=3
        )
        
        # 模拟处理失败
        with patch.object(a2a_client, '_process_message_queue_item', 
                         side_effect=Exception("处理失败")):
            await a2a_client._process_message_queue_item(queue_item)
        
        # 验证消息已重试
        assert queue_item.retry_count == 1
        assert a2a_client.message_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_message_max_retries(self, a2a_client):
        """测试消息最大重试次数"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        message = AgentMessage(
            message_id="test_message",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver"
        )
        
        queue_item = MessageQueueItem(
            message=message,
            priority=MessagePriority.NORMAL,
            timestamp=datetime.now(),
            retry_count=2,  # 已经重试2次
            max_retries=3
        )
        
        # 模拟处理失败
        with patch.object(a2a_client, '_process_message_queue_item', 
                         side_effect=Exception("处理失败")):
            await a2a_client._process_message_queue_item(queue_item)
        
        # 验证消息已达到最大重试次数
        assert queue_item.retry_count == 3
        assert a2a_client.connection_stats.failed_messages == 1
    
    @pytest.mark.asyncio
    async def test_heartbeat_loop(self, a2a_client):
        """测试心跳循环"""
        # 先连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        with patch.object(a2a_client, 'send_message') as mock_send:
            # 运行一次心跳
            await a2a_client._heartbeat_loop()
            
            # 验证发送了心跳消息
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            assert sent_message.message_type == MessageType.HEARTBEAT
            assert sent_message.sender_id == "a2a_client"
            assert sent_message.receiver_id == "a2a_server"
    
    @pytest.mark.asyncio
    async def test_reconnect_success(self, a2a_client):
        """测试成功重连"""
        # 模拟连接失败
        a2a_client.connection_status = ConnectionStatus.ERROR
        a2a_client.reconnect_attempts = 1
        
        with patch.object(a2a_client, 'connect', return_value=True):
            success = await a2a_client.reconnect()
            
            assert success is True
            assert a2a_client.reconnect_attempts == 1  # 重连成功后重置
    
    @pytest.mark.asyncio
    async def test_reconnect_failure(self, a2a_client):
        """测试重连失败"""
        # 模拟连接失败
        a2a_client.connection_status = ConnectionStatus.ERROR
        a2a_client.reconnect_attempts = 1
        
        with patch.object(a2a_client, 'connect', return_value=False):
            success = await a2a_client.reconnect()
            
            assert success is False
            assert a2a_client.reconnect_attempts == 2
    
    @pytest.mark.asyncio
    async def test_reconnect_max_attempts(self, a2a_client):
        """测试最大重连次数"""
        # 模拟已达到最大重连次数
        a2a_client.connection_status = ConnectionStatus.ERROR
        a2a_client.reconnect_attempts = 5  # 最大重连次数为5
        
        success = await a2a_client.reconnect()
        
        assert success is False
        assert a2a_client.connection_status == ConnectionStatus.ERROR
    
    def test_get_connection_stats(self, a2a_client):
        """测试获取连接统计"""
        stats = a2a_client.get_connection_stats()
        
        assert isinstance(stats, ConnectionStats)
        assert stats.total_messages_sent == 0
        assert stats.total_messages_received == 0
        assert stats.failed_messages == 0
    
    def test_get_queue_size(self, a2a_client):
        """测试获取队列大小"""
        queue_size = a2a_client.get_queue_size()
        
        assert queue_size == 0
    
    def test_is_connected(self, a2a_client):
        """测试检查连接状态"""
        # 初始状态未连接
        assert a2a_client.is_connected() is False
        
        # 模拟连接状态
        a2a_client.connection_status = ConnectionStatus.CONNECTED
        assert a2a_client.is_connected() is True
    
    def test_get_connection_status(self, a2a_client):
        """测试获取连接状态"""
        status = a2a_client.get_connection_status()
        
        assert status == ConnectionStatus.DISCONNECTED


class TestGlobalFunctions:
    """全局函数测试"""
    
    def test_get_a2a_client(self):
        """测试获取全局A2A客户端"""
        client1 = get_a2a_client()
        client2 = get_a2a_client()
        
        assert client1 is not None
        assert client2 is not None
        assert client1 is client2  # 应该是同一个实例
    
    @pytest.mark.asyncio
    async def test_start_stop_a2a_client(self):
        """测试启动和停止全局A2A客户端"""
        # 使用Mock来避免实际启动客户端
        with patch('src.a2a.enhanced_client.EnhancedA2AClient.connect') as mock_connect, \
             patch('src.a2a.enhanced_client.EnhancedA2AClient.disconnect') as mock_disconnect:
            
            # 测试启动
            await start_a2a_client()
            mock_connect.assert_called_once()
            
            # 测试停止
            await stop_a2a_client()
            mock_disconnect.assert_called_once()


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def a2a_client(self):
        """创建A2A客户端实例"""
        return EnhancedA2AClient("http://localhost:8000")
    
    @pytest.mark.asyncio
    async def test_complete_message_workflow(self, a2a_client):
        """测试完整消息工作流"""
        # 1. 连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 2. 发送消息
        message = AgentMessage(
            message_id="workflow_message",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver",
            payload={"task": {"task_id": "workflow_task"}}
        )
        
        message_id = await a2a_client.send_message(message, MessagePriority.HIGH)
        
        # 3. 验证消息已加入队列
        assert message_id == "workflow_message"
        assert a2a_client.get_queue_size() == 1
        
        # 4. 接收响应
        response_message = AgentMessage(
            message_id="response_message",
            message_type=MessageType.TASK_RESULT,
            sender_id="test_receiver",
            receiver_id="test_sender",
            correlation_id="workflow_message",
            payload={"task_result": {"task_id": "workflow_task", "success": True}}
        )
        
        await a2a_client.receive_message(response_message)
        
        # 5. 验证统计
        stats = a2a_client.get_connection_stats()
        assert stats.total_messages_sent == 1
        assert stats.total_messages_received == 1
    
    @pytest.mark.asyncio
    async def test_priority_message_processing(self, a2a_client):
        """测试优先级消息处理"""
        # 1. 连接
        with patch.object(a2a_client, '_message_processing_loop'), \
             patch.object(a2a_client, '_heartbeat_loop'):
            await a2a_client.connect()
        
        # 2. 发送不同优先级的消息
        low_priority_message = AgentMessage(
            message_id="low_priority",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver"
        )
        
        high_priority_message = AgentMessage(
            message_id="high_priority",
            message_type=MessageType.TASK_REQUEST,
            sender_id="test_sender",
            receiver_id="test_receiver"
        )
        
        # 先发送低优先级消息
        await a2a_client.send_message(low_priority_message, MessagePriority.LOW)
        
        # 然后发送高优先级消息
        await a2a_client.send_message(high_priority_message, MessagePriority.HIGH)
        
        # 3. 验证队列中有2条消息
        assert a2a_client.get_queue_size() == 2
        
        # 4. 验证优先级处理（高优先级应该先处理）
        # 注意：实际优先级队列处理需要检查实现细节
        # 这里主要验证消息已正确加入队列


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
