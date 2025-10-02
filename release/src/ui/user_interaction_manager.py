"""
用户交互优化管理器
提供界面响应速度优化、快捷键、拖拽操作、上下文菜单等功能
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
                            QGroupBox, QGridLayout, QProgressBar, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QFrame,
                            QTextEdit, QLineEdit, QListWidget, QListWidgetItem,
                            QTreeWidget, QTreeWidgetItem, QApplication, QMenu,
                            QMessageBox, QFileDialog)
from PyQt6.QtGui import QShortcut, QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime, QMimeData, QUrl
from PyQt6.QtGui import (QFont, QColor, QPalette, QTextCursor, QAction, QIcon, 
                        QKeySequence, QDrag, QDropEvent, QDragEnterEvent, 
                        QDragMoveEvent, QDragLeaveEvent)


class ShortcutAction(Enum):
    """快捷键动作枚举"""
    NEW_AGENT = "new_agent"
    OPEN_DEBUG_TOOLS = "open_debug_tools"
    SAVE_CONFIG = "save_config"
    RELOAD_CONFIG = "reload_config"
    QUIT_APPLICATION = "quit_application"
    SEARCH_AGENTS = "search_agents"
    SEARCH_CAPABILITIES = "search_capabilities"
    REFRESH_DATA = "refresh_data"
    EXPORT_REPORT = "export_report"
    IMPORT_DATA = "import_data"


@dataclass
class ShortcutConfig:
    """快捷键配置"""
    action: ShortcutAction
    key_sequence: QKeySequence
    description: str
    enabled: bool = True


class ShortcutManager:
    """快捷键管理器"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        self.shortcuts: Dict[ShortcutAction, QShortcut] = {}
        self.shortcut_configs: List[ShortcutConfig] = []
        self.setup_default_shortcuts()
        
    def setup_default_shortcuts(self):
        """设置默认快捷键"""
        self.shortcut_configs = [
            ShortcutConfig(
                ShortcutAction.NEW_AGENT,
                QKeySequence("Ctrl+N"),
                "创建新代理"
            ),
            ShortcutConfig(
                ShortcutAction.OPEN_DEBUG_TOOLS,
                QKeySequence("Ctrl+D"),
                "打开调试工具"
            ),
            ShortcutConfig(
                ShortcutAction.SAVE_CONFIG,
                QKeySequence("Ctrl+S"),
                "保存配置"
            ),
            ShortcutConfig(
                ShortcutAction.RELOAD_CONFIG,
                QKeySequence("Ctrl+R"),
                "重新加载配置"
            ),
            ShortcutConfig(
                ShortcutAction.QUIT_APPLICATION,
                QKeySequence("Ctrl+Q"),
                "退出应用"
            ),
            ShortcutConfig(
                ShortcutAction.SEARCH_AGENTS,
                QKeySequence("Ctrl+F"),
                "搜索代理"
            ),
            ShortcutConfig(
                ShortcutAction.SEARCH_CAPABILITIES,
                QKeySequence("Ctrl+Shift+F"),
                "搜索能力"
            ),
            ShortcutConfig(
                ShortcutAction.REFRESH_DATA,
                QKeySequence("F5"),
                "刷新数据"
            ),
            ShortcutConfig(
                ShortcutAction.EXPORT_REPORT,
                QKeySequence("Ctrl+E"),
                "导出报告"
            ),
            ShortcutConfig(
                ShortcutAction.IMPORT_DATA,
                QKeySequence("Ctrl+I"),
                "导入数据"
            )
        ]
        
    def register_shortcut(self, action: ShortcutAction, callback: Callable):
        """注册快捷键"""
        config = next((c for c in self.shortcut_configs if c.action == action), None)
        if config and config.enabled:
            shortcut = QShortcut(config.key_sequence, self.parent_widget)
            shortcut.activated.connect(callback)
            self.shortcuts[action] = shortcut
            return True
        return False
        
    def unregister_shortcut(self, action: ShortcutAction):
        """取消注册快捷键"""
        if action in self.shortcuts:
            self.shortcuts[action].setEnabled(False)
            del self.shortcuts[action]
            
    def get_shortcut_list(self) -> List[Dict[str, Any]]:
        """获取快捷键列表"""
        return [
            {
                'action': config.action.value,
                'key_sequence': config.key_sequence.toString(),
                'description': config.description,
                'enabled': config.enabled
            }
            for config in self.shortcut_configs
        ]


class DragDropManager:
    """拖拽管理器"""
    
    def __init__(self, target_widget: QWidget):
        self.target_widget = target_widget
        self.supported_formats = ['text/plain', 'text/uri-list']
        self.setup_drag_drop()
        
    def setup_drag_drop(self):
        """设置拖拽支持"""
        self.target_widget.setAcceptDrops(True)
        
    def enable_drag_drop(self):
        """启用拖拽功能"""
        self.target_widget.setAcceptDrops(True)
        
    def disable_drag_drop(self):
        """禁用拖拽功能"""
        self.target_widget.setAcceptDrops(False)
        
    def handle_drag_enter(self, event: QDragEnterEvent):
        """处理拖拽进入事件"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            
    def handle_drag_move(self, event: QDragMoveEvent):
        """处理拖拽移动事件"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
            
    def handle_drag_leave(self, event: QDragLeaveEvent):
        """处理拖拽离开事件"""
        event.accept()
        
    def handle_drop(self, event: QDropEvent, drop_callback: Callable):
        """处理拖拽释放事件"""
        mime_data = event.mimeData()
        
        if mime_data.hasUrls():
            # 处理文件拖拽
            urls = mime_data.urls()
            file_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
            drop_callback(file_paths, 'files')
            
        elif mime_data.hasText():
            # 处理文本拖拽
            text = mime_data.text()
            drop_callback([text], 'text')
            
        event.acceptProposedAction()


class ContextMenuManager:
    """上下文菜单管理器"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget
        self.context_menus: Dict[str, QMenu] = {}
        
    def create_context_menu(self, menu_id: str, title: str = "") -> QMenu:
        """创建上下文菜单"""
        menu = QMenu(title, self.parent_widget)
        self.context_menus[menu_id] = menu
        return menu
        
    def add_menu_action(self, menu_id: str, text: str, callback: Callable, 
                       shortcut: Optional[QKeySequence] = None,
                       icon: Optional[QIcon] = None) -> QAction:
        """添加菜单动作"""
        if menu_id not in self.context_menus:
            self.create_context_menu(menu_id)
            
        action = QAction(text, self.parent_widget)
        if shortcut:
            action.setShortcut(shortcut)
        if icon:
            action.setIcon(icon)
        action.triggered.connect(callback)
        
        self.context_menus[menu_id].addAction(action)
        return action
        
    def add_menu_separator(self, menu_id: str):
        """添加菜单分隔符"""
        if menu_id in self.context_menus:
            self.context_menus[menu_id].addSeparator()
            
    def show_context_menu(self, menu_id: str, position):
        """显示上下文菜单"""
        if menu_id in self.context_menus:
            self.context_menus[menu_id].exec(position)


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.optimization_enabled = True
        self.lazy_loading_enabled = True
        self.cache_enabled = True
        self.async_operations_enabled = True
        
    def optimize_table_performance(self, table_widget: QTableWidget, 
                                 row_count_threshold: int = 1000):
        """优化表格性能"""
        if not self.optimization_enabled:
            return
            
        # 设置表格优化选项
        table_widget.setSortingEnabled(False)  # 禁用排序以提高性能
        table_widget.setAlternatingRowColors(True)  # 交替行颜色提高可读性
        
        # 对于大数据量表格，启用懒加载
        if row_count_threshold > 1000 and self.lazy_loading_enabled:
            self.setup_lazy_loading(table_widget)
            
    def setup_lazy_loading(self, table_widget: QTableWidget):
        """设置懒加载"""
        # 这里可以实现懒加载逻辑
        # 例如：只加载可见区域的数据
        pass
        
    def optimize_tree_performance(self, tree_widget: QTreeWidget):
        """优化树形控件性能"""
        if not self.optimization_enabled:
            return
            
        tree_widget.setSortingEnabled(False)
        tree_widget.setAlternatingRowColors(True)
        
    def async_operation(self, operation: Callable, callback: Callable = None):
        """异步操作"""
        if not self.async_operations_enabled:
            result = operation()
            if callback:
                callback(result)
            return
            
        # 在实际实现中，这里可以使用QThread或asyncio
        # 这里简化实现，直接调用
        result = operation()
        if callback:
            QTimer.singleShot(0, lambda: callback(result))


class UserInteractionManager:
    """用户交互管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.shortcut_manager = ShortcutManager(main_window)
        self.context_menu_manager = ContextMenuManager(main_window)
        self.performance_optimizer = PerformanceOptimizer()
        
        # 拖拽管理器将在具体控件中初始化
        self.drag_drop_managers: Dict[str, DragDropManager] = {}
        
    def setup_global_shortcuts(self):
        """设置全局快捷键"""
        # 注册全局快捷键
        self.shortcut_manager.register_shortcut(
            ShortcutAction.NEW_AGENT, 
            self.main_window.show_agent_wizard
        )
        self.shortcut_manager.register_shortcut(
            ShortcutAction.OPEN_DEBUG_TOOLS,
            self.main_window.show_debug_tools
        )
        self.shortcut_manager.register_shortcut(
            ShortcutAction.SAVE_CONFIG,
            self.main_window.save_configuration
        )
        self.shortcut_manager.register_shortcut(
            ShortcutAction.RELOAD_CONFIG,
            self.main_window.reload_configuration
        )
        self.shortcut_manager.register_shortcut(
            ShortcutAction.QUIT_APPLICATION,
            self.main_window.close
        )
        
    def setup_context_menus(self):
        """设置上下文菜单"""
        # 代理列表上下文菜单
        agent_menu = self.context_menu_manager.create_context_menu(
            "agent_list", "代理操作"
        )
        self.context_menu_manager.add_menu_action(
            "agent_list", "启动代理", 
            lambda: self.main_window.start_selected_agent(),
            QKeySequence("F2")
        )
        self.context_menu_manager.add_menu_action(
            "agent_list", "停止代理", 
            lambda: self.main_window.stop_selected_agent(),
            QKeySequence("F3")
        )
        self.context_menu_manager.add_menu_separator("agent_list")
        self.context_menu_manager.add_menu_action(
            "agent_list", "查看详情", 
            lambda: self.main_window.show_agent_details(),
            QKeySequence("F4")
        )
        self.context_menu_manager.add_menu_action(
            "agent_list", "编辑代理", 
            lambda: self.main_window.edit_selected_agent(),
            QKeySequence("Ctrl+E")
        )
        
        # 能力列表上下文菜单
        capability_menu = self.context_menu_manager.create_context_menu(
            "capability_list", "能力操作"
        )
        self.context_menu_manager.add_menu_action(
            "capability_list", "测试能力", 
            lambda: self.main_window.test_selected_capability(),
            QKeySequence("F5")
        )
        self.context_menu_manager.add_menu_action(
            "capability_list", "查看详情", 
            lambda: self.main_window.show_capability_details(),
            QKeySequence("F6")
        )
        
    def setup_drag_drop_for_widget(self, widget_id: str, widget: QWidget, 
                                 drop_callback: Callable):
        """为控件设置拖拽功能"""
        drag_drop_manager = DragDropManager(widget)
        self.drag_drop_managers[widget_id] = drag_drop_manager
        
        # 连接拖拽事件
        widget.dragEnterEvent = lambda event: drag_drop_manager.handle_drag_enter(event)
        widget.dragMoveEvent = lambda event: drag_drop_manager.handle_drag_move(event)
        widget.dragLeaveEvent = lambda event: drag_drop_manager.handle_drag_leave(event)
        widget.dropEvent = lambda event: drag_drop_manager.handle_drop(event, drop_callback)
        
    def optimize_interface_performance(self):
        """优化界面性能"""
        # 优化表格性能
        if hasattr(self.main_window, 'agent_table'):
            self.performance_optimizer.optimize_table_performance(
                self.main_window.agent_table
            )
            
        if hasattr(self.main_window, 'capability_table'):
            self.performance_optimizer.optimize_table_performance(
                self.main_window.capability_table
            )
            
        # 优化树形控件性能
        if hasattr(self.main_window, 'template_tree'):
            self.performance_optimizer.optimize_tree_performance(
                self.main_window.template_tree
            )
            
    def show_context_menu(self, menu_id: str, position):
        """显示上下文菜单"""
        self.context_menu_manager.show_context_menu(menu_id, position)
        
    def get_shortcut_list(self) -> List[Dict[str, Any]]:
        """获取快捷键列表"""
        return self.shortcut_manager.get_shortcut_list()


class InteractionOptimizer:
    """交互优化器"""
    
    @staticmethod
    def optimize_button_responsiveness(button: QPushButton):
        """优化按钮响应性"""
        # 设置按钮样式和状态
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
    @staticmethod
    def optimize_table_responsiveness(table: QTableWidget):
        """优化表格响应性"""
        # 设置表格优化选项
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
    @staticmethod
    def optimize_text_edit_responsiveness(text_edit: QTextEdit):
        """优化文本编辑框响应性"""
        # 设置文本编辑框优化选项
        text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        text_edit.setAcceptRichText(False)
        
    @staticmethod
    def add_hover_effects(widget: QWidget):
        """添加悬停效果"""
        # 设置悬停样式
        widget.setStyleSheet("""
            QWidget:hover {
                background-color: #f0f0f0;
            }
        """)


# 使用示例
def setup_user_interaction_optimizations(main_window):
    """设置用户交互优化"""
    interaction_manager = UserInteractionManager(main_window)
    
    # 设置全局快捷键
    interaction_manager.setup_global_shortcuts()
    
    # 设置上下文菜单
    interaction_manager.setup_context_menus()
    
    # 优化界面性能
    interaction_manager.optimize_interface_performance()
    
    return interaction_manager
