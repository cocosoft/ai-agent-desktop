"""
代理模板管理界面
提供模板的创建、编辑、导入、导出等管理功能
"""

import os
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                            QListWidget, QListWidgetItem, QLabel, QPushButton,
                            QLineEdit, QComboBox, QTextEdit, QTabWidget,
                            QGroupBox, QFormLayout, QScrollArea, QMessageBox,
                            QFileDialog, QDialog, QDialogButtonBox, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..core.template_manager import TemplateManager, get_template_manager
from ..core.agent_model import AgentRegistry, AgentTemplate, AgentType
from ..utils.logger import get_log_manager


class TemplateDetailDialog(QDialog):
    """模板详情对话框"""
    
    def __init__(self, template: AgentTemplate, parent=None):
        super().__init__(parent)
        self.template = template
        self.logger = get_log_manager().logger
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"模板详情 - {self.template.name}")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_info_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_info_group)
        
        basic_layout.addRow("模板ID:", QLabel(self.template.template_id))
        basic_layout.addRow("名称:", QLabel(self.template.name))
        basic_layout.addRow("描述:", QLabel(self.template.description))
        basic_layout.addRow("类型:", QLabel(self.template.agent_type.value))
        basic_layout.addRow("分类:", QLabel(self.template.category))
        basic_layout.addRow("标签:", QLabel(", ".join(self.template.tags)))
        basic_layout.addRow("创建时间:", QLabel(self.template.created_at.strftime("%Y-%m-%d %H:%M:%S")))
        basic_layout.addRow("更新时间:", QLabel(self.template.updated_at.strftime("%Y-%m-%d %H:%M:%S")))
        
        layout.addWidget(basic_info_group)
        
        # 能力配置
        capabilities_group = QGroupBox("基础能力")
        capabilities_layout = QVBoxLayout(capabilities_group)
        
        capabilities_text = QTextEdit()
        capabilities_text.setReadOnly(True)
        capabilities_text.setPlainText("\n".join(self.template.base_capabilities))
        capabilities_layout.addWidget(capabilities_text)
        
        layout.addWidget(capabilities_group)
        
        # 推荐模型
        models_group = QGroupBox("推荐模型")
        models_layout = QVBoxLayout(models_group)
        
        models_text = QTextEdit()
        models_text.setReadOnly(True)
        
        models_content = []
        for capability, models in self.template.recommended_models.items():
            models_content.append(f"{capability}: {', '.join(models)}")
        
        models_text.setPlainText("\n".join(models_content))
        models_layout.addWidget(models_text)
        
        layout.addWidget(models_group)
        
        # 默认设置
        settings_group = QGroupBox("默认设置")
        settings_layout = QFormLayout(settings_group)
        
        for key, value in self.template.default_settings.items():
            settings_layout.addRow(f"{key}:", QLabel(str(value)))
        
        layout.addWidget(settings_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)


class TemplateManagerWidget(QWidget):
    """模板管理器主界面"""
    
    template_selected = pyqtSignal(AgentTemplate)
    
    def __init__(self, agent_registry: AgentRegistry, parent=None):
        super().__init__(parent)
        self.agent_registry = agent_registry
        self.template_manager = get_template_manager(agent_registry)
        self.logger = get_log_manager().logger
        self.current_template: Optional[AgentTemplate] = None
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索模板...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(self.search_edit)
        
        # 分类筛选
        self.category_combo = QComboBox()
        self.category_combo.addItem("所有分类", "")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        toolbar_layout.addWidget(QLabel("分类:"))
        toolbar_layout.addWidget(self.category_combo)
        
        toolbar_layout.addStretch()
        
        # 操作按钮
        self.create_button = QPushButton("创建模板")
        self.create_button.clicked.connect(self.create_template)
        toolbar_layout.addWidget(self.create_button)
        
        self.import_button = QPushButton("导入模板")
        self.import_button.clicked.connect(self.import_template)
        toolbar_layout.addWidget(self.import_button)
        
        self.export_button = QPushButton("导出模板")
        self.export_button.clicked.connect(self.export_template)
        self.export_button.setEnabled(False)
        toolbar_layout.addWidget(self.export_button)
        
        self.delete_button = QPushButton("删除模板")
        self.delete_button.clicked.connect(self.delete_template)
        self.delete_button.setEnabled(False)
        toolbar_layout.addWidget(self.delete_button)
        
        layout.addLayout(toolbar_layout)
        
        # 主内容区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 模板列表
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.on_template_selected)
        splitter.addWidget(self.template_list)
        
        # 模板详情
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        
        # 模板基本信息
        self.info_group = QGroupBox("模板信息")
        info_layout = QFormLayout(self.info_group)
        
        self.name_label = QLabel()
        self.description_label = QLabel()
        self.type_label = QLabel()
        self.category_label = QLabel()
        self.tags_label = QLabel()
        
        info_layout.addRow("名称:", self.name_label)
        info_layout.addRow("描述:", self.description_label)
        info_layout.addRow("类型:", self.type_label)
        info_layout.addRow("分类:", self.category_label)
        info_layout.addRow("标签:", self.tags_label)
        
        detail_layout.addWidget(self.info_group)
        
        # 能力配置
        self.capabilities_group = QGroupBox("基础能力")
        capabilities_layout = QVBoxLayout(self.capabilities_group)
        
        self.capabilities_text = QTextEdit()
        self.capabilities_text.setReadOnly(True)
        capabilities_layout.addWidget(self.capabilities_text)
        
        detail_layout.addWidget(self.capabilities_group)
        
        # 推荐模型
        self.models_group = QGroupBox("推荐模型")
        models_layout = QVBoxLayout(self.models_group)
        
        self.models_text = QTextEdit()
        self.models_text.setReadOnly(True)
        models_layout.addWidget(self.models_text)
        
        detail_layout.addWidget(self.models_group)
        
        # 默认设置
        self.settings_group = QGroupBox("默认设置")
        settings_layout = QFormLayout(self.settings_group)
        
        self.settings_widget = QWidget()
        self.settings_layout = QFormLayout(self.settings_widget)
        settings_layout.addRow(self.settings_widget)
        
        detail_layout.addWidget(self.settings_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.detail_button = QPushButton("查看详情")
        self.detail_button.clicked.connect(self.show_template_detail)
        self.detail_button.setEnabled(False)
        button_layout.addWidget(self.detail_button)
        
        self.use_button = QPushButton("使用此模板")
        self.use_button.clicked.connect(self.use_template)
        self.use_button.setEnabled(False)
        button_layout.addWidget(self.use_button)
        
        detail_layout.addLayout(button_layout)
        
        detail_layout.addStretch()
        
        splitter.addWidget(self.detail_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
    
    def load_templates(self):
        """加载模板列表"""
        self.template_list.clear()
        
        # 获取所有模板
        all_templates = self.template_manager.list_all_templates()
        
        # 更新分类列表
        categories = self.template_manager.get_template_categories()
        self.category_combo.clear()
        self.category_combo.addItem("所有分类", "")
        for category in categories:
            self.category_combo.addItem(category, category)
        
        # 添加模板到列表
        for template in all_templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template)
            
            # 标记自定义模板
            if template.template_id.startswith(('custom_', 'imported_', 'copy_', 'from_agent_')):
                item.setText(f"{template.name} (自定义)")
            
            self.template_list.addItem(item)
    
    def on_search_changed(self, text):
        """搜索文本改变"""
        # 这里可以添加搜索逻辑
        pass
    
    def on_category_changed(self, category):
        """分类改变"""
        # 这里可以添加分类筛选逻辑
        pass
    
    def on_template_selected(self, current, previous):
        """模板选择改变"""
        if not current:
            self.current_template = None
            self.clear_template_details()
            return
        
        self.current_template = current.data(Qt.ItemDataRole.UserRole)
        self.update_template_details()
        
        # 启用操作按钮
        self.export_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.detail_button.setEnabled(True)
        self.use_button.setEnabled(True)
    
    def clear_template_details(self):
        """清空模板详情"""
        self.name_label.setText("")
        self.description_label.setText("")
        self.type_label.setText("")
        self.category_label.setText("")
        self.tags_label.setText("")
        self.capabilities_text.clear()
        self.models_text.clear()
        
        # 清空设置
        for i in reversed(range(self.settings_layout.count())):
            widget = self.settings_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
    def update_template_details(self):
        """更新模板详情"""
        if not self.current_template:
            return
        
        template = self.current_template
        
        # 基本信息
        self.name_label.setText(template.name)
        self.description_label.setText(template.description)
        self.type_label.setText(template.agent_type.value)
        self.category_label.setText(template.category)
        self.tags_label.setText(", ".join(template.tags))
        
        # 基础能力
        self.capabilities_text.setPlainText("\n".join(template.base_capabilities))
        
        # 推荐模型
        models_content = []
        for capability, models in template.recommended_models.items():
            models_content.append(f"{capability}: {', '.join(models)}")
        self.models_text.setPlainText("\n".join(models_content))
        
        # 默认设置
        self.clear_template_details()  # 先清空设置
        for key, value in template.default_settings.items():
            label = QLabel(str(value))
            self.settings_layout.addRow(f"{key}:", label)
    
    def create_template(self):
        """创建模板"""
        # 这里可以打开创建模板的对话框
        QMessageBox.information(self, "创建模板", "创建模板功能待实现")
    
    def import_template(self):
        """导入模板"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模板文件", "", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            template = self.template_manager.import_template(file_path)
            if template:
                QMessageBox.information(self, "导入成功", f"成功导入模板: {template.name}")
                self.load_templates()
            else:
                QMessageBox.warning(self, "导入失败", "模板导入失败")
                
        except Exception as e:
            self.logger.error(f"导入模板失败: {str(e)}")
            QMessageBox.critical(self, "导入失败", f"导入模板时发生错误: {str(e)}")
    
    def export_template(self):
        """导出模板"""
        if not self.current_template:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存模板文件", f"{self.current_template.name}.json", "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            success = self.template_manager.export_template(self.current_template.template_id, file_path)
            if success:
                QMessageBox.information(self, "导出成功", f"模板已导出到: {file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "模板导出失败")
                
        except Exception as e:
            self.logger.error(f"导出模板失败: {str(e)}")
            QMessageBox.critical(self, "导出失败", f"导出模板时发生错误: {str(e)}")
    
    def delete_template(self):
        """删除模板"""
        if not self.current_template:
            return
        
        # 检查是否为自定义模板
        if not self.current_template.template_id.startswith(('custom_', 'imported_', 'copy_', 'from_agent_')):
            QMessageBox.warning(self, "删除失败", "只能删除自定义模板")
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除模板 '{self.current_template.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.template_manager.delete_template(self.current_template.template_id)
            if success:
                QMessageBox.information(self, "删除成功", "模板已删除")
                self.load_templates()
                self.clear_template_details()
            else:
                QMessageBox.warning(self, "删除失败", "模板删除失败")
    
    def show_template_detail(self):
        """显示模板详情"""
        if not self.current_template:
            return
        
        dialog = TemplateDetailDialog(self.current_template, self)
        dialog.exec()
    
    def use_template(self):
        """使用模板"""
        if not self.current_template:
            return
        
        self.template_selected.emit(self.current_template)
        QMessageBox.information(self, "使用模板", f"已选择模板: {self.current_template.name}")


# 测试函数
def test_template_manager():
    """测试模板管理器"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建代理注册表
    agent_registry = AgentRegistry()
    
    # 创建模板管理器
    template_manager = TemplateManager(agent_registry)
    
    # 创建界面
    widget = TemplateManagerWidget(agent_registry)
    widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    test_template_manager()
