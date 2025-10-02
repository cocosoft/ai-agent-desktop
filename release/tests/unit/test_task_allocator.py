"""
智能任务分配器单元测试
测试任务分配算法、策略选择、性能评估等功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from src.core.task_allocator import (
    TaskAllocator, AllocationStrategy, AllocationResult, get_task_allocator,
    allocate_task, update_agent_performance, update_agent_load
)
from src.core.task_router import Task, TaskPriority
from src.core.agent_lifecycle import AgentInstance, AgentStatus


class TestTaskAllocator:
    """智能任务分配器测试"""
    
    @pytest.fixture
    def task_allocator(self):
        """创建任务分配器实例"""
        return TaskAllocator()
    
    @pytest.fixture
    def sample_task(self):
        """创建示例任务"""
        return Task(
            task_id="test_task",
            capability_id="text_generation",
            input_data={"text": "测试输入"},
            priority=TaskPriority.NORMAL,
            timeout=60
        )
    
    @pytest.fixture
    def sample_agents(self):
        """创建示例代理列表"""
        # 创建模拟的AgentConfig对象
        mock_config_1 = Mock()
        mock_config_1.agent_id = "config_1"
        
        mock_config_2 = Mock()
        mock_config_2.agent_id = "config_2"
        
        mock_config_3 = Mock()
        mock_config_3.agent_id = "config_3"
        
        return [
            AgentInstance(
                instance_id="instance_1",
                agent_config=mock_config_1,
                status=AgentStatus.RUNNING
            ),
            AgentInstance(
                instance_id="instance_2",
                agent_config=mock_config_2,
                status=AgentStatus.RUNNING
            ),
            AgentInstance(
                instance_id="instance_3",
                agent_config=mock_config_3,
                status=AgentStatus.STOPPED  # 停止状态的代理
            )
        ]
    
    def test_task_allocator_creation(self, task_allocator):
        """测试任务分配器创建"""
        assert task_allocator is not None
        assert task_allocator.allocation_history == []
        assert task_allocator.agent_performance_stats == {}
        assert task_allocator.agent_load_stats == {}
    
    @pytest.mark.asyncio
    async def test_allocate_task_success(self, task_allocator, sample_task, sample_agents):
        """测试成功分配任务"""
        # 使用Mock模拟内部方法
        with patch.object(task_allocator, '_filter_suitable_agents', return_value=sample_agents[:2]), \
             patch.object(task_allocator, '_select_agent_by_strategy', return_value="agent_1"):
            
            agent_id = await task_allocator.allocate_task(sample_task, sample_agents)
            
            assert agent_id == "agent_1"
            assert len(task_allocator.allocation_history) == 1
            
            allocation_result = task_allocator.allocation_history[0]
            assert allocation_result.agent_id == "agent_1"
            assert allocation_result.task_id == "test_task"
            assert allocation_result.strategy == AllocationStrategy.BEST_MATCH
    
    @pytest.mark.asyncio
    async def test_allocate_task_no_agents(self, task_allocator, sample_task):
        """测试没有可用代理时分配任务"""
        agent_id = await task_allocator.allocate_task(sample_task, [])
        
        assert agent_id is None
        assert len(task_allocator.allocation_history) == 0
    
    @pytest.mark.asyncio
    async def test_allocate_task_no_suitable_agents(self, task_allocator, sample_task, sample_agents):
        """测试没有合适代理时分配任务"""
        with patch.object(task_allocator, '_filter_suitable_agents', return_value=[]):
            agent_id = await task_allocator.allocate_task(sample_task, sample_agents)
            
            assert agent_id is None
            assert len(task_allocator.allocation_history) == 0
    
    @pytest.mark.asyncio
    async def test_filter_suitable_agents(self, task_allocator, sample_task, sample_agents):
        """测试过滤合适代理"""
        suitable_agents = await task_allocator._filter_suitable_agents(sample_task, sample_agents)
        
        # 应该只包含运行状态的代理
        assert len(suitable_agents) == 2
        assert all(agent.status == AgentStatus.RUNNING for agent in suitable_agents)
        assert "instance_1" in [agent.instance_id for agent in suitable_agents]
        assert "instance_2" in [agent.instance_id for agent in suitable_agents]
        assert "instance_3" not in [agent.instance_id for agent in suitable_agents]
    
    @pytest.mark.asyncio
    async def test_agent_has_capability(self, task_allocator, sample_agents):
        """测试代理能力检查"""
        # 简化实现中，所有代理都具备所有能力
        for agent in sample_agents:
            has_capability = await task_allocator._agent_has_capability(agent, "text_generation")
            assert has_capability is True
    
    @pytest.mark.asyncio
    async def test_agent_can_handle_task(self, task_allocator, sample_task, sample_agents):
        """测试代理是否可以处理任务"""
        # 模拟正常负载
        with patch.object(task_allocator, '_get_agent_load', return_value=5), \
             patch.object(task_allocator, '_get_agent_performance_stats', return_value={
                 'success_rate': 0.8
             }):
            
            can_handle = await task_allocator._agent_can_handle_task(sample_agents[0], sample_task)
            assert can_handle is True
        
        # 模拟高负载
        with patch.object(task_allocator, '_get_agent_load', return_value=10):
            can_handle = await task_allocator._agent_can_handle_task(sample_agents[0], sample_task)
            assert can_handle is False
        
        # 模拟紧急任务但性能不足
        urgent_task = Task(
            task_id="urgent_task",
            capability_id="text_generation",
            input_data={"text": "紧急输入"},
            priority=TaskPriority.URGENT,
            timeout=60
        )
        
        with patch.object(task_allocator, '_get_agent_load', return_value=5), \
             patch.object(task_allocator, '_get_agent_performance_stats', return_value={
                 'success_rate': 0.6
             }):
            
            can_handle = await task_allocator._agent_can_handle_task(sample_agents[0], urgent_task)
            assert can_handle is False
    
    @pytest.mark.asyncio
    async def test_select_agent_by_strategy(self, task_allocator, sample_task, sample_agents):
        """测试根据策略选择代理"""
        suitable_agents = sample_agents[:2]  # 只使用运行状态的代理
        
        # 测试最佳匹配策略
        with patch.object(task_allocator, '_select_best_match', return_value="agent_1"):
            agent_id = await task_allocator._select_agent_by_strategy(
                sample_task, suitable_agents, AllocationStrategy.BEST_MATCH
            )
            assert agent_id == "agent_1"
        
        # 测试最快响应策略
        with patch.object(task_allocator, '_select_fastest_response', return_value="agent_2"):
            agent_id = await task_allocator._select_agent_by_strategy(
                sample_task, suitable_agents, AllocationStrategy.FASTEST_RESPONSE
            )
            assert agent_id == "agent_2"
        
        # 测试最低成本策略
        with patch.object(task_allocator, '_select_lowest_cost', return_value="agent_1"):
            agent_id = await task_allocator._select_agent_by_strategy(
                sample_task, suitable_agents, AllocationStrategy.LOWEST_COST
            )
            assert agent_id == "agent_1"
        
        # 测试轮询策略
        with patch.object(task_allocator, '_select_round_robin', return_value="agent_1"):
            agent_id = await task_allocator._select_agent_by_strategy(
                sample_task, suitable_agents, AllocationStrategy.ROUND_ROBIN
            )
            assert agent_id == "agent_1"
        
        # 测试负载均衡策略
        with patch.object(task_allocator, '_select_load_balanced', return_value="agent_2"):
            agent_id = await task_allocator._select_agent_by_strategy(
                sample_task, suitable_agents, AllocationStrategy.LOAD_BALANCED
            )
            assert agent_id == "agent_2"
    
    @pytest.mark.asyncio
    async def test_calculate_allocation_score(self, task_allocator, sample_task, sample_agents):
        """测试计算分配评分"""
        agent = sample_agents[0]
        
        with patch.object(task_allocator, '_calculate_capability_match', return_value=0.9), \
             patch.object(task_allocator, '_calculate_performance_score', return_value=0.8), \
             patch.object(task_allocator, '_calculate_load_score', return_value=0.7), \
             patch.object(task_allocator, '_calculate_priority_score', return_value=0.6):
            
            # 测试最佳匹配策略的评分
            score = await task_allocator._calculate_allocation_score(
                sample_task, agent, AllocationStrategy.BEST_MATCH
            )
            
            # 计算期望得分: 0.9*0.4 + 0.8*0.3 + 0.7*0.2 + 0.6*0.1 = 0.36 + 0.24 + 0.14 + 0.06 = 0.8
            expected_score = 0.9*0.4 + 0.8*0.3 + 0.7*0.2 + 0.6*0.1
            assert abs(score - expected_score) < 0.001
    
    @pytest.mark.asyncio
    async def test_calculate_capability_match(self, task_allocator, sample_task, sample_agents):
        """测试计算能力匹配度"""
        agent = sample_agents[0]
        match_score = await task_allocator._calculate_capability_match(sample_task, agent)
        
        # 简化实现中，所有代理的能力匹配度都是1.0
        assert match_score == 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_performance_score(self, task_allocator, sample_agents):
        """测试计算性能评分"""
        agent = sample_agents[0]
        
        # 模拟性能统计
        with patch.object(task_allocator, '_get_agent_performance_stats', return_value={
            'avg_response_time': 2.0,
            'success_rate': 0.95
        }):
            performance_score = await task_allocator._calculate_performance_score(agent)
            
            # 响应时间评分: 1 - (2.0 / 10.0) = 0.8
            # 成功率评分: 0.95
            # 综合评分: 0.8*0.6 + 0.95*0.4 = 0.48 + 0.38 = 0.86
            expected_score = 0.8*0.6 + 0.95*0.4
            assert abs(performance_score - expected_score) < 0.001
    
    @pytest.mark.asyncio
    async def test_calculate_load_score(self, task_allocator, sample_agents):
        """测试计算负载评分"""
        agent = sample_agents[0]
        
        # 模拟低负载
        with patch.object(task_allocator, '_get_agent_load', return_value=2):
            load_score = await task_allocator._calculate_load_score(agent)
            expected_score = 1 - (2 / 10)  # 0.8
            assert abs(load_score - expected_score) < 0.001
        
        # 模拟高负载
        with patch.object(task_allocator, '_get_agent_load', return_value=8):
            load_score = await task_allocator._calculate_load_score(agent)
            expected_score = 1 - (8 / 10)  # 0.2
            assert abs(load_score - expected_score) < 0.001
    
    @pytest.mark.asyncio
    async def test_calculate_priority_score(self, task_allocator, sample_agents):
        """测试计算优先级评分"""
        agent = sample_agents[0]
        
        # 测试不同优先级的任务
        test_cases = [
            (TaskPriority.LOW, 0.2),
            (TaskPriority.NORMAL, 0.5),
            (TaskPriority.HIGH, 0.8),
            (TaskPriority.URGENT, 1.0)
        ]
        
        for task_priority, expected_task_weight in test_cases:
            task = Task(
                task_id=f"task_{task_priority.value}",
                capability_id="text_generation",
                input_data={"text": "测试"},
                priority=task_priority,
                timeout=60
            )
            
            priority_score = await task_allocator._calculate_priority_score(task, agent)
            
            # 代理优先级默认为0.5
            agent_priority = 0.5
            expected_score = (expected_task_weight + agent_priority) / 2
            
            assert abs(priority_score - expected_score) < 0.001
    
    @pytest.mark.asyncio
    async def test_estimate_response_time(self, task_allocator, sample_task, sample_agents):
        """测试估计响应时间"""
        agent = sample_agents[0]
        
        with patch.object(task_allocator, '_get_agent_performance_stats', return_value={
            'avg_response_time': 1.5
        }):
            response_time = await task_allocator._estimate_response_time(sample_task, agent)
            
            # 正常优先级任务的复杂度因子为1.0
            # 估计响应时间: 1.5 * 1.0 = 1.5
            assert response_time == 1.5
    
    @pytest.mark.asyncio
    async def test_estimate_cost(self, task_allocator, sample_task, sample_agents):
        """测试估计成本"""
        agent = sample_agents[0]
        
        # 测试标准代理类型
        cost = await task_allocator._estimate_cost(sample_task, agent)
        # 标准代理的基础成本为1.0，正常优先级任务的复杂度因子为1.0
        assert cost == 1.0
        
        # 测试高级代理类型
        premium_agent = sample_agents[1]
        premium_agent.agent_type = "premium"  # 设置代理类型
        
        cost = await task_allocator._estimate_cost(sample_task, premium_agent)
        # 高级代理的基础成本为2.0
        assert cost == 2.0
    
    @pytest.mark.asyncio
    async def test_update_agent_performance(self, task_allocator):
        """测试更新代理性能"""
        agent_id = "test_agent"
        
        # 第一次更新
        await task_allocator.update_agent_performance(agent_id, 2.0, True)
        stats = await task_allocator._get_agent_performance_stats(agent_id)
        
        assert stats['total_requests'] == 1
        assert stats['failed_requests'] == 0
        assert stats['success_rate'] == 1.0
        # 第一次更新时，平均响应时间应该等于输入值
        assert stats['avg_response_time'] == 2.0
        
        # 第二次更新（失败）
        await task_allocator.update_agent_performance(agent_id, 3.0, False)
        stats = await task_allocator._get_agent_performance_stats(agent_id)
        
        assert stats['total_requests'] == 2
        assert stats['failed_requests'] == 1
        assert stats['success_rate'] == 0.5
        # 平均响应时间使用指数移动平均计算
        # 2.0 * 0.9 + 3.0 * 0.1 = 2.1
        assert abs(stats['avg_response_time'] - 2.1) < 0.001
    
    @pytest.mark.asyncio
    async def test_update_agent_load(self, task_allocator):
        """测试更新代理负载"""
        agent_id = "test_agent"
        
        await task_allocator.update_agent_load(agent_id, 5)
        load = await task_allocator._get_agent_load(agent_id)
        
        assert load == 5
    
    @pytest.mark.asyncio
    async def test_get_allocation_history(self, task_allocator):
        """测试获取分配历史"""
        # 添加一些分配记录
        for i in range(5):
            allocation_result = AllocationResult(
                agent_id=f"agent_{i}",
                task_id=f"task_{i}",
                allocation_score=0.8,
                strategy=AllocationStrategy.BEST_MATCH,
                estimated_response_time=1.0,
                estimated_cost=1.0,
                timestamp=datetime.now()
            )
            task_allocator.allocation_history.append(allocation_result)
        
        history = await task_allocator.get_allocation_history(limit=3)
        assert len(history) == 3
        assert history[0].agent_id == "agent_2"
        assert history[1].agent_id == "agent_3"
        assert history[2].agent_id == "agent_4"
    
    @pytest.mark.asyncio
    async def test_get_agent_performance_report(self, task_allocator):
        """测试获取代理性能报告"""
        agent_id = "test_agent"
        
        # 设置一些性能数据
        await task_allocator.update_agent_performance(agent_id, 2.0, True)
        await task_allocator.update_agent_load(agent_id, 3)
        
        # 添加分配记录
        allocation_result = AllocationResult(
            agent_id=agent_id,
            task_id="test_task",
            allocation_score=0.8,
            strategy=AllocationStrategy.BEST_MATCH,
            estimated_response_time=1.0,
            estimated_cost=1.0,
            timestamp=datetime.now()
        )
        task_allocator.allocation_history.append(allocation_result)
        
        # 获取性能报告
        report = await task_allocator.get_agent_performance_report(agent_id)
        
        assert report['agent_id'] == agent_id
        assert 'performance_stats' in report
        assert 'current_load' in report
        assert report['allocation_count'] == 1
        assert report['performance_stats']['total_requests'] == 1
        assert report['performance_stats']['success_rate'] == 1.0
        assert report['current_load'] == 3
    
    @pytest.mark.asyncio
    async def test_global_functions(self, sample_task, sample_agents):
        """测试全局便捷函数"""
        # 测试获取全局分配器
        allocator = get_task_allocator()
        assert allocator is not None
        
        # 测试分配任务函数
        with patch.object(allocator, 'allocate_task', return_value="agent_1"):
            agent_id = await allocate_task(sample_task, sample_agents)
            assert agent_id == "agent_1"
        
        # 测试更新代理性能函数
        with patch.object(allocator, 'update_agent_performance') as mock_update:
            await update_agent_performance("test_agent", 2.0, True)
            mock_update.assert_called_once_with("test_agent", 2.0, True)
        
        # 测试更新代理负载函数
        with patch.object(allocator, 'update_agent_load') as mock_update:
            await update_agent_load("test_agent", 5)
            mock_update.assert_called_once_with("test_agent", 5)
