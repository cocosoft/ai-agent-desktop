"""
代理创建向导界面
提供图形化的代理创建向导，引导用户完成代理配置
"""

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QComboBox, QListWidget, QListWidgetItem,
    QCheckBox, QSpinBox, QGroupBox, QFormLayout, QPushButton,
    QMessageBox, QProgressBar, QWidget, QLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..core.agent_model import AgentRegistry, AgentType, AgentPriority, AgentConfig, AgentCapabilityMapping
from ..core.capability_model import CapabilityRegistry
from ..core.model_manager import ModelManager


class AgentWizardPage(QWizardPage):
    """代理向导页面基类"""
    
    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setTitle(title)
        self.setSubTitle(subtitle)
        
        # 页面布局
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
    
    def add_widget(self, widget):
        """添加控件到页面"""
        if isinstance(widget, QLayout):
            # 如果是布局，需要创建容器
            container = QWidget()
            container.setLayout(widget)
            self.layout.addWidget(container)
        else:
            # 如果是控件，直接添加
            self.layout.addWidget(widget)


class AgentBasicInfoPage(AgentWizardPage):
    """代理基本信息页面"""
    
    def __init__(self, parent=None):
        super().__init__("基本信息", "配置代理的基本信息", parent)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 代理名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入代理名称")
        form_layout.addRow("代理名称:", self.name_edit)
        
        # 代理描述
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("输入代理描述")
        form_layout.addRow("代理描述:", self.description_edit)
        
        # 代理类型
        self.type_combo = QComboBox()
        for agent_type in AgentType:
            self.type_combo.addItem(agent_type.value.replace('_', ' ').title(), agent_type)
        form_layout.addRow("代理类型:", self.type_combo)
        
        # 优先级
        self.priority_combo = QComboBox()
        for priority in AgentPriority:
            self.priority_combo.addItem(priority.value.title(), priority)
        form_layout.addRow("优先级:", self.priority_combo)
        
        # 自动启动
        self.auto_start_check = QCheckBox("应用启动时自动启动代理")
        form_layout.addRow("自动启动:", self.auto_start_check)
        
        # 最大并发任务数
        self.max_tasks_spin = QSpinBox()
        self.max_tasks_spin.setRange(1, 20)
        self.max_tasks_spin.setValue(5)
        form_layout.addRow("最大并发任务:", self.max_tasks_spin)
        
        self.add_widget(form_layout)
        
        # 注册字段
        self.registerField("name*", self.name_edit)
        self.registerField("description", self.description_edit, "plainText")
        self.registerField("agent_type", self.type_combo, "currentData")
        self.registerField("priority", self.priority_combo, "currentData")
        self.registerField("auto_start", self.auto_start_check)
        self.registerField("max_tasks", self.max_tasks_spin)
    
    def validatePage(self):
        """验证页面数据"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "输入错误", "请输入代理名称")
            return False
        return True


class AgentTemplateSelectionPage(AgentWizardPage):
    """代理模板选择页面"""
    
    def __init__(self, agent_registry: AgentRegistry, parent=None):
        super().__init__("模板选择", "选择代理模板或从头开始创建", parent)
        self.agent_registry = agent_registry
        
        # 模板列表
        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self.on_template_selected)
        
        # 添加模板选项
        templates = self.agent_registry.list_templates()
        for template in templates:
            item = QListWidgetItem(f"{template.name}\n{template.description}")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)
        
        # 自定义选项
        custom_item = QListWidgetItem("自定义代理\n从头开始创建自定义代理")
        custom_item.setData(Qt.ItemDataRole.UserRole, None)
        self.template_list.addItem(custom_item)
        
        self.add_widget(self.template_list)
        
        # 注册字段
        self.registerField("selected_template", self, "selected_template")
    
    @property
    def selected_template(self):
        """获取选中的模板"""
        selected_items = self.template_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None
    
    def on_template_selected(self):
        """模板选择变化处理"""
        self.completeChanged.emit()
    
    def isComplete(self):
        """检查页面是否完成"""
        return self.template_list.selectedItems() is not None


class AgentCapabilitySelectionPage(AgentWizardPage):
    """能力选择页面"""
    
    def __init__(self, capability_registry: CapabilityRegistry, model_manager: ModelManager, parent=None):
        super().__init__("能力配置", "选择代理支持的能力和对应的模型", parent)
        self.capability_registry = capability_registry
        self.model_manager = model_manager
        
        # 能力选择区域
        capability_group = QGroupBox("选择能力")
        capability_layout = QVBoxLayout()
        
        # 能力列表
        self.capability_list = QListWidget()
        capabilities = self.capability_registry.get_all_capabilities()
        for capability in capabilities:
            item = QListWidgetItem(f"{capability.name}\n{capability.description}")
            item.setData(Qt.ItemDataRole.UserRole, capability)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.capability_list.addItem(item)
        
        capability_layout.addWidget(self.capability_list)
        capability_group.setLayout(capability_layout)
        
        # 模型映射区域
        mapping_group = QGroupBox("模型映射配置")
        mapping_layout = QVBoxLayout()
        
        # 能力-模型映射列表
        self.mapping_widgets = {}  # capability_id -> (combo, priority_spin, enabled_check)
        
        # 添加模型选择控件
        self.mapping_container = QVBoxLayout()
        mapping_layout.addLayout(self.mapping_container)
        
        mapping_group.setLayout(mapping_layout)
        
        # 主布局
        main_layout = QHBoxLayout()
        main_layout.addWidget(capability_group, 1)
        main_layout.addWidget(mapping_group, 1)
        
        self.add_widget(main_layout)
        
        # 连接信号
        self.capability_list.itemChanged.connect(self.on_capability_selection_changed)
    
    def on_capability_selection_changed(self, item):
        """能力选择变化处理"""
        capability = item.data(Qt.ItemDataRole.UserRole)
        capability_id = capability.capability_id
        
        if item.checkState() == Qt.CheckState.Checked:
            # 添加模型映射控件
            self.add_capability_mapping(capability)
        else:
            # 移除模型映射控件
            self.remove_capability_mapping(capability_id)
    
    def add_capability_mapping(self, capability):
        """为能力添加模型映射控件"""
        capability_id = capability.capability_id
        
        # 创建映射控件组
        mapping_widget = QGroupBox(capability.name)
        mapping_layout = QFormLayout()
        
        # 模型选择
        model_combo = QComboBox()
        models = self.model_manager.list_models()
        for model in models:
            model_combo.addItem(model.name, model.model_id)
        mapping_layout.addRow("选择模型:", model_combo)
        
        # 优先级
        priority_spin = QSpinBox()
        priority_spin.setRange(1, 10)
        priority_spin.setValue(1)
        mapping_layout.addRow("优先级:", priority_spin)
        
        # 启用状态
        enabled_check = QCheckBox("启用此能力")
        enabled_check.setChecked(True)
        mapping_layout.addRow("启用:", enabled_check)
        
        mapping_widget.setLayout(mapping_layout)
        
        # 保存控件引用
        self.mapping_widgets[capability_id] = (model_combo, priority_spin, enabled_check, mapping_widget)
        
        # 添加到容器
        self.mapping_container.addWidget(mapping_widget)
    
    def remove_capability_mapping(self, capability_id):
        """移除能力映射控件"""
        if capability_id in self.mapping_widgets:
            _, _, _, mapping_widget = self.mapping_widgets[capability_id]
            mapping_widget.setParent(None)
            mapping_widget.deleteLater()
            del self.mapping_widgets[capability_id]
    
    def get_capability_mappings(self):
        """获取能力映射配置"""
        mappings = []
        for capability_id, (model_combo, priority_spin, enabled_check, _) in self.mapping_widgets.items():
            mapping = AgentCapabilityMapping(
                capability_id=capability_id,
                model_id=model_combo.currentData(),
                priority=priority_spin.value(),
                enabled=enabled_check.isChecked()
            )
            mappings.append(mapping)
        return mappings


class AgentSummaryPage(AgentWizardPage):
    """代理配置摘要页面"""
    
    def __init__(self, parent=None):
        super().__init__("配置摘要", "确认代理配置信息", parent)
        
        # 摘要文本
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        self.summary_label.setFont(font)
        
        self.add_widget(self.summary_label)
    
    def initializePage(self):
        """初始化页面时更新摘要"""
        summary = self.generate_summary()
        self.summary_label.setText(summary)
    
    def generate_summary(self):
        """生成配置摘要"""
        name = self.field("name")
        description = self.field("description")
        agent_type = self.field("agent_type")
        priority = self.field("priority")
        auto_start = self.field("auto_start")
        max_tasks = self.field("max_tasks")
        
        summary = f"""
        <h3>代理配置摘要</h3>
        <table border="0" cellspacing="5">
        <tr><td><b>名称:</b></td><td>{name}</td></tr>
        <tr><td><b>描述:</b></td><td>{description}</td></tr>
        <tr><td><b>类型:</b></td><td>{agent_type.value.replace('_', ' ').title()}</td></tr>
        <tr><td><b>优先级:</b></td><td>{priority.value.title()}</td></tr>
        <tr><td><b>自动启动:</b></td><td>{'是' if auto_start else '否'}</td></tr>
        <tr><td><b>最大并发任务:</b></td><td>{max_tasks}</td></tr>
        </table>
        """
        
        # 添加能力映射信息（如果可用）
        capability_page = self.wizard().page(2)  # 能力选择页面
        if hasattr(capability_page, 'get_capability_mappings'):
            mappings = capability_page.get_capability_mappings()
            if mappings:
                summary += "<h4>能力配置:</h4><ul>"
                for mapping in mappings:
                    summary += f"<li>{mapping.capability_id} → {mapping.model_id} (优先级: {mapping.priority})</li>"
                summary += "</ul>"
        
        return summary


class AgentCreationWizard(QWizard):
    """代理创建向导"""
    
    agent_created = pyqtSignal(object)  # 代理创建完成信号
    
    def __init__(self, agent_registry: AgentRegistry, capability_registry: CapabilityRegistry, 
                 model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.agent_registry = agent_registry
        self.capability_registry = capability_registry
        self.model_manager = model_manager
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置向导界面"""
        self.setWindowTitle("创建新代理")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setMinimumSize(600, 500)
        
        # 添加页面
        self.addPage(AgentBasicInfoPage(self))
        self.addPage(AgentTemplateSelectionPage(self.agent_registry, self))
        self.addPage(AgentCapabilitySelectionPage(self.capability_registry, self.model_manager, self))
        self.addPage(AgentSummaryPage(self))
        
        # 设置按钮文本
        self.setButtonText(QWizard.WizardButton.NextButton, "下一步")
        self.setButtonText(QWizard.WizardButton.BackButton, "上一步")
        self.setButtonText(QWizard.WizardButton.FinishButton, "创建")
        self.setButtonText(QWizard.WizardButton.CancelButton, "取消")
    
    def accept(self):
        """完成向导时创建代理"""
        try:
            # 收集配置信息
            name = self.field("name")
            description = self.field("description")
            agent_type = self.field("agent_type")
            priority = self.field("priority")
            auto_start = self.field("auto_start")
            max_tasks = self.field("max_tasks")
            
            # 获取能力映射
            capability_page = self.page(2)
            capability_mappings = capability_page.get_capability_mappings() if hasattr(capability_page, 'get_capability_mappings') else []
            
            # 创建代理配置
            agent_config = AgentConfig(
                agent_id="",  # 将由注册表生成
                name=name,
                description=description,
                agent_type=agent_type,
                capabilities=capability_mappings,
                priority=priority,
                max_concurrent_tasks=max_tasks,
                auto_start=auto_start
            )
            
            # 注册代理
            if self.agent_registry.register_agent(agent_config):
                self.agent_created.emit(agent_config)
                QMessageBox.information(self, "创建成功", f"代理 '{name}' 创建成功！")
                super().accept()
            else:
                QMessageBox.warning(self, "创建失败", "代理创建失败，请检查配置")
        
        except Exception as e:
            QMessageBox.critical(self, "创建错误", f"创建代理时发生错误:\n{str(e)}")


# 使用示例
def create_agent_wizard_demo():
    """创建代理向导演示"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建必要的管理器实例
    agent_registry = AgentRegistry()
    capability_registry = CapabilityRegistry()
    model_manager = ModelManager()  # 需要实际的模型管理器
    
    # 创建向导
    wizard = AgentCreationWizard(agent_registry, capability_registry, model_manager)
    wizard.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    create_agent_wizard_demo()
