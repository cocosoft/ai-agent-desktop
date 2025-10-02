"""
任务路由引擎单元测试
测试基于能力的任务分配、负载均衡和优先级管理
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.core.task_router import (
    TaskRouter, Task, TaskResult, TaskPriority, RoutingStrategy, 
    AgentPerformance, get_task_router, start_task_router, stop_task_router
)
from src.core.agent_model import AgentInstance, AgentStatus, AgentConfig, AgentType


class TestTaskRouter:
    """任务路由引擎测试"""
    
    @pytest.fixture
    def task_router(self):
        """创建任务路由引擎"""
        return TaskRouter()
    
    @pytest.fixture
    def sample_agent(self):
        """创建示例代理"""
        config = AgentConfig(
            agent_id="test_agent",
            name="测试代理",
            description="测试代理描述",
            agent_type=AgentType.TEXT_GENERATION,
            priority=1,
            max_concurrent_tasks=5,
            capabilities=[]
        )
        
        return AgentInstance(
            instance_id="test_instance",
            agent_config=config,
            status=AgentStatus.RUNNING,
            performance_metrics={}
        )
    
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
    
    def test_task_router_creation(self, task_router):
        """测试任务路由引擎创建"""
        assert task_router is not None
        assert task_router.logger is not None
        assert isinstance(task_router.agent_performance, dict)
        assert task_router.routing_strategy == RoutingStrategy.BEST_MATCH
        assert task_router.running is False
        assert task_router.router_task is None
    
    @pytest.mark.asyncio
    async def test_submit_task(self, task_router):
        """测试提交任务"""
        capability_id = "text_generation"
        input_data = {"text": "测试输入"}
        
        task_id = await task_router.submit_task(
            capability_id=capability_id,
            input_data=input_data,
            priority=TaskPriority.HIGH,
            timeout=30,
            metadata={"test": "metadata"}
        )
        
        assert task_id is not None
        assert len(task_id) > 0
        
        # 检查任务队列
        assert task_router.task_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_route_task_no_agents(self, task_router, sample_task):
        """测试路由任务（无可用代理）"""
        result = await task_router._route_task(sample_task)
        
        assert result.task_id == sample_task.task_id
        assert result.success is False
        assert "没有可用的代理" in result.error_message
    
    @pytest.mark.asyncio
    async def test_select_agent_best_match(self, task_router, sample_agent, sample_task):
        """测试最佳匹配策略选择代理"""
        agents = [sample_agent]
        
        with patch.object(task_router, '_calculate_match_score', return_value=0.8):
            selected_agent = await task_router._select_best_match(agents, sample_task)
        
        assert selected_agent == sample_agent
    
    @pytest.mark.asyncio
    async def test_select_agent_fastest_response(self, task_router, sample_agent, sample_task):
        """测试最快响应策略选择代理"""
        agents = [sample_agent]
        
        # 设置性能指标
        perf = AgentPerformance(
            agent_id=sample_agent.agent_config.agent_id,
            capability_id=sample_task.capability_id,
            average_response_time=1.5
        )
        task_router.agent_performance[sample_agent.agent_config.agent_id] = {
            sample_task.capability_id: perf
        }
        
        selected_agent = await task_router._select_fastest_response(agents, sample_task)
        
        assert selected_agent == sample_agent
    
    @pytest.mark.asyncio
    async def test_select_agent_load_balanced(self, task_router, sample_agent, sample_task):
        """测试负载均衡策略选择代理"""
        agents = [sample_agent]
        
        with patch.object(task_router, '_calculate_agent_load', return_value=0.3):
            selected_agent = await task_router._select_load_balanced(agents, sample_task)
        
        assert selected_agent == sample_agent
    
    @pytest.mark.asyncio
    async def test_calculate_match_score(self, task_router, sample_agent, sample_task):
        """测试计算匹配分数"""
        with patch.object(task_router, '_check_capability_match', return_value=1.0), \
             patch.object(task_router, '_calculate_performance_score', return_value=0.8), \
             patch.object(task_router, '_calculate_load_score', return_value=0.9), \
             patch.object(task_router, '_calculate_priority_score', return_value=1.0):
            
            score = await task_router._calculate_match_score(sample_agent, sample_task)
        
        # 验证分数计算：1.0*0.4 + 0.8*0.3 + 0.9*0.2 + 1.0*0.1 = 0.4 + 0.24 + 0.18 + 0.1 = 0.92
        assert score == pytest.approx(0.92, 0.01)
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, task_router, sample_agent, sample_task):
        """测试成功执行任务"""
        result = await task_router._execute_task(sample_agent, sample_task)
        
        assert result.task_id == sample_task.task_id
        assert result.success is True
        assert result.output_data is not None
        assert "result" in result.output_data
        assert result.execution_time is not None
    
    @pytest.mark.asyncio
    async def test_update_performance_stats(self, task_router, sample_agent, sample_task):
        """测试更新性能统计"""
        result = TaskResult(
            task_id=sample_task.task_id,
            success=True,
            output_data={"result": "测试结果"},
            execution_time=1.5
        )
        
        await task_router._update_performance_stats(
            sample_agent, sample_task.capability_id, result, 1.5
        )
        
        # 验证性能统计已更新
        assert sample_agent.agent_config.agent_id in task_router.agent_performance
        assert sample_task.capability_id in task_router.agent_performance[sample_agent.agent_config.agent_id]
        
        perf = task_router.agent_performance[sample_agent.agent_config.agent_id][sample_task.capability_id]
        assert perf.total_tasks == 1
        assert perf.successful_tasks == 1
        assert perf.failed_tasks == 0
        assert perf.total_execution_time == 1.5
        assert perf.average_response_time == 1.5
        assert perf.success_rate == 1.0
        assert perf.last_used is not None
    
    @pytest.mark.asyncio
    async def test_update_performance_stats_failure(self, task_router, sample_agent, sample_task):
        """测试更新性能统计（任务失败）"""
        result = TaskResult(
            task_id=sample_task.task_id,
            success=False,
            error_message="任务执行失败",
            execution_time=0.5
        )
        
        await task_router._update_performance_stats(
            sample_agent, sample_task.capability_id, result, 0.5
        )
        
        perf = task_router.agent_performance[sample_agent.agent_config.agent_id][sample_task.capability_id]
        assert perf.total_tasks == 1
        assert perf.successful_tasks == 0
        assert perf.failed_tasks == 1
        assert perf.success_rate == 0.0
    
    def test_set_routing_strategy(self, task_router):
        """测试设置路由策略"""
        task_router.set_routing_strategy(RoutingStrategy.FASTEST_RESPONSE)
        
        assert task_router.routing_strategy == RoutingStrategy.FASTEST_RESPONSE
    
    def test_get_performance_stats(self, task_router):
        """测试获取性能统计"""
        # 添加一些性能数据
        perf1 = AgentPerformance(
            agent_id="agent1",
            capability_id="text_generation",
            total_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            total_execution_time=15.0,
            average_response_time=1.5,
            success_rate=0.8
        )
        
        perf2 = AgentPerformance(
            agent_id="agent2",
            capability_id="code_generation",
            total_tasks=5,
            successful_tasks=4,
            failed_tasks=1,
            total_execution_time=10.0,
            average_response_time=2.0,
            success_rate=0.8
        )
        
        task_router.agent_performance["agent1"] = {"text_generation": perf1}
        task_router.agent_performance["agent2"] = {"code_generation": perf2}
        
        stats = task_router.get_performance_stats()
        
        assert stats["total_tasks"] == 15
        assert stats["successful_tasks"] == 12
        assert stats["failed_tasks"] == 3
        assert stats["success_rate"] == pytest.approx(0.8, 0.01)
        assert stats["routing_strategy"] == "best_match"
        assert stats["running_tasks"] == 0
        assert stats["queued_tasks"] == 0
    
    @pytest.mark.asyncio
    async def test_start_stop_router(self, task_router):
        """测试启动和停止路由引擎"""
        # 启动路由引擎
        await task_router.start()
        assert task_router.running is True
        assert task_router.router_task is not None
        
        # 停止路由引擎
        await task_router.stop()
        assert task_router.running is False


class TestGlobalFunctions:
    """全局函数测试"""
    
    def test_get_task_router(self):
        """测试获取全局任务路由引擎"""
        router1 = get_task_router()
        router2 = get_task_router()
        
        assert router1 is not None
        assert router2 is not None
        assert router1 is router2  # 应该是同一个实例
    
    @pytest.mark.asyncio
    async def test_start_stop_task_router(self):
        """测试启动和停止全局任务路由引擎"""
        # 使用Mock来避免实际启动路由引擎
        with patch('src.core.task_router.TaskRouter.start') as mock_start, \
             patch('src.core.task_router.TaskRouter.stop') as mock_stop:
            
            # 测试启动
            await start_task_router()
            mock_start.assert_called_once()
            
            # 测试停止
            await stop_task_router()
            mock_stop.assert_called_once()


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def task_router(self):
        """创建任务路由引擎"""
        return TaskRouter()
    
    @pytest.fixture
    def sample_agents(self):
        """创建示例代理列表"""
        config1 = AgentConfig(
            agent_id="agent1",
            name="代理1",
            description="代理1描述",
            agent_type=AgentType.TEXT_GENERATION,
            priority=1,
            max_concurrent_tasks=5,
            capabilities=[]
        )
        
        config2 = AgentConfig(
            agent_id="agent2",
            name="代理2",
            description="代理2描述",
            agent_type=AgentType.CODE_GENERATION,
            priority=2,
            max_concurrent_tasks=3,
            capabilities=[]
        )
        
        agent1 = AgentInstance(
            instance_id="instance1",
            agent_config=config1,
            status=AgentStatus.RUNNING,
            performance_metrics={}
        )
        
        agent2 = AgentInstance(
            instance_id="instance2",
            agent_config=config2,
            status=AgentStatus.RUNNING,
            performance_metrics={}
        )
        
        return [agent1, agent2]
    
    @pytest.mark.asyncio
    async def test_complete_task_routing_workflow(self, task_router, sample_agents):
        """测试完整任务路由工作流"""
        # 1. 设置路由策略
        task_router.set_routing_strategy(RoutingStrategy.BEST_MATCH)
        
        # 2. 模拟获取可用代理
        with patch.object(task_router, '_get_available_agents', return_value=sample_agents):
            # 3. 创建任务
            task = Task(
                task_id="workflow_task",
                capability_id="text_generation",
                input_data={"text": "工作流测试输入"},
                priority=TaskPriority.HIGH
            )
            
            # 4. 路由任务
            with patch.object(task_router, '_calculate_match_score', return_value=0.9):
                result = await task_router._route_task(task)
            
            # 5. 验证结果
            assert result.task_id == task.task_id
            assert result.success is True
            assert result.agent_id is not None
        
        # 6. 验证性能统计已更新
        stats = task_router.get_performance_stats()
        assert stats["total_tasks"] == 1
        assert stats["successful_tasks"] == 1
        assert stats["success_rate"] == 1.0


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
