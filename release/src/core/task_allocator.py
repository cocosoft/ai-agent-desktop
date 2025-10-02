"""
智能任务分配器
基于能力、性能、负载等因素进行智能任务分配
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.core.agent_communication import AgentMessage, MessageType
from src.core.task_router import Task, TaskPriority
from src.core.agent_lifecycle import AgentInstance, AgentStatus
from src.utils.logger import get_log_manager


class AllocationStrategy(Enum):
    """任务分配策略"""
    BEST_MATCH = "best_match"  # 最佳能力匹配
    FASTEST_RESPONSE = "fastest_response"  # 最快响应
    LOWEST_COST = "lowest_cost"  # 最低成本
    ROUND_ROBIN = "round_robin"  # 轮询
    LOAD_BALANCED = "load_balanced"  # 负载均衡


@dataclass
class AllocationResult:
    """分配结果"""
    agent_id: str
    task_id: str
    allocation_score: float
    strategy: AllocationStrategy
    estimated_response_time: float
    estimated_cost: float
    timestamp: datetime


@dataclass
class AgentCapabilityScore:
    """代理能力评分"""
    agent_id: str
    capability_id: str
    match_score: float  # 能力匹配度 (0-1)
    performance_score: float  # 性能评分 (0-1)
    load_score: float  # 负载评分 (0-1)
    priority_score: float  # 优先级评分 (0-1)
    total_score: float  # 总分


class TaskAllocator:
    """智能任务分配器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        self.allocation_history: List[AllocationResult] = []
        self.agent_performance_stats: Dict[str, Dict[str, Any]] = {}
        self.agent_load_stats: Dict[str, Dict[str, Any]] = {}
        
    async def allocate_task(self, task: Task, available_agents: List[AgentInstance], 
                          strategy: AllocationStrategy = AllocationStrategy.BEST_MATCH) -> Optional[str]:
        """
        分配任务给合适的代理
        
        Args:
            task: 要分配的任务
            available_agents: 可用代理列表
            strategy: 分配策略
            
        Returns:
            分配的代理ID，如果无法分配则返回None
        """
        if not available_agents:
            self.logger.warning(f"没有可用代理来分配任务: {task.task_id}")
            return None
        
        # 过滤可用的代理
        suitable_agents = await self._filter_suitable_agents(task, available_agents)
        if not suitable_agents:
            self.logger.warning(f"没有合适的代理来处理任务: {task.task_id}")
            return None
        
        # 根据策略选择代理
        selected_agent_id = await self._select_agent_by_strategy(task, suitable_agents, strategy)
        
        if selected_agent_id:
            # 记录分配结果
            allocation_result = AllocationResult(
                agent_id=selected_agent_id,
                task_id=task.task_id,
                allocation_score=0.0,  # 将在评分方法中计算
                strategy=strategy,
                estimated_response_time=0.0,  # 将在评分方法中计算
                estimated_cost=0.0,  # 将在评分方法中计算
                timestamp=datetime.now()
            )
            self.allocation_history.append(allocation_result)
            
            self.logger.info(f"任务 {task.task_id} 已分配给代理 {selected_agent_id} (策略: {strategy.value})")
        
        return selected_agent_id
    
    async def _filter_suitable_agents(self, task: Task, agents: List[AgentInstance]) -> List[AgentInstance]:
        """过滤适合处理任务的代理"""
        suitable_agents = []
        
        for agent in agents:
            # 检查代理状态
            if agent.status != AgentStatus.RUNNING:
                continue
            
            # 检查代理是否具备所需能力
            if not await self._agent_has_capability(agent, task.capability_id):
                continue
            
            # 检查代理负载
            if not await self._agent_can_handle_task(agent, task):
                continue
            
            suitable_agents.append(agent)
        
        return suitable_agents
    
    async def _agent_has_capability(self, agent: AgentInstance, capability_id: str) -> bool:
        """检查代理是否具备指定能力"""
        # 这里应该检查代理的能力映射
        # 简化实现：假设代理具备所有能力
        return True
    
    async def _agent_can_handle_task(self, agent: AgentInstance, task: Task) -> bool:
        """检查代理是否可以处理任务"""
        # 检查代理的当前负载
        current_load = await self._get_agent_load(agent.instance_id)
        max_load = 10  # 最大负载阈值
        
        if current_load >= max_load:
            return False
        
        # 检查任务优先级和代理能力
        if task.priority == TaskPriority.URGENT:
            # 紧急任务需要高性能代理
            performance_stats = await self._get_agent_performance_stats(agent.instance_id)
            performance = performance_stats.get('success_rate', 0.5)
            if performance < 0.7:  # 性能阈值
                return False
        
        return True
    
    async def _select_agent_by_strategy(self, task: Task, agents: List[AgentInstance], 
                                      strategy: AllocationStrategy) -> Optional[str]:
        """根据策略选择代理"""
        if strategy == AllocationStrategy.BEST_MATCH:
            return await self._select_best_match(task, agents)
        elif strategy == AllocationStrategy.FASTEST_RESPONSE:
            return await self._select_fastest_response(task, agents)
        elif strategy == AllocationStrategy.LOWEST_COST:
            return await self._select_lowest_cost(task, agents)
        elif strategy == AllocationStrategy.ROUND_ROBIN:
            return await self._select_round_robin(task, agents)
        elif strategy == AllocationStrategy.LOAD_BALANCED:
            return await self._select_load_balanced(task, agents)
        else:
            # 默认使用最佳匹配
            return await self._select_best_match(task, agents)
    
    async def _select_best_match(self, task: Task, agents: List[AgentInstance]) -> Optional[str]:
        """选择最佳能力匹配的代理"""
        best_agent_id = None
        best_score = -1.0
        
        for agent in agents:
            score = await self._calculate_allocation_score(task, agent, AllocationStrategy.BEST_MATCH)
            
            if score > best_score:
                best_score = score
                best_agent_id = agent.agent_id
        
        return best_agent_id
    
    async def _select_fastest_response(self, task: Task, agents: List[AgentInstance]) -> Optional[str]:
        """选择响应最快的代理"""
        fastest_agent_id = None
        fastest_time = float('inf')
        
        for agent in agents:
            response_time = await self._estimate_response_time(task, agent)
            
            if response_time < fastest_time:
                fastest_time = response_time
                fastest_agent_id = agent.agent_id
        
        return fastest_agent_id
    
    async def _select_lowest_cost(self, task: Task, agents: List[AgentInstance]) -> Optional[str]:
        """选择成本最低的代理"""
        lowest_cost_agent_id = None
        lowest_cost = float('inf')
        
        for agent in agents:
            cost = await self._estimate_cost(task, agent)
            
            if cost < lowest_cost:
                lowest_cost = cost
                lowest_cost_agent_id = agent.agent_id
        
        return lowest_cost_agent_id
    
    async def _select_round_robin(self, task: Task, agents: List[AgentInstance]) -> Optional[str]:
        """轮询选择代理"""
        if not agents:
            return None
        
        # 简单的轮询实现
        # 在实际应用中，应该维护一个轮询索引
        return agents[0].agent_id
    
    async def _select_load_balanced(self, task: Task, agents: List[AgentInstance]) -> Optional[str]:
        """选择负载最均衡的代理"""
        balanced_agent_id = None
        best_load_score = float('inf')
        
        for agent in agents:
            load_score = await self._calculate_load_score(agent)
            
            if load_score < best_load_score:
                best_load_score = load_score
                balanced_agent_id = agent.agent_id
        
        return balanced_agent_id
    
    async def _calculate_allocation_score(self, task: Task, agent: AgentInstance, 
                                        strategy: AllocationStrategy) -> float:
        """计算分配评分"""
        # 能力匹配度 (40%)
        capability_match = await self._calculate_capability_match(task, agent)
        
        # 性能评分 (30%)
        performance_score = await self._calculate_performance_score(agent)
        
        # 负载评分 (20%)
        load_score = await self._calculate_load_score(agent)
        
        # 优先级评分 (10%)
        priority_score = await self._calculate_priority_score(task, agent)
        
        # 根据策略调整权重
        if strategy == AllocationStrategy.BEST_MATCH:
            weights = [0.4, 0.3, 0.2, 0.1]  # 能力匹配权重最高
        elif strategy == AllocationStrategy.FASTEST_RESPONSE:
            weights = [0.2, 0.5, 0.2, 0.1]  # 性能权重最高
        elif strategy == AllocationStrategy.LOWEST_COST:
            weights = [0.3, 0.2, 0.3, 0.2]  # 成本和负载权重较高
        elif strategy == AllocationStrategy.LOAD_BALANCED:
            weights = [0.2, 0.2, 0.5, 0.1]  # 负载权重最高
        else:  # ROUND_ROBIN 或其他
            weights = [0.25, 0.25, 0.25, 0.25]  # 平均权重
        
        total_score = (
            capability_match * weights[0] +
            performance_score * weights[1] +
            load_score * weights[2] +
            priority_score * weights[3]
        )
        
        return total_score
    
    async def _calculate_capability_match(self, task: Task, agent: AgentInstance) -> float:
        """计算能力匹配度"""
        # 简化实现：假设所有代理都具备所需能力
        # 在实际应用中，应该检查代理的具体能力配置
        return 1.0
    
    async def _calculate_performance_score(self, agent: AgentInstance) -> float:
        """计算性能评分"""
        performance_stats = await self._get_agent_performance_stats(agent.instance_id)
        
        # 基于响应时间、成功率等计算性能评分
        avg_response_time = performance_stats.get('avg_response_time', 1.0)
        success_rate = performance_stats.get('success_rate', 0.95)
        
        # 响应时间越短，性能评分越高
        response_time_score = max(0, 1 - (avg_response_time / 10.0))
        
        # 成功率越高，性能评分越高
        success_rate_score = success_rate
        
        # 综合性能评分
        performance_score = (response_time_score * 0.6 + success_rate_score * 0.4)
        
        return min(1.0, performance_score)
    
    async def _calculate_load_score(self, agent: AgentInstance) -> float:
        """计算负载评分"""
        current_load = await self._get_agent_load(agent.instance_id)
        max_load = 10  # 最大负载
        
        # 负载越低，评分越高
        load_score = max(0, 1 - (current_load / max_load))
        
        return load_score
    
    async def _calculate_priority_score(self, task: Task, agent: AgentInstance) -> float:
        """计算优先级评分"""
        # 基于任务优先级和代理优先级配置计算
        task_priority_weight = {
            TaskPriority.LOW: 0.2,
            TaskPriority.NORMAL: 0.5,
            TaskPriority.HIGH: 0.8,
            TaskPriority.URGENT: 1.0
        }.get(task.priority, 0.5)
        
        # 代理优先级配置（如果有）
        agent_priority = getattr(agent, 'priority', 0.5)
        
        priority_score = (task_priority_weight + agent_priority) / 2
        
        return priority_score
    
    async def _estimate_response_time(self, task: Task, agent: AgentInstance) -> float:
        """估计响应时间"""
        performance_stats = await self._get_agent_performance_stats(agent.instance_id)
        avg_response_time = performance_stats.get('avg_response_time', 1.0)
        
        # 基于任务复杂度和代理性能调整
        complexity_factor = self._get_task_complexity_factor(task)
        adjusted_response_time = avg_response_time * complexity_factor
        
        return adjusted_response_time
    
    async def _estimate_cost(self, task: Task, agent: AgentInstance) -> float:
        """估计成本"""
        # 简化实现：基于代理类型和任务复杂度估算成本
        agent_type = getattr(agent, 'agent_type', 'standard')
        
        cost_rates = {
            'standard': 1.0,
            'premium': 2.0,
            'enterprise': 5.0
        }
        
        base_cost = cost_rates.get(agent_type, 1.0)
        complexity_factor = self._get_task_complexity_factor(task)
        
        estimated_cost = base_cost * complexity_factor
        
        return estimated_cost
    
    def _get_task_complexity_factor(self, task: Task) -> float:
        """获取任务复杂度因子"""
        # 基于任务优先级和输入数据大小估算复杂度
        priority_factor = {
            TaskPriority.LOW: 0.5,
            TaskPriority.NORMAL: 1.0,
            TaskPriority.HIGH: 1.5,
            TaskPriority.URGENT: 2.0
        }.get(task.priority, 1.0)
        
        # 输入数据大小因子（如果有）
        input_size = len(str(task.input_data)) if task.input_data else 1
        size_factor = min(2.0, input_size / 100)  # 限制最大因子
        
        complexity_factor = priority_factor * size_factor
        
        return max(1.0, complexity_factor)  # 确保复杂度因子至少为1.0
    
    async def _get_agent_performance_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取代理性能统计"""
        if agent_id not in self.agent_performance_stats:
            # 初始化默认性能统计
            self.agent_performance_stats[agent_id] = {
                'avg_response_time': 1.0,
                'success_rate': 0.95,
                'total_requests': 0,
                'failed_requests': 0
            }
        
        return self.agent_performance_stats[agent_id]
    
    async def _get_agent_load(self, agent_id: str) -> int:
        """获取代理当前负载"""
        if agent_id not in self.agent_load_stats:
            # 初始化默认负载
            self.agent_load_stats[agent_id] = {
                'current_tasks': 0,
                'max_capacity': 10
            }
        
        return self.agent_load_stats[agent_id]['current_tasks']
    
    async def update_agent_performance(self, agent_id: str, response_time: float, success: bool):
        """更新代理性能统计"""
        stats = await self._get_agent_performance_stats(agent_id)
        
        stats['total_requests'] += 1
        if not success:
            stats['failed_requests'] += 1
        
        # 更新平均响应时间（指数移动平均）
        # 如果是第一次请求，直接使用输入值
        if stats['total_requests'] == 1:
            stats['avg_response_time'] = response_time
        else:
            alpha = 0.1  # 平滑因子
            stats['avg_response_time'] = (
                alpha * response_time + 
                (1 - alpha) * stats['avg_response_time']
            )
        
        # 更新成功率
        stats['success_rate'] = 1 - (stats['failed_requests'] / stats['total_requests'])
    
    async def update_agent_load(self, agent_id: str, task_count: int):
        """更新代理负载"""
        if agent_id not in self.agent_load_stats:
            self.agent_load_stats[agent_id] = {
                'current_tasks': 0,
                'max_capacity': 10
            }
        
        self.agent_load_stats[agent_id]['current_tasks'] = task_count
    
    async def get_allocation_history(self, limit: int = 100) -> List[AllocationResult]:
        """获取分配历史"""
        return self.allocation_history[-limit:]
    
    async def get_agent_performance_report(self, agent_id: str) -> Dict[str, Any]:
        """获取代理性能报告"""
        stats = await self._get_agent_performance_stats(agent_id)
        load_stats = await self._get_agent_load(agent_id)
        
        return {
            'agent_id': agent_id,
            'performance_stats': stats,
            'current_load': load_stats,
            'allocation_count': len([r for r in self.allocation_history if r.agent_id == agent_id])
        }


# 全局任务分配器实例
_task_allocator: Optional[TaskAllocator] = None


def get_task_allocator() -> TaskAllocator:
    """获取全局任务分配器实例"""
    global _task_allocator
    if _task_allocator is None:
        _task_allocator = TaskAllocator()
    return _task_allocator


async def allocate_task(task: Task, available_agents: List[AgentInstance], 
                       strategy: AllocationStrategy = AllocationStrategy.BEST_MATCH) -> Optional[str]:
    """分配任务（便捷函数）"""
    allocator = get_task_allocator()
    return await allocator.allocate_task(task, available_agents, strategy)


async def update_agent_performance(agent_id: str, response_time: float, success: bool):
    """更新代理性能（便捷函数）"""
    allocator = get_task_allocator()
    await allocator.update_agent_performance(agent_id, response_time, success)


async def update_agent_load(agent_id: str, task_count: int):
    """更新代理负载（便捷函数）"""
    allocator = get_task_allocator()
    await allocator.update_agent_load(agent_id, task_count)
