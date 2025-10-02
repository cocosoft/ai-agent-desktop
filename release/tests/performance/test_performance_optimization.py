"""
性能优化测试
测试性能分析工具、数据库优化、异步处理和内存优化的功能
"""

import pytest
import asyncio
import time
import tempfile
import os
from unittest.mock import Mock, patch

from src.utils.performance_analyzer import (
    PerformanceAnalyzer, 
    DatabaseOptimizer,
    AsyncOptimizer,
    MemoryOptimizer,
    PerformanceOptimizer,
    get_performance_optimizer,
    measure_performance
)
from src.data.database_manager import DatabaseManager


class TestPerformanceAnalyzer:
    """性能分析器测试"""
    
    def test_performance_analyzer_initialization(self):
        """测试性能分析器初始化"""
        analyzer = PerformanceAnalyzer()
        
        assert analyzer.metrics == []
        assert analyzer.database_query_count == 0
        assert analyzer.async_task_count == 0
        assert analyzer.tracemalloc_started is False
    
    def test_performance_measurement_decorator_sync(self):
        """测试同步函数性能测量装饰器"""
        analyzer = PerformanceAnalyzer()
        
        @analyzer.measure_performance
        def test_function():
            time.sleep(0.01)  # 10ms延迟
            return "test_result"
        
        result = test_function()
        
        assert result == "test_result"
        assert len(analyzer.metrics) == 1
        
        metric = analyzer.metrics[0]
        assert metric.function_name == "test_function"
        assert metric.execution_time >= 0.01
        assert metric.memory_usage >= 0
        assert metric.cpu_usage >= 0
    
    @pytest.mark.asyncio
    async def test_performance_measurement_decorator_async(self):
        """测试异步函数性能测量装饰器"""
        analyzer = PerformanceAnalyzer()
        
        @analyzer.measure_performance
        async def async_test_function():
            await asyncio.sleep(0.01)  # 10ms延迟
            return "async_result"
        
        result = await async_test_function()
        
        assert result == "async_result"
        assert len(analyzer.metrics) == 1
        
        metric = analyzer.metrics[0]
        assert metric.function_name == "async_test_function"
        assert metric.execution_time >= 0.01
    
    def test_performance_threshold_checking(self):
        """测试性能阈值检查"""
        analyzer = PerformanceAnalyzer()

        # 模拟超过阈值的性能指标
        metric = PerformanceMetrics(
            function_name="slow_function",
            execution_time=2.0,  # 超过1秒阈值
            memory_usage=200 * 1024 * 1024,  # 超过100MB阈值
            cpu_usage=90.0,  # 超过80%阈值
            database_queries=0,
            async_tasks=0,
            timestamp=time.time()
        )
        
        # 这里应该触发警告，但由于是测试环境，我们只验证逻辑
        analyzer._check_performance_thresholds(metric)
        
        # 验证指标记录
        assert len(analyzer.metrics) == 0  # 阈值检查不会自动添加指标
    
    def test_performance_report_generation(self):
        """测试性能报告生成"""
        analyzer = PerformanceAnalyzer()
        
        # 添加一些测试指标
        for i in range(3):
            metric = PerformanceMetrics(
                function_name=f"function_{i}",
                execution_time=0.1 + i * 0.05,
                memory_usage=50 * 1024 * 1024 + i * 10 * 1024 * 1024,
                cpu_usage=10.0 + i * 5.0,
                database_queries=i,
                async_tasks=i,
                timestamp=time.time()
            )
            analyzer.metrics.append(metric)
        
        report = analyzer.get_performance_report()
        
        assert report["total_functions"] == 3
        assert report["total_execution_time"] >= 0.3
        assert report["average_execution_time"] >= 0.1
        assert report["max_execution_time"] >= 0.2
        assert report["total_database_queries"] == 3
        assert report["total_async_tasks"] == 3
        assert len(report["slowest_functions"]) == 3


class TestDatabaseOptimizer:
    """数据库优化器测试"""
    
    @pytest.fixture
    def temp_database(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            db_manager = DatabaseManager(temp_db_path)
            db_manager.connect()
            db_manager.initialize_database()  # 修复方法名
            yield db_manager
            db_manager.disconnect()
        finally:
            if os.path.exists(temp_db_path):
                try:
                    os.unlink(temp_db_path)
                except PermissionError:
                    # 在Windows上，文件可能被锁定，忽略删除错误
                    pass
    
    def test_database_optimizer_initialization(self, temp_database):
        """测试数据库优化器初始化"""
        optimizer = DatabaseOptimizer(temp_database)
        
        assert optimizer.db_manager == temp_database
        assert optimizer.query_cache == {}
        assert optimizer.cache_hits == 0
        assert optimizer.cache_misses == 0
    
    def test_query_optimization_with_cache(self, temp_database):
        """测试带缓存的查询优化"""
        optimizer = DatabaseOptimizer(temp_database)
        
        # 第一次查询（应该缓存）
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        result1 = optimizer.optimize_query(query)
        
        # 第二次相同查询（应该从缓存获取）
        result2 = optimizer.optimize_query(query)
        
        assert result1 == result2
        assert optimizer.cache_hits == 1
        assert optimizer.cache_misses == 1
        assert len(optimizer.query_cache) == 1
    
    def test_query_stats(self, temp_database):
        """测试查询统计"""
        optimizer = DatabaseOptimizer(temp_database)
        
        # 执行一些查询
        for i in range(5):
            query = f"SELECT {i} as value"
            optimizer.optimize_query(query)
        
        stats = optimizer.get_query_stats()
        
        assert stats["cache_hits"] == 0  # 所有查询都不同，没有命中
        assert stats["cache_misses"] == 5
        assert stats["cache_hit_ratio"] == 0.0
        assert stats["cache_size"] == 5
    
    def test_cache_clear(self, temp_database):
        """测试缓存清除"""
        optimizer = DatabaseOptimizer(temp_database)
        
        # 添加一些缓存
        optimizer.optimize_query("SELECT 1")
        assert len(optimizer.query_cache) == 1
        
        # 清除缓存
        optimizer.clear_cache()
        
        assert len(optimizer.query_cache) == 0
        assert optimizer.cache_hits == 0
        assert optimizer.cache_misses == 0


class TestAsyncOptimizer:
    """异步优化器测试"""
    
    @pytest.mark.asyncio
    async def test_async_optimizer_initialization(self):
        """测试异步优化器初始化"""
        optimizer = AsyncOptimizer(max_concurrent_tasks=5)
        
        assert optimizer.max_concurrent_tasks == 5
        assert optimizer.active_tasks == 0
        assert optimizer.completed_tasks == 0
        assert optimizer.failed_tasks == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_limits(self):
        """测试带限制的异步任务执行"""
        optimizer = AsyncOptimizer(max_concurrent_tasks=2)
        
        async def test_task(task_id):
            await asyncio.sleep(0.01)
            return f"task_{task_id}"
        
        # 并发执行多个任务
        tasks = [optimizer.execute_with_limits(test_task(i)) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert results == ["task_0", "task_1", "task_2", "task_3", "task_4"]
        assert optimizer.completed_tasks == 5
        assert optimizer.failed_tasks == 0
    
    @pytest.mark.asyncio
    async def test_batch_execute(self):
        """测试批量执行"""
        optimizer = AsyncOptimizer(max_concurrent_tasks=3)
        
        async def test_task(task_id):
            await asyncio.sleep(0.01)
            return task_id
        
        # 创建任务列表
        coroutines = [test_task(i) for i in range(10)]
        
        # 批量执行
        results = await optimizer.batch_execute(coroutines, batch_size=4)
        
        assert len(results) == 10
        assert results == list(range(10))
        assert optimizer.completed_tasks == 10
    
    @pytest.mark.asyncio
    async def test_async_stats(self):
        """测试异步统计"""
        optimizer = AsyncOptimizer(max_concurrent_tasks=5)
        
        stats = optimizer.get_async_stats()
        
        assert stats["max_concurrent_tasks"] == 5
        assert stats["active_tasks"] == 0
        assert stats["completed_tasks"] == 0
        assert stats["failed_tasks"] == 0
        assert stats["total_tasks"] == 0


class TestMemoryOptimizer:
    """内存优化器测试"""
    
    def test_memory_optimizer_initialization(self):
        """测试内存优化器初始化"""
        optimizer = MemoryOptimizer()
        
        assert optimizer.memory_snapshots == []
        assert optimizer.optimization_suggestions == []
    
    def test_memory_snapshot(self):
        """测试内存快照"""
        optimizer = MemoryOptimizer()
        
        snapshot1 = optimizer.take_memory_snapshot("初始状态")
        snapshot2 = optimizer.take_memory_snapshot("操作后状态")
        
        assert len(optimizer.memory_snapshots) == 2
        assert optimizer.memory_snapshots[0]["description"] == "初始状态"
        assert optimizer.memory_snapshots[1]["description"] == "操作后状态"
    
    def test_memory_usage_analysis(self):
        """测试内存使用分析"""
        optimizer = MemoryOptimizer()
        
        # 需要至少两个快照才能分析
        optimizer.take_memory_snapshot("快照1")
        optimizer.take_memory_snapshot("快照2")
        
        analysis = optimizer.analyze_memory_usage()
        
        # 分析结果应该包含内存增长和减少信息
        assert "memory_increase" in analysis
        assert "memory_decrease" in analysis
        assert "suggestions" in analysis
    
    def test_data_structure_optimization(self):
        """测试数据结构优化"""
        optimizer = MemoryOptimizer()
        
        # 测试列表优化
        large_list = list(range(2000))
        optimized_list = optimizer.optimize_data_structures(large_list)
        
        # 对于大型列表，应该返回生成器
        assert hasattr(optimized_list, '__iter__')
        
        # 测试字典优化（目前没有特殊优化）
        large_dict = {i: f"value_{i}" for i in range(2000)}
        optimized_dict = optimizer.optimize_data_structures(large_dict)
        
        assert optimized_dict == large_dict  # 字典保持不变


class TestPerformanceOptimizer:
    """综合性能优化器测试"""
    
    def test_performance_optimizer_initialization(self):
        """测试性能优化器初始化"""
        optimizer = PerformanceOptimizer()
        
        assert isinstance(optimizer.analyzer, PerformanceAnalyzer)
        assert isinstance(optimizer.async_optimizer, AsyncOptimizer)
        assert isinstance(optimizer.memory_optimizer, MemoryOptimizer)
        assert optimizer.db_optimizer is None
        assert optimizer.optimization_results == {}
    
    def test_comprehensive_analysis(self):
        """测试综合分析"""
        optimizer = PerformanceOptimizer()
        
        # 启动监控
        optimizer.start_optimization()
        
        # 运行一些测试函数来生成指标
        @optimizer.analyzer.measure_performance
        def test_function():
            time.sleep(0.01)
            return "test"
        
        test_function()
        
        # 运行综合分析
        analysis_results = optimizer.run_comprehensive_analysis()
        
        # 验证分析结果包含所有必要的部分
        assert "performance_metrics" in analysis_results
        assert "async_stats" in analysis_results
        assert "memory_analysis" in analysis_results
        assert "optimization_suggestions" in analysis_results
        
        # 停止监控
        optimizer.stop_optimization()
    
    def test_optimization_report(self):
        """测试优化报告"""
        optimizer = PerformanceOptimizer()
        
        # 运行分析
        optimizer.run_comprehensive_analysis()
        
        # 获取报告
        report = optimizer.get_optimization_report()
        
        # 验证报告格式
        assert isinstance(report, str)
        assert "性能优化报告" in report
        assert "性能指标" in report or "尚未运行性能分析" in report


class TestGlobalPerformanceOptimizer:
    """全局性能优化器测试"""
    
    def test_global_optimizer_singleton(self):
        """测试全局优化器单例模式"""
        optimizer1 = get_performance_optimizer()
        optimizer2 = get_performance_optimizer()
        
        assert optimizer1 is optimizer2
    
    def test_measure_performance_decorator(self):
        """测试性能测量装饰器"""
        # 重置全局优化器
        global global_optimizer
        global_optimizer = None
        
        @measure_performance
        def test_function():
            time.sleep(0.01)
            return "decorator_test"
        
        result = test_function()
        
        assert result == "decorator_test"
        
        # 验证指标被记录
        optimizer = get_performance_optimizer()
        assert len(optimizer.analyzer.metrics) == 1


class TestPerformanceIntegration:
    """性能集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance_optimization(self, temp_database):
        """测试端到端性能优化"""
        # 创建性能优化器
        optimizer = PerformanceOptimizer(temp_database)
        optimizer.start_optimization()
        
        # 模拟一些操作
        @optimizer.analyzer.measure_performance
        async def database_operation():
            # 模拟数据库操作
            optimizer.analyzer.increment_database_query()
            await asyncio.sleep(0.01)
            return "db_result"
        
        @optimizer.analyzer.measure_performance  
        async def async_operation():
            # 模拟异步操作
            optimizer.analyzer.increment_async_task()
            await asyncio.sleep(0.01)
            return "async_result"
        
        # 执行操作
        db_result = await database_operation()
        async_result = await async_operation()
        
        assert db_result == "db_result"
        assert async_result == "async_result"
        
        # 运行综合分析
        analysis = optimizer.run_comprehensive_analysis()
        
        # 验证分析结果
        assert analysis["performance_metrics"]["total_database_queries"] == 1
        assert analysis["performance_metrics"]["total_async_tasks"] == 1
        
        # 获取优化报告
        report = optimizer.get_optimization_report()
        assert "性能优化报告" in report
        
        optimizer.stop_optimization()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
