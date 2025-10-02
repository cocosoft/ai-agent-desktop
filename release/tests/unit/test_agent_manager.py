"""
代理管理界面单元测试
测试代理管理界面的功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.ui.agent_manager import (
    AgentListWidget, AgentStatusWidget, AgentDetailDialog, AgentManager
)
from src.core.agent_model import AgentRegistry, AgentInstance, AgentStatus, AgentType, AgentPriority, AgentConfig, AgentCapabilityMapping
from src.core.capability_model import CapabilityRegistry, Capability, CapabilityType


class TestAgentListWidget:
    """代理列表控件测试"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def agent_instance(self):
        """创建测试代理实例"""
        config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="测试代理描述",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[],
            priority=AgentPriority.NORMAL,
            max_concurrent_tasks=5,
            auto_start=True
        )
        return AgentInstance(config, agent_config=config)
    
    def test_agent_list_widget_creation(self, app):
        """测试代理列表控件创建"""
        widget = AgentListWidget()
        
        assert widget is not None
        assert widget.minimumWidth() == 300
    
    def test_add_agent(self, app, agent_instance):
        """测试添加代理"""
        widget = AgentListWidget()
        widget.add_agent(agent_instance)
        
        assert widget.count() == 1
        
        item = widget.item(0)
        assert item.data(Qt.ItemDataRole.UserRole) == agent_instance
        assert agent_instance.agent_config.name in item.text()
        assert agent_instance.status.value in item.text()
    
    def test_agent_selection_signal(self, app, agent_instance):
        """测试代理选择信号"""
        widget = AgentListWidget()
        widget.add_agent(agent_instance)
        
        # 模拟选择代理
        selected_agent = None
        def on_agent_selected(agent):
            nonlocal selected_agent
            selected_agent = agent
        
        widget.agent_selected.connect(on_agent_selected)
        widget.setCurrentRow(0)
        
        assert selected_agent == agent_instance


class TestAgentStatusWidget:
    """代理状态监控控件测试"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def agent_instance(self):
        """创建测试代理实例"""
        config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="测试代理描述",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[],
            priority=AgentPriority.NORMAL,
            max_concurrent_tasks=5,
            auto_start=True
        )
        instance = AgentInstance(config, agent_config=config)
        instance.status = AgentStatus.RUNNING
        instance.total_tasks = 100
        instance.successful_tasks = 90
        instance.failed_tasks = 10
        instance.cpu_usage = 25
        instance.memory_usage = 50
        instance.disk_usage = 10
        return instance
    
    def test_agent_status_widget_creation(self, app):
        """测试代理状态监控控件创建"""
        widget = AgentStatusWidget()
        
        assert widget is not None
        assert widget.name_label is not None
        assert widget.status_label is not None
        assert widget.cpu_usage_bar is not None
    
    def test_update_agent_info(self, app, agent_instance):
        """测试更新代理信息"""
        widget = AgentStatusWidget()
        widget.update_agent_info(agent_instance)
        
        # 验证基本信息
        assert widget.name_label.text() == agent_instance.agent_config.name
        assert widget.type_label.text() == agent_instance.agent_config.agent_type.value.replace('_', ' ').title()
        assert widget.status_label.text() == agent_instance.status.value
        assert widget.priority_label.text() == agent_instance.agent_config.priority.value.title()
        
        # 验证性能指标（简化版本）
        assert widget.task_count_label.text() == "0"
        assert widget.success_rate_label.text() == "N/A"
        
        # 验证资源使用（简化版本）
        assert widget.cpu_usage_bar.value() == 0
        assert widget.memory_usage_bar.value() == 0
        assert widget.disk_usage_bar.value() == 0


class TestAgentDetailDialog:
    """代理详情对话框测试"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def agent_instance(self):
        """创建测试代理实例"""
        config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="测试代理描述",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[
                AgentCapabilityMapping(
                    capability_id="text_generation",
                    model_id="gpt-3.5-turbo",
                    priority=1,
                    enabled=True
                )
            ],
            priority=AgentPriority.NORMAL,
            max_concurrent_tasks=5,
            auto_start=True
        )
        instance = AgentInstance(config, agent_config=config)
        instance.status = AgentStatus.RUNNING
        instance.total_tasks = 100
        instance.successful_tasks = 90
        instance.failed_tasks = 10
        instance.cpu_usage = 25
        instance.memory_usage = 50
        instance.disk_usage = 10
        return instance
    
    def test_agent_detail_dialog_creation(self, app, agent_instance):
        """测试代理详情对话框创建"""
        dialog = AgentDetailDialog(agent_instance)
        
        assert dialog is not None
        assert dialog.windowTitle() == f"代理详情 - {agent_instance.agent_config.name}"
        assert dialog.minimumWidth() == 600
        assert dialog.minimumHeight() == 500
    
    def test_create_basic_tab(self, app, agent_instance):
        """测试基本信息标签页创建"""
        dialog = AgentDetailDialog(agent_instance)
        basic_tab = dialog.create_basic_tab()
        
        assert basic_tab is not None
    
    def test_create_capability_tab(self, app, agent_instance):
        """测试能力配置标签页创建"""
        dialog = AgentDetailDialog(agent_instance)
        capability_tab = dialog.create_capability_tab()
        
        assert capability_tab is not None
    
    def test_create_stats_tab(self, app, agent_instance):
        """测试性能统计标签页创建"""
        dialog = AgentDetailDialog(agent_instance)
        stats_tab = dialog.create_stats_tab()
        
        assert stats_tab is not None
    
    def test_create_log_tab(self, app, agent_instance):
        """测试日志标签页创建"""
        dialog = AgentDetailDialog(agent_instance)
        log_tab = dialog.create_log_tab()
        
        assert log_tab is not None


class TestAgentManager:
    """代理管理主界面测试"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表"""
        registry = AgentRegistry()
        return registry
    
    @pytest.fixture
    def capability_registry(self):
        """创建能力注册表"""
        registry = CapabilityRegistry()
        return registry
    
    @pytest.fixture
    def model_manager(self):
        """创建模型管理器Mock"""
        manager = Mock()
        return manager
    
    def test_agent_manager_creation(self, app, agent_registry, capability_registry, model_manager):
        """测试代理管理界面创建"""
        manager = AgentManager(agent_registry, capability_registry, model_manager)
        
        assert manager is not None
        assert manager.agent_list is not None
        assert manager.status_widget is not None
        assert manager.refresh_timer is not None
    
    def test_refresh_agent_list(self, app, agent_registry, capability_registry, model_manager):
        """测试刷新代理列表"""
        manager = AgentManager(agent_registry, capability_registry, model_manager)
        
        # 添加测试代理
        config = AgentConfig(
            agent_id="test_agent_1",
            name="测试代理",
            description="测试代理描述",
            agent_type=AgentType.TEXT_GENERATION,
            capabilities=[],
            priority=AgentPriority.NORMAL,
            max_concurrent_tasks=5,
            auto_start=True
        )
        agent_registry.register_agent(config)
        
        # 刷新列表
        manager.refresh_agent_list()
        
        # 验证代理被添加到列表
        assert manager.agent_list.count() == 1
    
    def test_create_agent(self, app, agent_registry, capability_registry, model_manager):
        """测试创建代理功能"""
        manager = AgentManager(agent_registry, capability_registry, model_manager)
        
        # 验证创建代理按钮存在
        toolbar = manager.create_toolbar()
        actions = toolbar.actions()
        action_names = [action.text() for action in actions]
        assert "创建代理" in action_names
    
    def test_get_selected_agent(self, app, agent_registry, capability_registry, model_manager):
        """测试获取选中代理"""
        manager = AgentManager(agent_registry, capability_registry, model_manager)
        
        # 初始状态下没有选中代理
        assert manager.get_selected_agent() is None


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
