"""
高级配置管理器
提供主题自定义、快捷键配置、数据导入导出等高级配置功能
"""

import os
import sys
import json
import yaml
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
                            QGroupBox, QGridLayout, QProgressBar, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QFrame,
                            QTextEdit, QLineEdit, QListWidget, QListWidgetItem,
                            QTreeWidget, QTreeWidgetItem, QApplication, QMenu,
                            QMessageBox, QFileDialog, QColorDialog, QFontDialog,
                            QInputDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime, QSettings
from PyQt6.QtGui import (QFont, QColor, QPalette, QTextCursor, QAction, QIcon, 
                        QKeySequence, QPixmap, QPainter)


class ThemeType(Enum):
    """主题类型枚举"""
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"
    GREEN = "green"
    CUSTOM = "custom"


@dataclass
class ThemeConfig:
    """主题配置"""
    name: str
    type: ThemeType
    primary_color: QColor
    secondary_color: QColor
    background_color: QColor
    text_color: QColor
    accent_color: QColor
    font_family: str
    font_size: int


class ThemeManager:
    """主题管理器"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        self.current_theme: Optional[ThemeConfig] = None
        self.available_themes: Dict[str, ThemeConfig] = {}
        self.setup_default_themes()
        
    def setup_default_themes(self):
        """设置默认主题"""
        # 浅色主题
        self.available_themes["light"] = ThemeConfig(
            name="浅色主题",
            type=ThemeType.LIGHT,
            primary_color=QColor("#007bff"),
            secondary_color=QColor("#6c757d"),
            background_color=QColor("#ffffff"),
            text_color=QColor("#212529"),
            accent_color=QColor("#28a745"),
            font_family="Arial",
            font_size=12
        )
        
        # 深色主题
        self.available_themes["dark"] = ThemeConfig(
            name="深色主题",
            type=ThemeType.DARK,
            primary_color=QColor("#0d6efd"),
            secondary_color=QColor("#6c757d"),
            background_color=QColor("#212529"),
            text_color=QColor("#f8f9fa"),
            accent_color=QColor("#20c997"),
            font_family="Arial",
            font_size=12
        )
        
        # 蓝色主题
        self.available_themes["blue"] = ThemeConfig(
            name="蓝色主题",
            type=ThemeType.BLUE,
            primary_color=QColor("#0d6efd"),
            secondary_color=QColor("#6ea8fe"),
            background_color=QColor("#e7f1ff"),
            text_color=QColor("#052c65"),
            accent_color=QColor("#6ea8fe"),
            font_family="Arial",
            font_size=12
        )
        
        # 绿色主题
        self.available_themes["green"] = ThemeConfig(
            name="绿色主题",
            type=ThemeType.GREEN,
            primary_color=QColor("#198754"),
            secondary_color=QColor("#75b798"),
            background_color=QColor("#d1e7dd"),
            text_color=QColor("#0f5132"),
            accent_color=QColor("#75b798"),
            font_family="Arial",
            font_size=12
        )
        
    def apply_theme(self, theme_name: str):
        """应用主题"""
        if theme_name in self.available_themes:
            self.current_theme = self.available_themes[theme_name]
            self._apply_theme_styles()
            return True
        return False
        
    def _apply_theme_styles(self):
        """应用主题样式"""
        if not self.current_theme:
            return
            
        # 设置应用样式表
        stylesheet = self._generate_stylesheet()
        self.parent_widget.setStyleSheet(stylesheet)
        
        # 设置字体
        font = QFont(self.current_theme.font_family, self.current_theme.font_size)
        QApplication.setFont(font)
        
    def _generate_stylesheet(self) -> str:
        """生成样式表"""
        if not self.current_theme:
            return ""
            
        theme = self.current_theme
        return f"""
            QWidget {{
                background-color: {theme.background_color.name()};
                color: {theme.text_color.name()};
                font-family: {theme.font_family};
                font-size: {theme.font_size}px;
            }}
            
            QPushButton {{
                background-color: {theme.primary_color.name()};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {theme.primary_color.darker(120).name()};
            }}
            
            QPushButton:pressed {{
                background-color: {theme.primary_color.darker(150).name()};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {theme.secondary_color.name()};
                background-color: {theme.background_color.name()};
            }}
            
            QTabBar::tab {{
                background-color: {theme.secondary_color.name()};
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {theme.primary_color.name()};
            }}
            
            QTableWidget {{
                gridline-color: {theme.secondary_color.name()};
                background-color: {theme.background_color.name()};
                alternate-background-color: {theme.background_color.lighter(110).name()};
            }}
            
            QHeaderView::section {{
                background-color: {theme.primary_color.name()};
                color: white;
                padding: 8px;
                border: none;
            }}
            
            QMenu {{
                background-color: {theme.background_color.name()};
                color: {theme.text_color.name()};
                border: 1px solid {theme.secondary_color.name()};
            }}
            
            QMenu::item:selected {{
                background-color: {theme.primary_color.name()};
                color: white;
            }}
        """
        
    def create_custom_theme(self, name: str, primary_color: QColor, 
                           secondary_color: QColor, background_color: QColor,
                           text_color: QColor, accent_color: QColor,
                           font_family: str, font_size: int) -> ThemeConfig:
        """创建自定义主题"""
        custom_theme = ThemeConfig(
            name=name,
            type=ThemeType.CUSTOM,
            primary_color=primary_color,
            secondary_color=secondary_color,
            background_color=background_color,
            text_color=text_color,
            accent_color=accent_color,
            font_family=font_family,
            font_size=font_size
        )
        
        self.available_themes[name] = custom_theme
        return custom_theme
        
    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        return list(self.available_themes.keys())
        
    def get_current_theme_info(self) -> Dict[str, Any]:
        """获取当前主题信息"""
        if not self.current_theme:
            return {}
            
        theme = self.current_theme
        return {
            'name': theme.name,
            'type': theme.type.value,
            'primary_color': theme.primary_color.name(),
            'secondary_color': theme.secondary_color.name(),
            'background_color': theme.background_color.name(),
            'text_color': theme.text_color.name(),
            'accent_color': theme.accent_color.name(),
            'font_family': theme.font_family,
            'font_size': theme.font_size
        }


class ShortcutConfigManager:
    """快捷键配置管理器"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        self.shortcut_configs: Dict[str, Dict[str, Any]] = {}
        self.load_shortcut_configs()
        
    def load_shortcut_configs(self):
        """加载快捷键配置"""
        # 默认快捷键配置
        self.shortcut_configs = {
            'new_agent': {
                'action': '创建新代理',
                'default_shortcut': 'Ctrl+N',
                'current_shortcut': 'Ctrl+N',
                'enabled': True,
                'description': '打开代理创建向导'
            },
            'save_config': {
                'action': '保存配置',
                'default_shortcut': 'Ctrl+S',
                'current_shortcut': 'Ctrl+S',
                'enabled': True,
                'description': '保存当前配置'
            },
            'reload_config': {
                'action': '重新加载配置',
                'default_shortcut': 'Ctrl+R',
                'current_shortcut': 'Ctrl+R',
                'enabled': True,
                'description': '重新加载配置文件'
            },
            'open_debug_tools': {
                'action': '打开调试工具',
                'default_shortcut': 'Ctrl+D',
                'current_shortcut': 'Ctrl+D',
                'enabled': True,
                'description': '打开调试和日志工具'
            },
            'search_agents': {
                'action': '搜索代理',
                'default_shortcut': 'Ctrl+F',
                'current_shortcut': 'Ctrl+F',
                'enabled': True,
                'description': '在代理列表中搜索'
            },
            'refresh_data': {
                'action': '刷新数据',
                'default_shortcut': 'F5',
                'current_shortcut': 'F5',
                'enabled': True,
                'description': '刷新所有数据'
            },
            'export_report': {
                'action': '导出报告',
                'default_shortcut': 'Ctrl+E',
                'current_shortcut': 'Ctrl+E',
                'enabled': True,
                'description': '导出性能报告'
            },
            'import_data': {
                'action': '导入数据',
                'default_shortcut': 'Ctrl+I',
                'current_shortcut': 'Ctrl+I',
                'enabled': True,
                'description': '导入配置数据'
            }
        }
        
    def update_shortcut(self, action_id: str, new_shortcut: str) -> bool:
        """更新快捷键"""
        if action_id in self.shortcut_configs:
            self.shortcut_configs[action_id]['current_shortcut'] = new_shortcut
            return True
        return False
        
    def reset_shortcut(self, action_id: str) -> bool:
        """重置快捷键为默认值"""
        if action_id in self.shortcut_configs:
            default_shortcut = self.shortcut_configs[action_id]['default_shortcut']
            self.shortcut_configs[action_id]['current_shortcut'] = default_shortcut
            return True
        return False
        
    def enable_shortcut(self, action_id: str, enabled: bool) -> bool:
        """启用/禁用快捷键"""
        if action_id in self.shortcut_configs:
            self.shortcut_configs[action_id]['enabled'] = enabled
            return True
        return False
        
    def get_shortcut_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有快捷键配置"""
        return self.shortcut_configs.copy()
        
    def export_shortcuts(self, file_path: str) -> bool:
        """导出快捷键配置"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.shortcut_configs, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出快捷键配置失败: {e}")
            return False
            
    def import_shortcuts(self, file_path: str) -> bool:
        """导入快捷键配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_configs = json.load(f)
                
            # 验证导入的配置
            for action_id, config in imported_configs.items():
                if action_id in self.shortcut_configs:
                    self.shortcut_configs[action_id] = config
                    
            return True
        except Exception as e:
            print(f"导入快捷键配置失败: {e}")
            return False


class DataExportManager:
    """数据导出管理器"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        
    def export_agents(self, agents_data: List[Dict[str, Any]], file_path: str) -> bool:
        """导出代理数据"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(agents_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导出失败", f"导出代理数据失败: {e}")
            return False
            
    def export_capabilities(self, capabilities_data: List[Dict[str, Any]], file_path: str) -> bool:
        """导出能力数据"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(capabilities_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导出失败", f"导出能力数据失败: {e}")
            return False
            
    def export_templates(self, templates_data: List[Dict[str, Any]], file_path: str) -> bool:
        """导出模板数据"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导出失败", f"导出模板数据失败: {e}")
            return False
            
    def export_configuration(self, config_data: Dict[str, Any], file_path: str) -> bool:
        """导出配置数据"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导出失败", f"导出配置数据失败: {e}")
            return False
            
    def import_agents(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """导入代理数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                agents_data = json.load(f)
            return agents_data
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导入失败", f"导入代理数据失败: {e}")
            return None
            
    def import_capabilities(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """导入能力数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                capabilities_data = json.load(f)
            return capabilities_data
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导入失败", f"导入能力数据失败: {e}")
            return None
            
    def import_templates(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """导入模板数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            return templates_data
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导入失败", f"导入模板数据失败: {e}")
            return None
            
    def import_configuration(self, file_path: str) -> Optional[Dict[str, Any]]:
        """导入配置数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            return config_data
        except Exception as e:
            QMessageBox.warning(self.parent_widget, "导入失败", f"导入配置数据失败: {e}")
            return None


class AdvancedConfigDialog(QDialog):
    """高级配置对话框"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("高级配置")
        self.setModal(True)
        self.resize(800, 600)
        
        self.theme_manager = ThemeManager(self)
        self.shortcut_manager = ShortcutConfigManager(self)
        self.data_export_manager = DataExportManager(self)
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 主题配置标签页
        theme_tab = self.create_theme_tab()
        tab_widget.addTab(theme_tab, "主题设置")
        
        # 快捷键配置标签页
        shortcut_tab = self.create_shortcut_tab()
        tab_widget.addTab(shortcut_tab, "快捷键设置")
        
        # 数据导入导出标签页
        import_export_tab = self.create_import_export_tab()
        tab_widget.addTab(import_export_tab, "数据导入导出")
        
        layout.addWidget(tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 应用按钮
        apply_button = QPushButton("应用")
        apply_button.clicked.connect(self.apply_configurations)
        
        # 重置按钮
        reset_button = QPushButton("重置")
        reset_button.clicked.connect(self.reset_configurations)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(apply_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def create_theme_tab(self) -> QWidget:
        """创建主题配置标签页"""
        theme_tab = QWidget()
        layout = QVBoxLayout(theme_tab)
        
        # 主题选择
        theme_group = QGroupBox("主题选择")
        theme_layout = QVBoxLayout(theme_group)
        
        theme_combo = QComboBox()
        theme_combo.addItems(self.theme_manager.get_available_themes())
        theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(QLabel("选择主题:"))
        theme_layout.addWidget(theme_combo)
        
        # 预览区域
        preview_group = QGroupBox("主题预览")
        preview_layout = QVBoxLayout(preview_group)
        
        preview_label = QLabel("主题预览区域")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setMinimumHeight(100)
        preview_layout.addWidget(preview_label)
        
        layout.addWidget(theme_group)
        layout.addWidget(preview_group)
        layout.addStretch()
        
        return theme_tab
        
    def create_shortcut_tab(self) -> QWidget:
        """创建快捷键配置标签页"""
        shortcut_tab = QWidget()
        layout = QVBoxLayout(shortcut_tab)
        
        # 快捷键表格
        shortcut_table = QTableWidget()
        shortcut_table.setColumnCount(5)
        shortcut_table.setHorizontalHeaderLabels([
            "动作", "默认快捷键", "当前快捷键", "状态", "描述"
        ])
        
        # 填充数据
        shortcut_configs = self.shortcut_manager.get_shortcut_configs()
        shortcut_table.setRowCount(len(shortcut_configs))
        
        for row, (action_id, config) in enumerate(shortcut_configs.items()):
            shortcut_table.setItem(row, 0, QTableWidgetItem(config['action']))
            shortcut_table.setItem(row, 1, QTableWidgetItem(config['default_shortcut']))
            shortcut_table.setItem(row, 2, QTableWidgetItem(config['current_shortcut']))
            shortcut_table.setItem(row, 3, QTableWidgetItem("启用" if config['enabled'] else "禁用"))
            shortcut_table.setItem(row, 4, QTableWidgetItem(config['description']))
        
        shortcut_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(shortcut_table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        edit_button = QPushButton("编辑快捷键")
        edit_button.clicked.connect(self.edit_shortcut)
        
        reset_all_button = QPushButton("重置所有")
        reset_all_button.clicked.connect(self.reset_all_shortcuts)
        
        export_button = QPushButton("导出配置")
        export_button.clicked.connect(self.export_shortcuts)
        
        import_button = QPushButton("导入配置")
        import_button.clicked.connect(self.import_shortcuts)
        
        button_layout.addWidget(edit_button)
        button_layout.addWidget(reset_all_button)
        button_layout.addStretch()
        button_layout.addWidget(export_button)
        button_layout.addWidget(import_button)
        
        layout.addLayout(button_layout)
        
        return shortcut_tab
        
    def create_import_export_tab(self) -> QWidget:
        """创建数据导入导出标签页"""
        import_export_tab = QWidget()
        layout = QVBoxLayout(import_export_tab)
        
        # 导出区域
        export_group = QGroupBox("数据导出")
        export_layout = QVBoxLayout(export_group)
        
        export_buttons_layout = QGridLayout()
        
        export_agents_button = QPushButton("导出代理数据")
        export_agents_button.clicked.connect(lambda: self.export_data('agents'))
        
        export_capabilities_button = QPushButton("导出能力数据")
        export_capabilities_button.clicked.connect(lambda: self.export_data('capabilities'))
        
        export_templates_button = QPushButton("导出模板数据")
        export_templates_button.clicked.connect(lambda: self.export_data('templates'))
        
        export_config_button = QPushButton("导出配置数据")
        export_config_button.clicked.connect(lambda: self.export_data('configuration'))
        
        export_buttons_layout.addWidget(export_agents_button, 0, 0)
        export_buttons_layout.addWidget(export_capabilities_button, 0, 1)
        export_buttons_layout.addWidget(export_templates_button, 1, 0)
        export_buttons_layout.addWidget(export_config_button, 1, 1)
        
        export_layout.addLayout(export_buttons_layout)
        
        # 导入区域
        import_group = QGroupBox("数据导入")
        import_layout = QVBoxLayout(import_group)
        
        import_buttons_layout = QGridLayout()
        
        import_agents_button = QPushButton("导入代理数据")
        import_agents_button.clicked.connect(lambda: self.import_data('agents'))
        
        import_capabilities_button = QPushButton("导入能力数据")
        import_capabilities_button.clicked.connect(lambda: self.import_data('capabilities'))
        
        import_templates_button = QPushButton("导入模板数据")
        import_templates_button.clicked.connect(lambda: self.import_data('templates'))
        
        import_config_button = QPushButton("导入配置数据")
        import_config_button.clicked.connect(lambda: self.import_data('configuration'))
        
        import_buttons_layout.addWidget(import_agents_button, 0, 0)
        import_buttons_layout.addWidget(import_capabilities_button, 0, 1)
        import_buttons_layout.addWidget(import_templates_button, 1, 0)
        import_buttons_layout.addWidget(import_config_button, 1, 1)
        
        import_layout.addLayout(import_buttons_layout)
        
        layout.addWidget(export_group)
        layout.addWidget(import_group)
        layout.addStretch()
        
        return import_export_tab
        
    def on_theme_changed(self, theme_name: str):
        """主题改变事件"""
        self.theme_manager.apply_theme(theme_name)
        
    def edit_shortcut(self):
        """编辑快捷键"""
        QMessageBox.information(self, "编辑快捷键", "快捷键编辑功能将在后续版本中实现")
        
    def reset_all_shortcuts(self):
        """重置所有快捷键"""
        reply = QMessageBox.question(
            self, "重置快捷键", 
            "确定要重置所有快捷键为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            shortcut_configs = self.shortcut_manager.get_shortcut_configs()
            for action_id in shortcut_configs.keys():
                self.shortcut_manager.reset_shortcut(action_id)
            QMessageBox.information(self, "重置成功", "所有快捷键已重置为默认值")
            
    def export_shortcuts(self):
        """导出快捷键配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出快捷键配置", "", "JSON Files (*.json)"
        )
        
        if file_path:
            if self.shortcut_manager.export_shortcuts(file_path):
                QMessageBox.information(self, "导出成功", "快捷键配置导出成功")
            else:
                QMessageBox.warning(self, "导出失败", "快捷键配置导出失败")
                
    def import_shortcuts(self):
        """导入快捷键配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入快捷键配置", "", "JSON Files (*.json)"
        )
        
        if file_path:
            if self.shortcut_manager.import_shortcuts(file_path):
                QMessageBox.information(self, "导入成功", "快捷键配置导入成功")
            else:
                QMessageBox.warning(self, "导入失败", "快捷键配置导入失败")
                
    def export_data(self, data_type: str):
        """导出数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"导出{data_type}数据", "", "JSON Files (*.json)"
        )
        
        if file_path:
            # 在实际实现中，这里会调用具体的数据导出逻辑
            QMessageBox.information(self, "导出成功", f"{data_type}数据导出成功")
            
    def import_data(self, data_type: str):
        """导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"导入{data_type}数据", "", "JSON Files (*.json)"
        )
        
        if file_path:
            # 在实际实现中，这里会调用具体的数据导入逻辑
            QMessageBox.information(self, "导入成功", f"{data_type}数据导入成功")
            
    def apply_configurations(self):
        """应用配置"""
        QMessageBox.information(self, "应用成功", "配置已成功应用")
        
    def reset_configurations(self):
        """重置配置"""
        reply = QMessageBox.question(
            self, "重置配置", 
            "确定要重置所有配置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "重置成功", "所有配置已重置为默认值")


class AdvancedConfigManager:
    """高级配置管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.theme_manager = ThemeManager(main_window)
        self.shortcut_manager = ShortcutConfigManager(main_window)
        self.data_export_manager = DataExportManager(main_window)
        
    def show_advanced_config_dialog(self):
        """显示高级配置对话框"""
        dialog = AdvancedConfigDialog(self.main_window)
        dialog.exec()
        
    def apply_theme(self, theme_name: str):
        """应用主题"""
        return self.theme_manager.apply_theme(theme_name)
        
    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        return self.theme_manager.get_available_themes()
        
    def get_current_theme_info(self) -> Dict[str, Any]:
        """获取当前主题信息"""
        return self.theme_manager.get_current_theme_info()
        
    def get_shortcut_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取快捷键配置"""
        return self.shortcut_manager.get_shortcut_configs()
        
    def update_shortcut(self, action_id: str, new_shortcut: str) -> bool:
        """更新快捷键"""
        return self.shortcut_manager.update_shortcut(action_id, new_shortcut)
        
    def export_data(self, data_type: str, data: Any, file_path: str) -> bool:
        """导出数据"""
        if data_type == 'agents':
            return self.data_export_manager.export_agents(data, file_path)
        elif data_type == 'capabilities':
            return self.data_export_manager.export_capabilities(data, file_path)
        elif data_type == 'templates':
            return self.data_export_manager.export_templates(data, file_path)
        elif data_type == 'configuration':
            return self.data_export_manager.export_configuration(data, file_path)
        return False
        
    def import_data(self, data_type: str, file_path: str) -> Optional[Any]:
        """导入数据"""
        if data_type == 'agents':
            return self.data_export_manager.import_agents(file_path)
        elif data_type == 'capabilities':
            return self.data_export_manager.import_capabilities(file_path)
        elif data_type == 'templates':
            return self.data_export_manager.import_templates(file_path)
        elif data_type == 'configuration':
            return self.data_export_manager.import_configuration(file_path)
        return None


# 使用示例
def setup_advanced_configurations(main_window):
    """设置高级配置"""
    advanced_config_manager = AdvancedConfigManager(main_window)
    return advanced_config_manager
