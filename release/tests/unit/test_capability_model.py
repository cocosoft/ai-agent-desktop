"""
能力数据模型单元测试
测试能力数据模型的基础功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.capability_model import (
    Capability, CapabilityType, CapabilityStatus, TestResult,
    CapabilityParameter, CapabilityOutput, CapabilityTest, CapabilityTestResult,
    CapabilityRegistry, create_standard_capabilities
)


class TestCapabilityModel:
    """能力数据模型测试类"""
    
    @pytest.fixture
    def sample_capability(self):
        """创建示例能力"""
        return Capability(
            capability_id="test_capability_v1",
            name="测试能力",
            description="这是一个测试能力",
            capability_type=CapabilityType.TEXT_GENERATION,
            parameters=[
                CapabilityParameter(
                    name="input_text",
                    type="string",
                    description="输入文本",
                    required=True
                ),
                CapabilityParameter(
                    name="max_length",
                    type="number",
                    description="最大长度",
                    required=False,
                    default_value=100,
                    constraints={"min": 1, "max": 1000}
                )
            ],
            outputs=[
                CapabilityOutput(
                    name="output_text",
                    type="string",
                    description="输出文本",
                    format="plain"
                )
            ],
            tags=["test", "text"],
            category="testing",
            complexity=2
        )
    
    @pytest.fixture
    def sample_test(self):
        """创建示例测试"""
        return CapabilityTest(
            test_id="test_1",
            name="基础测试",
            description="基础功能测试",
            input_data={"input_text": "测试输入"},
            expected_output={"output_text": "测试输出"},
            timeout=30,
            priority=1,
            tags=["basic"]
        )
    
    def test_capability_creation(self, sample_capability):
        """测试能力创建"""
        assert sample_capability.capability_id == "test_capability_v1"
        assert sample_capability.name == "测试能力"
        assert sample_capability.capability_type == CapabilityType.TEXT_GENERATION
        assert sample_capability.status == CapabilityStatus.AVAILABLE
        assert len(sample_capability.parameters) == 2
        assert len(sample_capability.outputs) == 1
        assert sample_capability.complexity == 2
    
    def test_capability_serialization(self, sample_capability):
        """测试能力序列化"""
        # 转换为字典
        capability_dict = sample_capability.to_dict()
        
        assert capability_dict["capability_id"] == "test_capability_v1"
        assert capability_dict["name"] == "测试能力"
        assert capability_dict["capability_type"] == "text_generation"
        assert capability_dict["status"] == "available"
        assert len(capability_dict["parameters"]) == 2
        assert len(capability_dict["outputs"]) == 1
        
        # 从字典恢复
        restored_capability = Capability.from_dict(capability_dict)
        
        assert restored_capability.capability_id == sample_capability.capability_id
        assert restored_capability.name == sample_capability.name
        assert restored_capability.capability_type == sample_capability.capability_type
        assert len(restored_capability.parameters) == len(sample_capability.parameters)
        assert len(restored_capability.outputs) == len(sample_capability.outputs)
    
    def test_capability_input_validation(self, sample_capability):
        """测试输入验证"""
        # 有效输入
        valid_input = {"input_text": "测试文本", "max_length": 200}
        assert sample_capability.validate_input(valid_input) is True
        
        # 无效输入 - 缺少必需参数
        invalid_input_missing = {"max_length": 200}
        assert sample_capability.validate_input(invalid_input_missing) is False
        
        # 无效输入 - 参数类型错误
        invalid_input_type = {"input_text": "测试文本", "max_length": "invalid"}
        assert sample_capability.validate_input(invalid_input_type) is False
        
        # 无效输入 - 超出约束范围
        invalid_input_constraint = {"input_text": "测试文本", "max_length": 2000}
        assert sample_capability.validate_input(invalid_input_constraint) is False
    
    def test_capability_test_management(self, sample_capability, sample_test):
        """测试测试用例管理"""
        # 添加测试用例
        sample_capability.add_test_case(sample_test)
        
        assert len(sample_capability.test_cases) == 1
        assert sample_capability.test_cases[0].test_id == "test_1"
        
        # 添加测试结果
        test_result = CapabilityTestResult(
            test_id="test_1",
            capability_id="test_capability_v1",
            model_id="test_model",
            result=TestResult.PASSED,
            actual_output={"output_text": "测试输出"},
            execution_time=1.5
        )
        
        sample_capability.add_test_result(test_result)
        
        assert len(sample_capability.test_results) == 1
        assert sample_capability.test_results[0].result == TestResult.PASSED
        
        # 验证统计信息更新
        stats = sample_capability.get_statistics()
        assert stats["usage_count"] == 1
        assert stats["success_rate"] == 1.0
        assert stats["average_response_time"] == 1.5
    
    def test_capability_registry(self, sample_capability):
        """测试能力注册表"""
        registry = CapabilityRegistry()
        
        # 注册能力
        assert registry.register_capability(sample_capability) is True
        assert registry.get_capability_count() == 1
        
        # 重复注册
        assert registry.register_capability(sample_capability) is False
        
        # 获取能力
        retrieved_capability = registry.get_capability("test_capability_v1")
        assert retrieved_capability is not None
        assert retrieved_capability.name == "测试能力"
        
        # 注销能力
        assert registry.unregister_capability("test_capability_v1") is True
        assert registry.get_capability_count() == 0
        
        # 注销不存在的能力
        assert registry.unregister_capability("nonexistent") is False
    
    def test_capability_search(self, sample_capability):
        """测试能力搜索"""
        registry = CapabilityRegistry()
        registry.register_capability(sample_capability)
        
        # 按类型搜索
        text_caps = registry.get_capabilities_by_type(CapabilityType.TEXT_GENERATION)
        assert len(text_caps) == 1
        
        # 按分类搜索
        test_caps = registry.get_capabilities_by_category("testing")
        assert len(test_caps) == 1
        
        # 按标签搜索
        test_tag_caps = registry.get_capabilities_by_tag("test")
        assert len(test_tag_caps) == 1
        
        # 文本搜索
        search_results = registry.search_capabilities("测试")
        assert len(search_results) == 1
        
        search_results = registry.search_capabilities("text")
        assert len(search_results) == 1
    
    def test_standard_capabilities(self):
        """测试标准能力"""
        registry = create_standard_capabilities()
        
        assert registry.get_capability_count() == 3
        
        # 验证文本生成能力
        text_gen = registry.get_capability("text_generation_v1")
        assert text_gen is not None
        assert text_gen.name == "文本生成"
        assert text_gen.capability_type == CapabilityType.TEXT_GENERATION
        
        # 验证代码生成能力
        code_gen = registry.get_capability("code_generation_v1")
        assert code_gen is not None
        assert code_gen.name == "代码生成"
        assert code_gen.capability_type == CapabilityType.CODE_GENERATION
        
        # 验证文本摘要能力
        text_summary = registry.get_capability("text_summary_v1")
        assert text_summary is not None
        assert text_summary.name == "文本摘要"
        assert text_summary.capability_type == CapabilityType.TEXT_SUMMARY
    
    def test_capability_statistics(self, sample_capability):
        """测试统计信息"""
        # 添加多个测试结果
        for i in range(3):
            result = CapabilityTestResult(
                test_id=f"test_{i}",
                capability_id="test_capability_v1",
                model_id="test_model",
                result=TestResult.PASSED if i < 2 else TestResult.FAILED,
                execution_time=1.0 + i * 0.5
            )
            sample_capability.add_test_result(result)
        
        stats = sample_capability.get_statistics()
        
        assert stats["usage_count"] == 2  # 只有PASSED结果计入使用次数
        assert stats["success_rate"] == 2/3  # 2个通过，1个失败
        assert stats["average_response_time"] == (1.0 + 1.5) / 2  # 平均响应时间
        assert stats["test_count"] == 0  # 测试用例数量（未添加测试用例）
        
        # 验证测试结果统计
        test_results = stats["test_results"]
        assert test_results["passed"] == 2
        assert test_results["failed"] == 1
        assert test_results["partial"] == 0
        assert test_results["timeout"] == 0
        assert test_results["error"] == 0
        assert test_results["not_tested"] == 0


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
