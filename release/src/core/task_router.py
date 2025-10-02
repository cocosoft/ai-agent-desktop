"""
任务路由引擎
实现基于能力的任务分配、负载均衡和优先级管理
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.agent_model import AgentConfig, AgentInstance, AgentStatus
from ..core.capability_model import Capability
from ..utils.logger import get_log_manager


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class RoutingStrategy(Enum):
    """路由策略"""
    BEST_MATCH = "best_match"           # 最佳匹配
    FASTEST_RESPONSE = "fastest"        # 最快响应
    LOWEST_COST = "lowest_cost"         # 最低成本
    ROUND_ROBIN = "round_robin"         # 轮询
    LOAD_BALANCED = "load_balanced"     # 负载均衡


@dataclass
class Task:
    """任务定义"""
    task_id: str
    capability_id: str
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: int = 60  # 秒
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    success: bool
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None  # 秒
    agent_id: Optional[str] = None
    completed_at: Optional[datetime] = None


@dataclass
class AgentPerformance:
    """代理性能指标"""
    agent_id: str
    capability_id: str
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_execution_time: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None


class TaskRouter:
    """任务路由引擎"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        
        # 代理性能统计
        self.agent_performance: Dict[str, Dict[str, AgentPerformance]] = {}
        
        # 任务队列
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
        # 正在执行的任务
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 路由策略
        self.routing_strategy = RoutingStrategy.BEST_MATCH
        
        # 路由引擎状态
        self.running = False
        self.router_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动路由引擎"""
        try:
            self.logger.info("启动任务路由引擎...")
            self.running = True
            self.router_task = asyncio.create_task(self._router_loop())
            self.logger.info("任务路由引擎启动成功")
            
        except Exception as e:
            self.logger.error(f"启动任务路由引擎失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止路由引擎"""
        try:
            self.logger.info("停止任务路由引擎...")
            self.running = False
            
            # 取消路由任务
            if self.router_task:
                self.router_task.cancel()
                try:
                    await self.router_task
                except asyncio.CancelledError:
                    pass
            
            # 取消所有正在执行的任务
            for task_id, task in list(self.running_tasks.items()):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("任务路由引擎已停止")
            
        except Exception as e:
            self.logger.error(f"停止任务路由引擎失败: {str(e)}")
    
    async def submit_task(self, capability_id: str, input_data: Dict[str, Any], 
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: int = 60,
                         metadata: Dict[str, Any] = None) -> str:
        """提交任务"""
        try:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                capability_id=capability_id,
                input_data=input_data,
                priority=priority,
                timeout=timeout,
                metadata=metadata or {}
            )
            
            await self.task_queue.put(task)
            self.logger.info(f"任务已提交: {task_id} (能力: {capability_id})")
            
            return task_id
            
        except Exception as e:
            self.logger.error(f"提交任务失败: {str(e)}")
            raise
    
    async def _router_loop(self):
        """路由循环"""
        while self.running:
            try:
                # 从队列获取任务
                task = await self.task_queue.get()
                
                # 路由任务到合适的代理
                routing_task = asyncio.create_task(self._route_task(task))
                self.running_tasks[task.task_id] = routing_task
                
                # 设置任务完成回调
                routing_task.add_done_callback(
                    lambda t: self._handle_task_completion(task.task_id, t)
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"路由循环错误: {str(e)}")
    
    async def _route_task(self, task: Task) -> TaskResult:
        """路由单个任务"""
        try:
            self.logger.info(f"开始路由任务: {task.task_id}")
            
            # 获取可用的代理
            available_agents = await self._get_available_agents(task.capability_id)
            
            if not available_agents:
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error_message=f"没有可用的代理支持能力: {task.capability_id}"
                )
            
            # 根据策略选择代理
            selected_agent = await self._select_agent(available_agents, task)
            
            if not selected_agent:
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error_message="无法选择合适的代理"
                )
            
            # 执行任务
            start_time = datetime.now()
            result = await self._execute_task(selected_agent, task)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 更新性能统计
            await self._update_performance_stats(selected_agent, task.capability_id, result, execution_time)
            
            return TaskResult(
                task_id=task.task_id,
                success=result.success,
                output_data=result.output_data,
                error_message=result.error_message,
                execution_time=execution_time,
                agent_id=selected_agent.agent_config.agent_id,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"路由任务失败: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error_message=f"路由任务失败: {str(e)}"
            )
    
    async def _get_available_agents(self, capability_id: str) -> List[AgentInstance]:
        """获取支持指定能力的可用代理"""
        # TODO: 从代理管理器获取可用代理
        # 这里返回空列表，实际实现需要集成代理管理器
        return []
    
    async def _select_agent(self, available_agents: List[AgentInstance], task: Task) -> Optional[AgentInstance]:
        """根据策略选择代理"""
        if not available_agents:
            return None
        
        if self.routing_strategy == RoutingStrategy.BEST_MATCH:
            return await self._select_best_match(available_agents, task)
        elif self.routing_strategy == RoutingStrategy.FASTEST_RESPONSE:
            return await self._select_fastest_response(available_agents, task)
        elif self.routing_strategy == RoutingStrategy.LOWEST_COST:
            return await self._select_lowest_cost(available_agents, task)
        elif self.routing_strategy == RoutingStrategy.ROUND_ROBIN:
            return await self._select_round_robin(available_agents, task)
        elif self.routing_strategy == RoutingStrategy.LOAD_BALANCED:
            return await self._select_load_balanced(available_agents, task)
        else:
            return available_agents[0]  # 默认选择第一个
    
    async def _select_best_match(self, agents: List[AgentInstance], task: Task) -> Optional[AgentInstance]:
        """选择最佳匹配代理"""
        best_agent = None
        best_score = -1
        
        for agent in agents:
            score = await self._calculate_match_score(agent, task)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent
    
    async def _select_fastest_response(self, agents: List[AgentInstance], task: Task) -> Optional[AgentInstance]:
        """选择最快响应代理"""
        fastest_agent = None
        fastest_time = float('inf')
        
        for agent in agents:
            perf = self._get_agent_performance(agent.agent_config.agent_id, task.capability_id)
            if perf and perf.average_response_time < fastest_time:
                fastest_time = perf.average_response_time
                fastest_agent = agent
        
        return fastest_agent or agents[0]
    
    async def _select_lowest_cost(self, agents: List[AgentInstance], task: Task) -> Optional[AgentInstance]:
        """选择最低成本代理"""
        # TODO: 实现成本计算逻辑
        # 暂时返回第一个代理
        return agents[0]
    
    async def _select_round_robin(self, agents: List[AgentInstance], task: Task) -> Optional[AgentInstance]:
        """轮询选择代理"""
        # TODO: 实现轮询逻辑
        # 暂时返回第一个代理
        return agents[0]
    
    async def _select_load_balanced(self, agents: List[AgentInstance], task: Task) -> Optional[AgentInstance]:
        """负载均衡选择代理"""
        least_loaded_agent = None
        min_load = float('inf')
        
        for agent in agents:
            load = await self._calculate_agent_load(agent)
            if load < min_load:
                min_load = load
                least_loaded_agent = agent
        
        return least_loaded_agent or agents[0]
    
    async def _calculate_match_score(self, agent: AgentInstance, task: Task) -> float:
        """计算代理匹配分数"""
        score = 0.0
        
        # 1. 能力匹配度 (40%)
        capability_match = await self._check_capability_match(agent, task.capability_id)
        score += capability_match * 0.4
        
        # 2. 性能分数 (30%)
        performance_score = await self._calculate_performance_score(agent, task.capability_id)
        score += performance_score * 0.3
        
        # 3. 负载分数 (20%)
        load_score = await self._calculate_load_score(agent)
        score += load_score * 0.2
        
        # 4. 优先级分数 (10%)
        priority_score = await self._calculate_priority_score(agent, task.priority)
        score += priority_score * 0.1
        
        return score
    
    async def _check_capability_match(self, agent: AgentInstance, capability_id: str) -> float:
        """检查能力匹配度"""
        # TODO: 实现能力匹配检查
        # 暂时返回1.0
        return 1.0
    
    async def _calculate_performance_score(self, agent: AgentInstance, capability_id: str) -> float:
        """计算性能分数"""
        perf = self._get_agent_performance(agent.agent_config.agent_id, capability_id)
        if not perf:
            return 0.5  # 默认分数
        
        # 基于成功率和响应时间计算分数
        success_score = perf.success_rate
        response_score = max(0, 1 - (perf.average_response_time / 10))  # 假设10秒为最大可接受时间
        
        return (success_score + response_score) / 2
    
    async def _calculate_load_score(self, agent: AgentInstance) -> float:
        """计算负载分数"""
        load = await self._calculate_agent_load(agent)
        return max(0, 1 - load)  # 负载越低分数越高
    
    async def _calculate_priority_score(self, agent: AgentInstance, task_priority: TaskPriority) -> float:
        """计算优先级分数"""
        # TODO: 实现优先级匹配逻辑
        # 暂时返回1.0
        return 1.0
    
    async def _calculate_agent_load(self, agent: AgentInstance) -> float:
        """计算代理负载"""
        # TODO: 实现负载计算逻辑
        # 暂时返回0.5
        return 0.5
    
    async def _execute_task(self, agent: AgentInstance, task: Task) -> TaskResult:
        """执行任务"""
        try:
            # TODO: 实现任务执行逻辑
            # 这里需要调用代理的实际执行方法
            self.logger.info(f"在代理 {agent.agent_config.agent_id} 上执行任务: {task.task_id}")
            
            # 模拟任务执行
            await asyncio.sleep(0.1)
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                output_data={"result": "模拟执行结果"},
                execution_time=0.1
            )
            
        except Exception as e:
            self.logger.error(f"执行任务失败: {str(e)}")
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error_message=f"执行任务失败: {str(e)}"
            )
    
    def _get_agent_performance(self, agent_id: str, capability_id: str) -> Optional[AgentPerformance]:
        """获取代理性能指标"""
        if agent_id not in self.agent_performance:
            return None
        
        capabilities = self.agent_performance[agent_id]
        return capabilities.get(capability_id)
    
    async def _update_performance_stats(self, agent: AgentInstance, capability_id: str, 
                                      result: TaskResult, execution_time: float):
        """更新性能统计"""
        agent_id = agent.agent_config.agent_id
        
        if agent_id not in self.agent_performance:
            self.agent_performance[agent_id] = {}
        
        if capability_id not in self.agent_performance[agent_id]:
            self.agent_performance[agent_id][capability_id] = AgentPerformance(
                agent_id=agent_id,
                capability_id=capability_id
            )
        
        perf = self.agent_performance[agent_id][capability_id]
        perf.total_tasks += 1
        
        if result.success:
            perf.successful_tasks += 1
        else:
            perf.failed_tasks += 1
        
        perf.total_execution_time += execution_time
        perf.average_response_time = perf.total_execution_time / perf.total_tasks
        perf.success_rate = perf.successful_tasks / perf.total_tasks
        perf.last_used = datetime.now()
    
    def _handle_task_completion(self, task_id: str, task_future: asyncio.Future):
        """处理任务完成"""
        try:
            # 从运行任务中移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # 获取任务结果
            result = task_future.result()
            
            if result.success:
                self.logger.info(f"任务完成: {task_id}")
            else:
                self.logger.warning(f"任务失败: {task_id} - {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"处理任务完成时出错: {str(e)}")
    
    def set_routing_strategy(self, strategy: RoutingStrategy):
        """设置路由策略"""
        self.routing_strategy = strategy
        self.logger.info(f"路由策略已设置为: {strategy.value}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total_tasks = 0
        successful_tasks = 0
        failed_tasks = 0
        
        for agent_capabilities in self.agent_performance.values():
            for perf in agent_capabilities.values():
                total_tasks += perf.total_tasks
                successful_tasks += perf.successful_tasks
                failed_tasks += perf.failed_tasks
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "routing_strategy": self.routing_strategy.value,
            "running_tasks": len(self.running_tasks),
            "queued_tasks": self.task_queue.qsize()
        }


# 全局路由引擎实例
_task_router: Optional[TaskRouter] = None


def get_task_router() -> TaskRouter:
    """获取全局任务路由引擎实例"""
    global _task_router
    if _task_router is None:
        _task_router = TaskRouter()
    return _task_router


async def start_task_router():
    """启动任务路由引擎"""
    router = get_task_router()
    await router.start()
    return router


async def stop_task_router():
    """停止任务路由引擎"""
    global _task_router
    if _task_router:
        await _task_router.stop()
        _task_router = None


async def submit_task(capability_id: str, input_data: Dict[str, Any], 
                     priority: TaskPriority = TaskPriority.NORMAL,
                     timeout: int = 60,
                     metadata: Dict[str, Any] = None) -> str:
    """提交任务到路由引擎"""
    router = get_task_router()
    return await router.submit_task
