"""
能力测试优化器
优化能力测试的覆盖范围、性能、结果分析等功能
"""

import asyncio
import time
import statistics
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
from datetime import datetime, timedelta

from .capability_model import (
    Capability, CapabilityType, CapabilityRegistry, 
    CapabilityTest, TestResult
)
from .capability_discovery import CapabilityDiscovery
from ..utils.logger import log_info, log_error, log_debug, log_warning


class TestOptimizationStrategy(Enum):
    """测试优化策略枚举"""
    COMPREHENSIVE = "comprehensive"  # 全面测试
    PERFORMANCE = "performance"      # 性能优先
    COST_EFFECTIVE = "cost_effective"  # 成本效益
    MINIMAL = "minimal"              # 最小化测试
    ADAPTIVE = "adaptive"            # 自适应测试


class TestPriority(Enum):
    """测试优先级枚举"""
    CRITICAL = "critical"    # 关键测试
    HIGH = "high"            # 高优先级
    MEDIUM = "medium"        # 中等优先级
    LOW = "low"              # 低优先级


@dataclass
class TestOptimizationConfig:
    """测试优化配置"""
    strategy: TestOptimizationStrategy = TestOptimizationStrategy.ADAPTIVE
    max_concurrent_tests: int = 5
    timeout_per_test: int = 30  # 秒
    max_test_cases_per_capability: int = 10
    min_success_rate: float = 0.6
    performance_threshold: float = 5000  # 毫秒
    cost_threshold: float = 0.1  # 成本阈值
    enable_retry: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒


@dataclass
class TestBatchResult:
    """测试批次结果"""
    batch_id: str
    capability_id: str
    model_id: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_response_time: float
    total_cost: float
    start_time: float
    end_time: float
    test_results: List[TestResult]
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    capability_id: str
    model_id: str
    total_tests: int
    successful_tests: int
    success_rate: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    std_response_time: float
    total_cost: float
    avg_cost_per_test: float
    last_test_time: float
    reliability_score: float
    performance_score: float
    cost_efficiency_score: float


class CapabilityTestOptimizer:
    """能力测试优化器"""
    
    def __init__(self, capability_registry: CapabilityRegistry, 
                 capability_discovery: CapabilityDiscovery,
                 config: Optional[TestOptimizationConfig] = None):
        self.capability_registry = capability_registry
        self.capability_discovery = capability_discovery
        self.config = config or TestOptimizationConfig()
        
        # 性能指标缓存
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        
        # 测试历史记录
        self.test_history: Dict[str, List[TestBatchResult]] = {}
        
        # 优化建议缓存
        self.optimization_suggestions: Dict[str, List[str]] = {}
    
    async def optimize_test_suite(self, capability_id: str, model_id: str, 
                                strategy: Optional[TestOptimizationStrategy] = None) -> List[CapabilityTest]:
        """优化测试套件"""
        capability = self.capability_registry.get_capability(capability_id)
        if not capability:
            log_error(f"能力不存在: {capability_id}")
            return []
        
        strategy = strategy or self.config.strategy
        
        # 获取基础测试用例
        base_tests = capability.tests or []
        
        if strategy == TestOptimizationStrategy.COMPREHENSIVE:
            return await self._generate_comprehensive_tests(capability, base_tests)
        elif strategy == TestOptimizationStrategy.PERFORMANCE:
            return await self._generate_performance_tests(capability, base_tests)
        elif strategy == TestOptimizationStrategy.COST_EFFECTIVE:
            return await self._generate_cost_effective_tests(capability, base_tests)
        elif strategy == TestOptimizationStrategy.MINIMAL:
            return await self._generate_minimal_tests(capability, base_tests)
        elif strategy == TestOptimizationStrategy.ADAPTIVE:
            return await self._generate_adaptive_tests(capability, model_id, base_tests)
        else:
            return base_tests
    
    async def _generate_comprehensive_tests(self, capability: Capability, 
                                          base_tests: List[CapabilityTest]) -> List[CapabilityTest]:
        """生成全面测试用例"""
        tests = base_tests.copy()
        
        # 基于能力类型添加特定测试
        if capability.capability_type == CapabilityType.TEXT_GENERATION:
            tests.extend(self._generate_text_generation_tests(capability))
        elif capability.capability_type == CapabilityType.CODE_GENERATION:
            tests.extend(self._generate_code_generation_tests(capability))
        elif capability.capability_type == CapabilityType.TEXT_SUMMARIZATION:
            tests.extend(self._generate_text_summarization_tests(capability))
        elif capability.capability_type == CapabilityType.TRANSLATION:
            tests.extend(self._generate_translation_tests(capability))
        elif capability.capability_type == CapabilityType.QUESTION_ANSWERING:
            tests.extend(self._generate_qa_tests(capability))
        
        # 添加边界测试
        tests.extend(self._generate_boundary_tests(capability))
        
        # 限制测试用例数量
        return tests[:self.config.max_test_cases_per_capability]
    
    async def _generate_performance_tests(self, capability: Capability, 
                                        base_tests: List[CapabilityTest]) -> List[CapabilityTest]:
        """生成性能优先测试用例"""
        tests = base_tests.copy()
        
        # 选择响应时间较短的测试用例
        if len(tests) > 3:
            # 假设前3个测试用例是性能测试
            tests = tests[:3]
        
        # 添加性能基准测试
        performance_test = CapabilityTest(
            test_id=f"performance_benchmark_{uuid.uuid4().hex[:8]}",
            name="性能基准测试",
            description="测试模型在标准任务上的性能表现",
            input_data={"prompt": "请生成一段关于人工智能的简短介绍，长度约100字。"},
            expected_output={"generated_text": "人工智能介绍"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(performance_test)
        
        return tests[:self.config.max_test_cases_per_capability]
    
    async def _generate_cost_effective_tests(self, capability: Capability, 
                                           base_tests: List[CapabilityTest]) -> List[CapabilityTest]:
        """生成成本效益测试用例"""
        tests = base_tests.copy()
        
        # 选择成本较低的测试用例
        if len(tests) > 2:
            tests = tests[:2]
        
        # 添加成本效益测试
        cost_test = CapabilityTest(
            test_id=f"cost_effective_{uuid.uuid4().hex[:8]}",
            name="成本效益测试",
            description="测试模型在成本控制下的表现",
            input_data={"prompt": "简单介绍一下你自己。"},
            expected_output={"generated_text": "自我介绍"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(cost_test)
        
        return tests[:self.config.max_test_cases_per_capability]
    
    async def _generate_minimal_tests(self, capability: Capability, 
                                    base_tests: List[CapabilityTest]) -> List[CapabilityTest]:
        """生成最小化测试用例"""
        # 只保留最基本的测试用例
        if base_tests:
            return base_tests[:1]
        else:
            # 创建一个基本测试用例
            basic_test = CapabilityTest(
                test_id=f"minimal_{uuid.uuid4().hex[:8]}",
                name="基本功能测试",
                description="测试模型的基本功能",
                input_data={"prompt": "你好，请回复。"},
                expected_output={"generated_text": "基本回复"},
                priority=1,
                timeout=self.config.timeout_per_test
            )
            return [basic_test]
    
    async def _generate_adaptive_tests(self, capability: Capability, model_id: str,
                                     base_tests: List[CapabilityTest]) -> List[CapabilityTest]:
        """生成自适应测试用例"""
        tests = base_tests.copy()
        
        # 获取历史性能指标
        metrics_key = f"{capability.capability_id}_{model_id}"
        metrics = self.performance_metrics.get(metrics_key)
        
        if metrics:
            # 基于历史性能调整测试策略
            if metrics.success_rate < self.config.min_success_rate:
                # 成功率低，减少测试用例
                tests = tests[:2]
            elif metrics.avg_response_time > self.config.performance_threshold:
                # 响应时间长，添加性能测试
                tests.extend(self._generate_performance_focused_tests(capability))
            elif metrics.avg_cost_per_test > self.config.cost_threshold:
                # 成本高，添加成本测试
                tests.extend(self._generate_cost_focused_tests(capability))
            else:
                # 性能良好，添加全面测试
                tests.extend(self._generate_comprehensive_tests_simple(capability))
        else:
            # 无历史数据，使用中等测试规模
            tests = tests[:5] if len(tests) > 5 else tests
        
        return tests[:self.config.max_test_cases_per_capability]
    
    def _generate_text_generation_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成文本生成测试用例"""
        tests = []
        
        # 不同长度的文本生成测试
        test_cases = [
            ("简短文本", "写一句关于天气的话。"),
            ("中等文本", "写一段关于人工智能发展的短文，约200字。"),
            ("长文本", "写一篇关于机器学习应用的文章，约500字。"),
            ("创意文本", "创作一个关于未来城市的短故事。"),
            ("技术文本", "解释一下深度学习的基本原理。")
        ]
        
        for name, prompt in test_cases:
            test = CapabilityTest(
                test_id=f"text_gen_{uuid.uuid4().hex[:8]}",
                name=f"文本生成测试 - {name}",
                description=f"测试{name}生成能力",
                input_data={"prompt": prompt},
                expected_output={"generated_text": f"{name}测试输出"},
                priority=1,
                timeout=self.config.timeout_per_test
            )
            tests.append(test)
        
        return tests
    
    def _generate_code_generation_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成代码生成测试用例"""
        tests = []
        
        test_cases = [
            ("简单函数", "写一个Python函数计算两个数的和。"),
            ("算法实现", "用Python实现快速排序算法。"),
            ("类设计", "设计一个表示学生的Python类。"),
            ("错误处理", "写一个包含错误处理的文件读取函数。"),
            ("API调用", "写一个使用requests库调用API的函数。")
        ]
        
        for name, prompt in test_cases:
            test = CapabilityTest(
                test_id=f"code_gen_{uuid.uuid4().hex[:8]}",
                name=f"代码生成测试 - {name}",
                description=f"测试{name}生成能力",
                input_data={"prompt": prompt},
                expected_output={"generated_text": f"{name}代码输出"},
                priority=1,
                timeout=self.config.timeout_per_test
            )
            tests.append(test)
        
        return tests
    
    def _generate_text_summarization_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成文本摘要测试用例"""
        tests = []
        
        sample_text = """
        人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
        可以设想，未来人工智能带来的科技产品，将会是人类智慧的容器。
        """
        
        test = CapabilityTest(
            test_id=f"summary_{uuid.uuid4().hex[:8]}",
            name="文本摘要测试",
            description="测试文本摘要能力",
            input_data={"text": sample_text, "max_length": 100},
            expected_output={"generated_text": "摘要输出"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(test)
        
        return tests
    
    def _generate_translation_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成翻译测试用例"""
        tests = []
        
        test_cases = [
            ("英译中", "Hello, how are you today?", "en", "zh"),
            ("中译英", "今天天气很好，适合出去散步。", "zh", "en"),
            ("长句翻译", "The quick brown fox jumps over the lazy dog.", "en", "zh")
        ]
        
        for name, text, source_lang, target_lang in test_cases:
            test = CapabilityTest(
                test_id=f"translation_{uuid.uuid4().hex[:8]}",
                name=f"翻译测试 - {name}",
                description=f"测试{name}能力",
                input_data={
                    "text": text,
                    "source_language": source_lang,
                    "target_language": target_lang
                },
                expected_output={"generated_text": f"{name}翻译输出"},
                priority=1,
                timeout=self.config.timeout_per_test
            )
            tests.append(test)
        
        return tests
    
    def _generate_qa_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成问答测试用例"""
        tests = []
        
        test_cases = [
            ("事实问答", "中国的首都是哪里？"),
            ("解释性问答", "什么是机器学习？"),
            ("推理问答", "如果明天下雨，我应该带什么？"),
            ("多轮问答", "先介绍一下Python，然后说说它的优点。")
        ]
        
        for name, question in test_cases:
            test = CapabilityTest(
                test_id=f"qa_{uuid.uuid4().hex[:8]}",
                name=f"问答测试 - {name}",
                description=f"测试{name}能力",
                input_data={"question": question},
                expected_output={"generated_text": f"{name}回答输出"},
                priority=1,
                timeout=self.config.timeout_per_test
            )
            tests.append(test)
        
        return tests
    
    def _generate_boundary_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成边界测试用例"""
        tests = []
        
        # 空输入测试
        empty_test = CapabilityTest(
            test_id=f"boundary_empty_{uuid.uuid4().hex[:8]}",
            name="边界测试 - 空输入",
            description="测试空输入处理",
            input_data={"prompt": ""},
            expected_output={"generated_text": "空输入处理"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(empty_test)
        
        # 超长输入测试
        long_text = "测试" * 1000  # 2000个字符
        long_test = CapabilityTest(
            test_id=f"boundary_long_{uuid.uuid4().hex[:8]}",
            name="边界测试 - 长输入",
            description="测试长输入处理",
            input_data={"prompt": long_text},
            expected_output={"generated_text": "长输入处理"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(long_test)
        
        return tests
    
    def _generate_performance_focused_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成性能关注测试用例"""
        tests = []
        
        # 响应时间测试
        perf_test = CapabilityTest(
            test_id=f"perf_focus_{uuid.uuid4().hex[:8]}",
            name="性能关注测试",
            description="测试模型响应时间",
            input_data={"prompt": "请快速回复一个简单的问候。"},
            expected_output={"generated_text": "性能测试输出"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(perf_test)
        
        return tests
    
    def _generate_cost_focused_tests(self, capability: Capability) -> List[CapabilityTest]:
        """生成成本关注测试用例"""
        tests = []
        
        # 低成本测试
        cost_test = CapabilityTest(
            test_id=f"cost_focus_{uuid.uuid4().hex[:8]}",
            name="成本关注测试",
            description="测试模型成本控制",
            input_data={"prompt": "用最少的字数回答：什么是AI？"},
            expected_output={"generated_text": "AI定义"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(cost_test)
        
        return tests
    
    def _generate_comprehensive_tests_simple(self, capability: Capability) -> List[CapabilityTest]:
        """生成简化全面测试用例"""
        tests = []
        
        # 综合能力测试
        comprehensive_test = CapabilityTest(
            test_id=f"comprehensive_simple_{uuid.uuid4().hex[:8]}",
            name="综合能力测试",
            description="测试模型综合能力",
            input_data={"prompt": "请展示你在文本理解、生成和推理方面的能力。"},
            expected_output={"generated_text": "综合能力测试输出"},
            priority=1,
            timeout=self.config.timeout_per_test
        )
        tests.append(comprehensive_test)
        
        return tests
    
    async def run_optimized_tests(self, capability_id: str, model_id: str, 
                                strategy: Optional[TestOptimizationStrategy] = None) -> TestBatchResult:
        """运行优化后的测试"""
        # 生成优化测试套件
        optimized_tests = await self.optimize_test_suite(capability_id, model_id, strategy)
        
        if not optimized_tests:
            log_error(f"无法为能力 {capability_id} 生成优化测试套件")
            return None
        
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        log_info(f"开始运行优化测试批次 {batch_id}，能力: {capability_id}，模型: {model_id}")
        
        # 运行测试
        test_results = []
        successful_tests = 0
        failed_tests = 0
        total_response_time = 0.0
        total_cost = 0.0
        
        # 限制并发测试数量
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tests)
        
        async def run_single_test(test: CapabilityTest):
            async with semaphore:
                try:
                    # 使用能力发现机制运行测试
                    result = await self.capability_discovery.test_capability_on_model(
                        capability_id, model_id, test
                    )
                    
                    if result and result.result == TestResult.PASSED:
                        nonlocal successful_tests
                        successful_tests += 1
                    else:
                        nonlocal failed_tests
                        failed_tests += 1
                    
                    if result:
                        test_results.append(result)
                        if result.execution_time:
                            nonlocal total_response_time
                            total_response_time += result.execution_time
                        # 注意：CapabilityTestResult 没有 cost 属性，这里跳过成本计算
                    
                    return result
                    
                except Exception as e:
                    log_error(f"测试执行失败: {test.test_id} - {e}")
                    failed_tests += 1
                    return None
        
        # 并发运行所有测试
        tasks = [run_single_test(test) for test in optimized_tests]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # 计算统计信息
        avg_response_time = total_response_time / len(test_results) if test_results else 0.0
        
        # 生成优化建议
        optimization_suggestions = self._generate_optimization_suggestions(
            capability_id, model_id, successful_tests, failed_tests, 
            avg_response_time, total_cost, len(optimized_tests)
        )
        
        # 更新性能指标
        self._update_performance_metrics(
            capability_id, model_id, successful_tests, failed_tests,
            avg_response_time, total_cost, len(optimized_tests)
        )
        
        # 保存测试历史
        batch_result = TestBatchResult(
            batch_id=batch_id,
            capability_id=capability_id,
            model_id=model_id,
            total_tests=len(optimized_tests),
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            avg_response_time=avg_response_time,
            total_cost=total_cost,
            start_time=start_time,
            end_time=end_time,
            test_results=test_results,
            optimization_suggestions=optimization_suggestions
        )
        
        # 保存到历史记录
        history_key = f"{capability_id}_{model_id}"
        if history_key not in self.test_history:
            self.test_history[history_key] = []
        self.test_history[history_key].append(batch_result)
        
        log_info(f"优化测试批次 {batch_id} 完成: {successful_tests}/{len(optimized_tests)} 通过")
        
        return batch_result
    
    def _generate_optimization_suggestions(self, capability_id: str, model_id: str,
                                         successful_tests: int, failed_tests: int,
                                         avg_response_time: float, total_cost: float,
                                         total_tests: int) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
        
        if success_rate < self.config.min_success_rate:
            suggestions.append(f"成功率较低 ({success_rate:.1%})，建议减少测试用例数量或更换模型")
        
        if avg_response_time > self.config.performance_threshold:
            suggestions.append(f"响应时间较长 ({avg_response_time:.0f}ms)，建议优化模型配置或使用性能更好的模型")
        
        if total_cost > self.config.cost_threshold * total_tests:
            suggestions.append(f"测试成本较高 ({total_cost:.4f})，建议使用成本更低的测试策略")
        
        if failed_tests > 0:
            suggestions.append(f"有 {failed_tests} 个测试失败，建议检查模型连接和配置")
        
        if success_rate > 0.8 and avg_response_time < 2000:
            suggestions.append("性能表现良好，可以考虑增加测试覆盖范围")
        
        return suggestions
    
    def _update_performance_metrics(self, capability_id: str, model_id: str,
                                  successful_tests: int, failed_tests: int,
                                  avg_response_time: float, total_cost: float,
                                  total_tests: int):
        """更新性能指标"""
        metrics_key = f"{capability_id}_{model_id}"
        
        success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
        
        if metrics_key in self.performance_metrics:
            # 更新现有指标
            metrics = self.performance_metrics[metrics_key]
            old_total = metrics.total_tests
            
            # 合并统计信息
            metrics.total_tests += total_tests
            metrics.successful_tests += successful_tests
            metrics.success_rate = (metrics.success_rate * old_total + success_rate * total_tests) / metrics.total_tests
            metrics.avg_response_time = (metrics.avg_response_time * old_total + avg_response_time * total_tests) / metrics.total_tests
            metrics.total_cost += total_cost
            metrics.avg_cost_per_test = metrics.total_cost / metrics.total_tests
            metrics.last_test_time = time.time()
            
            # 更新分数
            metrics.reliability_score = metrics.success_rate
            metrics.performance_score = max(0, 1 - (metrics.avg_response_time / self.config.performance_threshold))
            metrics.cost_efficiency_score = max(0, 1 - (metrics.avg_cost_per_test / self.config.cost_threshold))
            
        else:
            # 创建新指标
            metrics = PerformanceMetrics(
                capability_id=capability_id,
                model_id=model_id,
                total_tests=total_tests,
                successful_tests=successful_tests,
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                min_response_time=avg_response_time,
                max_response_time=avg_response_time,
                std_response_time=0.0,
                total_cost=total_cost,
                avg_cost_per_test=total_cost / total_tests if total_tests > 0 else 0.0,
                last_test_time=time.time(),
                reliability_score=success_rate,
                performance_score=max(0, 1 - (avg_response_time / self.config.performance_threshold)),
                cost_efficiency_score=max(0, 1 - ((total_cost / total_tests) / self.config.cost_threshold) if total_tests > 0 else 1.0)
            )
        
        self.performance_metrics[metrics_key] = metrics
    
    def get_performance_metrics(self, capability_id: str, model_id: str) -> Optional[PerformanceMetrics]:
        """获取性能指标"""
        metrics_key = f"{capability_id}_{model_id}"
        return self.performance_metrics.get(metrics_key)
    
    def get_test_history(self, capability_id: str, model_id: str) -> List[TestBatchResult]:
        """获取测试历史"""
        history_key = f"{capability_id}_{model_id}"
        return self.test_history.get(history_key, [])
    
    def generate_test_report(self, batch_result: TestBatchResult) -> Dict[str, Any]:
        """生成测试报告"""
        duration = batch_result.end_time - batch_result.start_time
        success_rate = batch_result.successful_tests / batch_result.total_tests if batch_result.total_tests > 0 else 0.0
        
        report = {
            "batch_id": batch_result.batch_id,
            "capability_id": batch_result.capability_id,
            "model_id": batch_result.model_id,
            "test_summary": {
                "total_tests": batch_result.total_tests,
                "successful_tests": batch_result.successful_tests,
                "failed_tests": batch_result.failed_tests,
                "success_rate": success_rate,
                "avg_response_time": batch_result.avg_response_time,
                "total_cost": batch_result.total_cost,
                "duration": duration
            },
            "optimization_suggestions": batch_result.optimization_suggestions,
            "test_details": [
                {
                    "test_id": result.test_id,
                    "status": result.result.value,
                    "response_time": result.execution_time,
                    "cost": 0.0,  # CapabilityTestResult 没有 cost 属性
                    "error_message": result.error_message
                }
                for result in batch_result.test_results
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        return report
    
    def export_performance_data(self) -> Dict[str, Any]:
        """导出性能数据"""
        return {
            "performance_metrics": {
                key: {
                    "capability_id": metrics.capability_id,
                    "model_id": metrics.model_id,
                    "total_tests": metrics.total_tests,
                    "successful_tests": metrics.successful_tests,
                    "success_rate": metrics.success_rate,
                    "avg_response_time": metrics.avg_response_time,
                    "total_cost": metrics.total_cost,
                    "avg_cost_per_test": metrics.avg_cost_per_test,
                    "last_test_time": metrics.last_test_time,
                    "reliability_score": metrics.reliability_score,
                    "performance_score": metrics.performance_score,
                    "cost_efficiency_score": metrics.cost_efficiency_score
                }
                for key, metrics in self.performance_metrics.items()
            },
            "test_history_summary": {
                key: len(history) for key, history in self.test_history.items()
            }
        }


# 测试函数
async def test_capability_test_optimizer():
    """测试能力测试优化器功能"""
    try:
        from unittest.mock import Mock
        
        # 创建模拟对象
        mock_registry = Mock()
        mock_discovery = Mock()
        
        # 创建模拟能力
        test_capability = Mock()
        test_capability.capability_id = "test_capability"
        test_capability.capability_type = CapabilityType.TEXT_GENERATION
        test_capability.tests = []
        mock_registry.get_capability.return_value = test_capability
        
        # 创建测试优化器
        optimizer = CapabilityTestOptimizer(mock_registry, mock_discovery)
        
        # 测试优化测试套件
        optimized_tests = await optimizer.optimize_test_suite("test_capability", "test_model")
        
        assert optimized_tests is not None
        assert len(optimized_tests) > 0
        
        print("✓ 能力测试优化器功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 能力测试优化器功能测试失败: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_capability_test_optimizer())
