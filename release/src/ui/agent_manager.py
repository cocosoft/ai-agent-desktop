"""
代理管理界面
提供代理列表、状态监控、启动/停止等管理功能
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTabWidget, QGroupBox, QFormLayout, QProgressBar, QSplitter, QToolBar,
    QMessageBox, QMenu, QInputDialog, QLineEdit, QTextEdit, QComboBox, QCheckBox,
    QSpinBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QDateTime
from PyQt6.QtGui import QIcon, QFont, QColor, QAction

from ..core.agent_model import AgentRegistry, AgentInstance, AgentStatus, AgentType, AgentPriority
from ..core.capability_model import CapabilityRegistry
from ..core.model_manager import ModelManager


class AgentListWidget(QListWidget):
    """代理列表控件"""
    
    agent_selected = pyqtSignal(object)  # 代理选择信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        self.setMinimumWidth(300)
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def add_agent(self, agent_instance: AgentInstance):
        """添加代理到列表"""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, agent_instance)
        self.update_agent_item(item, agent_instance)
        self.addItem(item)
    
    def update_agent_item(self, item: QListWidgetItem, agent_instance: AgentInstance):
        """更新代理列表项显示"""
        status_icon = self.get_status_icon(agent_instance.status)
        status_text = agent_instance.status.value
        
        item.setText(f"{agent_instance.agent_config.name}\n状态: {status_text}")
        item.setIcon(status_icon)
        
        # 设置状态颜色
        color = self.get_status_color(agent_instance.status)
        item.setForeground(color)
    
    def get_status_icon(self, status: AgentStatus):
        """获取状态图标"""
        # 这里使用文本图标，实际项目中可以使用真实图标
        return QIcon()
    
    def get_status_color(self, status: AgentStatus):
        """获取状态颜色"""
        colors = {
            AgentStatus.STOPPED: QColor("gray"),
            AgentStatus.RUNNING: QColor("green"),
            AgentStatus.ERROR: QColor("red"),
            AgentStatus.STARTING: QColor("orange"),
            AgentStatus.STOPPING: QColor("yellow")
        }
        return colors.get(status, QColor("lightgray"))
    
    def on_selection_changed(self):
        """选择变化处理"""
        selected_items = self.selectedItems()
        if selected_items:
            agent_instance = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.agent_selected.emit(agent_instance)


class AgentStatusWidget(QWidget):
    """代理状态监控控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_instance = None
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        
        # 基本信息组
        info_group = QGroupBox("基本信息")
        info_layout = QFormLayout()
        
        self.name_label = QLabel()
        self.type_label = QLabel()
        self.status_label = QLabel()
        self.priority_label = QLabel()
        
        info_layout.addRow("名称:", self.name_label)
        info_layout.addRow("类型:", self.type_label)
        info_layout.addRow("状态:", self.status_label)
        info_layout.addRow("优先级:", self.priority_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 性能指标组
        metrics_group = QGroupBox("性能指标")
        metrics_layout = QFormLayout()
        
        self.uptime_label = QLabel()
        self.task_count_label = QLabel()
        self.success_rate_label = QLabel()
        self.avg_response_label = QLabel()
        
        metrics_layout.addRow("运行时间:", self.uptime_label)
        metrics_layout.addRow("任务总数:", self.task_count_label)
        metrics_layout.addRow("成功率:", self.success_rate_label)
        metrics_layout.addRow("平均响应:", self.avg_response_label)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # 资源使用组
        resource_group = QGroupBox("资源使用")
        resource_layout = QFormLayout()
        
        self.cpu_usage_bar = QProgressBar()
        self.memory_usage_bar = QProgressBar()
        self.disk_usage_bar = QProgressBar()
        
        resource_layout.addRow("CPU使用:", self.cpu_usage_bar)
        resource_layout.addRow("内存使用:", self.memory_usage_bar)
        resource_layout.addRow("磁盘使用:", self.disk_usage_bar)
        
        resource_group.setLayout(resource_layout)
        layout.addWidget(resource_group)
        
        self.setLayout(layout)
    
    def update_agent_info(self, agent_instance: AgentInstance):
        """更新代理信息"""
        self.agent_instance = agent_instance
        
        # 基本信息
        self.name_label.setText(agent_instance.agent_config.name)
        self.type_label.setText(agent_instance.agent_config.agent_type.value.replace('_', ' ').title())
        self.status_label.setText(agent_instance.status.value)
        self.priority_label.setText(agent_instance.agent_config.priority.value.title())
        
        # 性能指标（简化版本，实际项目中需要实现这些方法）
        self.uptime_label.setText("未运行")
        self.task_count_label.setText("0")
        self.success_rate_label.setText("N/A")
        self.avg_response_label.setText("N/A")
        
        # 资源使用（模拟数据）
        self.cpu_usage_bar.setValue(0)
        self.memory_usage_bar.setValue(0)
        self.disk_usage_bar.setValue(0)


class AgentDetailDialog(QDialog):
    """代理详情对话框"""
    
    def __init__(self, agent_instance: AgentInstance, parent=None):
        super().__init__(parent)
        self.agent_instance = agent_instance
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle(f"代理详情 - {self.agent_instance.agent_config.name}")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 基本信息标签页
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "基本信息")
        
        # 能力配置标签页
        capability_tab = self.create_capability_tab()
        tab_widget.addTab(capability_tab, "能力配置")
        
        # 性能统计标签页
        stats_tab = self.create_stats_tab()
        tab_widget.addTab(stats_tab, "性能统计")
        
        # 日志标签页
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "运行日志")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def create_basic_tab(self):
        """创建基本信息标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        # 基本信息
        layout.addRow("代理ID:", QLabel(self.agent_instance.agent_config.agent_id))
        layout.addRow("名称:", QLabel(self.agent_instance.agent_config.name))
        layout.addRow("描述:", QLabel(self.agent_instance.agent_config.description))
        layout.addRow("类型:", QLabel(self.agent_instance.agent_config.agent_type.value.replace('_', ' ').title()))
        layout.addRow("优先级:", QLabel(self.agent_instance.agent_config.priority.value.title()))
        layout.addRow("状态:", QLabel(self.agent_instance.status.value))
        layout.addRow("最大并发任务:", QLabel(str(self.agent_instance.agent_config.max_concurrent_tasks)))
        layout.addRow("自动启动:", QLabel("是" if self.agent_instance.agent_config.auto_start else "否"))
        
        # 时间信息（简化版本）
        current_time = QDateTime.currentDateTime()
        layout.addRow("创建时间:", QLabel(current_time.toString("yyyy-MM-dd hh:mm:ss")))
        layout.addRow("最后启动:", QLabel("未启动"))
        
        widget.setLayout(layout)
        return widget
    
    def create_capability_tab(self):
        """创建能力配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 能力列表
        capability_list = QListWidget()
        for mapping in self.agent_instance.agent_config.capabilities:
            item_text = f"{mapping.capability_id} → {mapping.model_id}"
            item_text += f" (优先级: {mapping.priority}, 启用: {'是' if mapping.enabled else '否'})"
            item = QListWidgetItem(item_text)
            capability_list.addItem(item)
        
        layout.addWidget(QLabel("已配置的能力:"))
        layout.addWidget(capability_list)
        
        widget.setLayout(layout)
        return widget
    
    def create_stats_tab(self):
        """创建性能统计标签页"""
        widget = QWidget()
        layout = QFormLayout()
        
        # 任务统计（简化版本）
        layout.addRow("总任务数:", QLabel("0"))
        layout.addRow("成功任务:", QLabel("0"))
        layout.addRow("失败任务:", QLabel("0"))
        layout.addRow("成功率:", QLabel("N/A"))
        
        # 响应时间（简化版本）
        layout.addRow("平均响应时间:", QLabel("N/A"))
        layout.addRow("最大响应时间:", QLabel("N/A"))
        layout.addRow("最小响应时间:", QLabel("N/A"))
        
        # 资源使用（简化版本）
        layout.addRow("CPU使用率:", QLabel("0%"))
        layout.addRow("内存使用率:", QLabel("0%"))
        layout.addRow("磁盘使用率:", QLabel("0%"))
        
        widget.setLayout(layout)
        return widget
    
    def create_log_tab(self):
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 日志显示
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        
        # 模拟日志数据
        logs = [
            f"{QDateTime.currentDateTime().toString('hh:mm:ss')} - 代理启动成功",
            f"{QDateTime.currentDateTime().addSecs(-10).toString('hh:mm:ss')} - 处理任务 #123",
            f"{QDateTime.currentDateTime().addSecs(-20).toString('hh:mm:ss')} - 能力初始化完成"
        ]
        log_text.setText("\n".join(logs))
        
        layout.addWidget(QLabel("最近运行日志:"))
        layout.addWidget(log_text)
        
        widget.setLayout(layout)
        return widget


class AgentManager(QWidget):
    """代理管理主界面"""
    
    def __init__(self, agent_registry: AgentRegistry, capability_registry: CapabilityRegistry,
                 model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.agent_registry = agent_registry
        self.capability_registry = capability_registry
        self.model_manager = model_manager
        
        self.setup_ui()
        self.setup_timer()
        self.refresh_agent_list()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout()
        
        # 工具栏
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # 主内容区域
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 代理列表
        self.agent_list = AgentListWidget()
        self.agent_list.agent_selected.connect(self.on_agent_selected)
        splitter.addWidget(self.agent_list)
        
        # 状态面板
        self.status_widget = AgentStatusWidget()
        splitter.addWidget(self.status_widget)
        
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        
        # 创建代理按钮
        create_action = QAction("创建代理", self)
        create_action.triggered.connect(self.create_agent)
        toolbar.addAction(create_action)
        
        toolbar.addSeparator()
        
        # 启动按钮
        start_action = QAction("启动", self)
        start_action.triggered.connect(self.start_agent)
        toolbar.addAction(start_action)
        
        # 停止按钮
        stop_action = QAction("停止", self)
        stop_action.triggered.connect(self.stop_agent)
        toolbar.addAction(stop_action)
        
        # 重启按钮
        restart_action = QAction("重启", self)
        restart_action.triggered.connect(self.restart_agent)
        toolbar.addAction(restart_action)
        
        toolbar.addSeparator()
        
        # 详情按钮
        detail_action = QAction("详情", self)
        detail_action.triggered.connect(self.show_agent_detail)
        toolbar.addAction(detail_action)
        
        # 编辑按钮
        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(self.edit_agent)
        toolbar.addAction(edit_action)
        
        # 删除按钮
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self.delete_agent)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_agent_list)
        toolbar.addAction(refresh_action)
        
        return toolbar
    
    def setup_timer(self):
        """设置定时器"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_agent_list)
        self.refresh_timer.start(5000)  # 5秒刷新一次
    
    def refresh_agent_list(self):
        """刷新代理列表"""
        self.agent_list.clear()
        
        agents = self.agent_registry.list_agents()
        for agent_config in agents:
            # 创建代理实例（简化版本，实际项目中应该从注册表获取）
            agent_instance = AgentInstance(agent_config, agent_config=agent_config)
            if agent_instance:
                self.agent_list.add_agent(agent_instance)
    
    def on_agent_selected(self, agent_instance: AgentInstance):
        """代理选择处理"""
        self.status_widget.update_agent_info(agent_instance)
    
    def create_agent(self):
        """创建代理"""
        from .agent_wizard import AgentCreationWizard
        
        wizard = AgentCreationWizard(self.agent_registry, self.capability_registry, self.model_manager, self)
        wizard.agent_created.connect(self.on_agent_created)
        wizard.exec()
    
    def on_agent_created(self, agent_config):
        """代理创建完成处理"""
        self.refresh_agent_list()
        QMessageBox.information(self, "创建成功", f"代理 '{agent_config.name}' 创建成功！")
    
    def start_agent(self):
        """启动代理"""
        agent_instance = self.get_selected_agent()
        if not agent_instance:
            return
        
        try:
            if self.agent_registry.start_agent(agent_instance.agent_config.agent_id):
                self.refresh_agent_list()
                QMessageBox.information(self, "启动成功", f"代理 '{agent_instance.agent_config.name}' 启动成功")
            else:
                QMessageBox.warning(self, "启动失败", f"代理 '{agent_instance.agent_config.name}' 启动失败")
        except Exception as e:
            QMessageBox.critical(self, "启动错误", f"启动代理时发生错误:\n{str(e)}")
    
    def stop_agent(self):
        """停止代理"""
        agent_instance = self.get_selected_agent()
        if not agent_instance:
            return
        
        try:
            if self.agent_registry.stop_agent(agent_instance.agent_config.agent_id):
                self.refresh_agent_list()
                QMessageBox.information(self, "停止成功", f"代理 '{agent_instance.agent_config.name}' 停止成功")
            else:
                QMessageBox.warning(self, "停止失败", f"代理 '{agent_instance.agent_config.name}' 停止失败")
        except Exception as e:
            QMessageBox.critical(self, "停止错误", f"停止代理时发生错误:\n{str(e)}")
    
    def restart_agent(self):
        """重启代理"""
        agent_instance = self.get_selected_agent()
        if not agent_instance:
            return
        
        try:
            if self.agent_registry.restart_agent(agent_instance.agent_config.agent_id):
                self.refresh_agent_list()
                QMessageBox.information(self, "重启成功", f"代理 '{agent_instance.agent_config.name}' 重启成功")
            else:
                QMessageBox.warning(self, "重启失败", f"代理 '{agent_instance.agent_config.name}' 重启失败")
        except Exception as e:
            QMessageBox.critical(self, "重启错误", f"重启代理时发生错误:\n{str(e)}")
    
    def show_agent_detail(self):
        """显示代理详情"""
        agent_instance = self.get_selected_agent()
        if not agent_instance:
            QMessageBox.warning(self, "选择代理", "请先选择一个代理")
            return
        
        dialog = AgentDetailDialog(agent_instance, self)
        dialog.exec()
    
    def edit_agent(self):
        """编辑代理"""
        agent_instance = self.get_selected_agent()
        if not agent_instance:
            QMessageBox.warning(self, "选择代理", "请先选择一个代理")
            return
        
        # TODO: 实现代理编辑功能
        QMessageBox.information(self, "编辑代理", f"编辑代理 '{agent_instance.agent_config.name}' 功能待实现")
    
    def delete_agent(self):
        """删除代理"""
        agent_instance = self.get_selected_agent()
        if not agent_instance:
            QMessageBox.warning(self, "选择代理", "请先选择一个代理")
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除代理 '{agent_instance.agent_config.name}' 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.agent_registry.unregister_agent(agent_instance.agent_config.agent_id):
                    self.refresh_agent_list()
                    QMessageBox.information(self, "删除成功", f"代理 '{agent_instance.agent_config.name}' 删除成功")
                else:
                    QMessageBox.warning(self, "删除失败", f"代理 '{agent_instance.agent_config.name}' 删除失败")
            except Exception as e:
                QMessageBox.critical(self, "删除错误", f"删除代理时发生错误:\n{str(e)}")
    
    def get_selected_agent(self):
        """获取选中的代理"""
        selected_items = self.agent_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.ItemDataRole.UserRole)
        return None


# 使用示例
def create_agent_manager_demo():
    """创建代理管理界面试例"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 创建必要的管理器实例
    agent_registry = AgentRegistry()
    capability_registry = CapabilityRegistry()
    model_manager = ModelManager()  # 需要实际的模型管理器
    
    # 创建代理管理界面
    manager = AgentManager(agent_registry, capability_registry, model_manager)
    manager.setWindowTitle("代理管理器")
    manager.resize(800, 600)
    manager.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    create_agent_manager_demo()
