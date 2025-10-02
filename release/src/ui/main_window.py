"""
主窗口类实现
PyQt6主窗口框架，包含菜单栏、工具栏、状态栏和标签页导航
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                            QMenuBar, QToolBar, QStatusBar, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QPixmap
from PyQt6.QtWidgets import QStyle

# 导入配置管理相关模块
try:
    from .config_dialog import ConfigDialog
    from ..core.config_manager import init_config_manager, get_config_manager
except ImportError as e:
    print(f"配置模块导入失败: {e}")
    ConfigDialog = None


class MainWindow(QMainWindow):
    """AI Agent桌面应用主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agent Desktop")
        self.setMinimumSize(1200, 800)
        
        # 设置应用图标
        self.setWindowIcon(self._create_application_icon())
        
        # 初始化UI组件
        self._setup_ui()
        
        # 应用主题设置
        self._apply_theme()
        
    def _create_application_icon(self):
        """创建应用图标"""
        # 使用系统图标或创建简单的图标
        try:
            # 尝试使用系统图标
            return self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        except:
            # 创建简单的文本图标作为备选
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.blue)
            return QIcon(pixmap)
    
    def _setup_ui(self):
        """设置主界面UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_tool_bar()
        
        # 创建标签页导航
        self._create_tab_navigation(main_layout)
        
        # 创建状态栏
        self._create_status_bar()
        
    def _create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件(&F)")
        
        # 新建代理动作
        new_agent_action = QAction("新建代理(&N)", self)
        new_agent_action.setShortcut("Ctrl+N")
        new_agent_action.triggered.connect(self._new_agent)
        file_menu.addAction(new_agent_action)
        
        # 打开配置动作
        open_config_action = QAction("打开配置(&O)", self)
        open_config_action.setShortcut("Ctrl+O")
        open_config_action.triggered.connect(self._open_config)
        file_menu.addAction(open_config_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图(&V)")
        
        # 工具栏显示/隐藏
        toggle_toolbar_action = QAction("工具栏", self)
        toggle_toolbar_action.setCheckable(True)
        toggle_toolbar_action.setChecked(True)
        toggle_toolbar_action.triggered.connect(self._toggle_toolbar)
        view_menu.addAction(toggle_toolbar_action)
        
        # 状态栏显示/隐藏
        toggle_statusbar_action = QAction("状态栏", self)
        toggle_statusbar_action.setCheckable(True)
        toggle_statusbar_action.setChecked(True)
        toggle_statusbar_action.triggered.connect(self._toggle_statusbar)
        view_menu.addAction(toggle_statusbar_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助(&H)")
        
        # 关于动作
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self):
        """创建工具栏"""
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # 新建代理按钮
        new_agent_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon),
            "新建代理", self
        )
        new_agent_btn.triggered.connect(self._new_agent)
        self.toolbar.addAction(new_agent_btn)
        
        self.toolbar.addSeparator()
        
        # 启动服务器按钮
        start_server_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay),
            "启动服务器", self
        )
        start_server_btn.triggered.connect(self._start_server)
        self.toolbar.addAction(start_server_btn)
        
        # 停止服务器按钮
        stop_server_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop),
            "停止服务器", self
        )
        stop_server_btn.triggered.connect(self._stop_server)
        self.toolbar.addAction(stop_server_btn)
        
        self.toolbar.addSeparator()
        
        # 设置按钮
        settings_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView),
            "设置", self
        )
        settings_btn.triggered.connect(self._open_settings)
        self.toolbar.addAction(settings_btn)
    
    def _create_tab_navigation(self, main_layout):
        """创建标签页导航"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        
        # 代理管理标签页
        agent_tab = QWidget()
        agent_layout = QVBoxLayout(agent_tab)
        agent_layout.addWidget(QLabel("代理管理界面 - 开发中"))
        self.tab_widget.addTab(agent_tab, "代理管理")
        
        # 模型管理标签页
        model_tab = QWidget()
        model_layout = QVBoxLayout(model_tab)
        model_layout.addWidget(QLabel("模型管理界面 - 开发中"))
        self.tab_widget.addTab(model_tab, "模型管理")
        
        # 能力管理标签页
        capability_tab = QWidget()
        capability_layout = QVBoxLayout(capability_tab)
        capability_layout.addWidget(QLabel("能力管理界面 - 开发中"))
        self.tab_widget.addTab(capability_tab, "能力管理")
        
        # 监控面板标签页
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)
        monitor_layout.addWidget(QLabel("监控面板 - 开发中"))
        self.tab_widget.addTab(monitor_tab, "监控")
        
        main_layout.addWidget(self.tab_widget)
        
        # 连接标签页切换信号
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 显示当前标签页信息
        self.status_bar.showMessage("就绪 - 选择标签页开始工作")
        
        # 添加永久部件显示应用状态
        self.status_label = QLabel("应用状态: 正常")
        self.status_bar.addPermanentWidget(self.status_label)
    
    def _apply_theme(self):
        """应用主题设置"""
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background-color: #f0f0f0;
            }
        """)
    
    def _on_tab_changed(self, index):
        """标签页切换事件处理"""
        tab_names = ["代理管理", "模型管理", "能力管理", "监控"]
        if 0 <= index < len(tab_names):
            self.status_bar.showMessage(f"当前标签页: {tab_names[index]}")
    
    def _new_agent(self):
        """新建代理动作"""
        QMessageBox.information(self, "新建代理", "新建代理功能开发中")
    
    def _open_config(self):
        """打开配置动作"""
        QMessageBox.information(self, "打开配置", "打开配置功能开发中")
    
    def _toggle_toolbar(self, checked):
        """切换工具栏显示"""
        self.toolbar.setVisible(checked)
    
    def _toggle_statusbar(self, checked):
        """切换状态栏显示"""
        self.status_bar.setVisible(checked)
    
    def _start_server(self):
        """启动服务器"""
        self.status_bar.showMessage("正在启动A2A服务器...")
        QMessageBox.information(self, "启动服务器", "服务器启动功能开发中")
    
    def _stop_server(self):
        """停止服务器"""
        self.status_bar.showMessage("正在停止A2A服务器...")
        QMessageBox.information(self, "停止服务器", "服务器停止功能开发中")
    
    def _open_settings(self):
        """打开设置"""
        if ConfigDialog is None:
            QMessageBox.warning(self, "配置功能不可用", "配置管理模块导入失败，请检查依赖")
            return
        
        try:
            # 初始化配置管理器
            init_config_manager()
            
            # 创建并显示配置对话框
            config_dialog = ConfigDialog(self)
            config_dialog.config_changed.connect(self._on_config_changed)
            config_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开配置对话框失败: {e}")
    
    def _on_config_changed(self):
        """配置变更事件处理"""
        self.status_bar.showMessage("配置已更新，可能需要重启应用")
        # 这里可以添加配置变更后的处理逻辑
        # 比如重新加载主题、更新界面等
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>AI Agent Desktop</h3>
        <p>版本: 1.0.0</p>
        <p>一个强大的AI代理管理桌面应用</p>
        <p>支持多模型集成和A2A通信</p>
        <p>开发中...</p>
        """
        QMessageBox.about(self, "关于 AI Agent Desktop", about_text)
    
    def closeEvent(self, event):
        """应用关闭事件处理"""
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出AI Agent Desktop吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """应用主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("AI Agent Desktop")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AI Agent Project")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
