"""
性能分析工具
提供性能数据分析和优化建议
"""

import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
                            QGroupBox, QGridLayout, QProgressBar, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QFrame,
                            QTextEdit, QLineEdit, QListWidget, QListWidgetItem,
                            QTreeWidget, QTreeWidgetItem, QApplication, QMenu,
                            QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor, QAction, QIcon
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis

from ..core.agent_lifecycle import AgentLifecycleManager
from ..core.model_manager import ModelManager
from ..core.task_allocator import TaskAllocator
from ..utils.logger import get_log_manager
from ..utils.status_monitor import StatusMonitor


class PerformanceMetric(Enum):
    """性能指标"""
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    LOAD = "load"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceIssue:
    """性能问题"""
    issue_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_components: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        
    def analyze_response_time(self, metrics: Dict[str, Any]) -> Optional[PerformanceIssue]:
        """分析响应时间"""
        avg_response_time = metrics.get('avg_response_time', 0)
        max_response_time = metrics.get('max_response_time', 0)
        
        if avg_response_time > 10.0:  # 超过10秒
            return PerformanceIssue(
                issue_type="high_response_time",
                severity="high" if avg_response_time > 30.0 else "medium",
                description=f"平均响应时间过高: {avg_response_time:.2f}秒",
                affected_components=["模型调用", "任务处理"],
                recommendations=[
                    "检查模型服务器连接",
                    "优化任务处理逻辑",
                    "考虑增加模型实例",
                    "检查网络延迟"
                ],
                metrics={'avg_response_time': avg_response_time, 'max_response_time': max_response_time}
            )
        return None
        
    def analyze_success_rate(self, metrics: Dict[str, Any]) -> Optional[PerformanceIssue]:
        """分析成功率"""
        success_rate = metrics.get('success_rate', 1.0)
        
        if success_rate < 0.8:  # 成功率低于80%
            return PerformanceIssue(
                issue_type="low_success_rate",
                severity="critical" if success_rate < 0.5 else "high",
                description=f"成功率过低: {success_rate:.1%}",
                affected_components=["模型调用", "任务执行"],
                recommendations=[
                    "检查模型配置",
                    "验证输入数据格式",
                    "检查API密钥和配额",
                    "增加错误重试机制"
                ],
                metrics={'success_rate': success_rate}
            )
        return None
        
    def analyze_cpu_usage(self, metrics: Dict[str, Any]) -> Optional[PerformanceIssue]:
        """分析CPU使用率"""
        cpu_usage = metrics.get('cpu_usage', 0)
        
        if cpu_usage > 80.0:  # CPU使用率超过80%
            return PerformanceIssue(
                issue_type="high_cpu_usage",
                severity="high" if cpu_usage > 90.0 else "medium",
                description=f"CPU使用率过高: {cpu_usage:.1f}%",
                affected_components=["系统资源"],
                recommendations=[
                    "优化代码性能",
                    "减少并发任务数",
                    "检查内存泄漏",
                    "考虑升级硬件"
                ],
                metrics={'cpu_usage': cpu_usage}
            )
        return None
        
    def analyze_memory_usage(self, metrics: Dict[str, Any]) -> Optional[PerformanceIssue]:
        """分析内存使用率"""
        memory_usage = metrics.get('memory_usage', 0)
        
        if memory_usage > 85.0:  # 内存使用率超过85%
            return PerformanceIssue(
                issue_type="high_memory_usage",
                severity="critical" if memory_usage > 95.0 else "high",
                description=f"内存使用率过高: {memory_usage:.1f}%",
                affected_components=["系统资源"],
                recommendations=[
                    "检查内存泄漏",
                    "优化数据结构",
                    "减少缓存大小",
                    "增加系统内存"
                ],
                metrics={'memory_usage': memory_usage}
            )
        return None
        
    def analyze_load(self, metrics: Dict[str, Any]) -> Optional[PerformanceIssue]:
        """分析负载"""
        current_load = metrics.get('current_load', 0)
        max_load = metrics.get('max_load', 10)
        
        if current_load > max_load * 0.8:  # 负载超过最大负载的80%
            return PerformanceIssue(
                issue_type="high_load",
                severity="high" if current_load >= max_load else "medium",
                description=f"系统负载过高: {current_load}/{max_load}",
                affected_components=["任务处理", "资源分配"],
                recommendations=[
                    "增加代理实例",
                    "优化任务分配策略",
                    "减少并发任务数",
                    "升级系统配置"
                ],
                metrics={'current_load': current_load, 'max_load': max_load}
            )
        return None
        
    def analyze_error_rate(self, metrics: Dict[str, Any]) -> Optional[PerformanceIssue]:
        """分析错误率"""
        error_rate = metrics.get('error_rate', 0)
        
        if error_rate > 0.1:  # 错误率超过10%
            return PerformanceIssue(
                issue_type="high_error_rate",
                severity="critical" if error_rate > 0.3 else "high",
                description=f"错误率过高: {error_rate:.1%}",
                affected_components=["系统稳定性"],
                recommendations=[
                    "检查错误日志",
                    "增加错误处理机制",
                    "验证输入数据",
                    "检查外部服务状态"
                ],
                metrics={'error_rate': error_rate}
            )
        return None
        
    def analyze_performance(self, metrics: Dict[str, Any]) -> List[PerformanceIssue]:
        """分析性能"""
        issues = []
        
        analyzers = [
            self.analyze_response_time,
            self.analyze_success_rate,
            self.analyze_cpu_usage,
            self.analyze_memory_usage,
            self.analyze_load,
            self.analyze_error_rate
        ]
        
        for analyzer in analyzers:
            issue = analyzer(metrics)
            if issue:
                issues.append(issue)
                
        return issues


class PerformanceTrendAnalyzer:
    """性能趋势分析器"""
    
    def __init__(self):
        self.history_data: List[Dict[str, Any]] = []
        self.max_history = 1000
        
    def add_data_point(self, metrics: Dict[str, Any]):
        """添加数据点"""
        data_point = {
            'timestamp': datetime.now(),
            'metrics': metrics.copy()
        }
        self.history_data.append(data_point)
        
        # 限制历史数据数量
        if len(self.history_data) > self.max_history:
            self.history_data = self.history_data[-self.max_history:]
            
    def get_trend(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """获取趋势分析"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            point for point in self.history_data
            if point['timestamp'] >= cutoff_time
        ]
        
        if not recent_data:
            return {'trend': 'unknown', 'change': 0}
            
        values = [point['metrics'].get(metric_name, 0) for point in recent_data]
        
        if len(values) < 2:
            return {'trend': 'stable', 'change': 0}
            
        # 计算趋势
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        
        change = avg_second - avg_first
        change_percent = (change / avg_first * 100) if avg_first > 0 else 0
        
        if abs(change_percent) < 5:
            trend = 'stable'
        elif change_percent > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
            
        return {
            'trend': trend,
            'change': change,
            'change_percent': change_percent,
            'current_value': values[-1],
            'min_value': min(values),
            'max_value': max(values),
            'avg_value': sum(values) / len(values)
        }


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.optimization_history: List[Dict[str, Any]] = []
        
    def generate_optimization_plan(self, issues: List[PerformanceIssue]) -> Dict[str, Any]:
        """生成优化计划"""
        plan = {
            'generated_at': datetime.now(),
            'total_issues': len(issues),
            'critical_issues': len([i for i in issues if i.severity == 'critical']),
            'high_issues': len([i for i in issues if i.severity == 'high']),
            'medium_issues': len([i for i in issues if i.severity == 'medium']),
            'low_issues': len([i for i in issues if i.severity == 'low']),
            'optimizations': []
        }
        
        # 按优先级排序问题
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.severity, 0), reverse=True)
        
        for issue in sorted_issues:
            optimization = {
                'issue_type': issue.issue_type,
                'severity': issue.severity,
                'description': issue.description,
                'recommendations': issue.recommendations,
                'estimated_impact': self.estimate_impact(issue),
                'implementation_effort': self.estimate_effort(issue)
            }
            plan['optimizations'].append(optimization)
            
        return plan
        
    def estimate_impact(self, issue: PerformanceIssue) -> str:
        """估计影响"""
        impact_map = {
            'critical': '非常高',
            'high': '高',
            'medium': '中等',
            'low': '低'
        }
        return impact_map.get(issue.severity, '未知')
        
    def estimate_effort(self, issue: PerformanceIssue) -> str:
        """估计实施难度"""
        effort_map = {
            'critical': '复杂',
            'high': '中等',
            'medium': '简单',
            'low': '非常容易'
        }
        return effort_map.get(issue.severity, '未知')


class PerformanceAnalyzerWidget(QWidget):
    """性能分析器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = PerformanceAnalyzer()
        self.trend_analyzer = PerformanceTrendAnalyzer()
        self.optimizer = PerformanceOptimizer()
        self.current_issues: List[PerformanceIssue] = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("分析性能")
        toolbar_layout.addWidget(self.analyze_btn)
        
        self.export_btn = QPushButton("导出报告")
        toolbar_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("清空")
        toolbar_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addStretch()
        
        # 自动分析
        self.auto_analyze_check = QCheckBox("自动分析")
        toolbar_layout.addWidget(self.auto_analyze_check)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(30, 3600)
        self.interval_spin.setValue(300)
        self.interval_spin.setSuffix(" 秒")
        toolbar_layout.addWidget(QLabel("间隔:"))
        toolbar_layout.addWidget(self.interval_spin)
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 问题分析标签页
        self.issues_tab = QWidget()
        self.setup_issues_tab()
        self.tab_widget.addTab(self.issues_tab, "性能问题")
        
        # 趋势分析标签页
        self.trends_tab = QWidget()
        self.setup_trends_tab()
        self.tab_widget.addTab(self.trends_tab, "趋势分析")
        
        # 优化建议标签页
        self.optimization_tab = QWidget()
        self.setup_optimization_tab()
        self.tab_widget.addTab(self.optimization_tab, "优化建议")
        
        main_layout.addWidget(self.tab_widget)
        
    def setup_issues_tab(self):
        """设置问题分析标签页"""
        layout = QVBoxLayout(self.issues_tab)
        
        # 问题表格
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(5)
        self.issues_table.setHorizontalHeaderLabels([
            "问题类型", "严重程度", "描述", "影响组件", "状态"
        ])
        self.issues_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.issues_table)
        
        # 问题详情
        detail_group = QGroupBox("问题详情")
        detail_layout = QVBoxLayout(detail_group)
        
        self.issue_detail_text = QTextEdit()
        self.issue_detail_text.setReadOnly(True)
        detail_layout.addWidget(self.issue_detail_text)
        
        layout.addWidget(detail_group)
        
    def setup_trends_tab(self):
        """设置趋势分析标签页"""
        layout = QVBoxLayout(self.trends_tab)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        control_layout.addWidget(QLabel("指标:"))
        self.metric_combo = QComboBox()
        for metric in PerformanceMetric:
            self.metric_combo.addItem(metric.value.replace('_', ' ').title(), metric)
        control_layout.addWidget(self.metric_combo)
        
        control_layout.addWidget(QLabel("时间范围:"))
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItem("1小时", 1)
        self.time_range_combo.addItem("6小时", 6)
        self.time_range_combo.addItem("24小时", 24)
        self.time_range_combo.addItem("7天", 168)
        control_layout.addWidget(self.time_range_combo)
        
        self.update_trend_btn = QPushButton("更新趋势")
        control_layout.addWidget(self.update_trend_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 趋势图表
        self.trend_chart = QChart()
        self.trend_chart_view = QChartView(self.trend_chart)
        layout.addWidget(self.trend_chart_view)
        
        # 趋势统计
        stats_layout = QHBoxLayout()
        
        self.trend_label = QLabel("趋势: 未知")
        stats_layout.addWidget(self.trend_label)
        
        self.change_label = QLabel("变化: 0%")
        stats_layout.addWidget(self.change_label)
        
        self.current_value_label = QLabel("当前值: 0")
        stats_layout.addWidget(self.current_value_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
    def setup_optimization_tab(self):
        """设置优化建议标签页"""
        layout = QVBoxLayout(self.optimization_tab)
        
        # 优化计划
        self.optimization_text = QTextEdit()
        self.optimization_text.setReadOnly(True)
        self.optimization_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.optimization_text)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.generate_plan_btn = QPushButton("生成优化计划")
        button_layout.addWidget(self.generate_plan_btn)
        
        self.export_plan_btn = QPushButton("导出计划")
        button_layout.addWidget(self.export_plan_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
    def setup_connections(self):
        """设置信号连接"""
        self.analyze_btn.clicked.connect(self.analyze_performance)
        self.export_btn.clicked.connect(self.export_report)
        self.clear_btn.clicked.connect(self.clear_analysis)
        self.auto_analyze_check.stateChanged.connect(self.toggle_auto_analyze)
        self.update_trend_btn.clicked.connect(self.update_trend_analysis)
        self.generate_plan_btn.clicked.connect(self.generate_optimization_plan)
        self.export_plan_btn.clicked.connect(self.export_optimization_plan)
        self.issues_table.itemSelectionChanged.connect(self.on_issue_selected)
        
    def analyze_performance(self):
        """分析性能"""
        # 这里应该从实际的性能监控器获取数据
        # 简化实现：使用模拟数据
        mock_metrics = {
            'avg_response_time': 15.5,
            'max_response_time': 45.2,
            'success_rate': 0.75,
            'cpu_usage': 85.0,
            'memory_usage': 90.0,
            'current_load': 8,
            'max_load': 10,
            'error_rate': 0.25
        }
        
        # 添加数据点到趋势分析器
        self.trend_analyzer.add_data_point(mock_metrics)
        
        # 分析性能问题
        issues = self.analyzer.analyze_performance(mock_metrics)
        self.current_issues = issues
        
        # 更新UI
        self.update_issues_table()
        self.update_trend_analysis()
        
        # 显示分析结果
        if issues:
            QMessageBox.information(self, "分析完成", 
                                  f"发现 {len(issues)} 个性能问题")
        else:
            QMessageBox.information(self, "分析完成", "未发现性能问题")
            
    def update_issues_table(self):
        """更新问题表格"""
        self.issues_table.setRowCount(len(self.current_issues))
        
        for row, issue in enumerate(self.current_issues):
            # 问题类型
            self.issues_table.setItem(row, 0, QTableWidgetItem(issue.issue_type))
            
            # 严重程度
            severity_item = QTableWidgetItem(issue.severity)
            # 根据严重程度设置颜色
            if issue.severity == 'critical':
                severity_item.setBackground(QColor(255, 100, 100))
            elif issue.severity == 'high':
                severity_item.setBackground(QColor(255, 200, 100))
            elif issue.severity == 'medium':
                severity_item.setBackground(QColor(255, 255, 100))
            else:
                severity_item.setBackground(QColor(200, 255, 200))
            self.issues_table.setItem(row, 1, severity_item)
            
            # 描述
            self.issues_table.setItem(row, 2, QTableWidgetItem(issue.description))
            
            # 影响组件
            components_text = ", ".join(issue.affected_components)
            self.issues_table.setItem(row, 3, QTableWidgetItem(components_text))
            
            # 状态
            self.issues_table.setItem(row, 4, QTableWidgetItem("待处理"))
            
    def on_issue_selected(self):
        """问题选中事件"""
        selected_items = self.issues_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        if row < len(self.current_issues):
            issue = self.current_issues[row]
            self.show_issue_details(issue)
            
    def show_issue_details(self, issue: PerformanceIssue):
        """显示问题详情"""
        detail_text = f"问题类型: {issue.issue_type}\n"
        detail_text += f"严重程度: {issue.severity}\n"
        detail_text += f"描述: {issue.description}\n\n"
        
        detail_text += "影响组件:\n"
        for component in issue.affected_components:
            detail_text += f"  - {component}\n"
            
        detail_text += "\n优化建议:\n"
        for i, recommendation in enumerate(issue.recommendations, 1):
            detail_text += f"  {i}. {recommendation}\n"
            
        detail_text += "\n相关指标:\n"
        for key, value in issue.metrics.items():
            detail_text += f"  {key}: {value}\n"
            
        self.issue_detail_text.setText(detail_text)
        
    def update_trend_analysis(self):
        """更新趋势分析"""
        metric = self.metric_combo.currentData()
        hours = self.time_range_combo.currentData()
        
        if not metric:
            return
            
        trend = self.trend_analyzer.get_trend(metric.value, hours)
        
        # 更新趋势标签
        trend_text = f"趋势: {trend['trend']}"
        if trend['trend'] == 'increasing':
            trend_text += " ↗"
        elif trend['trend'] == 'decreasing':
            trend_text += " ↘"
        else:
            trend_text += " →"
        self.trend_label.setText(trend_text)
        
        # 更新变化标签
        change_text = f"变化: {trend['change_percent']:+.1f}%"
        self.change_label.setText(change_text)
        
        # 更新当前值标签
        current_text = f"当前值: {trend['current_value']:.2f}"
        self.current_value_label.setText(current_text)
        
        # 更新图表
        self.update_trend_chart(metric.value, hours)
        
    def update_trend_chart(self, metric_name: str, hours: int):
        """更新趋势图表"""
        self.trend_chart.removeAllSeries()
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            point for point in self.trend_analyzer.history_data
            if point['timestamp'] >= cutoff_time
        ]
        
        if not recent_data:
            return
            
        # 创建系列
        series = QLineSeries()
        series.setName(metric_name.replace('_', ' ').title())
        
        # 添加数据点
        for point in recent_data:
            timestamp_ms = int(point['timestamp'].timestamp() * 1000)
            value = point['metrics'].get(metric_name, 0)
            series.append(timestamp_ms, value)
            
        # 添加到图表
        self.trend_chart.addSeries(series)
        
        # 设置坐标轴
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MM-dd HH:mm")
        axis_x.setTitleText("时间")
        self.trend_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText(metric_name.replace('_', ' ').title())
        self.trend_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        # 设置图表标题
        self.trend_chart.setTitle(f"{metric_name.replace('_', ' ').title()} 趋势分析")
        
    def generate_optimization_plan(self):
        """生成优化计划"""
        if not self.current_issues:
            QMessageBox.information(self, "优化计划", "没有性能问题需要优化")
            return
            
        plan = self.optimizer.generate_optimization_plan(self.current_issues)
        
        # 格式化显示优化计划
        plan_text = f"AI Agent Desktop 性能优化计划\n"
        plan_text += f"生成时间: {plan['generated_at']}\n"
        plan_text += "=" * 50 + "\n\n"
        
        plan_text += f"总问题数: {plan['total_issues']}\n"
        plan_text += f"严重问题: {plan['critical_issues']}\n"
        plan_text += f"高优先级问题: {plan['high_issues']}\n"
        plan_text += f"中优先级问题: {plan['medium_issues']}\n"
        plan_text += f"低优先级问题: {plan['low_issues']}\n\n"
        
        plan_text += "优化建议:\n"
        for i, optimization in enumerate(plan['optimizations'], 1):
            plan_text += f"\n{i}. {optimization['description']}\n"
            plan_text += f"   严重程度: {optimization['severity']}\n"
            plan_text += f"   预计影响: {optimization['estimated_impact']}\n"
            plan_text += f"   实施难度: {optimization['implementation_effort']}\n"
            plan_text += "   具体建议:\n"
            for j, recommendation in enumerate(optimization['recommendations'], 1):
                plan_text += f"     {j}. {recommendation}\n"
                
        self.optimization_text.setText(plan_text)
        
    def export_optimization_plan(self):
        """导出优化计划"""
        plan_text = self.optimization_text.toPlainText()
        if not plan_text.strip():
            QMessageBox.information(self, "导出", "没有优化计划可导出")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出优化计划", "", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(plan_text)
                QMessageBox.information(self, "导出", "优化计划导出成功")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {e}")
                
    def export_report(self):
        """导出报告"""
        if not self.current_issues:
            QMessageBox.information(self, "导出", "没有分析结果可导出")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出性能分析报告", "", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("AI Agent Desktop 性能分析报告\n")
                    f.write(f"生成时间: {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"发现 {len(self.current_issues)} 个性能问题:\n\n")
                    
                    for i, issue in enumerate(self.current_issues, 1):
                        f.write(f"{i}. {issue.description}\n")
                        f.write(f"   严重程度: {issue.severity}\n")
                        f.write(f"   影响组件: {', '.join(issue.affected_components)}\n")
                        f.write("   优化建议:\n")
                        for j, recommendation in enumerate(issue.recommendations, 1):
                            f.write(f"     {j}. {recommendation}\n")
                        f.write("\n")
                        
                QMessageBox.information(self, "导出", "性能分析报告导出成功")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {e}")
                
    def clear_analysis(self):
        """清空分析"""
        self.current_issues.clear()
        self.trend_analyzer.history_data.clear()
        self.issues_table.setRowCount(0)
        self.issue_detail_text.clear()
        self.optimization_text.clear()
        self.trend_chart.removeAllSeries()
        
    def toggle_auto_analyze(self, state: int):
        """切换自动分析"""
        if state == Qt.CheckState.Checked.value:
            self.start_auto_analyze()
        else:
            self.stop_auto_analyze()
            
    def start_auto_analyze(self):
        """开始自动分析"""
        interval = self.interval_spin.value() * 1000  # 转换为毫秒
        self.auto_analyze_timer = QTimer()
        self.auto_analyze_timer.timeout.connect(self.analyze_performance)
        self.auto_analyze_timer.start(interval)
        
    def stop_auto_analyze(self):
        """停止自动分析"""
        if hasattr(self, 'auto_analyze_timer'):
            self.auto_analyze_timer.stop()
