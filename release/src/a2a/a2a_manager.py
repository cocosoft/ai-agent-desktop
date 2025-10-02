"""
A2A管理器
统一管理多个A2A客户端连接，提供简化的API接口
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .a2a_client import A2AClient, A2AAgentInfo, A2ATask, A2ATaskResult, A2AMessageType
from ..utils.logger import log_info, log_error, log_warning, log_performance


class A2AManagerStatus(Enum):
    """A2A管理器状态枚举"""
    INITIALIZED = "initialized"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class A2AServerConfig:
    """A2A服务器配置"""
    server_id: str
    server_url: str
    client_id: str
    enabled: bool = True
    priority: int = 1
    timeout: int = 30
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class A2AManagerStats:
    """A2A管理器统计信息"""
    total_servers: int = 0
    connected_servers: int = 0
    total_agents: int = 0
    total_tasks_sent: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    average_response_time: float = 0.0
    last_activity_time: float = 0.0


class A2AManager:
    """A2A管理器"""
    
    def __init__(self):
        """初始化A2A管理器"""
        self.status = A2AManagerStatus.INITIALIZED
        self.servers: Dict[str, A2AServerConfig] = {}
        self.clients: Dict[str, A2AClient] = {}
        self.agents: Dict[str, A2AAgentInfo] = {}
        self.task_results: Dict[str, A2ATaskResult] = {}
        self.stats = A2AManagerStats()
        self._lock = asyncio.Lock()
        self._task_callbacks: Dict[str, Callable] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_interval = 60  # 健康检查间隔（秒）
    
    async def initialize(self):
        """初始化管理器"""
        try:
            log_info("初始化A2A管理器")
            self.status = A2AManagerStatus.INITIALIZED
            self.stats.last_activity_time = time.time()
            
            # 启动健康检查任务
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            log_info("A2A管理器初始化完成")
            
        except Exception as e:
            self.status = A2AManagerStatus.ERROR
            log_error("A2A管理器初始化失败", e)
            raise
    
    async def shutdown(self):
        """关闭管理器"""
        try:
            log_info("关闭A2A管理器")
            
            # 停止健康检查任务
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 断开所有客户端连接
            for client in self.clients.values():
                await client.disconnect()
            
            self.clients.clear()
            self.status = A2AManagerStatus.DISCONNECTED
            
            log_info("A2A管理器已关闭")
            
        except Exception as e:
            log_error("A2A管理器关闭失败", e)
    
    def add_server(self, config: A2AServerConfig) -> bool:
        """
        添加A2A服务器
        
        Args:
            config: 服务器配置
            
        Returns:
            添加是否成功
        """
        try:
            if config.server_id in self.servers:
                log_warning(f"服务器已存在: {config.server_id}")
                return False
            
            self.servers[config.server_id] = config
            
            # 创建客户端
            client = A2AClient(config.server_url, config.client_id)
            self.clients[config.server_id] = client
            
            # 注册消息处理器
            client.register_message_handler(A2AMessageType.TASK_RESULT, self._handle_task_result)
            client.register_message_handler(A2AMessageType.STATUS_UPDATE, self._handle_status_update)
            client.register_message_handler(A2AMessageType.ERROR, self._handle_error)
            
            log_info(f"添加A2A服务器: {config.server_id} ({config.server_url})")
            self._update_stats()
            
            return True
            
        except Exception as e:
            log_error(f"添加A2A服务器失败: {config.server_id}", e)
            return False
    
    def remove_server(self, server_id: str) -> bool:
        """
        移除A2A服务器
        
        Args:
            server_id: 服务器ID
            
        Returns:
            移除是否成功
        """
        try:
            if server_id not in self.servers:
                log_warning(f"服务器不存在: {server_id}")
                return False
            
            # 断开客户端连接
            client = self.clients.get(server_id)
            if client:
                asyncio.create_task(client.disconnect())
                del self.clients[server_id]
            
            # 移除服务器配置
            del self.servers[server_id]
            
            log_info(f"移除A2A服务器: {server_id}")
            self._update_stats()
            
            return True
            
        except Exception as e:
            log_error(f"移除A2A服务器失败: {server_id}", e)
            return False
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        连接所有服务器
        
        Returns:
            连接结果字典 {server_id: success}
        """
        try:
            self.status = A2AManagerStatus.CONNECTING
            results = {}
            
            async with self._lock:
                for server_id, client in self.clients.items():
                    config = self.servers[server_id]
                    
                    if not config.enabled:
                        log_info(f"跳过禁用的服务器: {server_id}")
                        results[server_id] = False
                        continue
                    
                    try:
                        connected = await client.connect()
                        results[server_id] = connected
                        
                        if connected:
                            log_info(f"服务器连接成功: {server_id}")
                        else:
                            log_error(f"服务器连接失败: {server_id}")
                            
                    except Exception as e:
                        log_error(f"服务器连接异常: {server_id}", e)
                        results[server_id] = False
            
            # 更新状态
            connected_count = sum(1 for result in results.values() if result)
            if connected_count > 0:
                self.status = A2AManagerStatus.CONNECTED
            else:
                self.status = A2AManagerStatus.ERROR
            
            self._update_stats()
            return results
            
        except Exception as e:
            self.status = A2AManagerStatus.ERROR
            log_error("连接所有服务器失败", e)
            return {}
    
    async def disconnect_all(self):
        """断开所有服务器连接"""
        try:
            async with self._lock:
                for client in self.clients.values():
                    await client.disconnect()
            
            self.status = A2AManagerStatus.DISCONNECTED
            self._update_stats()
            
            log_info("所有A2A服务器连接已断开")
            
        except Exception as e:
            log_error("断开所有服务器连接失败", e)
    
    async def register_agent(self, agent_info: A2AAgentInfo, server_id: Optional[str] = None) -> bool:
        """
        注册代理
        
        Args:
            agent_info: 代理信息
            server_id: 目标服务器ID（None表示所有服务器）
            
        Returns:
            注册是否成功
        """
        try:
            results = []
            
            if server_id:
                # 注册到指定服务器
                client = self.clients.get(server_id)
                if client and client.status.value == "connected":
                    result = await client.register_agent(agent_info)
                    results.append(result)
                else:
                    log_error(f"服务器不可用: {server_id}")
                    return False
            else:
                # 注册到所有可用服务器
                for server_id, client in self.clients.items():
                    if client.status.value == "connected":
                        result = await client.register_agent(agent_info)
                        results.append(result)
            
            # 保存代理信息
            if any(results):
                self.agents[agent_info.agent_id] = agent_info
                self._update_stats()
                return True
            else:
                return False
            
        except Exception as e:
            log_error(f"注册代理失败: {agent_info.agent_id}", e)
            return False
    
    async def unregister_agent(self, agent_id: str, server_id: Optional[str] = None) -> bool:
        """
        注销代理
        
        Args:
            agent_id: 代理ID
            server_id: 目标服务器ID（None表示所有服务器）
            
        Returns:
            注销是否成功
        """
        try:
            results = []
            
            if server_id:
                # 从指定服务器注销
                client = self.clients.get(server_id)
                if client:
                    result = await client.unregister_agent(agent_id)
                    results.append(result)
            else:
                # 从所有服务器注销
                for client in self.clients.values():
                    result = await client.unregister_agent(agent_id)
                    results.append(result)
            
            # 移除代理信息
            if agent_id in self.agents:
                del self.agents[agent_id]
            
            self._update_stats()
            return any(results)
            
        except Exception as e:
            log_error(f"注销代理失败: {agent_id}", e)
            return False
    
    async def send_task(
        self, 
        task: A2ATask, 
        callback: Optional[Callable[[A2ATaskResult], None]] = None,
        server_id: Optional[str] = None
    ) -> bool:
        """
        发送任务
        
        Args:
            task: 任务
            callback: 任务完成回调函数
            server_id: 目标服务器ID（None表示自动选择）
            
        Returns:
            发送是否成功
        """
        try:
            start_time = time.time()
            
            # 选择目标服务器
            target_server_id = server_id or await self._select_server(task)
            if not target_server_id:
                log_error("没有可用的A2A服务器")
                return False
            
            client = self.clients.get(target_server_id)
            if not client or client.status.value != "connected":
                log_error(f"目标服务器不可用: {target_server_id}")
                return False
            
            # 保存回调函数
            if callback:
                self._task_callbacks[task.task_id] = callback
            
            # 发送任务
            result = await client.send_task(task, self._create_task_callback(task.task_id))
            
            if result:
                self.stats.total_tasks_sent += 1
                self.stats.last_activity_time = time.time()
                
                response_time = time.time() - start_time
                log_performance(f"A2A_SEND_TASK_{task.task_id}", response_time * 1000, 
                              f"server: {target_server_id}, agent: {task.agent_id}")
            
            return result
            
        except Exception as e:
            log_error(f"发送任务失败: {task.task_id}", e)
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
            all_agents = []
            
            for client in self.clients.values():
                if client.status.value == "connected":
                    agents = await client.get_available_agents(capability)
                    all_agents.extend(agents)
            
            # 去重
            unique_agents = {}
            for agent in all_agents:
                if agent.agent_id not in unique_agents:
                    unique_agents[agent.agent_id] = agent
            
            return list(unique_agents.values())
            
        except Exception as e:
            log_error("获取可用代理列表失败", e)
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        server_status = {}
        for server_id, client in self.clients.items():
            server_status[server_id] = client.get_status()
        
        return {
            "manager_status": self.status.value,
            "total_servers": len(self.servers),
            "connected_servers": sum(1 for client in self.clients.values() 
                                   if client.status.value == "connected"),
            "total_agents": len(self.agents),
            "server_status": server_status,
            "stats": {
                "total_tasks_sent": self.stats.total_tasks_sent,
                "total_tasks_completed": self.stats.total_tasks_completed,
                "total_tasks_failed": self.stats.total_tasks_failed,
                "average_response_time": self.stats.average_response_time,
                "last_activity_time": self.stats.last_activity_time
            }
        }
    
    async def _select_server(self, task: A2ATask) -> Optional[str]:
        """
        选择目标服务器
        
        Args:
            task: 任务
            
        Returns:
            服务器ID
        """
        try:
            # 简单的服务器选择策略：选择第一个可用的服务器
            for server_id, client in self.clients.items():
                config = self.servers[server_id]
                if config.enabled and client.status.value == "connected":
                    return server_id
            
            return None
            
        except Exception as e:
            log_error("选择服务器失败", e)
            return None
    
    def _create_task_callback(self, task_id: str) -> Callable:
        """创建任务回调函数"""
        def callback(result: A2ATaskResult):
            asyncio.create_task(self._handle_task_result_callback(task_id, result))
        return callback
    
    async def _handle_task_result_callback(self, task_id: str, result: A2ATaskResult):
        """处理任务结果回调"""
        try:
            # 保存任务结果
            self.task_results[task_id] = result
            
            # 更新统计信息
            if result.success:
                self.stats.total_tasks_completed += 1
            else:
                self.stats.total_tasks_failed += 1
            
            # 更新平均响应时间
            if result.execution_time > 0:
                total_time = self.stats.average_response_time * (self.stats.total_tasks_completed - 1)
                self.stats.average_response_time = (total_time + result.execution_time) / self.stats.total_tasks_completed
            
            self.stats.last_activity_time = time.time()
            
            # 调用用户回调函数
            user_callback = self._task_callbacks.get(task_id)
            if user_callback:
                try:
                    user_callback(result)
                except Exception as e:
                    log_error(f"用户任务回调函数执行失败: {task_id}", e)
            
            # 清理回调记录
            if task_id in self._task_callbacks:
                del self._task_callbacks[task_id]
            
            log_info(f"任务处理完成: {task_id} - {'成功' if result.success else '失败'}")
            
        except Exception as e:
            log_error(f"处理任务结果回调失败: {task_id}", e)
    
    async def _handle_task_result(self, message):
        """处理任务结果消息（转发给客户端）"""
        # 这个方法由各个客户端自己处理
        pass
    
    async def _handle_status_update(self, message):
        """处理状态更新消息（转发给客户端）"""
        # 这个方法由各个客户端自己处理
        pass
    
    async def _handle_error(self, message):
        """处理错误消息（转发给客户端）"""
        # 这个方法由各个客户端自己处理
        pass
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.status != A2AManagerStatus.DISCONNECTED:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error("健康检查失败", e)
    
    async def _perform_health_check(self):
        """执行健康检查"""
        try:
            for server_id, client in self.clients.items():
                if client.status.value == "connected":
                    # 简单的健康检查：获取服务器状态
                    try:
                        status = client.get_status()
                        if not status.get("active_heartbeat", False):
                            log_warning(f"服务器心跳异常: {server_id}")
                    except Exception as e:
                        log_error(f"服务器健康检查失败: {server_id}", e)
            
        except Exception as e:
            log_error("执行健康检查失败", e)
    
    def _update_stats(self):
        """更新统计信息"""
        self.stats.total_servers = len(self.servers)
        self.stats.connected_servers = sum(1 for client in self.clients.values() 
                                         if client.status.value == "connected")
        self.stats.total_agents = len(self.agents)


# 测试函数
async def test_a2a_manager():
    """测试A2A管理器功能"""
    try:
        # 创建管理器
        manager = A2AManager()
        await manager.initialize()
        
        # 添加服务器配置
        server_config = A2AServerConfig(
            server_id="test_server_1",
            server_url="http://localhost:8000",
            client_id="test_client_1"
        )
        
        manager.add_server(server_config)
        
        # 测试连接（需要实际运行的A2A服务器）
        # results = await manager.connect_all()
        # print(f"连接结果: {results}")
        
        # 测试代理注册
        agent_info = A2AAgentInfo(
            agent_id="test_agent_1",
            name="测试代理",
            capabilities=["text_generation", "code_generation"]
        )
        
        # 注册代理（需要连接）
        # registered = await manager.register_agent(agent_info)
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
        # sent = await manager.send_task(task, task_callback)
        # print(f"任务发送: {sent}")
        
        # 获取状态
        status = manager.get_status()
        print(f"管理器状态: {status}")
        
        # 关闭管理器
        await manager.shutdown()
        
        print("✓ A2A管理器基础功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ A2A管理器测试失败: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_a2a_manager())
