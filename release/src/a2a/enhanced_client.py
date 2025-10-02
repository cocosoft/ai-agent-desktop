"""
增强A2A客户端
改进A2A客户端连接、消息队列管理、异步消息处理等功能
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.agent_communication import AgentMessage, MessageType
from ..utils.logger import get_log_manager


class ConnectionStatus(Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class MessageQueueItem:
    """消息队列项"""
    message: AgentMessage
    priority: MessagePriority
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    callback: Optional[Callable] = None


@dataclass
class ConnectionStats:
    """连接统计"""
    total_messages_sent: int = 0
    total_messages_received: int = 0
    failed_messages: int = 0
    connection_attempts: int = 0
    successful_connections: int = 0
    total_connection_time: float = 0.0
    average_response_time: float = 0.0
    last_connection_time: Optional[datetime] = None
    last_error: Optional[str] = None


class EnhancedA2AClient:
    """增强A2A客户端"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.logger = get_log_manager().logger
        
        # 连接配置
        self.server_url = server_url
        self.connection_timeout = 30  # 秒
        self.reconnect_interval = 5  # 秒
        self.max_reconnect_attempts = 5
        
        # 连接状态
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.connection_stats = ConnectionStats()
        
        # 消息队列
        self.message_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.pending_responses: Dict[str, asyncio.Future] = {}
        
        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # 异步任务
        self.connection_task: Optional[asyncio.Task] = None
        self.message_processing_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # 连接重试
        self.reconnect_attempts = 0
        self.last_connection_attempt: Optional[datetime] = None
        
        # 注册默认消息处理器
        self._register_default_handlers()
    
    async def connect(self) -> bool:
        """连接到A2A服务器"""
        try:
            self.logger.info(f"连接到A2A服务器: {self.server_url}")
            self.connection_status = ConnectionStatus.CONNECTING
            self.connection_stats.connection_attempts += 1
            
            # TODO: 实际实现连接逻辑
            # 这里模拟连接过程
            await asyncio.sleep(0.1)  # 模拟连接延迟
            
            # 模拟连接成功
            self.connection_status = ConnectionStatus.CONNECTED
            self.connection_stats.successful_connections += 1
            self.connection_stats.last_connection_time = datetime.now()
            self.reconnect_attempts = 0
            
            # 启动消息处理任务
            self.message_processing_task = asyncio.create_task(self._message_processing_loop())
            
            # 启动心跳任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self.logger.info("A2A客户端连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"连接A2A服务器失败: {str(e)}")
            self.connection_status = ConnectionStatus.ERROR
            self.connection_stats.last_error = str(e)
            return False
    
    async def disconnect(self):
        """断开连接"""
        try:
            self.logger.info("断开A2A服务器连接")
            self.connection_status = ConnectionStatus.DISCONNECTED
            
            # 取消所有任务
            if self.message_processing_task:
                self.message_processing_task.cancel()
                try:
                    await self.message_processing_task
                except asyncio.CancelledError:
                    pass
            
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 清空消息队列
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            self.logger.info("A2A客户端已断开连接")
            
        except Exception as e:
            self.logger.error(f"断开连接失败: {str(e)}")
    
    async def send_message(self, message: AgentMessage, 
                          priority: MessagePriority = MessagePriority.NORMAL,
                          callback: Optional[Callable] = None) -> str:
        """发送消息"""
        try:
            if self.connection_status != ConnectionStatus.CONNECTED:
                raise Exception("客户端未连接")
            
            # 创建消息队列项
            queue_item = MessageQueueItem(
                message=message,
                priority=priority,
                timestamp=datetime.now(),
                callback=callback
            )
            
            # 添加到消息队列
            priority_value = priority.value
            await self.message_queue.put((priority_value, queue_item))
            
            self.logger.info(f"消息已加入队列: {message.message_type} (优先级: {priority.name})")
            return message.message_id
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            raise
    
    async def send_message_and_wait(self, message: AgentMessage,
                                   timeout: int = 30) -> Optional[AgentMessage]:
        """发送消息并等待响应"""
        try:
            # 创建响应Future
            response_future = asyncio.Future()
            self.pending_responses[message.message_id] = response_future
            
            # 发送消息
            await self.send_message(message)
            
            # 等待响应
            try:
                response = await asyncio.wait_for(response_future, timeout=timeout)
                return response
            except asyncio.TimeoutError:
                self.logger.warning(f"等待消息响应超时: {message.message_id}")
                return None
            finally:
                # 清理pending_responses
                if message.message_id in self.pending_responses:
                    del self.pending_responses[message.message_id]
                    
        except Exception as e:
            self.logger.error(f"发送消息并等待响应失败: {str(e)}")
            if message.message_id in self.pending_responses:
                del self.pending_responses[message.message_id]
            raise
    
    async def _message_processing_loop(self):
        """消息处理循环"""
        while self.connection_status == ConnectionStatus.CONNECTED:
            try:
                # 从队列获取消息
                priority, queue_item = await self.message_queue.get()
                
                # 处理消息
                await self._process_message_queue_item(queue_item)
                
                # 标记任务完成
                self.message_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"消息处理循环错误: {str(e)}")
    
    async def _process_message_queue_item(self, queue_item: MessageQueueItem):
        """处理消息队列项"""
        try:
            # TODO: 实际实现消息发送逻辑
            # 这里模拟消息发送
            self.logger.info(f"处理消息: {queue_item.message.message_type}")
            
            # 模拟网络延迟
            await asyncio.sleep(0.01)
            
            # 更新统计
            self.connection_stats.total_messages_sent += 1
            
            # 调用回调函数
            if queue_item.callback:
                try:
                    queue_item.callback(queue_item.message)
                except Exception as e:
                    self.logger.error(f"消息回调函数执行失败: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {str(e)}")
            queue_item.retry_count += 1
            
            if queue_item.retry_count < queue_item.max_retries:
                # 重新加入队列
                priority_value = queue_item.priority.value
                await self.message_queue.put((priority_value, queue_item))
                self.logger.info(f"消息重试: {queue_item.message.message_id} (重试次数: {queue_item.retry_count})")
            else:
                self.connection_stats.failed_messages += 1
                self.logger.error(f"消息发送失败，已达到最大重试次数: {queue_item.message.message_id}")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.connection_status == ConnectionStatus.CONNECTED:
            try:
                # 发送心跳消息
                heartbeat_message = AgentMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.HEARTBEAT,
                    sender_id="a2a_client",
                    receiver_id="a2a_server",
                    payload={"timestamp": datetime.now().isoformat()}
                )
                
                await self.send_message(heartbeat_message, MessagePriority.LOW)
                
                # 等待下一次心跳
                await asyncio.sleep(30)  # 30秒间隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳循环错误: {str(e)}")
                await asyncio.sleep(5)  # 错误后短暂等待
    
    async def receive_message(self, message: AgentMessage):
        """接收消息"""
        try:
            self.connection_stats.total_messages_received += 1
            
            # 检查是否是等待的响应
            if message.correlation_id and message.correlation_id in self.pending_responses:
                future = self.pending_responses[message.correlation_id]
                if not future.done():
                    future.set_result(message)
            
            # 调用消息处理器
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                self.logger.warning(f"未知消息类型，没有对应的处理器: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"接收消息处理失败: {str(e)}")
    
    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self.message_handlers[MessageType.TASK_RESULT] = self._handle_task_result
        self.message_handlers[MessageType.STATUS_UPDATE] = self._handle_status_update
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.ERROR] = self._handle_error
        self.message_handlers[MessageType.COLLABORATION_REQUEST] = self._handle_collaboration_request
        self.message_handlers[MessageType.COLLABORATION_RESPONSE] = self._handle_collaboration_response
    
    async def _handle_task_result(self, message: AgentMessage):
        """处理任务结果"""
        try:
            result_data = message.payload.get("task_result", {})
            self.logger.info(f"收到任务结果: {result_data.get('task_id')}")
            
            # TODO: 实际处理任务结果逻辑
            
        except Exception as e:
            self.logger.error(f"处理任务结果失败: {str(e)}")
    
    async def _handle_status_update(self, message: AgentMessage):
        """处理状态更新"""
        try:
            status_data = message.payload.get("status", {})
            self.logger.info(f"收到状态更新: {status_data}")
            
            # TODO: 实际处理状态更新逻辑
            
        except Exception as e:
            self.logger.error(f"处理状态更新失败: {str(e)}")
    
    async def _handle_heartbeat(self, message: AgentMessage):
        """处理心跳"""
        try:
            heartbeat_data = message.payload.get("heartbeat", {})
            self.logger.debug(f"收到心跳: {heartbeat_data}")
            
            # TODO: 实际处理心跳逻辑
            
        except Exception as e:
            self.logger.error(f"处理心跳失败: {str(e)}")
    
    async def _handle_error(self, message: AgentMessage):
        """处理错误消息"""
        try:
            error_data = message.payload.get("error", {})
            self.logger.error(f"收到错误消息: {error_data}")
            
            # TODO: 实际处理错误逻辑
            
        except Exception as e:
            self.logger.error(f"处理错误消息失败: {str(e)}")
    
    async def _handle_collaboration_request(self, message: AgentMessage):
        """处理协作请求"""
        try:
            request_data = message.payload.get("collaboration_request", {})
            self.logger.info(f"收到协作请求: {request_data.get('request_id')}")
            
            # TODO: 实际处理协作请求逻辑
            
        except Exception as e:
            self.logger.error(f"处理协作请求失败: {str(e)}")
    
    async def _handle_collaboration_response(self, message: AgentMessage):
        """处理协作响应"""
        try:
            response_data = message.payload.get("collaboration_response", {})
            self.logger.info(f"收到协作响应: {response_data.get('request_id')}")
            
            # TODO: 实际处理协作响应逻辑
            
        except Exception as e:
            self.logger.error(f"处理协作响应失败: {str(e)}")
    
    async def reconnect(self) -> bool:
        """重新连接"""
        try:
            if self.connection_status == ConnectionStatus.CONNECTED:
                await self.disconnect()
            
            self.connection_status = ConnectionStatus.RECONNECTING
            self.reconnect_attempts += 1
            
            if self.reconnect_attempts > self.max_reconnect_attempts:
                self.logger.error("已达到最大重连次数，停止重连")
                self.connection_status = ConnectionStatus.ERROR
                return False
            
            self.logger.info(f"尝试重新连接 (第 {self.reconnect_attempts} 次)")
            
            # 等待重连间隔
            await asyncio.sleep(self.reconnect_interval)
            
            # 尝试连接
            success = await self.connect()
            if success:
                self.logger.info("重连成功")
                return True
            else:
                self.logger.warning("重连失败，将继续尝试")
                return False
                
        except Exception as e:
            self.logger.error(f"重连失败: {str(e)}")
            return False
    
    def get_connection_stats(self) -> ConnectionStats:
        """获取连接统计"""
        return self.connection_stats
    
    def get_queue_size(self) -> int:
        """获取消息队列大小"""
        return self.message_queue.qsize()
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.connection_status == ConnectionStatus.CONNECTED
    
    def get_connection_status(self) -> ConnectionStatus:
        """获取连接状态"""
        return self.connection_status


# 全局A2A客户端实例
_a2a_client: Optional[EnhancedA2AClient] = None


def get_a2a_client(server_url: str = "http://localhost:8000") -> EnhancedA2AClient:
    """获取全局A2A客户端实例"""
    global _a2a_client
    if _a2a_client is None:
        _a2a_client = EnhancedA2AClient(server_url)
    return _a2a_client


async def start_a2a_client(server_url: str = "http://localhost:8000") -> EnhancedA2AClient:
    """启动A2A客户端"""
    client = get_a2a_client(server_url)
    await client.connect()
    return client


async def stop_a2a_client():
    """停止A2A客户端"""
    global _a2a_client
    if _a2a_client:
        await _a2a_client.disconnect()
        _a2a_client = None


async def send_a2a_message(message: AgentMessage, 
                          priority: MessagePriority = MessagePriority.NORMAL,
                          callback: Optional[Callable] = None) -> str:
    """发送A2A消息"""
    client = get_a2a_client()
    return await client.send_message(message, priority, callback)


async def send_a2a_message_and_wait(message: AgentMessage,
                                   timeout: int = 30) -> Optional[AgentMessage]:
    """发送A2A消息并等待响应"""
    client = get_a2a_client()
    return await client.send_message_and_wait(message, timeout)
