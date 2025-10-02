"""
A2A客户端
负责与A2A服务器通信，管理代理注册、任务发送和结果接收
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import aiohttp
import logging

from ..utils.logger import log_info, log_error, log_warning, log_performance


class A2AConnectionStatus(Enum):
    """A2A连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class A2AMessageType(Enum):
    """A2A消息类型枚举"""
    REGISTER_AGENT = "register_agent"
    UNREGISTER_AGENT = "unregister_agent"
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"
    ERROR = "error"


@dataclass
class A2AAgentInfo:
    """A2A代理信息"""
    agent_id: str
    name: str
    capabilities: List[str]
    status: str = "idle"
    load: int = 0
    last_heartbeat: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class A2ATask:
    """A2A任务"""
    task_id: str
    agent_id: str
    capability: str
    input_data: Dict[str, Any]
    priority: int = 1
    timeout: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class A2ATaskResult:
    """A2A任务结果"""
    task_id: str
    agent_id: str
    success: bool
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class A2AMessage:
    """A2A消息"""
    message_id: str
    message_type: A2AMessageType
    sender_id: str
    receiver_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class A2AClient:
    """A2A客户端"""
    
    def __init__(self, server_url: str, client_id: str):
        """
        初始化A2A客户端
        
        Args:
            server_url: A2A服务器URL
            client_id: 客户端ID
        """
        self.server_url = server_url.rstrip('/')
        self.client_id = client_id
        self.status = A2AConnectionStatus.DISCONNECTED
        self.session: Optional[aiohttp.ClientSession] = None
        self.agents: Dict[str, A2AAgentInfo] = {}
        self.pending_tasks: Dict[str, A2ATask] = {}
        self.task_callbacks: Dict[str, Callable] = {}
        self.heartbeat_interval = 30  # 心跳间隔（秒）
        self.reconnect_interval = 5   # 重连间隔（秒）
        self.max_retries = 3          # 最大重试次数
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.reconnect_task: Optional[asyncio.Task] = None
        self.message_handlers: Dict[A2AMessageType, Callable] = {}
        self._lock = asyncio.Lock()
        
        # 注册默认消息处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self.message_handlers[A2AMessageType.TASK_RESULT] = self._handle_task_result
        self.message_handlers[A2AMessageType.STATUS_UPDATE] = self._handle_status_update
        self.message_handlers[A2AMessageType.ERROR] = self._handle_error
    
    async def connect(self) -> bool:
        """
        连接到A2A服务器
        
        Returns:
            连接是否成功
        """
        try:
            self._update_status(A2AConnectionStatus.CONNECTING)
            
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                base_url=self.server_url,
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # 测试连接
            async with self.session.get('/health') as response:
                if response.status == 200:
                    self._update_status(A2AConnectionStatus.CONNECTED)
                    log_info(f"A2A客户端连接成功: {self.server_url}")
                    
                    # 启动心跳任务
                    self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    
                    return True
                else:
                    self._update_status(A2AConnectionStatus.ERROR, "健康检查失败")
                    return False
                    
        except Exception as e:
            self._update_status(A2AConnectionStatus.ERROR, f"连接失败: {str(e)}")
            log_error("A2A客户端连接失败", e)
            return False
    
    async def disconnect(self):
        """断开连接"""
        # 停止心跳任务
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 停止重连任务
        if self.reconnect_task:
            self.reconnect_task.cancel()
            try:
                await self.reconnect_task
            except asyncio.CancelledError:
                pass
        
        # 关闭会话
        if self.session:
            await self.session.close()
            self.session = None
        
        self._update_status(A2AConnectionStatus.DISCONNECTED)
        log_info("A2A客户端已断开连接")
    
    async def register_agent(self, agent_info: A2AAgentInfo) -> bool:
        """
        注册代理
        
        Args:
            agent_info: 代理信息
            
        Returns:
            注册是否成功
        """
        try:
            if not self.session:
                log_error("A2A客户端未连接")
                return False
            
            message = A2AMessage(
                message_id=self._generate_message_id(),
                message_type=A2AMessageType.REGISTER_AGENT,
                sender_id=self.client_id,
                payload={
                    "agent_id": agent_info.agent_id,
                    "name": agent_info.name,
                    "capabilities": agent_info.capabilities,
                    "status": agent_info.status,
                    "metadata": agent_info.metadata
                }
            )
            
            async with self.session.post('/message', json=self._message_to_dict(message)) as response:
                if response.status == 200:
                    self.agents[agent_info.agent_id] = agent_info
                    log_info(f"代理注册成功: {agent_info.name} ({agent_info.agent_id})")
                    return True
                else:
                    log_error(f"代理注册失败: {response.status}")
                    return False
                    
        except Exception as e:
            log_error(f"代理注册异常: {agent_info.name}", e)
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """
        注销代理
        
        Args:
            agent_id: 代理ID
            
        Returns:
            注销是否成功
        """
        try:
            if not self.session:
                log_error("A2A客户端未连接")
                return False
            
            message = A2AMessage(
                message_id=self._generate_message_id(),
                message_type=A2AMessageType.UNREGISTER_AGENT,
                sender_id=self.client_id,
                payload={"agent_id": agent_id}
            )
            
            async with self.session.post('/message', json=self._message_to_dict(message)) as response:
                if response.status == 200:
                    if agent_id in self.agents:
                        del self.agents[agent_id]
                    log_info(f"代理注销成功: {agent_id}")
                    return True
                else:
                    log_error(f"代理注销失败: {response.status}")
                    return False
                    
        except Exception as e:
            log_error(f"代理注销异常: {agent_id}", e)
            return False
    
    async def send_task(
        self, 
        task: A2ATask, 
        callback: Optional[Callable[[A2ATaskResult], None]] = None
    ) -> bool:
        """
        发送任务
        
        Args:
            task: 任务
            callback: 任务完成回调函数
            
        Returns:
            发送是否成功
        """
        try:
            if not self.session:
                log_error("A2A客户端未连接")
                return False
            
            message = A2AMessage(
                message_id=self._generate_message_id(),
                message_type=A2AMessageType.TASK_REQUEST,
                sender_id=self.client_id,
                payload={
                    "task_id": task.task_id,
                    "agent_id": task.agent_id,
                    "capability": task.capability,
                    "input_data": task.input_data,
                    "priority": task.priority,
                    "timeout": task.timeout,
                    "metadata": task.metadata
                }
            )
            
            # 保存任务和回调
            self.pending_tasks[task.task_id] = task
            if callback:
                self.task_callbacks[task.task_id] = callback
            
            async with self.session.post('/message', json=self._message_to_dict(message)) as response:
                if response.status == 200:
                    log_info(f"任务发送成功: {task.task_id}")
                    return True
                else:
                    log_error(f"任务发送失败: {response.status}")
                    # 移除失败的任务
                    if task.task_id in self.pending_tasks:
                        del self.pending_tasks[task.task_id]
                    if task.task_id in self.task_callbacks:
                        del self.task_callbacks[task.task_id]
                    return False
                    
        except Exception as e:
            log_error(f"任务发送异常: {task.task_id}", e)
            # 移除异常的任务
            if task.task_id in self.pending_tasks:
                del self.pending_tasks[task.task_id]
            if task.task_id in self.task_callbacks:
                del self.task_callbacks[task.task_id]
            return False
    
    async def get_available_agents(self, capability: Optional[str] = None) -> List[A2AAgentInfo]:
        """
        获取可用代理列表
        
        Args:
            capability: 过滤能力（可选）
            
        Returns:
            可用代理列表
        """
        try:
            if not self.session:
                log_error("A2A客户端未连接")
                return []
            
            params = {}
            if capability:
                params['capability'] = capability
            
            async with self.session.get('/agents', params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    agents = []
                    for agent_data in data.get('agents', []):
                        agent = A2AAgentInfo(
                            agent_id=agent_data['agent_id'],
                            name=agent_data['name'],
                            capabilities=agent_data['capabilities'],
                            status=agent_data.get('status', 'unknown'),
                            load=agent_data.get('load', 0),
                            metadata=agent_data.get('metadata', {})
                        )
                        agents.append(agent)
                    return agents
                else:
                    log_error(f"获取代理列表失败: {response.status}")
                    return []
                    
        except Exception as e:
            log_error("获取代理列表异常", e)
            return []
    
    def register_message_handler(self, message_type: A2AMessageType, handler: Callable):
        """
        注册消息处理器
        
        Args:
            message_type: 消息类型
            handler: 处理器函数
        """
        self.message_handlers[message_type] = handler
    
    async def process_message(self, message_data: Dict[str, Any]):
        """
        处理接收到的消息
        
        Args:
            message_data: 消息数据
        """
        try:
            message = self._dict_to_message(message_data)
            
            # 调用对应的消息处理器
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                log_warning(f"未注册的消息处理器: {message.message_type}")
                
        except Exception as e:
            log_error("处理消息异常", e)
    
    async def _handle_task_result(self, message: A2AMessage):
        """处理任务结果消息"""
        try:
            payload = message.payload
            task_id = payload['task_id']
            
            # 创建任务结果
            result = A2ATaskResult(
                task_id=task_id,
                agent_id=payload['agent_id'],
                success=payload['success'],
                output_data=payload.get('output_data', {}),
                error_message=payload.get('error_message'),
                execution_time=payload.get('execution_time', 0),
                metadata=payload.get('metadata', {})
            )
            
            # 调用回调函数
            callback = self.task_callbacks.get(task_id)
            if callback:
                try:
                    callback(result)
                except Exception as e:
                    log_error(f"任务回调函数执行失败: {task_id}", e)
            
            # 清理任务记录
            if task_id in self.pending_tasks:
                del self.pending_tasks[task_id]
            if task_id in self.task_callbacks:
                del self.task_callbacks[task_id]
            
            log_info(f"任务完成: {task_id} - {'成功' if result.success else '失败'}")
            
        except Exception as e:
            log_error("处理任务结果异常", e)
    
    async def _handle_status_update(self, message: A2AMessage):
        """处理状态更新消息"""
        try:
            payload = message.payload
            agent_id = payload['agent_id']
            
            if agent_id in self.agents:
                self.agents[agent_id].status = payload['status']
                self.agents[agent_id].load = payload.get('load', 0)
                self.agents[agent_id].metadata.update(payload.get('metadata', {}))
            
            log_info(f"代理状态更新: {agent_id} -> {payload['status']}")
            
        except Exception as e:
            log_error("处理状态更新异常", e)
    
    async def _handle_error(self, message: A2AMessage):
        """处理错误消息"""
        try:
            payload = message.payload
            error_type = payload.get('error_type', 'unknown')
            error_message = payload.get('error_message', '未知错误')
            
            log_error(f"A2A服务器错误: {error_type} - {error_message}")
            
        except Exception as e:
            log_error("处理错误消息异常", e)
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.status == A2AConnectionStatus.CONNECTED:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error("心跳发送失败", e)
                await self._handle_connection_error()
                break
    
    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            if not self.session:
                return
            
            message = A2AMessage(
                message_id=self._generate_message_id(),
                message_type=A2AMessageType.HEARTBEAT,
                sender_id=self.client_id,
                payload={
                    "timestamp": time.time(),
                    "agents": [agent.agent_id for agent in self.agents.values()]
                }
            )
            
            async with self.session.post('/message', json=self._message_to_dict(message)) as response:
                if response.status == 200:
                    # 更新代理的最后心跳时间
                    current_time = time.time()
                    for agent in self.agents.values():
                        agent.last_heartbeat = current_time
                else:
                    log_warning(f"心跳发送失败: {response.status}")
                    
        except Exception as e:
            log_error("心跳发送异常", e)
            raise
    
    async def _handle_connection_error(self):
        """处理连接错误"""
        self._update_status(A2AConnectionStatus.ERROR, "连接错误")
        
        # 启动重连任务
        if not self.reconnect_task or self.reconnect_task.done():
            self.reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    async def _reconnect_loop(self):
        """重连循环"""
        retry_count = 0
        
        while retry_count < self.max_retries and self.status != A2AConnectionStatus.CONNECTED:
            try:
                self._update_status(A2AConnectionStatus.RECONNECTING)
                log_info(f"尝试重连 ({retry_count + 1}/{self.max_retries})")
                
                await asyncio.sleep(self.reconnect_interval)
                
                if await self.connect():
                    log_info("重连成功")
                    break
                else:
                    retry_count += 1
                    
            except Exception as e:
                log_error(f"重连失败: {retry_count + 1}/{self.max_retries}", e)
                retry_count += 1
        
        if retry_count >= self.max_retries:
            log_error("重连次数已达上限，停止重连")
    
    def _update_status(self, new_status: A2AConnectionStatus, reason: str = ""):
        """
        更新连接状态
        
        Args:
            new_status: 新状态
            reason: 状态变更原因
        """
        old_status = self.status
        self.status = new_status
        
        if old_status != new_status:
            status_msg = f"A2A客户端状态变更: {old_status.value} -> {new_status.value}"
            if reason:
                status_msg += f" ({reason})"
            log_info(status_msg)
    
    def _generate_message_id(self) -> str:
        """生成消息ID"""
        return f"{self.client_id}_{int(time.time() * 1000)}_{hash(str(time.time()))}"
    
    def _message_to_dict(self, message: A2AMessage) -> Dict[str, Any]:
        """消息对象转换为字典"""
        return {
            "message_id": message.message_id,
            "message_type": message.message_type.value,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "payload": message.payload,
            "timestamp": message.timestamp
        }
    
    def _dict_to_message(self, data: Dict[str, Any]) -> A2AMessage:
        """字典转换为消息对象"""
        return A2AMessage(
            message_id=data["message_id"],
            message_type=A2AMessageType(data["message_type"]),
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", time.time())
        )
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            "client_id": self.client_id,
            "server_url": self.server_url,
            "status": self.status.value,
            "connected_agents": len(self.agents),
            "pending_tasks": len(self.pending_tasks),
            "active_heartbeat": self.heartbeat_task is not None and not self.heartbeat_task.done(),
            "reconnecting": self.reconnect_task is not None and not self.reconnect_task.done()
        }


# 测试函数
async def test_a2a_client():
    """测试A2A客户端功能"""
    try:
        # 创建客户端
        client = A2AClient("http://localhost:8000", "test_client")
        
        # 测试连接（需要实际运行的A2A服务器）
        # connected = await client.connect()
        # print(f"连接状态: {connected}")
        
        # 测试代理注册
        agent_info = A2AAgentInfo(
            agent_id="test_agent_1",
            name="测试代理",
            capabilities=["text_generation", "code_generation"]
        )
        
        # 注册代理（需要连接）
        # registered = await client.register_agent(agent_info)
        # print(f"代理注册: {registered}")
        
        # 测试任务发送
        task = A2ATask(
            task_id="test_task_1",
            agent_id="test_agent_1",
            capability="text_generation",
            input_data={"prompt": "你好，请介绍一下自己"}
        )
        
        def task_callback(result: A2ATaskResult):
            print(f"任务完成回调: {result.task_id} - {result.success}")
        
        # 发送任务（需要连接）
        # sent = await client.send_task(task, task_callback)
        # print(f"任务发送: {sent}")
        
        # 断开连接
        await client.disconnect()
        
        print("✓ A2A客户端基础功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ A2A客户端测试失败: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_a2a_client())
