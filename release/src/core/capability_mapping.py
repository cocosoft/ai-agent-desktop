"""
能力与模型关联管理
实现能力到模型的映射、优先级设置和选择算法
"""

import asyncio
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

from .capability_model import Capability, CapabilityType, CapabilityRegistry
from .model_manager import ModelManager
from ..utils.logger import log_info, log_error, log_debug


class MappingStrategy(Enum):
    """映射策略枚举"""
    BEST_MATCH = "best_match"  # 最佳匹配
    FASTEST = "fastest"        # 最快响应
    LOWEST_COST = "lowest_cost"  # 最低成本
    ROUND_ROBIN = "round_robin"  # 轮询
    LOAD_BALANCED = "load_balanced"  # 负载均衡


class CapabilityStatus(Enum):
    """能力状态枚举"""
    AVAILABLE = "available"      # 可用
    DEGRADED = "degraded"        # 降级
    UNAVAILABLE = "unavailable"  # 不可用
    TESTING = "testing"          # 测试中


@dataclass
class ModelCapabilityMapping:
    """模型能力映射"""
    mapping_id: str
    model_id: str
    capability_id: str
    capability_type: CapabilityType
    priority: int = 1  # 优先级，1-10，数字越大优先级越高
    success_rate: float = 0.0  # 成功率
    avg_response_time: float = 0.0  # 平均响应时间（毫秒）
    cost_per_request: float = 0.0  # 每次请求成本
    usage_count: int = 0  # 使用次数
    last_used: Optional[float] = None  # 最后使用时间
    status: CapabilityStatus = CapabilityStatus.AVAILABLE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityMappingResult:
    """能力映射结果"""
    capability_id: str
    model_id: str
    mapping_id: str
    confidence: float  # 置信度，0-1
    strategy: MappingStrategy
    estimated_response_time: float
    estimated_cost: float
    alternatives: List[str] = field(default_factory=list)  # 备选映射ID


class CapabilityMappingManager:
    """能力映射管理器"""
    
    def __init__(self, model_manager: ModelManager, capability_registry: CapabilityRegistry):
        self.model_manager = model_manager
        self.capability_registry = capability_registry
        self.mappings: Dict[str, ModelCapabilityMapping] = {}
        self.strategy_weights: Dict[MappingStrategy, float] = {
            MappingStrategy.BEST_MATCH: 0.4,
            MappingStrategy.FASTEST: 0.3,
            MappingStrategy.LOWEST_COST: 0.2,
            MappingStrategy.ROUND_ROBIN: 0.1
        }
        
        # 初始化默认映射
        self._initialize_default_mappings()
    
    def _initialize_default_mappings(self):
        """初始化默认映射"""
        # 这里可以添加一些默认的模型能力映射
        # 在实际应用中，这些映射可以通过能力发现机制自动创建
        pass
    
    def add_mapping(self, model_id: str, capability_id: str, 
                   priority: int = 1, metadata: Optional[Dict[str, Any]] = None) -> str:
        """添加能力映射"""
        capability = self.capability_registry.get_capability(capability_id)
        if not capability:
            raise ValueError(f"能力不存在: {capability_id}")
        
        mapping_id = str(uuid.uuid4())
        mapping = ModelCapabilityMapping(
            mapping_id=mapping_id,
            model_id=model_id,
            capability_id=capability_id,
            capability_type=capability.capability_type,
            priority=priority,
            metadata=metadata or {}
        )
        
        self.mappings[mapping_id] = mapping
        log_info(f"添加能力映射: {capability_id} -> {model_id} (映射ID: {mapping_id})")
        
        return mapping_id
    
    def remove_mapping(self, mapping_id: str) -> bool:
        """移除能力映射"""
        if mapping_id in self.mappings:
            mapping = self.mappings.pop(mapping_id)
            log_info(f"移除能力映射: {mapping.capability_id} -> {mapping.model_id}")
            return True
        return False
    
    def get_mappings_for_capability(self, capability_id: str) -> List[ModelCapabilityMapping]:
        """获取指定能力的映射"""
        return [m for m in self.mappings.values() if m.capability_id == capability_id]
    
    def get_mappings_for_model(self, model_id: str) -> List[ModelCapabilityMapping]:
        """获取指定模型的映射"""
        return [m for m in self.mappings.values() if m.model_id == model_id]
    
    def get_mapping_by_id(self, mapping_id: str) -> Optional[ModelCapabilityMapping]:
        """根据ID获取映射"""
        return self.mappings.get(mapping_id)
    
    def update_mapping_stats(self, mapping_id: str, success: bool, 
                           response_time: float, cost: float = 0.0):
        """更新映射统计信息"""
        mapping = self.mappings.get(mapping_id)
        if not mapping:
            return
        
        # 更新使用次数
        mapping.usage_count += 1
        mapping.last_used = time.time()
        
        # 更新成功率
        if mapping.usage_count == 1:
            mapping.success_rate = 1.0 if success else 0.0
        else:
            current_success_rate = mapping.success_rate
            mapping.success_rate = (current_success_rate * (mapping.usage_count - 1) + 
                                  (1.0 if success else 0.0)) / mapping.usage_count
        
        # 更新平均响应时间
        if mapping.usage_count == 1:
            mapping.avg_response_time = response_time
        else:
            current_avg_time = mapping.avg_response_time
            mapping.avg_response_time = (current_avg_time * (mapping.usage_count - 1) + 
                                       response_time) / mapping.usage_count
        
        # 更新成本
        if cost > 0:
            mapping.cost_per_request = cost
        
        # 更新状态
        if mapping.success_rate < 0.2:
            mapping.status = CapabilityStatus.UNAVAILABLE
        elif mapping.success_rate < 0.5:
            mapping.status = CapabilityStatus.DEGRADED
        else:
            mapping.status = CapabilityStatus.AVAILABLE
    
    def map_capability_to_model(self, capability_id: str, 
                              strategy: MappingStrategy = MappingStrategy.BEST_MATCH,
                              constraints: Optional[Dict[str, Any]] = None) -> Optional[CapabilityMappingResult]:
        """将能力映射到模型"""
        capability = self.capability_registry.get_capability(capability_id)
        if not capability:
            log_error(f"能力不存在: {capability_id}")
            return None
        
        # 获取该能力的所有映射
        mappings = self.get_mappings_for_capability(capability_id)
        if not mappings:
            log_error(f"没有找到能力 {capability_id} 的映射")
            return None
        
        # 过滤可用的映射
        available_mappings = [m for m in mappings if m.status == CapabilityStatus.AVAILABLE]
        if not available_mappings:
            log_error(f"能力 {capability_id} 没有可用的映射")
            return None
        
        # 根据策略选择最佳映射
        if strategy == MappingStrategy.BEST_MATCH:
            selected_mapping = self._select_best_match(available_mappings)
        elif strategy == MappingStrategy.FASTEST:
            selected_mapping = self._select_fastest(available_mappings)
        elif strategy == MappingStrategy.LOWEST_COST:
            selected_mapping = self._select_lowest_cost(available_mappings)
        elif strategy == MappingStrategy.ROUND_ROBIN:
            selected_mapping = self._select_round_robin(available_mappings)
        elif strategy == MappingStrategy.LOAD_BALANCED:
            selected_mapping = self._select_load_balanced(available_mappings)
        else:
            selected_mapping = self._select_best_match(available_mappings)
        
        if not selected_mapping:
            return None
        
        # 计算置信度
        confidence = self._calculate_confidence(selected_mapping)
        
        # 获取备选映射
        alternatives = [m.mapping_id for m in available_mappings if m.mapping_id != selected_mapping.mapping_id]
        
        return CapabilityMappingResult(
            capability_id=capability_id,
            model_id=selected_mapping.model_id,
            mapping_id=selected_mapping.mapping_id,
            confidence=confidence,
            strategy=strategy,
            estimated_response_time=selected_mapping.avg_response_time,
            estimated_cost=selected_mapping.cost_per_request,
            alternatives=alternatives[:3]  # 最多3个备选
        )
    
    def _select_best_match(self, mappings: List[ModelCapabilityMapping]) -> Optional[ModelCapabilityMapping]:
        """选择最佳匹配"""
        if not mappings:
            return None
        
        # 综合评分 = 成功率 * 0.4 + 优先级 * 0.3 + (1 - 响应时间比例) * 0.2 + (1 - 成本比例) * 0.1
        scored_mappings = []
        
        # 计算最大值用于归一化
        max_priority = max(m.priority for m in mappings)
        max_response_time = max(m.avg_response_time for m in mappings) if any(m.avg_response_time > 0 for m in mappings) else 1.0
        max_cost = max(m.cost_per_request for m in mappings) if any(m.cost_per_request > 0 for m in mappings) else 1.0
        
        for mapping in mappings:
            # 归一化各项指标
            priority_score = mapping.priority / max_priority
            response_time_score = 1 - (mapping.avg_response_time / max_response_time) if max_response_time > 0 else 0.5
            cost_score = 1 - (mapping.cost_per_request / max_cost) if max_cost > 0 else 0.5
            
            # 综合评分
            score = (mapping.success_rate * 0.4 + 
                    priority_score * 0.3 + 
                    response_time_score * 0.2 + 
                    cost_score * 0.1)
            
            scored_mappings.append((mapping, score))
        
        # 选择评分最高的映射
        scored_mappings.sort(key=lambda x: x[1], reverse=True)
        return scored_mappings[0][0] if scored_mappings else None
    
    def _select_fastest(self, mappings: List[ModelCapabilityMapping]) -> Optional[ModelCapabilityMapping]:
        """选择最快响应"""
        if not mappings:
            return None
        
        # 过滤有响应时间数据的映射
        valid_mappings = [m for m in mappings if m.avg_response_time > 0]
        if not valid_mappings:
            return self._select_best_match(mappings)
        
        # 选择响应时间最短的映射
        return min(valid_mappings, key=lambda m: m.avg_response_time)
    
    def _select_lowest_cost(self, mappings: List[ModelCapabilityMapping]) -> Optional[ModelCapabilityMapping]:
        """选择最低成本"""
        if not mappings:
            return None
        
        # 过滤有成本数据的映射
        valid_mappings = [m for m in mappings if m.cost_per_request > 0]
        if not valid_mappings:
            return self._select_best_match(mappings)
        
        # 选择成本最低的映射
        return min(valid_mappings, key=lambda m: m.cost_per_request)
    
    def _select_round_robin(self, mappings: List[ModelCapabilityMapping]) -> Optional[ModelCapabilityMapping]:
        """轮询选择"""
        if not mappings:
            return None
        
        # 按最后使用时间排序，选择最久未使用的
        mappings_with_time = [(m, m.last_used or 0) for m in mappings]
        mappings_with_time.sort(key=lambda x: x[1])
        return mappings_with_time[0][0]
    
    def _select_load_balanced(self, mappings: List[ModelCapabilityMapping]) -> Optional[ModelCapabilityMapping]:
        """负载均衡选择"""
        if not mappings:
            return None
        
        # 基于使用次数和响应时间的负载均衡
        scored_mappings = []
        for mapping in mappings:
            # 使用次数越少，响应时间越短，得分越高
            usage_penalty = mapping.usage_count * 0.1
            response_penalty = mapping.avg_response_time * 0.001 if mapping.avg_response_time > 0 else 0
            
            score = 1.0 - usage_penalty - response_penalty
            scored_mappings.append((mapping, score))
        
        scored_mappings.sort(key=lambda x: x[1], reverse=True)
        return scored_mappings[0][0] if scored_mappings else None
    
    def _calculate_confidence(self, mapping: ModelCapabilityMapping) -> float:
        """计算置信度"""
        # 置信度基于成功率、使用次数和响应时间稳定性
        base_confidence = mapping.success_rate
        
        # 使用次数越多，置信度越高（但边际效应递减）
        usage_boost = min(mapping.usage_count * 0.01, 0.2)  # 最多提升20%
        
        # 响应时间越稳定，置信度越高
        time_stability = 1.0  # 这里可以添加响应时间稳定性的计算
        
        confidence = base_confidence + usage_boost
        return min(confidence, 1.0)
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """获取映射统计信息"""
        total_mappings = len(self.mappings)
        available_mappings = len([m for m in self.mappings.values() if m.status == CapabilityStatus.AVAILABLE])
        degraded_mappings = len([m for m in self.mappings.values() if m.status == CapabilityStatus.DEGRADED])
        unavailable_mappings = len([m for m in self.mappings.values() if m.status == CapabilityStatus.UNAVAILABLE])
        
        # 按能力类型统计
        type_stats = {}
        for mapping in self.mappings.values():
            capability_type = mapping.capability_type.value
            if capability_type not in type_stats:
                type_stats[capability_type] = 0
            type_stats[capability_type] += 1
        
        return {
            "total_mappings": total_mappings,
            "available_mappings": available_mappings,
            "degraded_mappings": degraded_mappings,
            "unavailable_mappings": unavailable_mappings,
            "availability_rate": available_mappings / total_mappings if total_mappings > 0 else 0,
            "type_statistics": type_stats
        }
    
    def export_mappings(self) -> List[Dict[str, Any]]:
        """导出所有映射"""
        return [
            {
                "mapping_id": m.mapping_id,
                "model_id": m.model_id,
                "capability_id": m.capability_id,
                "capability_type": m.capability_type.value,
                "priority": m.priority,
                "success_rate": m.success_rate,
                "avg_response_time": m.avg_response_time,
                "cost_per_request": m.cost_per_request,
                "usage_count": m.usage_count,
                "last_used": m.last_used,
                "status": m.status.value,
                "metadata": m.metadata
            }
            for m in self.mappings.values()
        ]
    
    def import_mappings(self, mappings_data: List[Dict[str, Any]]):
        """导入映射"""
        for mapping_data in mappings_data:
            try:
                mapping = ModelCapabilityMapping(
                    mapping_id=mapping_data["mapping_id"],
                    model_id=mapping_data["model_id"],
                    capability_id=mapping_data["capability_id"],
                    capability_type=CapabilityType(mapping_data["capability_type"]),
                    priority=mapping_data.get("priority", 1),
                    success_rate=mapping_data.get("success_rate", 0.0),
                    avg_response_time=mapping_data.get("avg_response_time", 0.0),
                    cost_per_request=mapping_data.get("cost_per_request", 0.0),
                    usage_count=mapping_data.get("usage_count", 0),
                    last_used=mapping_data.get("last_used"),
                    status=CapabilityStatus(mapping_data.get("status", "available")),
                    metadata=mapping_data.get("metadata", {})
                )
                self.mappings[mapping.mapping_id] = mapping
            except Exception as e:
                log_error(f"导入映射失败: {mapping_data.get('mapping_id', 'unknown')} - {e}")


# 测试函数
async def test_capability_mapping():
    """测试能力映射功能"""
    try:
        from unittest.mock import Mock
        
        # 创建模拟对象
        mock_model_manager = Mock()
        mock_capability_registry = Mock()
        
        # 创建模拟能力
        test_capability = Mock()
        test_capability.capability_id = "test_capability"
        test_capability.capability_type = CapabilityType.TEXT_GENERATION
        mock_capability_registry.get_capability.return_value = test_capability
        
        # 创建能力映射管理器
        mapping_manager = CapabilityMappingManager(mock_model_manager, mock_capability_registry)
        
        # 添加测试映射
        mapping_id = mapping_manager.add_mapping("test_model", "test_capability", priority=5)
        
        # 测试映射获取
        mappings = mapping_manager.get_mappings_for_capability("test_capability")
        assert len(mappings) == 1
        assert mappings[0].mapping_id == mapping_id
        
        # 测试映射到模型
        result = mapping_manager.map_capability_to_model("test_capability")
        assert result is not None
        assert result.capability_id == "test_capability"
        assert result.model_id == "test_model"
        
        # 测试统计信息更新
        mapping_manager.update_mapping_stats(mapping_id, True, 100.0, 0.01)
        updated_mapping = mapping_manager.get_mapping_by_id(mapping_id)
        assert updated_mapping.usage_count == 1
        assert updated_mapping.success_rate == 1.0
        
        print("✓ 能力映射功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 能力映射功能测试失败: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_capability_mapping())
