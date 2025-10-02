"""
性能分析工具
用于分析应用性能瓶颈，优化数据库查询、异步处理、内存占用和响应速度
"""

import time
import asyncio
import psutil
import tracemalloc
from functools import wraps
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

from src.utils.logger import get_log_manager


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    function_name: str
    execution_time: float
    memory_usage: int
    cpu_usage: float
    database_queries: int
    async_tasks: int
    timestamp: float


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.logger = get_log_manager()
        self.metrics: List[PerformanceMetrics] = []
        self.database_query_count = 0
        self.async_task_count = 0
        self.tracemalloc_started = False
        
        # 性能基准
        self.benchmarks = {
            "database_query_time": 0.1,  # 100ms
            "async_task_time": 0.05,     # 50ms
            "memory_usage_mb": 100,      # 100MB
            "cpu_usage_percent": 80,     # 80%
            "response_time": 1.0         # 1秒
        }
    
    def start_monitoring(self):
        """开始性能监控"""
        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True
        # 使用logger的log方法而不是info方法
        self.logger.log("性能监控已启动", "INFO")
    
    def stop_monitoring(self):
        """停止性能监控"""
        if self.tracemalloc_started:
            tracemalloc.stop()
            self.tracemalloc_started = False
        self.logger.info("性能监控已停止")
    
    def measure_performance(self, func: Callable) -> Callable:
        """性能测量装饰器"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self._measure_async_performance(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return self._measure_sync_performance(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    async def _measure_async_performance(self, func: Callable, *args, **kwargs):
        """测量异步函数性能"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = psutil.cpu_percent(interval=None)
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent(interval=None)
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = end_cpu - start_cpu
            
            metrics = PerformanceMetrics(
                function_name=func.__name__,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                database_queries=self.database_query_count,
                async_tasks=self.async_task_count,
                timestamp=time.time()
            )
            
            self.metrics.append(metrics)
            self._check_performance_thresholds(metrics)
    
    def _measure_sync_performance(self, func: Callable, *args, **kwargs):
        """测量同步函数性能"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = psutil.cpu_percent(interval=None)
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent(interval=None)
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = end_cpu - start_cpu
            
            metrics = PerformanceMetrics(
                function_name=func.__name__,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                database_queries=self.database_query_count,
                async_tasks=self.async_task_count,
                timestamp=time.time()
            )
            
            self.metrics.append(metrics)
            self._check_performance_thresholds(metrics)
    
    def _get_memory_usage(self) -> int:
        """获取内存使用量（字节）"""
        process = psutil.Process()
        return process.memory_info().rss
    
    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """检查性能阈值"""
        warnings = []
        
        if metrics.execution_time > self.benchmarks["response_time"]:
            warnings.append(f"执行时间过长: {metrics.execution_time:.3f}s")
        
        if metrics.memory_usage > self.benchmarks["memory_usage_mb"] * 1024 * 1024:
            warnings.append(f"内存使用过高: {metrics.memory_usage / (1024*1024):.2f}MB")
        
        if metrics.cpu_usage > self.benchmarks["cpu_usage_percent"]:
            warnings.append(f"CPU使用过高: {metrics.cpu_usage:.1f}%")
        
        if warnings:
            self.logger.warning(f"性能警告 - {metrics.function_name}: {'; '.join(warnings)}")
    
    def increment_database_query(self):
        """增加数据库查询计数"""
        self.database_query_count += 1
    
    def increment_async_task(self):
        """增加异步任务计数"""
        self.async_task_count += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.metrics:
            return {"status": "no_metrics"}
        
        total_execution_time = sum(m.execution_time for m in self.metrics)
        avg_execution_time = total_execution_time / len(self.metrics)
        max_execution_time = max(m.execution_time for m in self.metrics)
        
        total_memory_usage = sum(m.memory_usage for m in self.metrics)
        avg_memory_usage = total_memory_usage / len(self.metrics)
        max_memory_usage = max(m.memory_usage for m in self.metrics)
        
        total_cpu_usage = sum(m.cpu_usage for m in self.metrics)
        avg_cpu_usage = total_cpu_usage / len(self.metrics)
        max_cpu_usage = max(m.cpu_usage for m in self.metrics)
        
        slowest_functions = sorted(
            self.metrics, 
            key=lambda x: x.execution_time, 
            reverse=True
        )[:5]
        
        return {
            "total_functions": len(self.metrics),
            "total_execution_time": total_execution_time,
            "average_execution_time": avg_execution_time,
            "max_execution_time": max_execution_time,
            "average_memory_usage_mb": avg_memory_usage / (1024 * 1024),
            "max_memory_usage_mb": max_memory_usage / (1024 * 1024),
            "average_cpu_usage": avg_cpu_usage,
            "max_cpu_usage": max_cpu_usage,
            "total_database_queries": self.database_query_count,
            "total_async_tasks": self.async_task_count,
            "slowest_functions": [
                {
                    "name": m.function_name,
                    "time": m.execution_time,
                    "memory_mb": m.memory_usage / (1024 * 1024),
                    "cpu_percent": m.cpu_usage
                }
                for m in slowest_functions
            ]
        }
    
    def clear_metrics(self):
        """清除性能指标"""
        self.metrics.clear()
        self.database_query_count = 0
        self.async_task_count = 0


class DatabaseOptimizer:
    """数据库查询优化器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.analyzer = PerformanceAnalyzer()
        self.query_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def optimize_query(self, query: str, params: tuple = ()) -> str:
        """优化SQL查询"""
        # 简单的查询优化逻辑
        optimized_query = query.strip()
        
        # 移除不必要的空格
        optimized_query = ' '.join(optimized_query.split())
        
        # 添加查询缓存键
        cache_key = f"{optimized_query}:{str(params)}"
        
        if cache_key in self.query_cache:
            self.cache_hits += 1
            return self.query_cache[cache_key]
        
        self.cache_misses += 1
        
        # 执行查询并缓存结果
        cursor = self.db_manager.connection.cursor()
        cursor.execute(optimized_query, params)
        result = cursor.fetchall()
        
        # 缓存小结果集（小于100行）
        if len(result) < 100:
            self.query_cache[cache_key] = result
        
        return result
    
    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计"""
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "cache_size": len(self.query_cache)
        }
    
    def clear_cache(self):
        """清除查询缓存"""
        self.query_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0


class AsyncOptimizer:
    """异步处理优化器"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.task_queue = asyncio.Queue()
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
    
    async def execute_with_limits(self, coro):
        """带限制执行异步任务"""
        async with self.semaphore:
            self.active_tasks += 1
            try:
                result = await coro
                self.completed_tasks += 1
                return result
            except Exception as e:
                self.failed_tasks += 1
                raise e
            finally:
                self.active_tasks -= 1
    
    async def batch_execute(self, coroutines: List, batch_size: int = 5):
        """批量执行异步任务"""
        results = []
        for i in range(0, len(coroutines), batch_size):
            batch = coroutines[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.execute_with_limits(coro) for coro in batch],
                return_exceptions=True
            )
            results.extend(batch_results)
        return results
    
    def get_async_stats(self) -> Dict[str, Any]:
        """获取异步统计"""
        return {
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_tasks": self.completed_tasks + self.failed_tasks
        }


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        self.memory_snapshots = []
        self.optimization_suggestions = []
    
    def take_memory_snapshot(self, description: str = ""):
        """获取内存快照"""
        import gc
        gc.collect()  # 强制垃圾回收
        
        snapshot = tracemalloc.take_snapshot()
        self.memory_snapshots.append({
            "description": description,
            "snapshot": snapshot,
            "timestamp": time.time()
        })
        
        return snapshot
    
    def analyze_memory_usage(self):
        """分析内存使用情况"""
        if len(self.memory_snapshots) < 2:
            return {"status": "insufficient_snapshots"}
        
        current_snapshot = self.memory_snapshots[-1]["snapshot"]
        previous_snapshot = self.memory_snapshots[-2]["snapshot"]
        
        stats = current_snapshot.compare_to(previous_snapshot, 'lineno')
        
        memory_increase = []
        memory_decrease = []
        
        for stat in stats[:10]:  # 只看前10个变化最大的
            if stat.size_diff > 0:
                memory_increase.append({
                    "file": stat.traceback[-1].filename,
                    "line": stat.traceback[-1].lineno,
                    "size_increase_kb": stat.size_diff / 1024,
                    "total_size_kb": stat.size / 1024
                })
            elif stat.size_diff < 0:
                memory_decrease.append({
                    "file": stat.traceback[-1].filename,
                    "line": stat.traceback[-1].lineno,
                    "size_decrease_kb": abs(stat.size_diff) / 1024
                })
        
        # 生成优化建议
        suggestions = self._generate_memory_suggestions(memory_increase)
        
        return {
            "memory_increase": memory_increase,
            "memory_decrease": memory_decrease,
            "suggestions": suggestions
        }
    
    def _generate_memory_suggestions(self, memory_increase: List[Dict]) -> List[str]:
        """生成内存优化建议"""
        suggestions = []
        
        for item in memory_increase:
            if item["size_increase_kb"] > 100:  # 超过100KB的增长
                suggestions.append(
                    f"检测到内存泄漏: {item['file']}:{item['line']} "
                    f"增加了 {item['size_increase_kb']:.1f}KB"
                )
        
        if not suggestions:
            suggestions.append("内存使用正常，未检测到明显的内存泄漏")
        
        return suggestions
    
    def optimize_data_structures(self, data):
        """优化数据结构"""
        if isinstance(data, list) and len(data) > 1000:
            # 对于大型列表，考虑使用生成器
            return (item for item in data)
        
        if isinstance(data, dict) and len(data) > 1000:
            # 对于大型字典，考虑使用更高效的数据结构
            # 这里可以添加更复杂的优化逻辑
            pass
        
        return data


class PerformanceOptimizer:
    """综合性能优化器"""
    
    def __init__(self, db_manager=None):
        self.analyzer = PerformanceAnalyzer()
        self.db_optimizer = DatabaseOptimizer(db_manager) if db_manager else None
        self.async_optimizer = AsyncOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        
        self.optimization_results = {}
    
    def start_optimization(self):
        """开始性能优化"""
        self.analyzer.start_monitoring()
        self.logger.info("性能优化已启动")
    
    def stop_optimization(self):
        """停止性能优化"""
        self.analyzer.stop_monitoring()
        self.logger.info("性能优化已停止")
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """运行综合分析"""
        analysis_results = {}
        
        # 性能指标分析
        analysis_results["performance_metrics"] = self.analyzer.get_performance_report()
        
        # 数据库优化分析
        if self.db_optimizer:
            analysis_results["database_stats"] = self.db_optimizer.get_query_stats()
        
        # 异步处理分析
        analysis_results["async_stats"] = self.async_optimizer.get_async_stats()
        
        # 内存使用分析
        analysis_results["memory_analysis"] = self.memory_optimizer.analyze_memory_usage()
        
        # 生成优化建议
        analysis_results["optimization_suggestions"] = self._generate_optimization_suggestions(analysis_results)
        
        self.optimization_results = analysis_results
        return analysis_results
    
    def _generate_optimization_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 性能指标建议
        perf_metrics = analysis_results.get("performance_metrics", {})
        if perf_metrics.get("max_execution_time", 0) > 1.0:
            suggestions.append("优化执行时间过长的函数")
        
        if perf_metrics.get("max_memory_usage_mb", 0) > 100:
            suggestions.append("优化内存使用，减少大对象创建")
        
        # 数据库建议
        db_stats = analysis_results.get("database_stats", {})
        if db_stats.get("cache_hit_ratio", 0) < 0.5:
            suggestions.append("增加数据库查询缓存")
        
        # 异步处理建议
        async_stats = analysis_results.get("async_stats", {})
        if async_stats.get("failed_tasks", 0) > 0:
            suggestions.append("优化异步任务错误处理")
        
        # 内存建议
        memory_analysis = analysis_results.get("memory_analysis", {})
        if memory_analysis.get("suggestions"):
            suggestions.extend(memory_analysis["suggestions"])
        
        if not suggestions:
            suggestions.append("系统性能良好，无需重大优化")
        
        return suggestions
    
    def get_optimization_report(self) -> str:
        """获取优化报告"""
        if not self.optimization_results:
            return "尚未运行性能分析"
        
        report = ["=== 性能优化报告 ==="]
        
        # 性能指标
        perf_metrics = self.optimization_results.get("performance_metrics", {})
        if perf_metrics.get("status") != "no_metrics":
            report.append("\n--- 性能指标 ---")
            report.append(f"总函数调用: {perf_metrics.get('total_functions', 0)}")
            report.append(f"总执行时间: {perf_metrics.get('total_execution_time', 0):.3f}s")
            report.append(f"平均执行时间: {perf_metrics.get('average_execution_time', 0):.3f}s")
            report.append(f"最大执行时间: {perf_metrics.get('max_execution_time', 0):.3f}s")
            report.append(f"最大内存使用: {perf_metrics.get('max_memory_usage_mb', 0):.2f}MB")
            report.append(f"最大CPU使用: {perf_metrics.get('max_cpu_usage', 0):.1f}%")
            
            # 最慢的函数
            slowest = perf_metrics.get("slowest_functions", [])
            if slowest:
                report.append("\n最慢的函数:")
                for func in slowest:
                    report.append(f"  {func['name']}: {func['time']:.3f}s")
        
        # 数据库统计
        db_stats = self.optimization_results.get("database_stats", {})
        if db_stats:
            report.append("\n--- 数据库统计 ---")
            report.append(f"缓存命中: {db_stats.get('cache_hits', 0)}")
            report.append(f"缓存未命中: {db_stats.get('cache_misses', 0)}")
            report.append(f"缓存命中率: {db_stats.get('cache_hit_ratio', 0):.2%}")
            report.append(f"缓存大小: {db_stats.get('cache_size', 0)}")
        
        # 异步统计
        async_stats = self.optimization_results.get("async_stats", {})
        if async_stats:
            report.append("\n--- 异步处理统计 ---")
            report.append(f"最大并发任务: {async_stats.get('max_concurrent_tasks', 0)}")
            report.append(f"活跃任务: {async_stats.get('active_tasks', 0)}")
            report.append(f"完成的任务: {async_stats.get('completed_tasks', 0)}")
            report.append(f"失败的任务: {async_stats.get('failed_tasks', 0)}")
        
        # 内存分析
        memory_analysis = self.optimization_results.get("memory_analysis", {})
        if memory_analysis.get("status") != "insufficient_snapshots":
            report.append("\n--- 内存分析 ---")
            memory_increase = memory_analysis.get("memory_increase", [])
            if memory_increase:
                report.append("内存增长:")
                for item in memory_increase[:3]:  # 只显示前3个
                    report.append(f"  {item['file']}:{item['line']} +{item['size_increase_kb']:.1f}KB")
        
        # 优化建议
        suggestions = self.optimization_results.get("optimization_suggestions", [])
        if suggestions:
            report.append("\n--- 优化建议 ---")
            for i, suggestion in enumerate(suggestions, 1):
                report.append(f"{i}. {suggestion}")
        
        return "\n".join(report)


# 全局性能优化器实例
global_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer(db_manager=None) -> PerformanceOptimizer:
    """获取全局性能优化器实例"""
    global global_optimizer
    if global_optimizer is None:
        global_optimizer = PerformanceOptimizer(db_manager)
    return global_optimizer


def measure_performance(func: Callable) -> Callable:
    """性能测量装饰器（简化版本）"""
    optimizer = get_performance_optimizer()
    return optimizer.analyzer.measure_performance(func)
