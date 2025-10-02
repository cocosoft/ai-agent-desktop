"""
能力映射单元测试
测试能力与模型关联管理的功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.core.capability_mapping import (
    CapabilityMappingManager, ModelCapabilityMapping, CapabilityMappingResult,
    MappingStrategy, CapabilityStatus
)
from src.core.capability_model import (
    Capability, CapabilityType, CapabilityRegistry,
    CapabilityParameter, CapabilityOutput
)


class TestCapabilityMapping:
    """能力映射测试类"""
    
    @pytest.fixture
    def mock_model_manager(self):
        """创建模拟的模型管理器"""
        mock_manager = Mock()
        return mock_manager
    
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
        
        registry.register_capability(test_capability)
        return registry
    
    @pytest.fixture
    def mapping_manager(self, mock_model_manager, capability_registry):
        """创建能力映射管理器"""
        return CapabilityMappingManager(mock_model_manager, capability_registry)
    
    def test_initialization(self, mapping_manager):
        """测试初始化"""
        assert mapping_manager is not None
        assert mapping_manager.model_manager is not None
        assert mapping_manager.capability_registry is not None
        assert mapping_manager.mappings == {}
    
    def test_add_mapping(self, mapping_manager, capability_registry):
        """测试添加能力映射"""
        mapping_id = mapping_manager.add_mapping(
            "test_model_1", 
            "test_capability_1", 
            priority=5,
            metadata={"test": "data"}
        )
        
        # 检查映射是否添加成功
        assert mapping_id is not None
        assert len(mapping_manager.mappings) == 1
        
        mapping = mapping_manager.get_mapping_by_id(mapping_id)
        assert mapping is not None
        assert mapping.model_id == "test_model_1"
        assert mapping.capability_id == "test_capability_1"
        assert mapping.capability_type == CapabilityType.TEXT_GENERATION
        assert mapping.priority == 5
        assert mapping.metadata == {"test": "data"}
        assert mapping.status == CapabilityStatus.AVAILABLE
    
    def test_add_mapping_invalid_capability(self, mapping_manager):
        """测试添加无效能力的映射"""
        with pytest.raises(ValueError, match="能力不存在: invalid_capability"):
            mapping_manager.add_mapping("test_model", "invalid_capability")
    
    def test_remove_mapping(self, mapping_manager):
        """测试移除能力映射"""
        # 先添加一个映射
        mapping_id = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        
        # 检查映射存在
        assert mapping_manager.get_mapping_by_id(mapping_id) is not None
        
        # 移除映射
        result = mapping_manager.remove_mapping(mapping_id)
        assert result is True
        
        # 检查映射已移除
        assert mapping_manager.get_mapping_by_id(mapping_id) is None
        assert len(mapping_manager.mappings) == 0
    
    def test_remove_nonexistent_mapping(self, mapping_manager):
        """测试移除不存在的映射"""
        result = mapping_manager.remove_mapping("nonexistent_mapping")
        assert result is False
    
    def test_get_mappings_for_capability(self, mapping_manager):
        """测试获取指定能力的映射"""
        # 添加多个映射
        mapping_id1 = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        mapping_id2 = mapping_manager.add_mapping("test_model_2", "test_capability_1")
        
        # 获取映射
        mappings = mapping_manager.get_mappings_for_capability("test_capability_1")
        
        # 检查结果
        assert len(mappings) == 2
        mapping_ids = [m.mapping_id for m in mappings]
        assert mapping_id1 in mapping_ids
        assert mapping_id2 in mapping_ids
    
    def test_get_mappings_for_model(self, mapping_manager):
        """测试获取指定模型的映射"""
        # 添加多个映射
        mapping_id1 = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        mapping_id2 = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        
        # 获取映射
        mappings = mapping_manager.get_mappings_for_model("test_model_1")
        
        # 检查结果
        assert len(mappings) == 2
        mapping_ids = [m.mapping_id for m in mappings]
        assert mapping_id1 in mapping_ids
        assert mapping_id2 in mapping_ids
    
    def test_update_mapping_stats(self, mapping_manager):
        """测试更新映射统计信息"""
        # 添加映射
        mapping_id = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        
        # 初始状态检查
        mapping = mapping_manager.get_mapping_by_id(mapping_id)
        assert mapping.usage_count == 0
        assert mapping.success_rate == 0.0
        assert mapping.avg_response_time == 0.0
        
        # 更新统计信息
        mapping_manager.update_mapping_stats(mapping_id, True, 100.0, 0.01)
        
        # 检查更新后的状态
        updated_mapping = mapping_manager.get_mapping_by_id(mapping_id)
        assert updated_mapping.usage_count == 1
        assert updated_mapping.success_rate == 1.0
        assert updated_mapping.avg_response_time == 100.0
        assert updated_mapping.cost_per_request == 0.01
        assert updated_mapping.status == CapabilityStatus.AVAILABLE
    
    def test_update_mapping_stats_multiple(self, mapping_manager):
        """测试多次更新映射统计信息"""
        # 添加映射
        mapping_id = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        
        # 多次更新
        mapping_manager.update_mapping_stats(mapping_id, True, 100.0)
        mapping_manager.update_mapping_stats(mapping_id, False, 200.0)
        mapping_manager.update_mapping_stats(mapping_id, True, 150.0)
        
        # 检查统计信息
        mapping = mapping_manager.get_mapping_by_id(mapping_id)
        assert mapping.usage_count == 3
        assert mapping.success_rate == pytest.approx(2/3, 0.01)  # 2/3成功率
        assert mapping.avg_response_time == pytest.approx(150.0, 0.01)  # 平均响应时间
    
    def test_map_capability_to_model_best_match(self, mapping_manager):
        """测试最佳匹配策略"""
        # 添加多个映射
        mapping_id1 = mapping_manager.add_mapping("test_model_1", "test_capability_1", priority=5)
        mapping_id2 = mapping_manager.add_mapping("test_model_2", "test_capability_1", priority=8)
        
        # 更新统计信息，使第二个映射更优
        mapping_manager.update_mapping_stats(mapping_id1, True, 200.0, 0.02)
        mapping_manager.update_mapping_stats(mapping_id2, True, 100.0, 0.01)
        
        # 测试最佳匹配
        result = mapping_manager.map_capability_to_model(
            "test_capability_1", 
            strategy=MappingStrategy.BEST_MATCH
        )
        
        # 检查结果
        assert result is not None
        assert result.capability_id == "test_capability_1"
        assert result.model_id == "test_model_2"  # 应该选择优先级更高、响应时间更短的模型
        assert result.strategy == MappingStrategy.BEST_MATCH
        assert result.confidence > 0
    
    def test_map_capability_to_model_fastest(self, mapping_manager):
        """测试最快响应策略"""
        # 添加多个映射
        mapping_id1 = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        mapping_id2 = mapping_manager.add_mapping("test_model_2", "test_capability_1")
        
        # 更新响应时间
        mapping_manager.update_mapping_stats(mapping_id1, True, 300.0)
        mapping_manager.update_mapping_stats(mapping_id2, True, 100.0)
        
        # 测试最快响应策略
        result = mapping_manager.map_capability_to_model(
            "test_capability_1", 
            strategy=MappingStrategy.FASTEST
        )
        
        # 检查结果
        assert result is not None
        assert result.model_id == "test_model_2"  # 应该选择响应时间更短的模型
        assert result.strategy == MappingStrategy.FASTEST
    
    def test_map_capability_to_model_lowest_cost(self, mapping_manager):
        """测试最低成本策略"""
        # 添加多个映射
        mapping_id1 = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        mapping_id2 = mapping_manager.add_mapping("test_model_2", "test_capability_1")
        
        # 更新成本
        mapping_manager.update_mapping_stats(mapping_id1, True, 100.0, 0.05)
        mapping_manager.update_mapping_stats(mapping_id2, True, 100.0, 0.01)
        
        # 测试最低成本策略
        result = mapping_manager.map_capability_to_model(
            "test_capability_1", 
            strategy=MappingStrategy.LOWEST_COST
        )
        
        # 检查结果
        assert result is not None
        assert result.model_id == "test_model_2"  # 应该选择成本更低的模型
        assert result.strategy == MappingStrategy.LOWEST_COST
    
    def test_map_capability_to_model_round_robin(self, mapping_manager):
        """测试轮询策略"""
        # 添加多个映射
        mapping_id1 = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        mapping_id2 = mapping_manager.add_mapping("test_model_2", "test_capability_1")
        
        # 测试轮询策略
        result1 = mapping_manager.map_capability_to_model(
            "test_capability_1", 
            strategy=MappingStrategy.ROUND_ROBIN
        )
        
        # 检查结果
        assert result1 is not None
        
        # 再次测试应该选择另一个映射
        result2 = mapping_manager.map_capability_to_model(
            "test_capability_1", 
            strategy=MappingStrategy.ROUND_ROBIN
        )
        
        assert result2 is not None
        # 由于轮询策略基于最后使用时间，这里不保证一定选择不同的模型
    
    def test_map_capability_to_model_no_mappings(self, mapping_manager):
        """测试没有映射的情况"""
        result = mapping_manager.map_capability_to_model("nonexistent_capability")
        assert result is None
    
    def test_map_capability_to_model_no_available_mappings(self, mapping_manager):
        """测试没有可用映射的情况"""
        # 添加映射但设置为不可用
        mapping_id = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        
        # 多次更新统计信息使成功率低于20%，变为不可用状态
        for _ in range(5):
            mapping_manager.update_mapping_stats(mapping_id, False, 100.0)
        
        # 检查状态变为不可用
        mapping = mapping_manager.get_mapping_by_id(mapping_id)
        assert mapping.status == CapabilityStatus.UNAVAILABLE
        
        # 测试映射
        result = mapping_manager.map_capability_to_model("test_capability_1")
        assert result is None
    
    def test_get_mapping_statistics(self, mapping_manager):
        """测试获取映射统计信息"""
        # 添加多个映射
        mapping_id1 = mapping_manager.add_mapping("test_model_1", "test_capability_1")
        mapping_id2 = mapping_manager.add_mapping("test_model_2", "test_capability_1")
        
        # 更新统计信息
        mapping_manager.update_mapping_stats(mapping_id1, True, 100.0)
        
        # 更新第二个映射使其变为降级状态（成功率在0.2-0.5之间）
        mapping_manager.update_mapping_stats(mapping_id2, True, 200.0)  # 第一次成功
        mapping_manager.update_mapping_stats(mapping_id2, False, 200.0)  # 第二次失败
        mapping_manager.update_mapping_stats(mapping_id2, False, 200.0)  # 第三次失败
        
        # 获取统计信息
        stats = mapping_manager.get_mapping_statistics()
        
        # 检查统计信息
        assert stats["total_mappings"] == 2
        assert stats["available_mappings"] == 1
        assert stats["degraded_mappings"] == 1
        assert stats["unavailable_mappings"] == 0
        assert stats["availability_rate"] == 0.5
        assert "text_generation" in stats["type_statistics"]
        assert stats["type_statistics"]["text_generation"] == 2
    
    def test_export_import_mappings(self, mapping_manager):
        """测试导出和导入映射"""
        # 添加映射
        mapping_id = mapping_manager.add_mapping("test_model_1", "test_capability_1", priority=5)
        mapping_manager.update_mapping_stats(mapping_id, True, 100.0, 0.01)
        
        # 导出映射
        exported_data = mapping_manager.export_mappings()
        
        # 检查导出数据
        assert len(exported_data) == 1
        mapping_data = exported_data[0]
        assert mapping_data["mapping_id"] == mapping_id
        assert mapping_data["model_id"] == "test_model_1"
        assert mapping_data["capability_id"] == "test_capability_1"
        assert mapping_data["priority"] == 5
        assert mapping_data["success_rate"] == 1.0
        assert mapping_data["avg_response_time"] == 100.0
        assert mapping_data["cost_per_request"] == 0.01
        
        # 创建新的映射管理器并导入数据
        new_mapping_manager = CapabilityMappingManager(
            Mock(),  # 模拟模型管理器
            Mock()   # 模拟能力注册表
        )
        new_mapping_manager.import_mappings(exported_data)
        
        # 检查导入结果
        imported_mapping = new_mapping_manager.get_mapping_by_id(mapping_id)
        assert imported_mapping is not None
        assert imported_mapping.model_id == "test_model_1"
        assert imported_mapping.capability_id == "test_capability_1"
        assert imported_mapping.priority == 5
        assert imported_mapping.success_rate == 1.0
        assert imported_mapping.avg_response_time == 100.0
        assert imported_mapping.cost_per_request == 0.01


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
