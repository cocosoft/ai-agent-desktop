"""
调试工具主界面
集成所有调试和日志工具
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
                            QGroupBox, QGridLayout, QProgressBar, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QFrame,
                            QTextEdit, QLineEdit, QListWidget, QListWidgetItem,
                            QTreeWidget, QTreeWidgetItem, QApplication, QMenu,
                            QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QDateTime
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor, QAction, QIcon

from .log_viewer import LogViewerWidget
from .debug_collector import DebugCollectorWidget
from .performance_analyzer import PerformanceAnalyzerWidget
from .problem_diagnoser import ProblemDiagnoserWidget


class DebugToolsWidget(QWidget):
    """调试工具主组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("AI Agent Desktop - 调试工具")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 状态栏
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.time_label = QLabel()
        self.update_time()
        status_layout.addWidget(self.time_label)
        
        main_layout.addLayout(status_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 日志查看器标签页
        self.log_viewer = LogViewerWidget()
        self.tab_widget.addTab(self.log_viewer, "日志查看器")
        
        # 调试信息收集器标签页
        self.debug_collector = DebugCollectorWidget()
        self.tab_widget.addTab(self.debug_collector, "调试信息")
        
        # 性能分析器标签页
        self.performance_analyzer = PerformanceAnalyzerWidget()
        self.tab_widget.addTab(self.performance_analyzer, "性能分析")
        
        # 问题诊断器标签页
        self.problem_diagnoser = ProblemDiagnoserWidget()
        self.tab_widget.addTab(self.problem_diagnoser, "问题诊断")
        
        main_layout.addWidget(self.tab_widget)
        
        # 全局操作
        global_layout = QHBoxLayout()
        
        self.quick_diagnose_btn = QPushButton("快速诊断")
        global_layout.addWidget(self.quick_diagnose_btn)
        
        self.export_all_btn = QPushButton("导出所有报告")
        global_layout.addWidget(self.export_all_btn)
        
        self.clear_all_btn = QPushButton("清空所有")
        global_layout.addWidget(self.clear_all_btn)
        
        global_layout.addStretch()
        
        # 自动模式
        self.auto_mode_check = QCheckBox("自动模式")
        global_layout.addWidget(self.auto_mode_check)
        
        main_layout.addLayout(global_layout)
        
    def setup_connections(self):
        """设置信号连接"""
        self.quick_diagnose_btn.clicked.connect(self.quick_diagnose)
        self.export_all_btn.clicked.connect(self.export_all_reports)
        self.clear_all_btn.clicked.connect(self.clear_all_data)
        self.auto_mode_check.stateChanged.connect(self.toggle_auto_mode)
        
        # 更新时间定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新一次
        
    def update_time(self):
        """更新时间显示"""
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.time_label.setText(current_time)
        
    def quick_diagnose(self):
        """快速诊断"""
        self.status_label.setText("正在执行快速诊断...")
        QApplication.processEvents()
        
        try:
            # 执行问题诊断
            self.problem_diagnoser.diagnose_problems()
            
            # 收集调试信息
            self.debug_collector.collect_debug_info()
            
            # 分析性能
            self.performance_analyzer.analyze_performance()
            
            self.status_label.setText("快速诊断完成")
            QMessageBox.information(self, "快速诊断", "快速诊断已完成")
            
        except Exception as e:
            self.status_label.setText(f"快速诊断失败: {e}")
            QMessageBox.critical(self, "快速诊断失败", f"快速诊断过程出错: {e}")
            
    def export_all_reports(self):
        """导出所有报告"""
        self.status_label.setText("正在导出所有报告...")
        QApplication.processEvents()
        
        try:
            # 创建报告目录
            report_dir = f"debug_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(report_dir, exist_ok=True)
            
            # 导出问题诊断报告
            problem_report_path = os.path.join(report_dir, "problem_diagnosis.txt")
            if hasattr(self.problem_diagnoser, 'current_problems') and self.problem_diagnoser.current_problems:
                with open(problem_report_path, 'w', encoding='utf-8') as f:
                    f.write("AI Agent Desktop 问题诊断报告\n")
                    f.write(f"生成时间: {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, problem in enumerate(self.problem_diagnoser.current_problems, 1):
                        f.write(f"{i}. {problem.description}\n")
                        f.write(f"   类型: {problem.problem_type.value}\n")
                        f.write(f"   严重程度: {problem.severity}\n")
                        f.write(f"   根本原因: {problem.root_cause}\n")
                        f.write(f"   影响组件: {', '.join(problem.affected_components)}\n")
                        f.write("   解决方案:\n")
                        for j, solution in enumerate(problem.solutions, 1):
                            f.write(f"     {j}. {solution}\n")
                        f.write("\n")
            
            # 导出性能分析报告
            performance_report_path = os.path.join(report_dir, "performance_analysis.txt")
            if hasattr(self.performance_analyzer, 'current_issues') and self.performance_analyzer.current_issues:
                with open(performance_report_path, 'w', encoding='utf-8') as f:
                    f.write("AI Agent Desktop 性能分析报告\n")
                    f.write(f"生成时间: {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, issue in enumerate(self.performance_analyzer.current_issues, 1):
                        f.write(f"{i}. {issue.description}\n")
                        f.write(f"   严重程度: {issue.severity}\n")
                        f.write(f"   影响组件: {', '.join(issue.affected_components)}\n")
                        f.write("   优化建议:\n")
                        for j, recommendation in enumerate(issue.recommendations, 1):
                            f.write(f"     {j}. {recommendation}\n")
                        f.write("\n")
            
            # 导出调试信息报告
            debug_report_path = os.path.join(report_dir, "debug_info.json")
            if hasattr(self.debug_collector, 'collected_info') and self.debug_collector.collected_info:
                import json
                report_data = {
                    'generated_at': datetime.now().isoformat(),
                    'debug_info': [
                        {
                            'type': info.info_type.value,
                            'timestamp': info.timestamp.isoformat(),
                            'description': info.description,
                            'data': info.data
                        }
                        for info in self.debug_collector.collected_info
                    ]
                }
                with open(debug_report_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.status_label.setText(f"所有报告已导出到: {report_dir}")
            QMessageBox.information(self, "导出完成", f"所有报告已导出到目录: {report_dir}")
            
        except Exception as e:
            self.status_label.setText(f"导出失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出所有报告失败: {e}")
            
    def clear_all_data(self):
        """清空所有数据"""
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空所有调试工具的数据吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 清空日志查看器
                if hasattr(self.log_viewer, 'clear_logs'):
                    self.log_viewer.clear_logs()
                    
                # 清空调试收集器
                if hasattr(self.debug_collector, 'clear_info'):
                    self.debug_collector.clear_info()
                    
                # 清空性能分析器
                if hasattr(self.performance_analyzer, 'clear_analysis'):
                    self.performance_analyzer.clear_analysis()
                    
                # 清空问题诊断器
                if hasattr(self.problem_diagnoser, 'clear_diagnosis'):
                    self.problem_diagnoser.clear_diagnosis()
                    
                self.status_label.setText("所有数据已清空")
                QMessageBox.information(self, "清空完成", "所有调试工具的数据已清空")
                
            except Exception as e:
                self.status_label.setText(f"清空失败: {e}")
                QMessageBox.critical(self, "清空失败", f"清空数据失败: {e}")
                
    def toggle_auto_mode(self, state: int):
        """切换自动模式"""
        if state == Qt.CheckState.Checked.value:
            self.start_auto_mode()
        else:
            self.stop_auto_mode()
            
    def start_auto_mode(self):
        """开始自动模式"""
        self.status_label.setText("自动模式已启动")
        
        # 启动所有自动功能
        if hasattr(self.log_viewer, 'realtime_check'):
            self.log_viewer.realtime_check.setChecked(True)
            
        if hasattr(self.debug_collector, 'auto_collect_check'):
            self.debug_collector.auto_collect_check.setChecked(True)
            
        if hasattr(self.performance_analyzer, 'auto_analyze_check'):
            self.performance_analyzer.auto_analyze_check.setChecked(True)
            
        if hasattr(self.problem_diagnoser, 'auto_diagnose_check'):
            self.problem_diagnoser.auto_diagnose_check.setChecked(True)
            
    def stop_auto_mode(self):
        """停止自动模式"""
        self.status_label.setText("自动模式已停止")
        
        # 停止所有自动功能
        if hasattr(self.log_viewer, 'realtime_check'):
            self.log_viewer.realtime_check.setChecked(False)
            
        if hasattr(self.debug_collector, 'auto_collect_check'):
            self.debug_collector.auto_collect_check.setChecked(False)
            
        if hasattr(self.performance_analyzer, 'auto_analyze_check'):
            self.performance_analyzer.auto_analyze_check.setChecked(False)
            
        if hasattr(self.problem_diagnoser, 'auto_diagnose_check'):
            self.problem_diagnoser.auto_diagnose_check.setChecked(False)
            
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self.status_label.setText("调试工具已就绪")
        
    def closeEvent(self, event):
        """关闭事件"""
        # 停止所有定时器
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
            
        # 停止自动模式
        self.stop_auto_mode()
        
        super().closeEvent(event)


class DebugToolsManager:
    """调试工具管理器"""
    
    def __init__(self):
        self.debug_tools_widget = None
        
    def show_debug_tools(self, parent=None):
        """显示调试工具"""
        if self.debug_tools_widget is None:
            self.debug_tools_widget = DebugToolsWidget(parent)
            
        self.debug_tools_widget.show()
        self.debug_tools_widget.raise_()
        self.debug_tools_widget.activateWindow()
        
        return self.debug_tools_widget
        
    def close_debug_tools(self):
        """关闭调试工具"""
        if self.debug_tools_widget:
            self.debug_tools_widget.close()
            self.debug_tools_widget = None


# 全局调试工具管理器实例
debug_tools_manager = DebugToolsManager()


def show_debug_tools(parent=None):
    """显示调试工具（全局函数）"""
    return debug_tools_manager.show_debug_tools(parent)


def close_debug_tools():
    """关闭调试工具（全局函数）"""
    debug_tools_manager.close_debug_tools()
