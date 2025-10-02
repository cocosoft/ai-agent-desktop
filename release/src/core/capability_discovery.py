"""
能力自动发现机制
实现AI模型能力的自动发现、测试和验证功能
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
import json
import uuid
from enum import Enum

from .capability_model import (
    Capability, CapabilityType, CapabilityStatus, TestResult,
    CapabilityParameter, CapabilityOutput, CapabilityTest, CapabilityTestResult,
    CapabilityRegistry
)
from ..adapters.base_adapter import BaseAdapter
from ..core.model_manager import ModelManager
from ..utils.logger import log_info, log_error, log_warning, log_debug


class DiscoveryStatus(Enum):
    """发现状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DiscoveryResult:
    """发现结果"""
    capability_id: str
    model_id: str
    status: DiscoveryStatus
    test_results: List[CapabilityTestResult] = field(default_factory=list)
    discovered_capabilities: List[Capability] = field(default_factory=list)
    error_message: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveryTask:
    """发现任务"""
    task_id: str
    model_id: str
    capability_types: List[CapabilityType] = field(default_factory=list)
    status: DiscoveryStatus = DiscoveryStatus.PENDING
    progress: float = 0.0
    results: List[DiscoveryResult] = field(default_factory=list)
    created_time: float = field(default_factory=time.time)
    updated_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapabilityDiscovery:
    """能力发现器"""
    
    def __init__(self, model_manager: ModelManager, capability_registry: CapabilityRegistry):
        self.model_manager = model_manager
        self.capability_registry = capability_registry
        self.discovery_tasks: Dict[str, DiscoveryTask] = {}
        self.test_functions: Dict[CapabilityType, Callable] = {}
        self._register_test_functions()
    
    def _register_test_functions(self):
        """注册测试函数"""
        self.test_functions[CapabilityType.TEXT_GENERATION] = self._test_text_generation
        self.test_functions[CapabilityType.CODE_GENERATION] = self._test_code_generation
        self.test_functions[CapabilityType.TEXT_SUMMARY] = self._test_text_summary
        self.test_functions[CapabilityType.TRANSLATION] = self._test_translation
        self.test_functions[CapabilityType.QUESTION_ANSWERING] = self._test_question_answering
    
    async def discover_model_capabilities(self, model_id: str, 
                                        capability_types: Optional[List[CapabilityType]] = None) -> str:
        """发现模型能力"""
        task_id = str(uuid.uuid4())
        
        # 如果没有指定能力类型，则测试所有已知类型
        if capability_types is None:
            capability_types = list(self.test_functions.keys())
        
        task = DiscoveryTask(
            task_id=task_id,
            model_id=model_id,
            capability_types=capability_types
        )
        
        self.discovery_tasks[task_id] = task
        log_info(f"开始发现模型能力: {model_id} (任务ID: {task_id})")
        
        # 异步执行发现任务
        asyncio.create_task(self._execute_discovery_task(task))
        
        return task_id
    
    async def _execute_discovery_task(self, task: DiscoveryTask):
        """执行发现任务"""
        try:
            task.status = DiscoveryStatus.RUNNING
            task.updated_time = time.time()
            
            total_capabilities = len(task.capability_types)
            
            for i, capability_type in enumerate(task.capability_types):
                # 更新进度
                task.progress = (i / total_capabilities) * 100
                task.updated_time = time.time()
                
                # 测试特定能力类型
                result = await self._test_capability_type(task.model_id, capability_type)
                task.results.append(result)
                
                # 如果发现能力，则注册到注册表
                for capability in result.discovered_capabilities:
                    self.capability_registry.register_capability(capability)
            
            # 任务完成
            task.status = DiscoveryStatus.COMPLETED
            task.progress = 100.0
            task.updated_time = time.time()
            
            discovered_count = len([r for r in task.results if r.discovered_capabilities])
            log_info(f"模型能力发现完成: {task.model_id} (任务ID: {task.task_id}, 发现能力: {discovered_count})")
            
        except Exception as e:
            task.status = DiscoveryStatus.FAILED
            task.updated_time = time.time()
            log_error(f"模型能力发现失败: {task.model_id} (任务ID: {task.task_id}) - {e}")
    
    async def _test_capability_type(self, model_id: str, capability_type: CapabilityType) -> DiscoveryResult:
        """测试特定能力类型"""
        result = DiscoveryResult(
            capability_id=f"{capability_type.value}_test",
            model_id=model_id,
            status=DiscoveryStatus.RUNNING
        )
        
        try:
            # 获取测试函数
            test_function = self.test_functions.get(capability_type)
            if not test_function:
                result.status = DiscoveryStatus.FAILED
                result.error_message = f"未找到测试函数: {capability_type}"
                return result
            
            # 执行测试
            test_results = await test_function(model_id)
            result.test_results = test_results
            
            # 分析测试结果
            if self._is_capability_supported(test_results):
                capability = self._create_capability_from_test(capability_type, test_results)
                result.discovered_capabilities.append(capability)
                result.status = DiscoveryStatus.COMPLETED
            else:
                result.status = DiscoveryStatus.COMPLETED
            log_info(f"模型不支持能力: {capability_type} (模型ID: {model_id})")
            
        except Exception as e:
            result.status = DiscoveryStatus.FAILED
            result.error_message = str(e)
            log_error(f"能力测试失败: {capability_type} (模型ID: {model_id}) - {e}")
        
        result.end_time = time.time()
        return result
    
    def _is_capability_supported(self, test_results: List[CapabilityTestResult]) -> bool:
        """判断能力是否被支持"""
        if not test_results:
            return False
        
        # 计算通过率
        passed_tests = len([r for r in test_results if r.result == TestResult.PASSED])
        total_tests = len(test_results)
        
        # 如果通过率超过60%，则认为支持该能力（降低阈值以提高发现率）
        return (passed_tests / total_tests) >= 0.6 if total_tests > 0 else False
    
    def _create_capability_from_test(self, capability_type: CapabilityType, 
                                   test_results: List[CapabilityTestResult]) -> Capability:
        """从测试结果创建能力"""
        # 根据能力类型创建对应的能力定义
        if capability_type == CapabilityType.TEXT_GENERATION:
            return self._create_text_generation_capability(test_results)
        elif capability_type == CapabilityType.CODE_GENERATION:
            return self._create_code_generation_capability(test_results)
        elif capability_type == CapabilityType.TEXT_SUMMARY:
            return self._create_text_summary_capability(test_results)
        elif capability_type == CapabilityType.TRANSLATION:
            return self._create_translation_capability(test_results)
        elif capability_type == CapabilityType.QUESTION_ANSWERING:
            return self._create_question_answering_capability(test_results)
        else:
            # 默认能力定义
            return Capability(
                capability_id=f"{capability_type.value}_{int(time.time())}",
                name=capability_type.value.replace('_', ' ').title(),
                description=f"自动发现的{capability_type.value}能力",
                capability_type=capability_type,
                status=CapabilityStatus.EXPERIMENTAL
            )
    
    def _create_text_generation_capability(self, test_results: List[CapabilityTestResult]) -> Capability:
        """创建文本生成能力"""
        return Capability(
            capability_id=f"text_generation_auto_{int(time.time())}",
            name="文本生成",
            description="根据提示生成文本内容",
            capability_type=CapabilityType.TEXT_GENERATION,
            parameters=[
                CapabilityParameter(
                    name="prompt",
                    type="string",
                    description="生成文本的提示",
                    required=True
                ),
                CapabilityParameter(
                    name="max_length",
                    type="number",
                    description="生成文本的最大长度",
                    required=False,
                    default_value=1000,
                    constraints={"min": 1, "max": 10000}
                ),
                CapabilityParameter(
                    name="temperature",
                    type="number",
                    description="生成温度，控制随机性",
                    required=False,
                    default_value=0.7,
                    constraints={"min": 0.0, "max": 2.0}
                )
            ],
            outputs=[
                CapabilityOutput(
                    name="generated_text",
                    type="string",
                    description="生成的文本内容",
                    format="plain"
                )
            ],
            tags=["text", "generation", "ai", "auto_discovered"],
            category="text_processing",
            complexity=2,
            status=CapabilityStatus.AVAILABLE
        )
    
    def _create_code_generation_capability(self, test_results: List[CapabilityTestResult]) -> Capability:
        """创建代码生成能力"""
        return Capability(
            capability_id=f"code_generation_auto_{int(time.time())}",
            name="代码生成",
            description="根据需求生成代码",
            capability_type=CapabilityType.CODE_GENERATION,
            parameters=[
                CapabilityParameter(
                    name="requirement",
                    type="string",
                    description="代码需求描述",
                    required=True
                ),
                CapabilityParameter(
                    name="language",
                    type="string",
                    description="编程语言",
                    required=False,
                    default_value="python"
                )
            ],
            outputs=[
                CapabilityOutput(
                    name="generated_code",
                    type="string",
                    description="生成的代码",
                    format="code"
                )
            ],
            tags=["code", "generation", "programming", "auto_discovered"],
            category="development",
            complexity=3,
            status=CapabilityStatus.AVAILABLE
        )
    
    def _create_text_summary_capability(self, test_results: List[CapabilityTestResult]) -> Capability:
        """创建文本摘要能力"""
        return Capability(
            capability_id=f"text_summary_auto_{int(time.time())}",
            name="文本摘要",
            description="对长文本进行摘要",
            capability_type=CapabilityType.TEXT_SUMMARY,
            parameters=[
                CapabilityParameter(
                    name="text",
                    type="string",
                    description="需要摘要的文本",
                    required=True
                ),
                CapabilityParameter(
                    name="max_length",
                    type="number",
                    description="摘要最大长度",
                    required=False,
                    default_value=200
                )
            ],
            outputs=[
                CapabilityOutput(
                    name="summary",
                    type="string",
                    description="生成的摘要",
                    format="plain"
                )
            ],
            tags=["text", "summary", "ai", "auto_discovered"],
            category="text_processing",
            complexity=2,
            status=CapabilityStatus.AVAILABLE
        )
    
    def _create_translation_capability(self, test_results: List[CapabilityTestResult]) -> Capability:
        """创建翻译能力"""
        return Capability(
            capability_id=f"translation_auto_{int(time.time())}",
            name="翻译",
            description="文本翻译功能",
            capability_type=CapabilityType.TRANSLATION,
            parameters=[
                CapabilityParameter(
                    name="text",
                    type="string",
                    description="需要翻译的文本",
                    required=True
                ),
                CapabilityParameter(
                    name="target_language",
                    type="string",
                    description="目标语言",
                    required=True
                )
            ],
            outputs=[
                CapabilityOutput(
                    name="translated_text",
                    type="string",
                    description="翻译后的文本",
                    format="plain"
                )
            ],
            tags=["translation", "language", "auto_discovered"],
            category="language",
            complexity=2,
            status=CapabilityStatus.AVAILABLE
        )
    
    def _create_question_answering_capability(self, test_results: List[CapabilityTestResult]) -> Capability:
        """创建问答能力"""
        return Capability(
            capability_id=f"question_answering_auto_{int(time.time())}",
            name="问答",
            description="回答用户问题",
            capability_type=CapabilityType.QUESTION_ANSWERING,
            parameters=[
                CapabilityParameter(
                    name="question",
                    type="string",
                    description="用户问题",
                    required=True
                ),
                CapabilityParameter(
                    name="context",
                    type="string",
                    description="上下文信息",
                    required=False
                )
            ],
            outputs=[
                CapabilityOutput(
                    name="answer",
                    type="string",
                    description="回答内容",
                    format="plain"
                )
            ],
            tags=["qa", "question", "answer", "auto_discovered"],
            category="knowledge",
            complexity=2,
            status=CapabilityStatus.AVAILABLE
        )
    
    async def _test_text_generation(self, model_id: str) -> List[CapabilityTestResult]:
        """测试文本生成能力"""
        test_results = []
        
        # 测试用例1：基础文本生成
        test_id = "text_gen_basic"
        start_time = time.time()
        try:
            result = await self.model_manager.generate_text(
                model_id=model_id,
                prompt="请生成一段关于人工智能的简短介绍",
                max_length=100
            )
            execution_time = time.time() - start_time
            
            # 验证结果
            if result and len(result) > 10:
                test_result = TestResult.PASSED
            else:
                test_result = TestResult.FAILED
            
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="text_generation",
                model_id=model_id,
                result=test_result,
                actual_output={"generated_text": result},
                execution_time=execution_time
            ))
            
        except Exception as e:
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="text_generation",
                model_id=model_id,
                result=TestResult.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            ))
        
        # 测试用例2：长文本生成
        test_id = "text_gen_long"
        start_time = time.time()
        try:
            result = await self.model_manager.generate_text(
                model_id=model_id,
                prompt="写一篇关于机器学习的文章，包含监督学习和无监督学习的区别",
                max_length=500
            )
            execution_time = time.time() - start_time
            
            # 验证结果
            if result and len(result) > 100:
                test_result = TestResult.PASSED
            else:
                test_result = TestResult.FAILED
            
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="text_generation",
                model_id=model_id,
                result=test_result,
                actual_output={"generated_text": result},
                execution_time=execution_time
            ))
            
        except Exception as e:
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="text_generation",
                model_id=model_id,
                result=TestResult.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            ))
        
        return test_results
    
    async def _test_code_generation(self, model_id: str) -> List[CapabilityTestResult]:
        """测试代码生成能力"""
        test_results = []
        
        # 测试用例1：简单代码生成
        test_id = "code_gen_simple"
        start_time = time.time()
        try:
            result = await self.model_manager.generate_text(
                model_id=model_id,
                prompt="写一个Python函数，计算两个数的和",
                max_length=200
            )
            execution_time = time.time() - start_time
            
            # 验证结果
            if result and ("def" in result or "function" in result):
                test_result = TestResult.PASSED
            else:
                test_result = TestResult.FAILED
            
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="code_generation",
                model_id=model_id,
                result=test_result,
                actual_output={"generated_code": result},
                execution_time=execution_time
            ))
            
        except Exception as e:
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="code_generation",
                model_id=model_id,
                result=TestResult.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            ))
        
        return test_results
    
    async def _test_text_summary(self, model_id: str) -> List[CapabilityTestResult]:
        """测试文本摘要能力"""
        test_results = []
        
        # 测试用例1：文本摘要
        test_id = "text_summary_basic"
        start_time = time.time()
        try:
            long_text = """
            人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
            该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
            """
            
            result = await self.model_manager.generate_text(
                model_id=model_id,
                prompt=f"请对以下文本进行摘要：{long_text}",
                max_length=100
            )
            execution_time = time.time() - start_time
            
            # 验证结果
            if result and len(result) > 20 and len(result) < len(long_text):
                test_result = TestResult.PASSED
            else:
                test_result = TestResult.FAILED
            
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="text_summary",
                model_id=model_id,
                result=test_result,
                actual_output={"summary": result},
                execution_time=execution_time
            ))
            
        except Exception as e:
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="text_summary",
                model_id=model_id,
                result=TestResult.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            ))
        
        return test_results
    
    async def _test_translation(self, model_id: str) -> List[CapabilityTestResult]:
        """测试翻译能力"""
        test_results = []
        
        # 测试用例1：中英翻译
        test_id = "translation_en_zh"
        start_time = time.time()
        try:
            result = await self.model_manager.generate_text(
                model_id=model_id,
                prompt="Translate 'Hello, how are you?' to Chinese",
                max_length=50
            )
            execution_time = time.time() - start_time
            
            # 验证结果
            if result and any(word in result.lower() for word in ["你好", "您好", "how are you"]):
                test_result = TestResult.PASSED
            else:
                test_result = TestResult.FAILED
            
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="translation",
                model_id=model_id,
                result=test_result,
                actual_output={"translated_text": result},
                execution_time=execution_time
            ))
            
        except Exception as e:
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="translation",
                model_id=model_id,
                result=TestResult.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            ))
        
        return test_results
    
    async def _test_question_answering(self, model_id: str) -> List[CapabilityTestResult]:
        """测试问答能力"""
        test_results = []
        
        # 测试用例1：基础问答
        test_id = "qa_basic"
        start_time = time.time()
        try:
            result = await self.model_manager.generate_text(
                model_id=model_id,
                prompt="What is the capital of France?",
                max_length=50
            )
            execution_time = time.time() - start_time
            
            # 验证结果
            if result and "paris" in result.lower():
                test_result = TestResult.PASSED
            else:
                test_result = TestResult.FAILED
            
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="question_answering",
                model_id=model_id,
                result=test_result,
                actual_output={"answer": result},
                execution_time=execution_time
            ))
            
        except Exception as e:
            test_results.append(CapabilityTestResult(
                test_id=test_id,
                capability_id="question_answering",
                model_id=model_id,
                result=TestResult.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            ))
        
        return test_results
    
    def get_task_status(self, task_id: str) -> Optional[DiscoveryTask]:
        """获取任务状态"""
        return self.discovery_tasks.get(task_id)
    
    def get_all_tasks(self) -> List[DiscoveryTask]:
        """获取所有任务"""
        return list(self.discovery_tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.discovery_tasks.get(task_id)
        if task and task.status in [DiscoveryStatus.PENDING, DiscoveryStatus.RUNNING]:
            task.status = DiscoveryStatus.CANCELLED
            task.updated_time = time.time()
            log_info(f"取消发现任务: {task_id}")
            return True
        return False
    
    def get_discovery_statistics(self) -> Dict[str, Any]:
        """获取发现统计信息"""
        total_tasks = len(self.discovery_tasks)
        completed_tasks = len([t for t in self.discovery_tasks.values() 
                              if t.status == DiscoveryStatus.COMPLETED])
        failed_tasks = len([t for t in self.discovery_tasks.values() 
                           if t.status == DiscoveryStatus.FAILED])
        running_tasks = len([t for t in self.discovery_tasks.values() 
                            if t.status == DiscoveryStatus.RUNNING])
        
        # 统计发现的能力数量
        discovered_capabilities = 0
        for task in self.discovery_tasks.values():
            for result in task.results:
                discovered_capabilities += len(result.discovered_capabilities)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "discovered_capabilities": discovered_capabilities,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
        }


# 测试函数
async def test_capability_discovery():
    """测试能力发现机制"""
    try:
        # 创建模拟的模型管理器和能力注册表
        from unittest.mock import Mock, AsyncMock
        
        mock_model_manager = Mock()
        mock_model_manager.generate_text = AsyncMock(return_value="测试生成的文本内容")
        
        capability_registry = CapabilityRegistry()
        
        # 创建能力发现器
        discovery = CapabilityDiscovery(mock_model_manager, capability_registry)
        
        # 测试能力发现
        task_id = await discovery.discover_model_capabilities("test_model")
        
        # 等待任务完成
        await asyncio.sleep(0.1)
        
        # 检查任务状态
        task = discovery.get_task_status(task_id)
        assert task is not None
        assert task.status == DiscoveryStatus.COMPLETED
        
        # 检查统计信息
        stats = discovery.get_discovery_statistics()
        assert stats["total_tasks"] == 1
        assert stats["completed_tasks"] == 1
        
        print("✓ 能力发现机制测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 能力发现机制测试失败: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_capability_discovery())
