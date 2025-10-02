"""
能力测试优化器单元测试
测试能力测试优化的功能
"""

import pytest
import sys
import os
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.capability_test_optimizer import (
    CapabilityTestOptimizer, TestOptimizationConfig, TestOptimizationStrategy,
    TestPriority, TestBatchResult, PerformanceMetrics
)
from src.core.capability_model import (
    Capability, CapabilityType, CapabilityRegistry,
    CapabilityParameter, CapabilityOutput, CapabilityTest, TestResult, CapabilityTestResult
)
from src.core.capability_discovery import CapabilityDiscovery


class TestCapabilityTestOptimizer:
    """能力测试优化器测试类"""
    
    @pytest.fixture
    def capability_registry(self):
        """创建能力注册表"""
        registry = CapabilityRegistry()
        
        # 添加测试能力
        test_capability = Capability(
            capability_id="test_capability_1",
            name="测试能力1",
            description="这是一个测试能力",
            capability_type=CapabilityType.TEXT_GENERATION,
            parameters=[
                CapabilityParameter(
                    name="prompt",
                    type="string",
                    description="输入提示",
                    required=True
                )
            ],
            outputs=[
                CapabilityOutput(
                    name="generated_text",
                    type="string",
                    description="生成的文本",
                    format="plain"
                )
            ],
            tags=["test", "text"],
            category="text_processing",
            complexity=2
        )
        
        # 添加基础测试用例
        base_test = CapabilityTest(
            test_id="base_test_1",
            name="基础测试",
            description="基础功能测试",
            input_data={"prompt": "你好，请回复。"},
            expected_output={"generated_text": "测试回复"},
            priority=1,
            timeout=30
        )
        test_capability.tests = [base_test]
        
        registry.register_capability(test_capability)
        return registry
    
    @pytest.fixture
    def capability_discovery(self):
        """创建能力发现器"""
        discovery = Mock(spec=CapabilityDiscovery)
        discovery.test_capability_on_model = AsyncMock()
        return discovery
    
    @pytest.fixture
    def test_optimizer(self, capability_registry, capability_discovery):
        """创建能力测试优化器"""
        return CapabilityTestOptimizer(capability_registry, capability_discovery)
    
    def test_initialization(self, test_optimizer):
        """测试初始化"""
        assert test_optimizer is not None
        assert test_optimizer.capability_registry is not None
        assert test_optimizer.capability_discovery is not None
        assert test_optimizer.config is not None
        assert test_optimizer.performance_metrics == {}
        assert test_optimizer.test_history == {}
    
    @pytest.mark.asyncio
    async def test_optimize_test_suite_comprehensive(self, test_optimizer):
        """测试全面测试策略"""
        optimized_tests = await test_optimizer.optimize_test_suite(
            "test_capability_1", "test_model_1", TestOptimizationStrategy.COMPREHENSIVE
        )
        
        assert optimized_tests is not None
        assert len(optimized_tests) > 0
        assert len(optimized_tests) <= test_optimizer.config.max_test_cases_per_capability
        
        # 检查是否包含基础测试和生成的测试
        test_names = [test.name for test in optimized_tests]
        assert "基础测试" in test_names
        assert any("文本生成测试" in name for name in test_names)
    
    @pytest.mark.asyncio
    async def test_optimize_test_suite_performance(self, test_optimizer):
        """测试性能优先策略"""
        optimized_tests = await test_optimizer.optimize_test_suite(
            "test_capability_1", "test_model_1", TestOptimizationStrategy.PERFORMANCE
        )
        
        assert optimized_tests is not None
        assert len(optimized_tests) <= test_optimizer.config.max_test_cases_per_capability
        
        # 检查是否包含性能基准测试
        test_names = [test.name for test in optimized_tests]
        assert "性能基准测试" in test_names
    
    @pytest.mark.asyncio
    async def test_optimize_test_suite_cost_effective(self, test_optimizer):
        """测试成本效益策略"""
        optimized_tests = await test_optimizer.optimize_test_suite(
            "test_capability_1", "test_model_1", TestOptimizationStrategy.COST_EFFECTIVE
        )
        
        assert optimized_tests is not None
        assert len(optimized_tests) <= test_optimizer.config.max_test_cases_per_capability
        
        # 检查是否包含成本效益测试
        test_names = [test.name for test in optimized_tests]
        assert "成本效益测试" in test_names
    
    @pytest.mark.asyncio
    async def test_optimize_test_suite_minimal(self, test_optimizer):
        """测试最小化策略"""
        optimized_tests = await test_optimizer.optimize_test_suite(
            "test_capability_1", "test_model_1", TestOptimizationStrategy.MINIMAL
        )
        
        assert optimized_tests is not None
        assert len(optimized_tests) <= 1  # 最小化策略应该只有1个测试
    
    @pytest.mark.asyncio
    async def test_optimize_test_suite_adaptive(self, test_optimizer):
        """测试自适应策略"""
        optimized_tests = await test_optimizer.optimize_test_suite(
            "test_capability_1", "test_model_1", TestOptimizationStrategy.ADAPTIVE
        )
        
        assert optimized_tests is not None
        assert len(optimized_tests) <= test_optimizer.config.max_test_cases_per_capability
    
    @pytest.mark.asyncio
    async def test_optimize_test_suite_invalid_capability(self, test_optimizer):
        """测试无效能力"""
        optimized_tests = await test_optimizer.optimize_test_suite(
            "invalid_capability", "test_model_1"
        )
        
        assert optimized_tests == []
    
    @pytest.mark.asyncio
    async def test_run_optimized_tests(self, test_optimizer, capability_discovery):
        """测试运行优化测试"""
        # 模拟测试结果
        mock_result = CapabilityTestResult(
            test_id="test_1",
            capability_id="test_capability_1",
            model_id="test_model_1",
            result=TestResult.PASSED,
            actual_output={"generated_text": "测试回复"},
            error_message=None,
            execution_time=100.0,
            timestamp=time.time()
        )
        capability_discovery.test_capability_on_model.return_value = mock_result
        
        # 运行优化测试
        batch_result = await test_optimizer.run_optimized_tests(
            "test_capability_1", "test_model_1"
        )
        
        assert batch_result is not None
        assert batch_result.batch_id is not None
        assert batch_result.capability_id == "test_capability_1"
        assert batch_result.model_id == "test_model_1"
        assert batch_result.total_tests > 0
        assert batch_result.successful_tests > 0
        assert batch_result.avg_response_time > 0
        assert len(batch_result.test_results) > 0
        assert len(batch_result.optimization_suggestions) >= 0
    
    @pytest.mark.asyncio
    async def test_run_optimized_tests_with_failures(self, test_optimizer, capability_discovery):
        """测试运行优化测试（包含失败）"""
        # 模拟部分测试失败
        def mock_test_result(test_id):
            if "performance" in test_id:
                return CapabilityTestResult(
                    test_id=test_id,
                    capability_id="test_capability_1",
                    model_id="test_model_1",
                    result=TestResult.FAILED,
                    actual_output={},
                    error_message="超时错误",
                    execution_time=200.0,
                    timestamp=time.time()
                )
            else:
                return CapabilityTestResult(
                    test_id=test_id,
                    capability_id="test_capability_1",
                    model_id="test_model_1",
                    result=TestResult.PASSED,
                    actual_output={"generated_text": "测试回复"},
                    error_message=None,
                    execution_time=100.0,
                    timestamp=time.time()
                )
        
        capability_discovery.test_capability_on_model.side_effect = mock_test_result
        
        # 运行优化测试
        batch_result = await test_optimizer.run_optimized_tests(
            "test_capability_1", "test_model_1"
        )
        
        assert batch_result is not None
        assert batch_result.failed_tests > 0
        assert len(batch_result.optimization_suggestions) > 0
    
    def test_generate_optimization_suggestions(self, test_optimizer):
        """测试生成优化建议"""
        # 测试低成功率情况
        suggestions = test_optimizer._generate_optimization_suggestions(
            "test_capability_1", "test_model_1",
            successful_tests=2, failed_tests=8,
            avg_response_time=1000.0, total_cost=0.5, total_tests=10
        )
        
        assert len(suggestions) > 0
        assert any("成功率较低" in suggestion for suggestion in suggestions)
        
        # 测试高响应时间情况
        suggestions = test_optimizer._generate_optimization_suggestions(
            "test_capability_1", "test_model_1",
            successful_tests=8, failed_tests=2,
            avg_response_time=6000.0, total_cost=0.1, total_tests=10
        )
        
        assert len(suggestions) > 0
        assert any("响应时间较长" in suggestion for suggestion in suggestions)
        
        # 测试高成本情况
        suggestions = test_optimizer._generate_optimization_suggestions(
            "test_capability_1", "test_model_1",
            successful_tests=8, failed_tests=2,
            avg_response_time=1000.0, total_cost=2.0, total_tests=10
        )
        
        assert len(suggestions) > 0
        assert any("测试成本较高" in suggestion for suggestion in suggestions)
        
        # 测试良好性能情况
        suggestions = test_optimizer._generate_optimization_suggestions(
            "test_capability_1", "test_model_1",
            successful_tests=9, failed_tests=1,
            avg_response_time=1500.0, total_cost=0.05, total_tests=10
        )
        
        assert len(suggestions) > 0
        assert any("性能表现良好" in suggestion for suggestion in suggestions)
    
    def test_update_performance_metrics(self, test_optimizer):
        """测试更新性能指标"""
        # 第一次更新
        test_optimizer._update_performance_metrics(
            "test_capability_1", "test_model_1",
            successful_tests=8, failed_tests=2,
            avg_response_time=1000.0, total_cost=0.1, total_tests=10
        )
        
        metrics_key = "test_capability_1_test_model_1"
        assert metrics_key in test_optimizer.performance_metrics
        
        metrics = test_optimizer.performance_metrics[metrics_key]
        assert metrics.capability_id == "test_capability_1"
        assert metrics.model_id == "test_model_1"
        assert metrics.total_tests == 10
        assert metrics.successful_tests == 8
        assert metrics.success_rate == 0.8
        assert metrics.avg_response_time == 1000.0
        assert metrics.total_cost == 0.1
        assert metrics.avg_cost_per_test == 0.01
        
        # 第二次更新
        test_optimizer._update_performance_metrics(
            "test_capability_1", "test_model_1",
            successful_tests=5, failed_tests=0,
            avg_response_time=800.0, total_cost=0.05, total_tests=5
        )
        
        updated_metrics = test_optimizer.performance_metrics[metrics_key]
        assert updated_metrics.total_tests == 15
        assert updated_metrics.successful_tests == 13
        assert updated_metrics.success_rate == pytest.approx(13/15, 0.01)
        assert updated_metrics.avg_response_time == pytest.approx((1000*10 + 800*5)/15, 0.01)
        assert updated_metrics.total_cost == pytest.approx(0.15, 0.01)
        assert updated_metrics.avg_cost_per_test == pytest.approx(0.01, 0.01)
    
    def test_get_performance_metrics(self, test_optimizer):
        """测试获取性能指标"""
        # 先更新指标
        test_optimizer._update_performance_metrics(
            "test_capability_1", "test_model_1",
            successful_tests=8, failed_tests=2,
            avg_response_time=1000.0, total_cost=0.1, total_tests=10
        )
        
        # 获取指标
        metrics = test_optimizer.get_performance_metrics("test_capability_1", "test_model_1")
        
        assert metrics is not None
        assert metrics.capability_id == "test_capability_1"
        assert metrics.model_id == "test_model_1"
        assert metrics.total_tests == 10
        assert metrics.success_rate == 0.8
        
        # 获取不存在的指标
        metrics = test_optimizer.get_performance_metrics("nonexistent", "model")
        assert metrics is None
    
    def test_get_test_history(self, test_optimizer):
        """测试获取测试历史"""
        # 初始状态应该为空
        history = test_optimizer.get_test_history("test_capability_1", "test_model_1")
        assert history == []
        
        # 添加测试历史
        batch_result = TestBatchResult(
            batch_id="test_batch_1",
            capability_id="test_capability_1",
            model_id="test_model_1",
            total_tests=5,
            successful_tests=4,
            failed_tests=1,
            avg_response_time=1000.0,
            total_cost=0.05,
            start_time=1000.0,
            end_time=1100.0,
            test_results=[],
            optimization_suggestions=[]
        )
        
        history_key = "test_capability_1_test_model_1"
        test_optimizer.test_history[history_key] = [batch_result]
        
        # 获取历史
        history = test_optimizer.get_test_history("test_capability_1", "test_model_1")
        assert len(history) == 1
        assert history[0].batch_id == "test_batch_1"
    
    def test_generate_test_report(self, test_optimizer):
        """测试生成测试报告"""
        # 创建测试结果
        test_results = [
            CapabilityTestResult(
                test_id="test_1",
                capability_id="test_capability_1",
                model_id="test_model_1",
                result=TestResult.PASSED,
                actual_output={"generated_text": "回复1"},
                error_message=None,
                execution_time=100.0,
                timestamp=time.time()
            ),
            CapabilityTestResult(
                test_id="test_2",
                capability_id="test_capability_1",
                model_id="test_model_1",
                result=TestResult.FAILED,
                actual_output={},
                error_message="超时错误",
                execution_time=200.0,
                timestamp=time.time()
            )
        ]
        
        batch_result = TestBatchResult(
            batch_id="test_batch_1",
            capability_id="test_capability_1",
            model_id="test_model_1",
            total_tests=2,
            successful_tests=1,
            failed_tests=1,
            avg_response_time=150.0,
            total_cost=0.03,
            start_time=1000.0,
            end_time=1100.0,
            test_results=test_results,
            optimization_suggestions=["建议1", "建议2"]
        )
        
        # 生成报告
        report = test_optimizer.generate_test_report(batch_result)
        
        assert report is not None
        assert report["batch_id"] == "test_batch_1"
        assert report["capability_id"] == "test_capability_1"
        assert report["model_id"] == "test_model_1"
        assert report["test_summary"]["total_tests"] == 2
        assert report["test_summary"]["successful_tests"] == 1
        assert report["test_summary"]["failed_tests"] == 1
        assert report["test_summary"]["success_rate"] == 0.5
        assert report["test_summary"]["avg_response_time"] == 150.0
        assert report["test_summary"]["total_cost"] == 0.03
        assert report["test_summary"]["duration"] == 100.0
        assert len(report["optimization_suggestions"]) == 2
        assert len(report["test_details"]) == 2
        assert "timestamp" in report
    
    def test_export_performance_data(self, test_optimizer):
        """测试导出性能数据"""
        # 先更新一些指标
        test_optimizer._update_performance_metrics(
            "test_capability_1", "test_model_1",
            successful_tests=8, failed_tests=2,
            avg_response_time=1000.0, total_cost=0.1, total_tests=10
        )
        
        test_optimizer._update_performance_metrics(
            "test_capability_2", "test_model_2",
            successful_tests=5, failed_tests=0,
            avg_response_time=800.0, total_cost=0.05, total_tests=5
        )
        
        # 添加测试历史
        batch_result = TestBatchResult(
            batch_id="test_batch_1",
            capability_id="test_capability_1",
            model_id="test_model_1",
            total_tests=5,
            successful_tests=4,
            failed_tests=1,
            avg_response_time=1000.0,
            total_cost=0.05,
            start_time=1000.0,
            end_time=1100.0,
            test_results=[],
            optimization_suggestions=[]
        )
        
        history_key = "test_capability_1_test_model_1"
        test_optimizer.test_history[history_key] = [batch_result]
        
        # 导出性能数据
        performance_data = test_optimizer.export_performance_data()
        
        assert performance_data is not None
        assert "performance_metrics" in performance_data
        assert "test_history_summary" in performance_data
        
        # 检查性能指标
        assert len(performance_data["performance_metrics"]) == 2
        assert "test_capability_1_test_model_1" in performance_data["performance_metrics"]
        assert "test_capability_2_test_model_2" in performance_data["performance_metrics"]
        
        # 检查测试历史摘要
        assert "test_capability_1_test_model_1" in performance_data["test_history_summary"]
        assert performance_data["test_history_summary"]["test_capability_1_test_model_1"] == 1


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
