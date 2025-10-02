"""
能力管理界面
提供能力列表、搜索、测试、编辑等功能
"""

import sys
import asyncio
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QProgressBar, QMessageBox, QTabWidget, QTextEdit,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox,
    QSplitter, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon

from ..core.capability_model import (
    Capability, CapabilityType, CapabilityStatus, CapabilityRegistry
)
from ..core.capability_discovery import CapabilityDiscovery, DiscoveryStatus
from ..core.model_manager import ModelManager
from ..utils.logger import log_info, log_error


class CapabilityManagerWidget(QWidget):
    """能力管理界面主控件"""
    
    # 信号定义
    capability_selected = pyqtSignal(str)  # 能力ID
    discovery_started = pyqtSignal(str)    # 任务ID
    discovery_completed = pyqtSignal(str)  # 任务ID
    
    def __init__(self, model_manager: ModelManager, capability_registry: CapabilityRegistry):
        super().__init__()
        self.model_manager = model_manager
        self.capability_registry = capability_registry
        self.capability_discovery = CapabilityDiscovery(model_manager, capability_registry)
        
        self.current_capability_id = None
        self.discovery_tasks = {}
        
        self.init_ui()
        self.setup_connections()
        self.refresh_capability_list()
        
        # 设置定时器更新发现任务状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_discovery_status)
        self.status_timer.start(1000)  # 每秒更新一次
    
    def init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout()
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索能力...")
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar_layout.addWidget(QLabel("搜索:"))
        toolbar_layout.addWidget(self.search_input)
        
        # 类型筛选
        self.type_filter = QComboBox()
        self.type_filter.addItem("所有类型", None)
        for capability_type in CapabilityType:
            self.type_filter.addItem(capability_type.value.replace('_', ' ').title(), capability_type)
        self.type_filter.currentIndexChanged.connect(self.on_filter_changed)
        toolbar_layout.addWidget(QLabel("类型:"))
        toolbar_layout.addWidget(self.type_filter)
        
        # 状态筛选
        self.status_filter = QComboBox()
        self.status_filter.addItem("所有状态", None)
        for status in CapabilityStatus:
            self.status_filter.addItem(status.value.title(), status)
        self.status_filter.currentIndexChanged.connect(self.on_filter_changed)
        toolbar_layout.addWidget(QLabel("状态:"))
        toolbar_layout.addWidget(self.status_filter)
        
        toolbar_layout.addStretch()
        
        # 发现按钮
        self.discover_btn = QPushButton("发现能力")
        self.discover_btn.clicked.connect(self.start_capability_discovery)
        toolbar_layout.addWidget(self.discover_btn)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_capability_list)
        toolbar_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(toolbar_layout)
        
        # 分割器：左侧能力列表，右侧详情
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：能力列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 能力列表表格
        self.capability_table = QTableWidget()
        self.capability_table.setColumnCount(5)
        self.capability_table.setHorizontalHeaderLabels([
            "ID", "名称", "类型", "状态", "复杂度"
        ])
        self.capability_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.capability_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.capability_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.capability_table.itemSelectionChanged.connect(self.on_capability_selected)
        
        left_layout.addWidget(QLabel("能力列表"))
        left_layout.addWidget(self.capability_table)
        
        # 发现任务状态
        self.discovery_status_group = QGroupBox("发现任务状态")
        discovery_layout = QVBoxLayout()
        
        self.discovery_progress = QProgressBar()
        self.discovery_progress.setVisible(False)
        discovery_layout.addWidget(self.discovery_progress)
        
        self.discovery_status_label = QLabel("没有运行中的发现任务")
        discovery_layout.addWidget(self.discovery_status_label)
        
        self.discovery_status_group.setLayout(discovery_layout)
        left_layout.addWidget(self.discovery_status_group)
        
        splitter.addWidget(left_widget)
        
        # 右侧：能力详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 能力详情标签页
        self.detail_tabs = QTabWidget()
        
        # 基本信息标签页
        self.basic_info_tab = QWidget()
        self.setup_basic_info_tab()
        self.detail_tabs.addTab(self.basic_info_tab, "基本信息")
        
        # 参数信息标签页
        self.parameters_tab = QWidget()
        self.setup_parameters_tab()
        self.detail_tabs.addTab(self.parameters_tab, "参数")
        
        # 测试信息标签页
        self.tests_tab = QWidget()
        self.setup_tests_tab()
        self.detail_tabs.addTab(self.tests_tab, "测试")
        
        right_layout.addWidget(self.detail_tabs)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("测试能力")
        self.test_btn.clicked.connect(self.test_capability)
        self.test_btn.setEnabled(False)
        button_layout.addWidget(self.test_btn)
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self.edit_capability)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_capability)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        right_layout.addLayout(button_layout)
        
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def setup_basic_info_tab(self):
        """设置基本信息标签页"""
        layout = QFormLayout()
        
        # 能力ID
        self.capability_id_label = QLabel()
        layout.addRow("能力ID:", self.capability_id_label)
        
        # 能力名称
        self.capability_name_label = QLabel()
        layout.addRow("名称:", self.capability_name_label)
        
        # 能力类型
        self.capability_type_label = QLabel()
        layout.addRow("类型:", self.capability_type_label)
        
        # 能力状态
        self.capability_status_label = QLabel()
        layout.addRow("状态:", self.capability_status_label)
        
        # 能力描述
        self.capability_description = QTextEdit()
        self.capability_description.setReadOnly(True)
        self.capability_description.setMaximumHeight(100)
        layout.addRow("描述:", self.capability_description)
        
        # 分类和标签
        self.capability_category_label = QLabel()
        layout.addRow("分类:", self.capability_category_label)
        
        self.capability_tags_label = QLabel()
        layout.addRow("标签:", self.capability_tags_label)
        
        # 复杂度
        self.capability_complexity_label = QLabel()
        layout.addRow("复杂度:", self.capability_complexity_label)
        
        # 使用统计
        self.capability_usage_label = QLabel()
        layout.addRow("使用次数:", self.capability_usage_label)
        
        self.capability_success_rate_label = QLabel()
        layout.addRow("成功率:", self.capability_success_rate_label)
        
        self.basic_info_tab.setLayout(layout)
    
    def setup_parameters_tab(self):
        """设置参数信息标签页"""
        layout = QVBoxLayout()
        
        # 参数表格
        self.parameters_table = QTableWidget()
        self.parameters_table.setColumnCount(6)
        self.parameters_table.setHorizontalHeaderLabels([
            "名称", "类型", "必需", "默认值", "约束", "描述"
        ])
        self.parameters_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(QLabel("输入参数:"))
        layout.addWidget(self.parameters_table)
        
        # 输出表格
        self.outputs_table = QTableWidget()
        self.outputs_table.setColumnCount(4)
        self.outputs_table.setHorizontalHeaderLabels([
            "名称", "类型", "格式", "描述"
        ])
        self.outputs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(QLabel("输出定义:"))
        layout.addWidget(self.outputs_table)
        
        self.parameters_tab.setLayout(layout)
    
    def setup_tests_tab(self):
        """设置测试信息标签页"""
        layout = QVBoxLayout()
        
        # 测试用例表格
        self.tests_table = QTableWidget()
        self.tests_table.setColumnCount(5)
        self.tests_table.setHorizontalHeaderLabels([
            "测试ID", "输入参数", "预期输出", "实际输出", "结果"
        ])
        self.tests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(QLabel("测试用例:"))
        layout.addWidget(self.tests_table)
        
        # 测试结果统计
        stats_layout = QHBoxLayout()
        
        self.total_tests_label = QLabel("总测试: 0")
        stats_layout.addWidget(self.total_tests_label)
        
        self.passed_tests_label = QLabel("通过: 0")
        stats_layout.addWidget(self.passed_tests_label)
        
        self.failed_tests_label = QLabel("失败: 0")
        stats_layout.addWidget(self.failed_tests_label)
        
        self.success_rate_label = QLabel("成功率: 0%")
        stats_layout.addWidget(self.success_rate_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        self.tests_tab.setLayout(layout)
    
    def setup_connections(self):
        """设置信号连接"""
        # 发现任务状态更新信号
        self.discovery_started.connect(self.on_discovery_started)
        self.discovery_completed.connect(self.on_discovery_completed)
    
    def refresh_capability_list(self):
        """刷新能力列表"""
        capabilities = self.capability_registry.get_all_capabilities()
        
        # 应用筛选
        filtered_capabilities = self.filter_capabilities(capabilities)
        
        self.capability_table.setRowCount(len(filtered_capabilities))
        
        for row, capability in enumerate(filtered_capabilities):
            # ID
            id_item = QTableWidgetItem(capability.capability_id)
            id_item.setData(Qt.ItemDataRole.UserRole, capability.capability_id)
            self.capability_table.setItem(row, 0, id_item)
            
            # 名称
            name_item = QTableWidgetItem(capability.name)
            self.capability_table.setItem(row, 1, name_item)
            
            # 类型
            type_item = QTableWidgetItem(capability.capability_type.value)
            self.capability_table.setItem(row, 2, type_item)
            
            # 状态
            status_item = QTableWidgetItem(capability.status.value)
            self.capability_table.setItem(row, 3, status_item)
            
            # 复杂度
            complexity_item = QTableWidgetItem(str(capability.complexity))
            self.capability_table.setItem(row, 4, complexity_item)
    
    def filter_capabilities(self, capabilities: List[Capability]) -> List[Capability]:
        """筛选能力列表"""
        filtered = capabilities
        
        # 搜索筛选
        search_text = self.search_input.text().lower()
        if search_text:
            filtered = [c for c in filtered if 
                       search_text in c.capability_id.lower() or
                       search_text in c.name.lower() or
                       search_text in c.description.lower() or
                       any(search_text in tag.lower() for tag in c.tags)]
        
        # 类型筛选
        type_filter = self.type_filter.currentData()
        if type_filter:
            filtered = [c for c in filtered if c.capability_type == type_filter]
        
        # 状态筛选
        status_filter = self.status_filter.currentData()
        if status_filter:
            filtered = [c for c in filtered if c.status == status_filter]
        
        return filtered
    
    def on_search_changed(self):
        """搜索文本改变"""
        self.refresh_capability_list()
    
    def on_filter_changed(self):
        """筛选条件改变"""
        self.refresh_capability_list()
    
    def on_capability_selected(self):
        """能力选择改变"""
        selected_items = self.capability_table.selectedItems()
        if not selected_items:
            self.clear_capability_details()
            return
        
        capability_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.current_capability_id = capability_id
        
        capability = self.capability_registry.get_capability(capability_id)
        if capability:
            self.show_capability_details(capability)
            self.capability_selected.emit(capability_id)
        
        # 启用操作按钮
        self.test_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def clear_capability_details(self):
        """清空能力详情"""
        self.current_capability_id = None
        
        # 清空基本信息
        self.capability_id_label.setText("")
        self.capability_name_label.setText("")
        self.capability_type_label.setText("")
        self.capability_status_label.setText("")
        self.capability_description.clear()
        self.capability_category_label.setText("")
        self.capability_tags_label.setText("")
        self.capability_complexity_label.setText("")
        self.capability_usage_label.setText("")
        self.capability_success_rate_label.setText("")
        
        # 清空参数表格
        self.parameters_table.setRowCount(0)
        self.outputs_table.setRowCount(0)
        
        # 清空测试表格
        self.tests_table.setRowCount(0)
        self.total_tests_label.setText("总测试: 0")
        self.passed_tests_label.setText("通过: 0")
        self.failed_tests_label.setText("失败: 0")
        self.success_rate_label.setText("成功率: 0%")
        
        # 禁用操作按钮
        self.test_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
    
    def show_capability_details(self, capability: Capability):
        """显示能力详情"""
        # 基本信息
        self.capability_id_label.setText(capability.capability_id)
        self.capability_name_label.setText(capability.name)
        self.capability_type_label.setText(capability.capability_type.value)
        self.capability_status_label.setText(capability.status.value)
        self.capability_description.setText(capability.description)
        self.capability_category_label.setText(capability.category or "未分类")
        self.capability_tags_label.setText(", ".join(capability.tags))
        self.capability_complexity_label.setText(str(capability.complexity))
        
        # 使用统计
        self.capability_usage_label.setText(str(capability.usage_count))
        success_rate = (capability.success_count / capability.usage_count * 100) if capability.usage_count > 0 else 0
        self.capability_success_rate_label.setText(f"{success_rate:.1f}%")
        
        # 参数信息
        self.show_parameters(capability)
        
        # 测试信息
        self.show_tests(capability)
    
    def show_parameters(self, capability: Capability):
        """显示参数信息"""
        # 输入参数
        self.parameters_table.setRowCount(len(capability.parameters))
        for row, param in enumerate(capability.parameters):
            self.parameters_table.setItem(row, 0, QTableWidgetItem(param.name))
            self.parameters_table.setItem(row, 1, QTableWidgetItem(param.type))
            self.parameters_table.setItem(row, 2, QTableWidgetItem("是" if param.required else "否"))
            self.parameters_table.setItem(row, 3, QTableWidgetItem(str(param.default_value or "")))
            self.parameters_table.setItem(row, 4, QTableWidgetItem(str(param.constraints or "")))
            self.parameters_table.setItem(row, 5, QTableWidgetItem(param.description))
        
        # 输出定义
        self.outputs_table.setRowCount(len(capability.outputs))
        for row, output in enumerate(capability.outputs):
            self.outputs_table.setItem(row, 0, QTableWidgetItem(output.name))
            self.outputs_table.setItem(row, 1, QTableWidgetItem(output.type))
            self.outputs_table.setItem(row, 2, QTableWidgetItem(output.format))
            self.outputs_table.setItem(row, 3, QTableWidgetItem(output.description))
    
    def show_tests(self, capability: Capability):
        """显示测试信息"""
        # 测试用例
        self.tests_table.setRowCount(len(capability.tests))
        for row, test in enumerate(capability.tests):
            self.tests_table.setItem(row, 0, QTableWidgetItem(test.test_id))
            self.tests_table.setItem(row, 1, QTableWidgetItem(str(test.input_parameters)))
            self.tests_table.setItem(row, 2, QTableWidgetItem(str(test.expected_output)))
            self.tests_table.setItem(row, 3, QTableWidgetItem(str(test.actual_output or "")))
            self.tests_table.setItem(row, 4, QTableWidgetItem(test.result.value if test.result else "未测试"))
        
        # 测试统计
        total_tests = len(capability.tests)
        passed_tests = len([t for t in capability.tests if t.result and t.result.value == "passed"])
        failed_tests = len([t for t in capability.tests if t.result and t.result.value == "failed"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.total_tests_label.setText(f"总测试: {total_tests}")
        self.passed_tests_label.setText(f"通过: {passed_tests}")
        self.failed_tests_label.setText(f"失败: {failed_tests}")
        self.success_rate_label.setText(f"成功率: {success_rate:.1f}%")
    
    def start_capability_discovery(self):
        """开始能力发现"""
        try:
            # 获取可用模型
            available_models = self.model_manager.get_available_models()
            if not available_models:
                QMessageBox.warning(self, "警告", "没有可用的模型进行能力发现")
                return
            
            # 使用第一个可用模型进行发现
            model_id = available_models[0].model_id
            
            # 异步启动发现任务
            asyncio.create_task(self._async_start_discovery(model_id))
            
        except Exception as e:
            log_error("启动能力发现失败", e)
            QMessageBox.critical(self, "错误", f"启动能力发现失败: {str(e)}")
    
    async def _async_start_discovery(self, model_id: str):
        """异步启动能力发现"""
        try:
            task_id = await self.capability_discovery.discover_model_capabilities(model_id)
            self.discovery_tasks[task_id] = model_id
            self.discovery_started.emit(task_id)
            
        except Exception as e:
            log_error("异步启动能力发现失败", e)
    
    def on_discovery_started(self, task_id: str):
        """发现任务开始"""
        self.discovery_progress.setVisible(True)
        self.discovery_progress.setValue(0)
        self.discovery_status_label.setText(f"发现任务进行中: {task_id}")
        self.discover_btn.setEnabled(False)
    
    def on_discovery_completed(self, task_id: str):
        """发现任务完成"""
        self.discovery_progress.setValue(100)
        self.discovery_status_label.setText(f"发现任务完成: {task_id}")
        
        # 延迟隐藏进度条
        QTimer.singleShot(2000, lambda: self.discovery_progress.setVisible(False))
        self.discover_btn.setEnabled(True)
        
        # 刷新能力列表
        self.refresh_capability_list()
        
        # 显示发现结果
        task = self.capability_discovery.get_task_status(task_id)
        if task:
            discovered_count = len([r for r in task.results if r.discovered_capabilities])
            QMessageBox.information(self, "发现完成", 
                                  f"能力发现任务完成！\n发现 {discovered_count} 个新能力")
    
    def update_discovery_status(self):
        """更新发现任务状态"""
        tasks = self.capability_discovery.get_all_tasks()
        running_tasks = [t for t in tasks if t.status == DiscoveryStatus.RUNNING]
        
        if running_tasks:
            task = running_tasks[0]  # 显示第一个运行中的任务
            self.discovery_progress.setValue(int(task.progress))
            self.discovery_status_label.setText(f"发现任务进行中: {task.task_id} ({task.progress:.1f}%)")
            
            # 检查任务是否完成
            if task.status == DiscoveryStatus.COMPLETED:
                self.discovery_completed.emit(task.task_id)
            elif task.status == DiscoveryStatus.FAILED:
                self.discovery_status_label.setText(f"发现任务失败: {task.task_id}")
                self.discover_btn.setEnabled(True)
        else:
            if not self.discovery_progress.isVisible():
                self.discovery_status_label.setText("没有运行中的发现任务")
    
    def test_capability(self):
        """测试能力"""
        if not self.current_capability_id:
            return
        
        capability = self.capability_registry.get_capability(self.current_capability_id)
        if not capability:
            QMessageBox.warning(self, "警告", "未找到选中的能力")
            return
        
        # 这里可以实现具体的测试逻辑
        QMessageBox.information(self, "测试", f"开始测试能力: {capability.name}")
        
        # TODO: 实现能力测试逻辑
        log_info(f"开始测试能力: {capability.capability_id}")
    
    def edit_capability(self):
        """编辑能力"""
        if not self.current_capability_id:
            return
        
        capability = self.capability_registry.get_capability(self.current_capability_id)
        if not capability:
            QMessageBox.warning(self, "警告", "未找到选中的能力")
            return
        
        # 这里可以实现能力编辑对话框
        QMessageBox.information(self, "编辑", f"编辑能力: {capability.name}")
        
        # TODO: 实现能力编辑对话框
        log_info(f"编辑能力: {capability.capability_id}")
    
    def delete_capability(self):
        """删除能力"""
        if not self.current_capability_id:
            return
        
        capability = self.capability_registry.get_capability(self.current_capability_id)
        if not capability:
            QMessageBox.warning(self, "警告", "未找到选中的能力")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除能力 '{capability.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.capability_registry.unregister_capability(self.current_capability_id)
                self.refresh_capability_list()
                self.clear_capability_details()
                QMessageBox.information(self, "成功", "能力删除成功")
                log_info(f"删除能力: {self.current_capability_id}")
            except Exception as e:
                log_error("删除能力失败", e)
                QMessageBox.critical(self, "错误", f"删除能力失败: {str(e)}")


# 测试函数
def test_capability_manager():
    """测试能力管理界面"""
    try:
        from PyQt6.QtWidgets import QApplication
        from unittest.mock import Mock
        
        # 创建模拟对象
        mock_model_manager = Mock()
        mock_capability_registry = Mock()
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建能力管理界面
        manager = CapabilityManagerWidget(mock_model_manager, mock_capability_registry)
        manager.show()
        
        print("✓ 能力管理界面测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 能力管理界面测试失败: {e}")
        return False


if __name__ == "__main__":
    test_capability_manager()
