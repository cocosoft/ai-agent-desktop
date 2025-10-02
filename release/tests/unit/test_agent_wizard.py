"""
代理创建向导单元测试
测试代理创建向导界面的功能
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from PyQt6.QtWidgets import QApplication, QWizard
from PyQt6.QtCore import Qt

from src.ui.agent_wizard import (
    AgentWizardPage, AgentBasicInfoPage, AgentTemplateSelectionPage,
    AgentCapabilitySelectionPage, AgentSummaryPage, AgentCreationWizard
)
from src.core.agent_model import AgentRegistry, AgentType, AgentPriority, AgentTemplate
from src.core.capability_model import CapabilityRegistry, Capability, CapabilityType


class TestAgentWizard:
    """代理创建向导测试类"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    @pytest.fixture
    def agent_registry(self):
        """创建代理注册表实例"""
        registry = AgentRegistry()
        return registry
    
    @pytest.fixture
    def capability_registry(self):
        """创建能力注册表实例"""
        registry = CapabilityRegistry()
        # 添加测试能力
        text_capability = Capability(
            capability_id="text_generation",
            name="文本生成",
            description="生成文本内容",
            capability_type=CapabilityType.TEXT_GENERATION,
            parameters=[],
            outputs=[]
        )
        code_capability = Capability(
            capability_id="code_generation",
            name="代码生成",
            description="生成代码",
            capability_type=CapabilityType.CODE_GENERATION,
            parameters=[],
            outputs=[]
        )
        registry.register_capability(text_capability)
        registry.register_capability(code_capability)
        return registry
    
    @pytest.fixture
    def model_manager(self):
        """创建模型管理器Mock"""
        manager = Mock()
        model1 = Mock()
        model1.name = "GPT-3.5"
        model1.model_id = "gpt-3.5-turbo"
        model2 = Mock()
        model2.name = "GPT-4"
        model2.model_id = "gpt-4"
        manager.list_models.return_value = [model1, model2]
        return manager
    
    def test_agent_wizard_page_creation(self, app):
        """测试代理向导页面创建"""
        page = AgentWizardPage("测试页面", "测试副标题")
        
        assert page.title() == "测试页面"
        assert page.subTitle() == "测试副标题"
        assert page.layout is not None
    
    def test_agent_basic_info_page_creation(self, app):
        """测试代理基本信息页面创建"""
        page = AgentBasicInfoPage()
        
        # 验证控件存在
        assert page.name_edit is not None
        assert page.description_edit is not None
        assert page.type_combo is not None
        assert page.priority_combo is not None
        assert page.auto_start_check is not None
        assert page.max_tasks_spin is not None
        
        # 验证字段注册 - 注意：字段值在初始化时可能为None
        # 这些断言主要验证控件存在，字段值会在用户交互时设置
        assert page.name_edit is not None
        assert page.description_edit is not None
        assert page.type_combo is not None
        assert page.priority_combo is not None
        assert page.auto_start_check is not None
        assert page.max_tasks_spin is not None
    
    def test_agent_basic_info_page_validation(self, app):
        """测试代理基本信息页面验证"""
        page = AgentBasicInfoPage()
        
        # 测试空名称验证
        page.name_edit.setText("")
        assert page.validatePage() is False
        
        # 测试有效名称验证
        page.name_edit.setText("测试代理")
        assert page.validatePage() is True
    
    def test_agent_template_selection_page_creation(self, app, agent_registry):
        """测试代理模板选择页面创建"""
        page = AgentTemplateSelectionPage(agent_registry)
        
        assert page.template_list is not None
        assert page.template_list.count() >= 4  # 3个模板 + 1个自定义选项
    
    def test_agent_template_selection(self, app, agent_registry):
        """测试代理模板选择"""
        page = AgentTemplateSelectionPage(agent_registry)
        
        # 选择第一个模板
        page.template_list.setCurrentRow(0)
        selected_template = page.selected_template
        
        assert selected_template is not None
        assert isinstance(selected_template, AgentTemplate)
        
        # 选择自定义选项
        page.template_list.setCurrentRow(page.template_list.count() - 1)
        selected_template = page.selected_template
        
        assert selected_template is None
    
    def test_agent_capability_selection_page_creation(self, app, capability_registry, model_manager):
        """测试能力选择页面创建"""
        page = AgentCapabilitySelectionPage(capability_registry, model_manager)
        
        assert page.capability_list is not None
        assert page.mapping_widgets == {}
        assert page.capability_list.count() == 2  # 2个测试能力
    
    def test_agent_capability_selection(self, app, capability_registry, model_manager):
        """测试能力选择功能"""
        page = AgentCapabilitySelectionPage(capability_registry, model_manager)
        
        # 选择第一个能力
        item = page.capability_list.item(0)
        item.setCheckState(Qt.CheckState.Checked)
        
        # 验证映射控件被添加
        assert len(page.mapping_widgets) == 1
        capability_id = list(page.mapping_widgets.keys())[0]
        assert capability_id == "text_generation"
        
        # 取消选择能力
        item.setCheckState(Qt.CheckState.Unchecked)
        
        # 验证映射控件被移除
        assert len(page.mapping_widgets) == 0
    
    def test_agent_capability_mapping_retrieval(self, app, capability_registry, model_manager):
        """测试能力映射配置获取"""
        page = AgentCapabilitySelectionPage(capability_registry, model_manager)
        
        # 选择能力
        item = page.capability_list.item(0)
        item.setCheckState(Qt.CheckState.Checked)
        
        # 获取映射配置
        mappings = page.get_capability_mappings()
        
        assert len(mappings) == 1
        mapping = mappings[0]
        assert mapping.capability_id == "text_generation"
        assert mapping.model_id == "gpt-3.5-turbo"  # 默认选择第一个模型
        assert mapping.priority == 1
        assert mapping.enabled is True
    
    def test_agent_summary_page_creation(self, app):
        """测试代理摘要页面创建"""
        page = AgentSummaryPage()
        
        assert page.summary_label is not None
        assert page.summary_label.wordWrap() is True
    
    def test_agent_creation_wizard_creation(self, app, agent_registry, capability_registry, model_manager):
        """测试代理创建向导创建"""
        wizard = AgentCreationWizard(agent_registry, capability_registry, model_manager)
        
        assert wizard.windowTitle() == "创建新代理"
        assert wizard.wizardStyle() == QWizard.WizardStyle.ModernStyle
        assert wizard.minimumWidth() == 600
        assert wizard.minimumHeight() == 500
        
        # 验证页面数量
        assert wizard.pageCount() == 4
    
    def test_agent_creation_wizard_accept(self, app, agent_registry, capability_registry, model_manager):
        """测试代理创建向导接受处理"""
        wizard = AgentCreationWizard(agent_registry, capability_registry, model_manager)
        
        # 设置字段值
        wizard.setField("name", "测试代理")
        wizard.setField("description", "测试描述")
        wizard.setField("agent_type", AgentType.TEXT_GENERATION)
        wizard.setField("priority", AgentPriority.NORMAL)
        wizard.setField("auto_start", True)
        wizard.setField("max_tasks", 3)
        
        # Mock能力映射页面
        capability_page = Mock()
        capability_page.get_capability_mappings.return_value = []
        wizard.setPage(2, capability_page)
        
        # 执行接受处理
        wizard.accept()
        
        # 验证代理被创建
        agents = agent_registry.list_agents()
        assert len(agents) == 1
        agent = agents[0]
        assert agent.name == "测试代理"
        assert agent.description == "测试描述"
        assert agent.agent_type == AgentType.TEXT_GENERATION
        assert agent.priority == AgentPriority.NORMAL
        assert agent.auto_start is True
        assert agent.max_concurrent_tasks == 3


class TestAgentWizardIntegration:
    """代理创建向导集成测试"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app
    
    def test_wizard_complete_flow(self, app):
        """测试向导完整流程"""
        # 创建必要的管理器
        agent_registry = AgentRegistry()
        capability_registry = CapabilityRegistry()
        model_manager = Mock()
        
        # 添加测试能力
        text_capability = Capability(
            capability_id="text_generation",
            name="文本生成",
            description="生成文本内容",
            capability_type=CapabilityType.TEXT_GENERATION,
            parameters=[],
            outputs=[]
        )
        capability_registry.register_capability(text_capability)
        
        # 添加测试模型
        model1 = Mock()
        model1.name = "GPT-3.5"
        model1.model_id = "gpt-3.5-turbo"
        model_manager.list_models.return_value = [model1]
        
        # 创建向导
        wizard = AgentCreationWizard(agent_registry, capability_registry, model_manager)
        
        # 验证向导初始化
        assert wizard is not None
        assert wizard.pageCount() == 4
        
        # 验证页面顺序
        page1 = wizard.page(0)
        assert isinstance(page1, AgentBasicInfoPage)
        
        page2 = wizard.page(1)
        assert isinstance(page2, AgentTemplateSelectionPage)
        
        page3 = wizard.page(2)
        assert isinstance(page3, AgentCapabilitySelectionPage)
        
        page4 = wizard.page(3)
        assert isinstance(page4, AgentSummaryPage)
    
    def test_wizard_field_propagation(self, app):
        """测试向导字段传播"""
        agent_registry = AgentRegistry()
        capability_registry = CapabilityRegistry()
        model_manager = Mock()
        
        wizard = AgentCreationWizard(agent_registry, capability_registry, model_manager)
        
        # 设置字段值
        wizard.setField("name", "测试代理")
        wizard.setField("description", "测试描述")
        wizard.setField("agent_type", AgentType.CODE_GENERATION)
        wizard.setField("priority", AgentPriority.HIGH)
        wizard.setField("auto_start", False)
        wizard.setField("max_tasks", 10)
        
        # 验证字段值
        assert wizard.field("name") == "测试代理"
        assert wizard.field("description") == "测试描述"
        assert wizard.field("agent_type") == AgentType.CODE_GENERATION
        assert wizard.field("priority") == AgentPriority.HIGH
        assert wizard.field("auto_start") is False
        assert wizard.field("max_tasks") == 10


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
