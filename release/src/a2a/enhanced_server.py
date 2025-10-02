"""
增强的A2A服务器
提供代理注册发现、心跳检测、状态同步等高级功能
"""

import asyncio
import datetime
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.agent_execution.context import RequestContext
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCard,
    Message,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
    Part,
    AgentCapabilities
)
from a2a.utils.message import new_agent_text_message

from ..core.agent_model import AgentRegistry, AgentInstance, AgentStatus
from ..utils.logger import get_log_manager


class AgentConnectionStatus(Enum):
    """代理连接状态"""
    CONNECTED = "connected"      # 已连接
    DISCONNECTED = "disconnected"  # 已断开
    HEARTBEAT_LOST = "heartbeat_lost"  # 心跳丢失


@dataclass
class RegisteredAgent:
    """已注册代理信息"""
    agent_id: str
    instance_id: str
    agent_card: AgentCard
    connection_status: AgentConnectionStatus
    last_heartbeat: datetime.datetime
    capabilities: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime.datetime = field(default_factory=datetime.datetime.now)


class EnhancedA2AServer:
    """增强的A2A服务器"""
    
    def __init__(self, agent_registry: AgentRegistry, host: str = "0.0.0.0", port: int = 8000):
        self.agent_registry = agent_registry
        self.host = host
        self.port = port
        self.logger = get_log_manager().logger
        
        # 代理注册表
        self.registered_agents: Dict[str, RegisteredAgent] = {}
        
        # 心跳检测配置
        self.heartbeat_interval = 30  # 秒
        self.heartbeat_timeout = 60   # 秒
        
        # 任务存储
        self.task_store = InMemoryTaskStore()
        
        # 事件队列
        self.event_queue = EventQueue()
        
        # 服务器状态
        self.running = False
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动服务器"""
        try:
            self.logger.info(f"启动增强A2A服务器: {self.host}:{self.port}")
            
            # 创建FastAPI应用
            self.app = self._create_fastapi_app()
            
            # 启动心跳检测
            self.running = True
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            self.logger.info("增强A2A服务器启动成功")
            
        except Exception as e:
            self.logger.error(f"启动增强A2A服务器失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止服务器"""
        try:
            self.logger.info("停止增强A2A服务器...")
            
            # 停止心跳检测
            self.running = False
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 断开所有代理连接
            for agent_id in list(self.registered_agents.keys()):
                await self._disconnect_agent(agent_id)
            
            self.logger.info("增强A2A服务器已停止")
            
        except Exception as e:
            self.logger.error(f"停止增强A2A服务器失败: {str(e)}")
    
    def _create_fastapi_app(self):
        """创建FastAPI应用"""
        # 创建默认代理执行器
        agent_executor = EnhancedAgentExecutor(self)
        
        # 创建请求处理器
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=self.task_store
        )
        
        # 创建服务器代理卡片
        server_agent_card = self._create_server_agent_card()
        
        # 创建FastAPI应用
        app = A2AFastAPIApplication(
            agent_card=server_agent_card,
            http_handler=request_handler
        ).build(
            title="增强A2A服务器",
            description="支持代理注册发现、心跳检测、状态同步的A2A服务器",
            version="1.0.0"
        )
        
        # 添加自定义端点
        self._add_custom_endpoints(app)
        
        return app
    
    def _create_server_agent_card(self) -> AgentCard:
        """创建服务器代理卡片"""
        return AgentCard(
            name="增强A2A服务器",
            version="1.0.0",
            description="支持代理注册发现、心跳检测、状态同步的A2A服务器",
            url=f"http://{self.host}:{self.port}/",
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=True,
            ),
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            skills=[
                {
                    "id": "agent_management",
                    "name": "代理管理",
                    "description": "代理注册、发现、状态监控",
                    "tags": ["management", "discovery"]
                },
                {
                    "id": "task_routing",
                    "name": "任务路由",
                    "description": "智能任务分配和路由",
                    "tags": ["routing", "load_balancing"]
                }
            ]
        )
    
    def _add_custom_endpoints(self, app):
        """添加自定义端点"""
        
        @app.get("/api/agents")
        async def list_agents():
            """列出所有已注册代理"""
            agents = []
            for agent in self.registered_agents.values():
                agents.append({
                    "agent_id": agent.agent_id,
                    "instance_id": agent.instance_id,
                    "name": agent.agent_card.name,
                    "connection_status": agent.connection_status.value,
                    "last_heartbeat": agent.last_heartbeat.isoformat(),
                    "capabilities": agent.capabilities,
                    "registered_at": agent.registered_at.isoformat()
                })
            return {"agents": agents}
        
        @app.get("/api/agents/{agent_id}")
        async def get_agent(agent_id: str):
            """获取代理详情"""
            agent = self.registered_agents.get(agent_id)
            if not agent:
                return {"error": "代理未找到"}, 404
            
            return {
                "agent_id": agent.agent_id,
                "instance_id": agent.instance_id,
                "agent_card": {
                    "name": agent.agent_card.name,
                    "description": agent.agent_card.description,
                    "capabilities": agent.agent_card.capabilities.dict(),
                    "skills": agent.agent_card.skills
                },
                "connection_status": agent.connection_status.value,
                "last_heartbeat": agent.last_heartbeat.isoformat(),
                "capabilities": agent.capabilities,
                "metadata": agent.metadata,
                "registered_at": agent.registered_at.isoformat()
            }
        
        @app.post("/api/agents/{agent_id}/heartbeat")
        async def receive_heartbeat(agent_id: str):
            """接收代理心跳"""
            agent = self.registered_agents.get(agent_id)
            if not agent:
                return {"error": "代理未注册"}, 404
            
            # 更新心跳时间
            agent.last_heartbeat = datetime.datetime.now()
            agent.connection_status = AgentConnectionStatus.CONNECTED
            
            self.logger.debug(f"收到代理 {agent_id} 的心跳")
            return {"status": "ok", "timestamp": agent.last_heartbeat.isoformat()}
        
        @app.get("/api/system/status")
        async def get_system_status():
            """获取系统状态"""
            total_agents = len(self.registered_agents)
            connected_agents = len([
                a for a in self.registered_agents.values() 
                if a.connection_status == AgentConnectionStatus.CONNECTED
            ])
            
            return {
                "server_status": "running",
                "total_agents": total_agents,
                "connected_agents": connected_agents,
                "disconnected_agents": total_agents - connected_agents,
                "heartbeat_interval": self.heartbeat_interval,
                "heartbeat_timeout": self.heartbeat_timeout
            }
    
    async def register_agent(self, agent_id: str, instance_id: str, agent_card: AgentCard, 
                           capabilities: List[str], metadata: Dict[str, Any] = None) -> bool:
        """注册代理"""
        try:
            if agent_id in self.registered_agents:
                self.logger.warning(f"代理 {agent_id} 已注册")
                return False
            
            registered_agent = RegisteredAgent(
                agent_id=agent_id,
                instance_id=instance_id,
                agent_card=agent_card,
                connection_status=AgentConnectionStatus.CONNECTED,
                last_heartbeat=datetime.datetime.now(),
                capabilities=capabilities,
                metadata=metadata or {}
            )
            
            self.registered_agents[agent_id] = registered_agent
            
            self.logger.info(f"代理 {agent_id} 注册成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注册代理 {agent_id} 失败: {str(e)}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销代理"""
        try:
            if agent_id not in self.registered_agents:
                self.logger.warning(f"代理 {agent_id} 未注册")
                return False
            
            del self.registered_agents[agent_id]
            
            self.logger.info(f"代理 {agent_id} 注销成功")
            return True
            
        except Exception as e:
            self.logger.error(f"注销代理 {agent_id} 失败: {str(e)}")
            return False
    
    async def _heartbeat_monitor(self):
        """心跳检测监控"""
        while self.running:
            try:
                current_time = datetime.datetime.now()
                
                for agent_id, agent in list(self.registered_agents.items()):
                    time_since_heartbeat = (current_time - agent.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > self.heartbeat_timeout:
                        # 心跳超时，标记为断开连接
                        if agent.connection_status != AgentConnectionStatus.DISCONNECTED:
                            agent.connection_status = AgentConnectionStatus.DISCONNECTED
                            self.logger.warning(f"代理 {agent_id} 心跳丢失，标记为断开连接")
                    
                    elif time_since_heartbeat > self.heartbeat_interval:
                        # 心跳延迟，标记为心跳丢失
                        if agent.connection_status == AgentConnectionStatus.CONNECTED:
                            agent.connection_status = AgentConnectionStatus.HEARTBEAT_LOST
                            self.logger.warning(f"代理 {agent_id} 心跳延迟")
                
                # 每10秒检查一次
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"心跳检测监控错误: {str(e)}")
                await asyncio.sleep(10)
    
    async def check_heartbeat_once(self):
        """执行一次心跳检查（用于测试）"""
        current_time = datetime.datetime.now()
        
        for agent_id, agent in list(self.registered_agents.items()):
            time_since_heartbeat = (current_time - agent.last_heartbeat).total_seconds()
            
            if time_since_heartbeat > self.heartbeat_timeout:
                # 心跳超时，标记为断开连接
                if agent.connection_status != AgentConnectionStatus.DISCONNECTED:
                    agent.connection_status = AgentConnectionStatus.DISCONNECTED
                    self.logger.warning(f"代理 {agent_id} 心跳丢失，标记为断开连接")
            
            elif time_since_heartbeat > self.heartbeat_interval:
                # 心跳延迟，标记为心跳丢失
                if agent.connection_status == AgentConnectionStatus.CONNECTED:
                    agent.connection_status = AgentConnectionStatus.HEARTBEAT_LOST
                    self.logger.warning(f"代理 {agent_id} 心跳延迟")
    
    async def _disconnect_agent(self, agent_id: str):
        """断开代理连接"""
        agent = self.registered_agents.get(agent_id)
        if agent:
            agent.connection_status = AgentConnectionStatus.DISCONNECTED
            self.logger.info(f"代理 {agent_id} 已断开连接")
    
    def get_connected_agents(self) -> List[RegisteredAgent]:
        """获取已连接的代理"""
        return [
            agent for agent in self.registered_agents.values()
            if agent.connection_status == AgentConnectionStatus.CONNECTED
        ]
    
    def get_agents_by_capability(self, capability: str) -> List[RegisteredAgent]:
        """根据能力获取代理"""
        return [
            agent for agent in self.registered_agents.values()
            if capability in agent.capabilities and 
            agent.connection_status == AgentConnectionStatus.CONNECTED
        ]


class EnhancedAgentExecutor(AgentExecutor):
    """增强的代理执行器"""
    
    def __init__(self, server: EnhancedA2AServer):
        self.server = server
        self.logger = get_log_manager().logger
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """执行代理逻辑"""
        try:
            message = context.message
            
            # 提取用户消息
            user_text = ""
            for part in message.parts:
                if hasattr(part, 'text') and part.text:
                    user_text = part.text
                    break
            
            # 智能路由逻辑
            if "状态" in user_text or "status" in user_text.lower():
                response_text = await self._handle_status_request()
            elif "代理" in user_text or "agent" in user_text.lower():
                response_text = await self._handle_agent_request()
            elif "帮助" in user_text or "help" in user_text.lower():
                response_text = self._handle_help_request()
            else:
                response_text = f"我收到了你的消息：'{user_text}'。这是增强A2A服务器的响应。"
            
            # 创建响应消息
            response_message = new_agent_text_message(response_text)
            
            # 发布消息到事件队列
            await event_queue.enqueue_event(response_message)
            
            # 创建并发布任务完成事件
            task = Task(
                id=context.task_id,
                context_id=context.context_id,
                messages=[message, response_message],
                status=TaskStatus(state=TaskState.completed)
            )
            await event_queue.enqueue_event(task)
            
        except Exception as e:
            self.logger.error(f"代理执行错误: {e}")
            # 发布错误状态
            task = Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.failed)
            )
            await event_queue.enqueue_event(task)
    
    async def _handle_status_request(self) -> str:
        """处理状态请求"""
        connected_agents = self.server.get_connected_agents()
        total_agents = len(self.server.registered_agents)
        
        status_info = f"系统状态:\n"
        status_info += f"- 总代理数: {total_agents}\n"
        status_info += f"- 已连接代理: {len(connected_agents)}\n"
        status_info += f"- 服务器运行时间: 正常\n"
        
        if connected_agents:
            status_info += "\n已连接代理:\n"
            for agent in connected_agents:
                status_info += f"- {agent.agent_card.name} ({agent.agent_id})\n"
        
        return status_info
    
    async def _handle_agent_request(self) -> str:
        """处理代理请求"""
        agents = self.server.registered_agents.values()
        
        if not agents:
            return "当前没有注册的代理。"
        
        response = "已注册代理:\n"
        for agent in agents:
            status_emoji = "🟢" if agent.connection_status == AgentConnectionStatus.CONNECTED else "🔴"
            response += f"{status_emoji} {agent.agent_card.name} - {agent.connection_status.value}\n"
            if agent.capabilities:
                response += f"   能力: {', '.join(agent.capabilities)}\n"
        
        return response
    
    def _handle_help_request(self) -> str:
        """处理帮助请求"""
        help_text = """
增强A2A服务器帮助:

可用命令:
- "状态" 或 "status" - 查看系统状态
- "代理" 或 "agent" - 查看代理列表
- "帮助" 或 "help" - 显示此帮助信息

服务器特性:
- 代理注册发现
- 心跳检测监控
- 状态同步
- 智能任务路由
- 负载均衡

支持的协议:
- A2A (Agent-to-Agent)
- JSON-RPC
- HTTP REST API
"""
        return help_text.strip()
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """取消任务"""
        try:
            # 发布任务取消状态
            task = Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.canceled)
            )
            await event_queue.enqueue_event(task)
        except Exception as e:
            self.logger.error(f"取消任务错误: {e}")


# 全局服务器实例
_enhanced_server: Optional[EnhancedA2AServer] = None


def get_enhanced_server(agent_registry: AgentRegistry, host: str = "0.0.0.0", port: int = 8000) -> EnhancedA2AServer:
    """获取全局增强A2A服务器实例"""
    global _enhanced_server
    if _enhanced_server is None:
        _enhanced_server = EnhancedA2AServer(agent_registry, host, port)
    return _enhanced_server


async def start_enhanced_server(agent_registry: AgentRegistry, host: str = "0.0.0.0", port: int = 8000):
    """启动增强A2A服务器"""
    server = get_enhanced_server(agent_registry, host, port)
    await server.start()
    return server


async def stop_enhanced_server():
    """停止增强A2A服务器"""
    global _enhanced_server
    if _enhanced_server:
        await _enhanced_server.stop()
        _enhanced_server = None
