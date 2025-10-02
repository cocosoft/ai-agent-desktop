"""
能力管理界面单元测试
测试能力管理界面的功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.ui.capability_manager import CapabilityManagerWidget
from src.core.capability_model import (
    Capability, CapabilityType, CapabilityStatus, CapabilityRegistry,
    CapabilityParameter, CapabilityOutput, CapabilityTest
)
from src.core.capability_discovery import DiscoveryStatus, DiscoveryTask


class TestCapabilityManager:
    """能力管理界面测试类"""
    
    @pytest.fixture
    def mock_model_manager(self):
        """创建模拟的模型管理器"""
        mock_manager = Mock()
        mock_manager.get_available_models = Mock(return_value=[
            Mock(model_id="test_model_1", name="测试模型1"),
            Mock(model_id="test_model_2", name="测试模型2")
        ])
        return mock_manager
    
    @pytest.fixture
    def capability_registry(self):
        """创建能力注册表"""
        registry = CapabilityRegistry()
        
        # 添加一些测试能力
        test_capability = Capability(
            capability_id="test_capability_1",
            name="测试能力1",
            description="这是一个测试能力",
            capability_type=CapabilityType.TEXT_GENERATION,
            status=CapabilityStatus.AVAILABLE,
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
    def capability_manager(self, mock_model_manager, capability_registry):
        """创建能力管理界面"""
        return CapabilityManagerWidget(mock_model_manager, capability_registry)
    
    def test_initialization(self, capability_manager):
        """测试初始化"""
        assert capability_manager is not None
        assert capability_manager.model_manager is not None
        assert capability_manager.capability_registry is not None
        assert capability_manager.capability_discovery is not None
    
    def test_refresh_capability_list(self, capability_manager, capability_registry):
        """测试刷新能力列表"""
        # 初始刷新
        capability_manager.refresh_capability_list()
        
        # 检查表格行数
        assert capability_manager.capability_table.rowCount() == 1
        
        # 检查表格内容
        assert capability_manager.capability_table.item(0, 0).text() == "test_capability_1"
        assert capability_manager.capability_table.item(0, 1).text() == "测试能力1"
        assert capability_manager.capability_table.item(0, 2).text() == "text_generation"
        assert capability_manager.capability_table.item(0, 3).text() == "available"
        assert capability_manager.capability_table.item(0, 4).text() == "2"
    
    def test_filter_capabilities(self, capability_manager, capability_registry):
        """测试能力筛选"""
        # 添加更多测试能力
        capability2 = Capability(
            capability_id="test_capability_2",
            name="代码生成能力",
            description="生成代码",
            capability_type=CapabilityType.CODE_GENERATION,
            status=CapabilityStatus.EXPERIMENTAL,
            tags=["code", "generation"],
            complexity=3
        )
        capability_registry.register_capability(capability2)
        
        # 测试搜索筛选
        capability_manager.search_input.setText("代码")
        filtered = capability_manager.filter_capabilities(capability_registry.get_all_capabilities())
        assert len(filtered) == 1
        assert filtered[0].capability_id == "test_capability_2"
        
        # 测试类型筛选
        capability_manager.search_input.clear()
        capability_manager.type_filter.setCurrentIndex(2)  # CODE_GENERATION
        filtered = capability_manager.filter_capabilities(capability_registry.get_all_capabilities())
        assert len(filtered) == 1
        assert filtered[0].capability_type == CapabilityType.CODE_GENERATION
        
        # 测试状态筛选
        capability_manager.type_filter.setCurrentIndex(0)  # 所有类型
        capability_manager.status_filter.setCurrentIndex(2)  # EXPERIMENTAL
        filtered = capability_manager.filter_capabilities(capability_registry.get_all_capabilities())
        assert len(filtered) == 1
        assert filtered[0].status == CapabilityStatus.EXPERIMENTAL
    
    def test_capability_selection(self, capability_manager):
        """测试能力选择"""
        # 选择第一个能力
        capability_manager.capability_table.selectRow(0)
        
        # 检查当前选择的能力ID
        assert capability_manager.current_capability_id == "test_capability_1"
        
        # 检查操作按钮状态
        assert capability_manager.test_btn.isEnabled() is True
        assert capability_manager.edit_btn.isEnabled() is True
        assert capability_manager.delete_btn.isEnabled() is True
    
    def test_show_capability_details(self, capability_manager):
        """测试显示能力详情"""
        # 选择能力
        capability_manager.capability_table.selectRow(0)
        
        # 检查基本信息显示
        assert capability_manager.capability_id_label.text() == "test_capability_1"
        assert capability_manager.capability_name_label.text() == "测试能力1"
        assert capability_manager.capability_type_label.text() == "text_generation"
        assert capability_manager.capability_status_label.text() == "available"
        assert capability_manager.capability_description.toPlainText() == "这是一个测试能力"
        assert capability_manager.capability_category_label.text() == "text_processing"
        assert capability_manager.capability_tags_label.text() == "test, text"
        assert capability_manager.capability_complexity_label.text() == "2"
        
        # 检查参数表格
        assert capability_manager.parameters_table.rowCount() == 1
        assert capability_manager.parameters_table.item(0, 0).text() == "prompt"
        assert capability_manager.parameters_table.item(0, 1).text() == "string"
        assert capability_manager.parameters_table.item(0, 2).text() == "是"
        
        # 检查输出表格
        assert capability_manager.outputs_table.rowCount() == 1
        assert capability_manager.outputs_table.item(0, 0).text() == "generated_text"
        assert capability_manager.outputs_table.item(0, 1).text() == "string"
        assert capability_manager.outputs_table.item(0, 2).text() == "plain"
    
    def test_clear_capability_details(self, capability_manager):
        """测试清空能力详情"""
        # 先选择一个能力
        capability_manager.capability_table.selectRow(0)
        assert capability_manager.current_capability_id is not None
        
        # 清空详情
        capability_manager.clear_capability_details()
        
        # 检查详情已清空
        assert capability_manager.current_capability_id is None
        assert capability_manager.capability_id_label.text() == ""
        assert capability_manager.capability_name_label.text() == ""
        assert capability_manager.parameters_table.rowCount() == 0
        assert capability_manager.outputs_table.rowCount() == 0
        
        # 检查操作按钮已禁用
        assert capability_manager.test_btn.isEnabled() is False
        assert capability_manager.edit_btn.isEnabled() is False
        assert capability_manager.delete_btn.isEnabled() is False
    
    def test_delete_capability(self, capability_manager, capability_registry):
        """测试删除能力"""
        # 选择能力
        capability_manager.capability_table.selectRow(0)
        
        # 检查能力存在
        assert capability_registry.get_capability("test_capability_1") is not None
        
        # 使用patch模拟QMessageBox.question返回Yes
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=Mock(return_value=Mock(StandardButton.Yes))):
            capability_manager.delete_capability()
        
        # 检查能力已被删除
        assert capability_registry.get_capability("test_capability_1") is None
        assert capability_manager.capability_table.rowCount() == 0
    
    def test_start_capability_discovery(self, capability_manager):
        """测试开始能力发现"""
        # 使用patch模拟异步调用
        with patch.object(capability_manager.capability_discovery, 'discover_model_capabilities', 
                         new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = "test_task_id"
            
            # 启动发现
            capability_manager.start_capability_discovery()
            
            # 检查发现任务已启动
            mock_discover.assert_called_once()
    
    def test_update_discovery_status(self, capability_manager):
        """测试更新发现任务状态"""
        # 创建模拟的发现任务
        task = DiscoveryTask(
            task_id="test_task",
            model_id="test_model",
            status=DiscoveryStatus.RUNNING,
            progress=50.0
        )
        
        # 使用patch模拟获取任务列表
        with patch.object(capability_manager.capability_discovery, 'get_all_tasks', 
                         return_value=[task]):
            capability_manager.update_discovery_status()
            
            # 检查进度条状态
            assert capability_manager.discovery_progress.value() == 50
            assert capability_manager.discovery_progress.isVisible() is True
            assert "test_task" in capability_manager.discovery_status_label.text()
    
    def test_on_discovery_started(self, capability_manager):
        """测试发现任务开始"""
        capability_manager.on_discovery_started("test_task_id")
        
        # 检查界面状态
        assert capability_manager.discovery_progress.isVisible() is True
        assert capability_manager.discovery_progress.value() == 0
        assert capability_manager.discover_btn.isEnabled() is False
        assert "test_task_id" in capability_manager.discovery_status_label.text()
    
    def test_on_discovery_completed(self, capability_manager):
        """测试发现任务完成"""
        capability_manager.on_discovery_completed("test_task_id")
        
        # 检查界面状态
        assert capability_manager.discovery_progress.value() == 100
        assert capability_manager.discover_btn.isEnabled() is True
        assert "test_task_id" in capability_manager.discovery_status_label.text()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
