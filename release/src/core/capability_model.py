"""
能力数据模型
定义AI代理的能力数据结构和相关功能
"""

from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
import json
import time
from datetime import datetime
import uuid

from ..utils.logger import log_info, log_error, log_warning


class CapabilityType(Enum):
    """能力类型枚举"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    TEXT_SUMMARY = "text_summary"
    TRANSLATION = "translation"
    QUESTION_ANSWERING = "question_answering"
    DATA_ANALYSIS = "data_analysis"
    IMAGE_GENERATION = "image_generation"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"
    FILE_PROCESSING = "file_processing"
    WEB_SEARCH = "web_search"
    CALCULATION = "calculation"
    REASONING = "reasoning"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_WRITING = "technical_writing"
    CUSTOM = "custom"


class CapabilityStatus(Enum):
    """能力状态枚举"""
    AVAILABLE = "available"
    TESTING = "testing"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class TestResult(Enum):
    """测试结果枚举"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"
    NOT_TESTED = "not_tested"


@dataclass
class CapabilityParameter:
    """能力参数定义"""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = False
    default_value: Optional[Any] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    examples: List[Any] = field(default_factory=list)


@dataclass
class CapabilityOutput:
    """能力输出定义"""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    format: Optional[str] = None  # 如 "json", "markdown", "html" 等
    examples: List[Any] = field(default_factory=list)


@dataclass
class CapabilityTest:
    """能力测试定义"""
    test_id: str
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    timeout: int = 30
    priority: int = 1
    tags: List[str] = field(default_factory=list)


@dataclass
class CapabilityTestResult:
    """能力测试结果"""
    test_id: str
    capability_id: str
    model_id: str
    result: TestResult
    actual_output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Capability:
    """能力定义"""
    capability_id: str
    name: str
    description: str
    capability_type: CapabilityType
    version: str = "1.0.0"
    status: CapabilityStatus = CapabilityStatus.AVAILABLE
    
    # 输入输出定义
    parameters: List[CapabilityParameter] = field(default_factory=list)
    outputs: List[CapabilityOutput] = field(default_factory=list)
    
    # 测试相关
    test_cases: List[CapabilityTest] = field(default_factory=list)
    test_results: List[CapabilityTestResult] = field(default_factory=list)
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    complexity: int = 1  # 1-5，复杂度等级
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他能力ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 统计信息
    usage_count: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    last_used: Optional[float] = None
    created_time: float = field(default_factory=time.time)
    updated_time: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "description": self.description,
            "capability_type": self.capability_type.value,
            "version": self.version,
            "status": self.status.value,
            "parameters": [self._parameter_to_dict(p) for p in self.parameters],
            "outputs": [self._output_to_dict(o) for o in self.outputs],
            "test_cases": [self._test_to_dict(t) for t in self.test_cases],
            "tags": self.tags,
            "category": self.category,
            "complexity": self.complexity,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "average_response_time": self.average_response_time,
            "last_used": self.last_used,
            "created_time": self.created_time,
            "updated_time": self.updated_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Capability':
        """从字典创建实例"""
        capability = cls(
            capability_id=data["capability_id"],
            name=data["name"],
            description=data["description"],
            capability_type=CapabilityType(data["capability_type"]),
            version=data.get("version", "1.0.0"),
            status=CapabilityStatus(data.get("status", "available")),
            parameters=[cls._parameter_from_dict(p) for p in data.get("parameters", [])],
            outputs=[cls._output_from_dict(o) for o in data.get("outputs", [])],
            test_cases=[cls._test_from_dict(t) for t in data.get("test_cases", [])],
            tags=data.get("tags", []),
            category=data.get("category", "general"),
            complexity=data.get("complexity", 1),
            dependencies=data.get("dependencies", []),
            metadata=data.get("metadata", {}),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0),
            average_response_time=data.get("average_response_time", 0.0),
            last_used=data.get("last_used"),
            created_time=data.get("created_time", time.time()),
            updated_time=data.get("updated_time", time.time())
        )
        
        # 处理测试结果
        test_results = data.get("test_results", [])
        capability.test_results = [cls._test_result_from_dict(tr) for tr in test_results]
        
        return capability
    
    def _parameter_to_dict(self, parameter: CapabilityParameter) -> Dict[str, Any]:
        """参数转换为字典"""
        return {
            "name": parameter.name,
            "type": parameter.type,
            "description": parameter.description,
            "required": parameter.required,
            "default_value": parameter.default_value,
            "constraints": parameter.constraints,
            "examples": parameter.examples
        }
    
    @classmethod
    def _parameter_from_dict(cls, data: Dict[str, Any]) -> CapabilityParameter:
        """从字典创建参数"""
        return CapabilityParameter(
            name=data["name"],
            type=data["type"],
            description=data["description"],
            required=data.get("required", False),
            default_value=data.get("default_value"),
            constraints=data.get("constraints", {}),
            examples=data.get("examples", [])
        )
    
    def _output_to_dict(self, output: CapabilityOutput) -> Dict[str, Any]:
        """输出转换为字典"""
        return {
            "name": output.name,
            "type": output.type,
            "description": output.description,
            "format": output.format,
            "examples": output.examples
        }
    
    @classmethod
    def _output_from_dict(cls, data: Dict[str, Any]) -> CapabilityOutput:
        """从字典创建输出"""
        return CapabilityOutput(
            name=data["name"],
            type=data["type"],
            description=data["description"],
            format=data.get("format"),
            examples=data.get("examples", [])
        )
    
    def _test_to_dict(self, test: CapabilityTest) -> Dict[str, Any]:
        """测试转换为字典"""
        return {
            "test_id": test.test_id,
            "name": test.name,
            "description": test.description,
            "input_data": test.input_data,
            "expected_output": test.expected_output,
            "timeout": test.timeout,
            "priority": test.priority,
            "tags": test.tags
        }
    
    @classmethod
    def _test_from_dict(cls, data: Dict[str, Any]) -> CapabilityTest:
        """从字典创建测试"""
        return CapabilityTest(
            test_id=data["test_id"],
            name=data["name"],
            description=data["description"],
            input_data=data["input_data"],
            expected_output=data["expected_output"],
            timeout=data.get("timeout", 30),
            priority=data.get("priority", 1),
            tags=data.get("tags", [])
        )
    
    @classmethod
    def _test_result_from_dict(cls, data: Dict[str, Any]) -> CapabilityTestResult:
        """从字典创建测试结果"""
        return CapabilityTestResult(
            test_id=data["test_id"],
            capability_id=data["capability_id"],
            model_id=data["model_id"],
            result=TestResult(data["result"]),
            actual_output=data.get("actual_output"),
            error_message=data.get("error_message"),
            execution_time=data.get("execution_time", 0.0),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {})
        )
    
    def add_test_case(self, test: CapabilityTest):
        """添加测试用例"""
        self.test_cases.append(test)
        self.updated_time = time.time()
    
    def add_test_result(self, result: CapabilityTestResult):
        """添加测试结果"""
        self.test_results.append(result)
        self.updated_time = time.time()
        
        # 更新统计信息
        if result.result == TestResult.PASSED:
            self.usage_count += 1
            self.average_response_time = (
                (self.average_response_time * (self.usage_count - 1) + result.execution_time) 
                / self.usage_count
            )
        
        # 计算成功率
        total_tests = len([r for r in self.test_results if r.result != TestResult.NOT_TESTED])
        if total_tests > 0:
            passed_tests = len([r for r in self.test_results if r.result == TestResult.PASSED])
            self.success_rate = passed_tests / total_tests
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据"""
        try:
            for param in self.parameters:
                if param.required and param.name not in input_data:
                    return False
                
                if param.name in input_data:
                    value = input_data[param.name]
                    if not self._validate_parameter_value(param, value):
                        return False
            
            return True
            
        except Exception as e:
            log_error(f"验证输入数据失败: {self.capability_id}", e)
            return False
    
    def _validate_parameter_value(self, param: CapabilityParameter, value: Any) -> bool:
        """验证参数值"""
        # 类型检查
        if param.type == "string" and not isinstance(value, str):
            return False
        elif param.type == "number" and not isinstance(value, (int, float)):
            return False
        elif param.type == "boolean" and not isinstance(value, bool):
            return False
        elif param.type == "array" and not isinstance(value, list):
            return False
        elif param.type == "object" and not isinstance(value, dict):
            return False
        
        # 约束检查
        constraints = param.constraints
        if constraints:
            if "min" in constraints and value < constraints["min"]:
                return False
            if "max" in constraints and value > constraints["max"]:
                return False
            if "min_length" in constraints and len(value) < constraints["min_length"]:
                return False
            if "max_length" in constraints and len(value) > constraints["max_length"]:
                return False
            if "pattern" in constraints and not re.match(constraints["pattern"], str(value)):
                return False
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "average_response_time": self.average_response_time,
            "last_used": self.last_used,
            "test_count": len(self.test_cases),
            "test_results": {
                "passed": len([r for r in self.test_results if r.result == TestResult.PASSED]),
                "failed": len([r for r in self.test_results if r.result == TestResult.FAILED]),
                "partial": len([r for r in self.test_results if r.result == TestResult.PARTIAL]),
                "timeout": len([r for r in self.test_results if r.result == TestResult.TIMEOUT]),
                "error": len([r for r in self.test_results if r.result == TestResult.ERROR]),
                "not_tested": len([r for r in self.test_results if r.result == TestResult.NOT_TESTED])
            }
        }


@dataclass
class CapabilityRegistry:
    """能力注册表"""
    capabilities: Dict[str, Capability] = field(default_factory=dict)
    
    def register_capability(self, capability: Capability) -> bool:
        """注册能力"""
        if capability.capability_id in self.capabilities:
            log_warning(f"能力已存在: {capability.capability_id}")
            return False
        
        self.capabilities[capability.capability_id] = capability
        log_info(f"注册能力: {capability.name} ({capability.capability_id})")
        return True
    
    def unregister_capability(self, capability_id: str) -> bool:
        """注销能力"""
        if capability_id not in self.capabilities:
            log_warning(f"能力不存在: {capability_id}")
            return False
        
        del self.capabilities[capability_id]
        log_info(f"注销能力: {capability_id}")
        return True
    
    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """获取能力"""
        return self.capabilities.get(capability_id)
    
    def get_capabilities_by_type(self, capability_type: CapabilityType) -> List[Capability]:
        """按类型获取能力"""
        return [cap for cap in self.capabilities.values() 
                if cap.capability_type == capability_type]
    
    def get_capabilities_by_category(self, category: str) -> List[Capability]:
        """按分类获取能力"""
        return [cap for cap in self.capabilities.values() 
                if cap.category == category]
    
    def get_capabilities_by_tag(self, tag: str) -> List[Capability]:
        """按标签获取能力"""
        return [cap for cap in self.capabilities.values() 
                if tag in cap.tags]
    
    def search_capabilities(self, query: str) -> List[Capability]:
        """搜索能力"""
        query = query.lower()
        results = []
        
        for capability in self.capabilities.values():
            if (query in capability.name.lower() or 
                query in capability.description.lower() or
                any(query in tag.lower() for tag in capability.tags)):
                results.append(capability)
        
        return results
    
    def get_all_capabilities(self) -> List[Capability]:
        """获取所有能力"""
        return list(self.capabilities.values())
    
    def get_capability_count(self) -> int:
        """获取能力数量"""
        return len(self.capabilities)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "capabilities": {
                cap_id: capability.to_dict() 
                for cap_id, capability in self.capabilities.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CapabilityRegistry':
        """从字典创建实例"""
        registry = cls()
        
        capabilities_data = data.get("capabilities", {})
        for cap_id, cap_data in capabilities_data.items():
            capability = Capability.from_dict(cap_data)
            registry.capabilities[cap_id] = capability
        
        return registry


# 预定义的标准能力
def create_standard_capabilities() -> CapabilityRegistry:
    """创建标准能力"""
    registry = CapabilityRegistry()
    
    # 文本生成能力
    text_generation = Capability(
        capability_id="text_generation_v1",
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
        tags=["text", "generation", "ai"],
        category="text_processing",
        complexity=2
    )
    
    # 代码生成能力
    code_generation = Capability(
        capability_id="code_generation_v1",
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
            ),
            CapabilityParameter(
                name="framework",
                type="string",
                description="使用的框架",
                required=False
            )
        ],
        outputs=[
            CapabilityOutput(
                name="generated_code",
                type="string",
                description="生成的代码",
                format="code"
            ),
            CapabilityOutput(
                name="explanation",
                type="string",
                description="代码解释",
                format="markdown"
            )
        ],
        tags=["code", "generation", "programming"],
        category="development",
        complexity=3
    )
    
    # 文本摘要能力
    text_summary = Capability(
        capability_id="text_summary_v1",
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
        tags=["text", "summary", "ai"],
        category="text_processing",
        complexity=2
    )
    
    # 注册所有标准能力
    registry.register_capability(text_generation)
    registry.register_capability(code_generation)
    registry.register_capability(text_summary)
    
    return registry


# 测试函数
def test_capability_model():
    """测试能力数据模型"""
    try:
        # 创建标准能力
        registry = create_standard_capabilities()
        
        # 测试能力注册
        assert registry.get_capability_count() == 3
        assert registry.get_capability("text_generation_v1") is not None
        
        # 测试能力搜索
        text_caps = registry.get_capabilities_by_type(CapabilityType.TEXT_GENERATION)
        assert len(text_caps) == 1
        
        # 测试能力序列化
        text_gen = registry.get_capability("text_generation_v1")
        capability_dict = text_gen.to_dict()
        assert capability_dict["capability_id"] == "text_generation_v1"
        
        # 测试能力反序列化
        restored_capability = Capability.from_dict(capability_dict)
        assert restored_capability.name == "文本生成"
        
        # 测试输入验证
        valid_input = {"prompt": "你好", "max_length": 500}
        assert text_gen.validate_input(valid_input) is True
        
        invalid_input = {"max_length": 500}  # 缺少必需的prompt参数
        assert text_gen.validate_input(invalid_input) is False
        
        # 测试统计信息
        stats = text_gen.get_statistics()
        assert stats["name"] == "文本生成"
        assert stats["usage_count"] == 0
        
        print("✓ 能力数据模型测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 能力数据模型测试失败: {e}")
        return False


if __name__ == "__main__":
    test_capability_model()
