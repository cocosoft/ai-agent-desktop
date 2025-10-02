"""
性能监控面板
提供实时性能监控、资源使用监控、性能报警等功能
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
                            QGroupBox, QGridLayout, QProgressBar, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis

from ..core.agent_lifecycle import AgentLifecycleManager, AgentInstance, AgentStatus
from ..core.task_allocator import TaskAllocator
from ..core.model_manager import ModelManager
from ..utils.logger import get_log_manager


class PerformanceMetric(Enum):
    """性能指标枚举"""
    RESPONSE_TIME = "response_time"  # 响应时间
    SUCCESS_RATE = "success_rate"    # 成功率
    THROUGHPUT = "throughput"        # 吞吐量
    CPU_USAGE = "cpu_usage"          # CPU使用率
    MEMORY_USAGE = "memory_usage"    # 内存使用率
    LOAD = "load"                    # 负载


@dataclass
class PerformanceDataPoint:
    """性能数据点"""
    timestamp: datetime
    value: float
    metric: PerformanceMetric
    agent_id: Optional[str] = None
    model_id: Optional[str] = None


@dataclass
class AlertCondition:
    """报警条件"""
    metric: PerformanceMetric
    threshold: float
    operator: str  # ">", "<", ">=", "<=", "=="
    duration: int  # 持续时间（秒）
    severity: str  # "info", "warning", "critical"


@dataclass
class PerformanceAlert:
    """性能报警"""
    alert_id: str
    condition: AlertCondition
    current_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False


class PerformanceDataCollector:
    """性能数据收集器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        self.data_points: List[PerformanceDataPoint] = []
        self.collection_interval = 5  # 收集间隔（秒）
        self.max_data_points = 1000   # 最大数据点数
        
    async def collect_agent_performance(self, agent_instance: AgentInstance) -> List[PerformanceDataPoint]:
        """收集代理性能数据"""
        points = []
        current_time = datetime.now()
        
        # 收集响应时间
        if hasattr(agent_instance, 'avg_response_time'):
            points.append(PerformanceDataPoint(
                timestamp=current_time,
                value=agent_instance.avg_response_time,
                metric=PerformanceMetric.RESPONSE_TIME,
                agent_id=agent_instance.instance_id
            ))
        
        # 收集成功率
        if hasattr(agent_instance, 'successful_tasks') and hasattr(agent_instance, 'total_tasks'):
            if agent_instance.total_tasks > 0:
                success_rate = agent_instance.successful_tasks / agent_instance.total_tasks
                points.append(PerformanceDataPoint(
                    timestamp=current_time,
                    value=success_rate,
                    metric=PerformanceMetric.SUCCESS_RATE,
                    agent_id=agent_instance.instance_id
                ))
        
        # 收集负载
        points.append(PerformanceDataPoint(
            timestamp=current_time,
            value=agent_instance.current_tasks,
            metric=PerformanceMetric.LOAD,
            agent_id=agent_instance.instance_id
        ))
        
        # 收集资源使用
        if hasattr(agent_instance, 'cpu_usage'):
            points.append(PerformanceDataPoint(
                timestamp=current_time,
                value=agent_instance.cpu_usage,
                metric=PerformanceMetric.CPU_USAGE,
                agent_id=agent_instance.instance_id
            ))
        
        if hasattr(agent_instance, 'memory_usage'):
            points.append(PerformanceDataPoint(
                timestamp=current_time,
                value=agent_instance.memory_usage,
                metric=PerformanceMetric.MEMORY_USAGE,
                agent_id=agent_instance.instance_id
            ))
        
        return points
    
    async def collect_system_performance(self) -> List[PerformanceDataPoint]:
        """收集系统性能数据"""
        points = []
        current_time = datetime.now()
        
        # 这里可以添加系统级别的性能数据收集
        # 例如：总吞吐量、系统负载等
        
        return points
    
    def add_data_points(self, points: List[PerformanceDataPoint]):
        """添加数据点"""
        self.data_points.extend(points)
        
        # 限制数据点数量
        if len(self.data_points) > self.max_data_points:
            self.data_points = self.data_points[-self.max_data_points:]
    
    def get_recent_data(self, metric: PerformanceMetric, agent_id: Optional[str] = None, 
                       hours: int = 1) -> List[PerformanceDataPoint]:
        """获取最近的数据点"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_points = [
            point for point in self.data_points
            if point.metric == metric and point.timestamp >= cutoff_time
        ]
        
        if agent_id:
            filtered_points = [point for point in filtered_points if point.agent_id == agent_id]
        
        return filtered_points
    
    def get_statistics(self, metric: PerformanceMetric, agent_id: Optional[str] = None,
                      hours: int = 1) -> Dict[str, float]:
        """获取统计信息"""
        data_points = self.get_recent_data(metric, agent_id, hours)
        
        if not data_points:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'avg': 0,
                'latest': 0
            }
        
        values = [point.value for point in data_points]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1] if values else 0
        }


class AlertManager:
    """报警管理器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        self.conditions: List[AlertCondition] = []
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
        
    def add_condition(self, condition: AlertCondition):
        """添加报警条件"""
        self.conditions.append(condition)
        
    def remove_condition(self, condition_id: str):
        """移除报警条件"""
        self.conditions = [c for c in self.conditions if getattr(c, 'condition_id', '') != condition_id]
        
    def check_conditions(self, data_collector: PerformanceDataCollector):
        """检查报警条件"""
        current_time = datetime.now()
        
        for condition in self.conditions:
            # 获取最近的数据 - 将duration（秒）转换为hours
            hours = condition.duration / 3600  # 转换为小时
            data_points = data_collector.get_recent_data(
                condition.metric, 
                hours=hours
            )
            
            if not data_points:
                continue
                
            # 检查条件
            values = [point.value for point in data_points]
            current_value = values[-1] if values else 0
            
            condition_met = False
            if condition.operator == ">":
                condition_met = all(v > condition.threshold for v in values)
            elif condition.operator == "<":
                condition_met = all(v < condition.threshold for v in values)
            elif condition.operator == ">=":
                condition_met = all(v >= condition.threshold for v in values)
            elif condition.operator == "<=":
                condition_met = all(v <= condition.threshold for v in values)
            elif condition.operator == "==":
                condition_met = all(v == condition.threshold for v in values)
            
            alert_id = f"{condition.metric.value}_{condition.operator}_{condition.threshold}"
            
            if condition_met and alert_id not in self.active_alerts:
                # 触发新报警
                alert = PerformanceAlert(
                    alert_id=alert_id,
                    condition=condition,
                    current_value=current_value,
                    triggered_at=current_time
                )
                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
                
                self.logger.warning(
                    f"性能报警触发: {condition.metric.value} {condition.operator} {condition.threshold}, "
                    f"当前值: {current_value}"
                )
                
            elif not condition_met and alert_id in self.active_alerts:
                # 解除报警
                alert = self.active_alerts[alert_id]
                alert.resolved_at = current_time
                del self.active_alerts[alert_id]
                
                self.logger.info(
                    f"性能报警解除: {condition.metric.value} {condition.operator} {condition.threshold}"
                )
    
    def acknowledge_alert(self, alert_id: str):
        """确认报警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """获取活跃报警"""
        return list(self.active_alerts.values())
    
    def get_recent_alerts(self, hours: int = 24) -> List[PerformanceAlert]:
        """获取最近报警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.triggered_at >= cutoff_time]


class PerformanceChartWidget(QWidget):
    """性能图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_collector = None
        self.chart = QChart()
        self.chart_view = QChartView(self.chart)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.addWidget(self.chart_view)
        
        # 设置图表样式
        self.chart.setTitle("性能监控图表")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
    def update_chart(self, metric: PerformanceMetric, agent_id: Optional[str] = None, hours: int = 1):
        """更新图表"""
        if not self.data_collector:
            return
            
        # 清除现有系列
        self.chart.removeAllSeries()
        
        # 获取数据
        data_points = self.data_collector.get_recent_data(metric, agent_id, hours)
        
        if not data_points:
            return
            
        # 创建系列
        series = QLineSeries()
        series.setName(f"{metric.value} - {agent_id or 'System'}")
        
        # 添加数据点
        for point in data_points:
            # 将时间转换为毫秒时间戳
            timestamp_ms = int(point.timestamp.timestamp() * 1000)
            series.append(timestamp_ms, point.value)
        
        # 添加到图表
        self.chart.addSeries(series)
        
        # 设置坐标轴
        axis_x = QDateTimeAxis()
        axis_x.setFormat("hh:mm:ss")
        axis_x.setTitleText("时间")
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText(metric.value)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        # 自动调整坐标轴范围
        values = [point.value for point in data_points]
        if values:
            axis_y.setRange(min(values) * 0.9, max(values) * 1.1)


class PerformanceStatsWidget(QWidget):
    """性能统计组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_collector = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QGridLayout(self)
        
        # 创建统计标签
        self.labels = {}
        metrics = [
            PerformanceMetric.RESPONSE_TIME,
            PerformanceMetric.SUCCESS_RATE,
            PerformanceMetric.THROUGHPUT,
            PerformanceMetric.CPU_USAGE,
            PerformanceMetric.MEMORY_USAGE,
            PerformanceMetric.LOAD
        ]
        
        for i, metric in enumerate(metrics):
            # 指标名称标签
            name_label = QLabel(f"{metric.value}:")
            name_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(name_label, i, 0)
            
            # 统计值标签
            value_label = QLabel("N/A")
            value_label.setStyleSheet("color: #2E86AB;")
            layout.addWidget(value_label, i, 1)
            
            self.labels[metric] = value_label
        
    def update_stats(self, agent_id: Optional[str] = None):
        """更新统计信息"""
        if not self.data_collector:
            return
            
        for metric, label in self.labels.items():
            stats = self.data_collector.get_statistics(metric, agent_id)
            
            if stats['count'] > 0:
                if metric == PerformanceMetric.SUCCESS_RATE:
                    text = f"{stats['latest']:.1%} (平均: {stats['avg']:.1%})"
                else:
                    text = f"{stats['latest']:.2f} (平均: {stats['avg']:.2f})"
            else:
                text = "无数据"
                
            label.setText(text)


class AlertWidget(QWidget):
    """报警组件"""
    
    alert_acknowledged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.alert_manager = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 报警表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "指标", "条件", "当前值", "触发时间", "状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.acknowledge_btn = QPushButton("确认选中报警")
        self.acknowledge_btn.clicked.connect(self.acknowledge_selected)
        button_layout.addWidget(self.acknowledge_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def update_alerts(self):
        """更新报警显示"""
        if not self.alert_manager:
            return
            
        alerts = self.alert_manager.get_active_alerts()
        self.table.setRowCount(len(alerts))
        
        for row, alert in enumerate(alerts):
            # 指标
            self.table.setItem(row, 0, QTableWidgetItem(alert.condition.metric.value))
            
            # 条件
            condition_text = f"{alert.condition.operator} {alert.condition.threshold}"
            self.table.setItem(row, 1, QTableWidgetItem(condition_text))
            
            # 当前值
            self.table.setItem(row, 2, QTableWidgetItem(f"{alert.current_value:.2f}"))
            
            # 触发时间
            time_text = alert.triggered_at.strftime("%H:%M:%S")
            self.table.setItem(row, 3, QTableWidgetItem(time_text))
            
            # 状态
            status = "已确认" if alert.acknowledged else "活跃"
            status_item = QTableWidgetItem(status)
            if not alert.acknowledged:
                status_item.setBackground(QColor(255, 200, 200))  # 红色背景
            self.table.setItem(row, 4, status_item)
    
    def acknowledge_selected(self):
        """确认选中的报警"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
            
        # 获取选中的报警ID
        row = selected_items[0].row()
        if row >= 0 and row < self.table.rowCount():
            metric_item = self.table.item(row, 0)
            condition_item = self.table.item(row, 1)
            
            if metric_item and condition_item:
                # 这里需要根据实际情况构建alert_id
                # 简化实现：使用行索引
                alert_id = f"alert_{row}"
                self.alert_acknowledged.emit(alert_id)


class PerformanceMonitorWidget(QWidget):
    """性能监控面板主组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_collector = PerformanceDataCollector()
        self.alert_manager = AlertManager()
        self.collection_timer = QTimer()
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 代理选择
        control_layout.addWidget(QLabel("监控代理:"))
        self.agent_combo = QComboBox()
        self.agent_combo.addItem("所有代理", None)
        control_layout.addWidget(self.agent_combo)
        
        # 时间范围选择
        control_layout.addWidget(QLabel("时间范围:"))
        self.time_combo = QComboBox()
        self.time_combo.addItem("1小时", 1)
        self.time_combo.addItem("6小时", 6)
        self.time_combo.addItem("24小时", 24)
        control_layout.addWidget(self.time_combo)
        
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：统计信息
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 性能统计
        self.stats_widget = PerformanceStatsWidget()
        self.stats_widget.data_collector = self.data_collector
        left_layout.addWidget(self.stats_widget)
        
        # 报警组件
        alert_group = QGroupBox("性能报警")
        alert_layout = QVBoxLayout(alert_group)
        self.alert_widget = AlertWidget()
        self.alert_widget.alert_manager = self.alert_manager
        self.alert_widget.alert_acknowledged.connect(self.alert_manager.acknowledge_alert)
        alert_layout.addWidget(self.alert_widget)
        left_layout.addWidget(alert_group)
        
        splitter.addWidget(left_widget)
        
        # 右侧：图表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 图表选择
        chart_control_layout = QHBoxLayout()
        chart_control_layout.addWidget(QLabel("监控指标:"))
        self.metric_combo = QComboBox()
        for metric in PerformanceMetric:
            self.metric_combo.addItem(metric.value, metric)
        chart_control_layout.addWidget(self.metric_combo)
        
        self.refresh_btn = QPushButton("刷新图表")
        self.refresh_btn.clicked.connect(self.refresh_chart)
        chart_control_layout.addWidget(self.refresh_btn)
        
        chart_control_layout.addStretch()
        right_layout.addLayout(chart_control_layout)
        
        # 性能图表
        self.chart_widget = PerformanceChartWidget()
        self.chart_widget.data_collector = self.data_collector
        right_layout.addWidget(self.chart_widget)
        
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
        # 连接信号
        self.agent_combo.currentIndexChanged.connect(self.on_agent_changed)
        self.time_combo.currentIndexChanged.connect(self.on_time_changed)
        self.metric_combo.currentIndexChanged.connect(self.on_metric_changed)
        
    def setup_timers(self):
        """设置定时器"""
        # 数据收集定时器
        self.collection_timer.timeout.connect(self.collect_data)
        self.collection_timer.start(5000)  # 5秒收集一次
        
        # 报警检查定时器
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.check_alerts)
        self.alert_timer.start(10000)  # 10秒检查一次
        
        # 界面更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(2000)  # 2秒更新一次
        
    def collect_data(self):
        """收集性能数据"""
        # 这里应该从实际的代理管理器获取代理实例
        # 简化实现：创建模拟数据
        pass
        
    def check_alerts(self):
        """检查报警条件"""
        self.alert_manager.check_conditions(self.data_collector)
        
    def update_ui(self):
        """更新UI"""
        self.stats_widget.update_stats(self.get_selected_agent())
        self.alert_widget.update_alerts()
        
    def get_selected_agent(self) -> Optional[str]:
        """获取选中的代理ID"""
        return self.agent_combo.currentData()
        
    def get_selected_time_range(self) -> int:
        """获取选中的时间范围"""
        return self.time_combo.currentData()
        
    def get_selected_metric(self) -> PerformanceMetric:
        """获取选中的指标"""
        return self.metric_combo.currentData()
        
    def on_agent_changed(self):
        """代理选择改变"""
        self.stats_widget.update_stats(self.get_selected_agent())
        self.refresh_chart()
        
    def on_time_changed(self):
        """时间范围改变"""
        self.refresh_chart()
        
    def on_metric_changed(self):
        """指标选择改变"""
        self.refresh_chart()
        
    def refresh_chart(self):
        """刷新图表"""
        agent_id = self.get_selected_agent()
        metric = self.get_selected_metric()
        hours = self.get_selected_time_range()
        
        self.chart_widget.update_chart(metric, agent_id, hours)
        
    def add_agents(self, agents: List[AgentInstance]):
        """添加代理到选择列表"""
        self.agent_combo.clear()
        self.agent_combo.addItem("所有代理", None)
        
        for agent in agents:
            self.agent_combo.addItem(f"{agent.instance_id} ({agent.status.value})", agent.instance_id)
        
    def add_default_alert_conditions(self):
        """添加默认报警条件"""
        # 响应时间过长
        self.alert_manager.add_condition(AlertCondition(
            metric=PerformanceMetric.RESPONSE_TIME,
            threshold=10.0,
            operator=">",
            duration=30,
            severity="warning"
        ))
        
        # 成功率过低
        self.alert_manager.add_condition(AlertCondition(
            metric=PerformanceMetric.SUCCESS_RATE,
            threshold=0.8,
            operator="<",
            duration=60,
            severity="critical"
        ))
        
        # 负载过高
        self.alert_manager.add_condition(AlertCondition(
            metric=PerformanceMetric.LOAD,
            threshold=8,
            operator=">",
            duration=30,
            severity="warning"
        ))
        
        # CPU使用率过高
        self.alert_manager.add_condition(AlertCondition(
            metric=PerformanceMetric.CPU_USAGE,
            threshold=80.0,
            operator=">",
            duration=60,
            severity="warning"
        ))
        
        # 内存使用率过高
        self.alert_manager.add_condition(AlertCondition(
            metric=PerformanceMetric.MEMORY_USAGE,
            threshold=85.0,
            operator=">",
            duration=60,
            severity="critical"
        ))
