"""
性能监控面板单元测试
测试性能数据收集、报警管理、图表显示等功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.ui.performance_monitor import (
    PerformanceDataCollector, AlertManager, PerformanceMetric,
    PerformanceDataPoint, AlertCondition, PerformanceAlert
)
from src.core.agent_lifecycle import AgentInstance, AgentStatus


class TestPerformanceDataCollector:
    """性能数据收集器测试"""
    
    @pytest.fixture
    def data_collector(self):
        """创建数据收集器实例"""
        return PerformanceDataCollector()
    
    @pytest.fixture
    def sample_agent(self):
        """创建示例代理"""
        mock_config = Mock()
        mock_config.agent_id = "test_agent_config"
        
        return AgentInstance(
            instance_id="test_agent",
            agent_config=mock_config,
            status=AgentStatus.RUNNING
        )
    
    @pytest.mark.asyncio
    async def test_collect_agent_performance(self, data_collector, sample_agent):
        """测试收集代理性能数据"""
        # 设置代理属性
        sample_agent.avg_response_time = 2.5
        sample_agent.successful_tasks = 8
        sample_agent.total_tasks = 10
        sample_agent.current_tasks = 3
        sample_agent.cpu_usage = 45.0
        sample_agent.memory_usage = 65.0
        
        points = await data_collector.collect_agent_performance(sample_agent)
        
        # 应该收集到5个数据点
        assert len(points) == 5
        
        # 验证数据点类型
        metrics = [point.metric for point in points]
        assert PerformanceMetric.RESPONSE_TIME in metrics
        assert PerformanceMetric.SUCCESS_RATE in metrics
        assert PerformanceMetric.LOAD in metrics
        assert PerformanceMetric.CPU_USAGE in metrics
        assert PerformanceMetric.MEMORY_USAGE in metrics
        
        # 验证成功率计算
        success_rate_point = next(p for p in points if p.metric == PerformanceMetric.SUCCESS_RATE)
        assert success_rate_point.value == 0.8  # 8/10 = 0.8
    
    @pytest.mark.asyncio
    async def test_collect_agent_performance_missing_attributes(self, data_collector, sample_agent):
        """测试收集缺少属性的代理性能数据"""
        # 不设置任何属性，只使用默认属性
        points = await data_collector.collect_agent_performance(sample_agent)
        
        # 应该收集响应时间和负载数据
        assert len(points) == 2
        
        # 验证数据点类型
        metrics = [point.metric for point in points]
        assert PerformanceMetric.RESPONSE_TIME in metrics
        assert PerformanceMetric.LOAD in metrics
        
        # 验证默认值
        response_time_point = next(p for p in points if p.metric == PerformanceMetric.RESPONSE_TIME)
        load_point = next(p for p in points if p.metric == PerformanceMetric.LOAD)
        assert response_time_point.value == 0.0  # 默认响应时间
        assert load_point.value == 0  # 默认current_tasks为0
    
    def test_add_data_points(self, data_collector):
        """测试添加数据点"""
        points = [
            PerformanceDataPoint(
                timestamp=datetime.now(),
                value=1.0,
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=datetime.now(),
                value=0.9,
                metric=PerformanceMetric.SUCCESS_RATE,
                agent_id="agent_1"
            )
        ]
        
        data_collector.add_data_points(points)
        
        assert len(data_collector.data_points) == 2
        assert data_collector.data_points[0].value == 1.0
        assert data_collector.data_points[1].value == 0.9
    
    def test_get_recent_data(self, data_collector):
        """测试获取最近数据"""
        # 添加一些测试数据
        now = datetime.now()
        old_time = now - timedelta(hours=2)
        
        points = [
            PerformanceDataPoint(
                timestamp=old_time,
                value=1.0,
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now,
                value=2.0,
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now,
                value=0.8,
                metric=PerformanceMetric.SUCCESS_RATE,
                agent_id="agent_1"
            )
        ]
        
        data_collector.add_data_points(points)
        
        # 获取最近1小时的响应时间数据
        recent_data = data_collector.get_recent_data(
            PerformanceMetric.RESPONSE_TIME, 
            agent_id="agent_1",
            hours=1
        )
        
        # 应该只返回最近的数据点
        assert len(recent_data) == 1
        assert recent_data[0].value == 2.0
    
    def test_get_statistics(self, data_collector):
        """测试获取统计信息"""
        # 添加测试数据
        now = datetime.now()
        points = [
            PerformanceDataPoint(
                timestamp=now - timedelta(minutes=30),
                value=1.0,
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now - timedelta(minutes=15),
                value=2.0,
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now,
                value=3.0,
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            )
        ]
        
        data_collector.add_data_points(points)
        
        stats = data_collector.get_statistics(
            PerformanceMetric.RESPONSE_TIME,
            agent_id="agent_1",
            hours=1
        )
        
        assert stats['count'] == 3
        assert stats['min'] == 1.0
        assert stats['max'] == 3.0
        assert stats['avg'] == 2.0
        assert stats['latest'] == 3.0
    
    def test_get_statistics_no_data(self, data_collector):
        """测试获取无数据的统计信息"""
        stats = data_collector.get_statistics(
            PerformanceMetric.RESPONSE_TIME,
            agent_id="nonexistent_agent",
            hours=1
        )
        
        assert stats['count'] == 0
        assert stats['min'] == 0
        assert stats['max'] == 0
        assert stats['avg'] == 0
        assert stats['latest'] == 0


class TestAlertManager:
    """报警管理器测试"""
    
    @pytest.fixture
    def alert_manager(self):
        """创建报警管理器实例"""
        return AlertManager()
    
    @pytest.fixture
    def sample_condition(self):
        """创建示例报警条件"""
        return AlertCondition(
            metric=PerformanceMetric.RESPONSE_TIME,
            threshold=5.0,
            operator=">",
            duration=30,
            severity="warning"
        )
    
    @pytest.fixture
    def sample_data_collector(self):
        """创建示例数据收集器"""
        collector = PerformanceDataCollector()
        
        # 添加一些测试数据
        now = datetime.now()
        points = [
            PerformanceDataPoint(
                timestamp=now - timedelta(seconds=20),
                value=6.0,  # 超过阈值
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now - timedelta(seconds=10),
                value=7.0,  # 超过阈值
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now,
                value=8.0,  # 超过阈值
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            )
        ]
        
        collector.add_data_points(points)
        return collector
    
    def test_add_condition(self, alert_manager, sample_condition):
        """测试添加报警条件"""
        alert_manager.add_condition(sample_condition)
        
        assert len(alert_manager.conditions) == 1
        assert alert_manager.conditions[0] == sample_condition
    
    def test_remove_condition(self, alert_manager, sample_condition):
        """测试移除报警条件"""
        # 添加条件ID以便移除
        sample_condition.condition_id = "test_condition"
        alert_manager.add_condition(sample_condition)
        
        alert_manager.remove_condition("test_condition")
        
        assert len(alert_manager.conditions) == 0
    
    def test_check_conditions_trigger_alert(self, alert_manager, sample_condition, sample_data_collector):
        """测试触发报警条件"""
        alert_manager.add_condition(sample_condition)
        
        alert_manager.check_conditions(sample_data_collector)
        
        # 应该触发报警
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        
        alert = active_alerts[0]
        assert alert.condition == sample_condition
        assert alert.current_value == 8.0  # 最新值
        assert not alert.acknowledged
    
    def test_check_conditions_no_trigger(self, alert_manager, sample_data_collector):
        """测试不触发报警条件"""
        # 创建不会触发的条件
        condition = AlertCondition(
            metric=PerformanceMetric.RESPONSE_TIME,
            threshold=10.0,  # 阈值更高
            operator=">",
            duration=30,
            severity="warning"
        )
        
        alert_manager.add_condition(condition)
        alert_manager.check_conditions(sample_data_collector)
        
        # 不应该触发报警
        assert len(alert_manager.get_active_alerts()) == 0
    
    def test_check_conditions_resolve_alert(self, alert_manager, sample_condition, sample_data_collector):
        """测试解除报警"""
        # 先触发报警
        alert_manager.add_condition(sample_condition)
        alert_manager.check_conditions(sample_data_collector)
        
        assert len(alert_manager.get_active_alerts()) == 1
        
        # 创建不满足条件的数据
        new_collector = PerformanceDataCollector()
        now = datetime.now()
        points = [
            PerformanceDataPoint(
                timestamp=now - timedelta(seconds=20),
                value=3.0,  # 低于阈值
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now - timedelta(seconds=10),
                value=2.0,  # 低于阈值
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            ),
            PerformanceDataPoint(
                timestamp=now,
                value=1.0,  # 低于阈值
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id="agent_1"
            )
        ]
        
        new_collector.add_data_points(points)
        
        # 再次检查条件
        alert_manager.check_conditions(new_collector)
        
        # 报警应该被解除
        assert len(alert_manager.get_active_alerts()) == 0
        assert len(alert_manager.alert_history) == 1
        assert alert_manager.alert_history[0].resolved_at is not None
    
    def test_acknowledge_alert(self, alert_manager, sample_condition, sample_data_collector):
        """测试确认报警"""
        alert_manager.add_condition(sample_condition)
        alert_manager.check_conditions(sample_data_collector)
        
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        
        alert_id = active_alerts[0].alert_id
        alert_manager.acknowledge_alert(alert_id)
        
        # 报警应该被确认
        updated_alerts = alert_manager.get_active_alerts()
        assert len(updated_alerts) == 1
        assert updated_alerts[0].acknowledged is True
    
    def test_get_recent_alerts(self, alert_manager, sample_condition, sample_data_collector):
        """测试获取最近报警"""
        alert_manager.add_condition(sample_condition)
        alert_manager.check_conditions(sample_data_collector)
        
        recent_alerts = alert_manager.get_recent_alerts(hours=24)
        
        assert len(recent_alerts) == 1
        assert recent_alerts[0].condition == sample_condition


class TestPerformanceMetric:
    """性能指标枚举测试"""
    
    def test_metric_values(self):
        """测试指标值"""
        assert PerformanceMetric.RESPONSE_TIME.value == "response_time"
        assert PerformanceMetric.SUCCESS_RATE.value == "success_rate"
        assert PerformanceMetric.THROUGHPUT.value == "throughput"
        assert PerformanceMetric.CPU_USAGE.value == "cpu_usage"
        assert PerformanceMetric.MEMORY_USAGE.value == "memory_usage"
        assert PerformanceMetric.LOAD.value == "load"
    
    def test_metric_iteration(self):
        """测试指标迭代"""
        metrics = list(PerformanceMetric)
        assert len(metrics) == 6
        
        metric_names = [metric.value for metric in metrics]
        expected_names = [
            "response_time", "success_rate", "throughput",
            "cpu_usage", "memory_usage", "load"
        ]
        
        assert metric_names == expected_names


class TestPerformanceDataPoint:
    """性能数据点测试"""
    
    def test_data_point_creation(self):
        """测试数据点创建"""
        timestamp = datetime.now()
        data_point = PerformanceDataPoint(
            timestamp=timestamp,
            value=2.5,
            metric=PerformanceMetric.RESPONSE_TIME,
            agent_id="test_agent"
        )
        
        assert data_point.timestamp == timestamp
        assert data_point.value == 2.5
        assert data_point.metric == PerformanceMetric.RESPONSE_TIME
        assert data_point.agent_id == "test_agent"
    
    def test_data_point_without_agent(self):
        """测试无代理的数据点"""
        timestamp = datetime.now()
        data_point = PerformanceDataPoint(
            timestamp=timestamp,
            value=75.0,
            metric=PerformanceMetric.CPU_USAGE
        )
        
        assert data_point.timestamp == timestamp
        assert data_point.value == 75.0
        assert data_point.metric == PerformanceMetric.CPU_USAGE
        assert data_point.agent_id is None


class TestAlertCondition:
    """报警条件测试"""
    
    def test_condition_creation(self):
        """测试条件创建"""
        condition = AlertCondition(
            metric=PerformanceMetric.SUCCESS_RATE,
            threshold=0.8,
            operator="<",
            duration=60,
            severity="critical"
        )
        
        assert condition.metric == PerformanceMetric.SUCCESS_RATE
        assert condition.threshold == 0.8
        assert condition.operator == "<"
        assert condition.duration == 60
        assert condition.severity == "critical"
    
    def test_condition_operators(self):
        """测试条件操作符"""
        operators = [">", "<", ">=", "<=", "=="]
        
        for operator in operators:
            condition = AlertCondition(
                metric=PerformanceMetric.RESPONSE_TIME,
                threshold=5.0,
                operator=operator,
                duration=30,
                severity="warning"
            )
            
            assert condition.operator == operator


class TestPerformanceAlert:
    """性能报警测试"""
    
    def test_alert_creation(self):
        """测试报警创建"""
        condition = AlertCondition(
            metric=PerformanceMetric.LOAD,
            threshold=8,
            operator=">",
            duration=30,
            severity="warning"
        )
        
        triggered_at = datetime.now()
        alert = PerformanceAlert(
            alert_id="test_alert",
            condition=condition,
            current_value=9.0,
            triggered_at=triggered_at
        )
        
        assert alert.alert_id == "test_alert"
        assert alert.condition == condition
        assert alert.current_value == 9.0
        assert alert.triggered_at == triggered_at
        assert alert.resolved_at is None
        assert alert.acknowledged is False
    
    def test_alert_with_resolution(self):
        """测试带解决时间的报警"""
        condition = AlertCondition(
            metric=PerformanceMetric.MEMORY_USAGE,
            threshold=90.0,
            operator=">",
            duration=60,
            severity="critical"
        )
        
        triggered_at = datetime.now()
        resolved_at = triggered_at + timedelta(minutes=5)
        
        alert = PerformanceAlert(
            alert_id="test_alert",
            condition=condition,
            current_value=95.0,
            triggered_at=triggered_at,
            resolved_at=resolved_at,
            acknowledged=True
        )
        
        assert alert.alert_id == "test_alert"
        assert alert.condition == condition
        assert alert.current_value == 95.0
        assert alert.triggered_at == triggered_at
        assert alert.resolved_at == resolved_at
        assert alert.acknowledged is True
