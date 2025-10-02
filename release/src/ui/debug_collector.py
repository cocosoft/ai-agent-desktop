"""
调试信息收集器
收集系统状态、应用状态、性能数据等调试信息
"""

import os
import sys
import psutil
import platform
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
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

from ..core.agent_lifecycle import AgentLifecycleManager
from ..core.model_manager import ModelManager
from ..core.task_allocator import TaskAllocator
from ..utils.logger import get_log_manager
from ..utils.status_monitor import StatusMonitor


class DebugInfoType(Enum):
    """调试信息类型"""
    SYSTEM_INFO = "system_info"
    APPLICATION_INFO = "application_info"
    AGENT_STATUS = "agent_status"
    MODEL_STATUS = "model_status"
    PERFORMANCE_DATA = "performance_data"
    LOG_SUMMARY = "log_summary"
    ERROR_REPORT = "error_report"


@dataclass
class DebugInfo:
    """调试信息"""
    info_type: DebugInfoType
    timestamp: datetime
    data: Dict[str, Any]
    description: str = ""


class SystemInfoCollector:
    """系统信息收集器"""
    
    @staticmethod
    def collect_system_info() -> Dict[str, Any]:
        """收集系统信息"""
        return {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            },
            'cpu': {
                'physical_cores': psutil.cpu_count(logical=False),
                'total_cores': psutil.cpu_count(logical=True),
                'usage_percent': psutil.cpu_percent(interval=1),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv
            },
            'process': {
                'pid': os.getpid(),
                'name': psutil.Process().name(),
                'memory_percent': psutil.Process().memory_percent(),
                'cpu_percent': psutil.Process().cpu_percent(),
                'threads': psutil.Process().num_threads(),
                'open_files': len(psutil.Process().open_files()),
                'connections': len(psutil.Process().connections())
            }
        }


class ApplicationInfoCollector:
    """应用信息收集器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        
    def collect_application_info(self) -> Dict[str, Any]:
        """收集应用信息"""
        try:
            from ..core.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            return {
                'application': {
                    'name': 'AI Agent Desktop',
                    'version': '1.0.0',
                    'start_time': getattr(self, '_start_time', datetime.now()),
                    'uptime': (datetime.now() - getattr(self, '_start_time', datetime.now())).total_seconds()
                },
                'configuration': {
                    'database_path': config.database.path,
                    'log_level': config.logging.level,
                    'max_log_files': config.logging.max_files,
                    'a2a_server_host': config.a2a_server.host,
                    'a2a_server_port': config.a2a_server.port
                },
                'modules': {
                    'loaded_modules': list(sys.modules.keys()),
                    'python_path': sys.path
                }
            }
        except Exception as e:
            self.logger.error(f"收集应用信息失败: {e}")
            return {}


class AgentStatusCollector:
    """代理状态收集器"""
    
    def __init__(self, agent_manager: Optional[AgentLifecycleManager] = None):
        self.agent_manager = agent_manager
        
    def collect_agent_status(self) -> Dict[str, Any]:
        """收集代理状态"""
        if not self.agent_manager:
            return {'agents': []}
            
        try:
            agents_info = []
            for agent in self.agent_manager.get_all_agents():
                agents_info.append({
                    'instance_id': agent.instance_id,
                    'status': agent.status.value,
                    'current_tasks': agent.current_tasks,
                    'total_tasks': agent.total_tasks,
                    'successful_tasks': agent.successful_tasks,
                    'failed_tasks': agent.failed_tasks,
                    'avg_response_time': getattr(agent, 'avg_response_time', 0),
                    'health_status': getattr(agent, 'health_status', 'unknown'),
                    'last_health_check': getattr(agent, 'last_health_check', None),
                    'resource_usage': getattr(agent, 'resource_usage', {})
                })
                
            return {
                'total_agents': len(agents_info),
                'running_agents': len([a for a in agents_info if a['status'] == 'running']),
                'agents': agents_info
            }
        except Exception as e:
            return {'error': str(e), 'agents': []}


class ModelStatusCollector:
    """模型状态收集器"""
    
    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager
        
    def collect_model_status(self) -> Dict[str, Any]:
        """收集模型状态"""
        if not self.model_manager:
            return {'models': []}
            
        try:
            models_info = []
            for model in self.model_manager.get_available_models():
                models_info.append({
                    'model_id': model.model_id,
                    'adapter_type': model.adapter_type,
                    'status': getattr(model, 'status', 'unknown'),
                    'requests_count': getattr(model, 'requests_count', 0),
                    'success_rate': getattr(model, 'success_rate', 0),
                    'avg_response_time': getattr(model, 'avg_response_time', 0),
                    'current_load': getattr(model, 'current_load', 0),
                    'last_used': getattr(model, 'last_used', None)
                })
                
            return {
                'total_models': len(models_info),
                'active_models': len([m for m in models_info if m['status'] == 'active']),
                'models': models_info
            }
        except Exception as e:
            return {'error': str(e), 'models': []}


class PerformanceDataCollector:
    """性能数据收集器"""
    
    def __init__(self, status_monitor: Optional[StatusMonitor] = None):
        self.status_monitor = status_monitor
        
    def collect_performance_data(self) -> Dict[str, Any]:
        """收集性能数据"""
        if not self.status_monitor:
            return {'metrics': {}}
            
        try:
            metrics = self.status_monitor.get_all_metrics()
            return {
                'timestamp': datetime.now(),
                'metrics': metrics
            }
        except Exception as e:
            return {'error': str(e), 'metrics': {}}


class DebugInfoCollector:
    """调试信息收集器"""
    
    def __init__(self):
        self.system_collector = SystemInfoCollector()
        self.app_collector = ApplicationInfoCollector()
        self.agent_collector = AgentStatusCollector()
        self.model_collector = ModelStatusCollector()
        self.performance_collector = PerformanceDataCollector()
        
    def collect_all_info(self) -> List[DebugInfo]:
        """收集所有调试信息"""
        debug_infos = []
        
        # 收集系统信息
        system_info = self.system_collector.collect_system_info()
        debug_infos.append(DebugInfo(
            info_type=DebugInfoType.SYSTEM_INFO,
            timestamp=datetime.now(),
            data=system_info,
            description="系统信息"
        ))
        
        # 收集应用信息
        app_info = self.app_collector.collect_application_info()
        debug_infos.append(DebugInfo(
            info_type=DebugInfoType.APPLICATION_INFO,
            timestamp=datetime.now(),
            data=app_info,
            description="应用信息"
        ))
        
        # 收集代理状态
        agent_info = self.agent_collector.collect_agent_status()
        debug_infos.append(DebugInfo(
            info_type=DebugInfoType.AGENT_STATUS,
            timestamp=datetime.now(),
            data=agent_info,
            description="代理状态"
        ))
        
        # 收集模型状态
        model_info = self.model_collector.collect_model_status()
        debug_infos.append(DebugInfo(
            info_type=DebugInfoType.MODEL_STATUS,
            timestamp=datetime.now(),
            data=model_info,
            description="模型状态"
        ))
        
        # 收集性能数据
        performance_info = self.performance_collector.collect_performance_data()
        debug_infos.append(DebugInfo(
            info_type=DebugInfoType.PERFORMANCE_DATA,
            timestamp=datetime.now(),
            data=performance_info,
            description="性能数据"
        ))
        
        return debug_infos


class DebugCollectorWidget(QWidget):
    """调试信息收集器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.debug_collector = DebugInfoCollector()
        self.collected_info: List[DebugInfo] = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.collect_btn = QPushButton("收集调试信息")
        toolbar_layout.addWidget(self.collect_btn)
        
        self.export_btn = QPushButton("导出报告")
        toolbar_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("清空")
        toolbar_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addStretch()
        
        # 自动收集
        self.auto_collect_check = QCheckBox("自动收集")
        toolbar_layout.addWidget(self.auto_collect_check)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 3600)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" 秒")
        toolbar_layout.addWidget(QLabel("间隔:"))
        toolbar_layout.addWidget(self.interval_spin)
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：信息类型选择
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        info_group = QGroupBox("调试信息类型")
        info_layout = QVBoxLayout(info_group)
        
        self.info_checks = {}
        for info_type in DebugInfoType:
            check = QCheckBox(info_type.value.replace('_', ' ').title())
            check.setChecked(True)
            self.info_checks[info_type] = check
            info_layout.addWidget(check)
            
        left_layout.addWidget(info_group)
        
        # 状态信息
        status_group = QGroupBox("状态")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        left_layout.addWidget(status_group)
        
        left_layout.addStretch()
        
        splitter.addWidget(left_widget)
        
        # 右侧：信息显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 信息显示区域
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont("Consolas", 9))
        right_layout.addWidget(self.info_text)
        
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter)
        
    def setup_connections(self):
        """设置信号连接"""
        self.collect_btn.clicked.connect(self.collect_debug_info)
        self.export_btn.clicked.connect(self.export_report)
        self.clear_btn.clicked.connect(self.clear_info)
        self.auto_collect_check.stateChanged.connect(self.toggle_auto_collect)
        
    def collect_debug_info(self):
        """收集调试信息"""
        self.status_label.setText("正在收集调试信息...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        QApplication.processEvents()
        
        try:
            # 获取选中的信息类型
            selected_types = [
                info_type for info_type, check in self.info_checks.items()
                if check.isChecked()
            ]
            
            # 收集信息
            all_info = self.debug_collector.collect_all_info()
            filtered_info = [
                info for info in all_info 
                if info.info_type in selected_types
            ]
            
            self.collected_info = filtered_info
            self.display_collected_info()
            
            self.status_label.setText(f"收集完成: {len(filtered_info)} 项信息")
            
        except Exception as e:
            self.status_label.setText(f"收集失败: {e}")
            QMessageBox.critical(self, "错误", f"收集调试信息失败: {e}")
            
        finally:
            self.progress_bar.setVisible(False)
            
    def display_collected_info(self):
        """显示收集的信息"""
        self.info_text.clear()
        
        for info in self.collected_info:
            self.info_text.append(f"=== {info.description} ===")
            self.info_text.append(f"时间: {info.timestamp}")
            self.info_text.append("")
            
            # 格式化显示数据
            formatted_data = self.format_debug_data(info.data)
            self.info_text.append(formatted_data)
            self.info_text.append("")
            
    def format_debug_data(self, data: Dict[str, Any], indent: int = 0) -> str:
        """格式化调试数据"""
        lines = []
        prefix = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self.format_debug_data(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  [{i}]:")
                        lines.append(self.format_debug_data(item, indent + 2))
                    else:
                        lines.append(f"{prefix}  [{i}]: {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")
                
        return "\n".join(lines)
        
    def export_report(self):
        """导出报告"""
        if not self.collected_info:
            QMessageBox.information(self, "导出", "没有调试信息可导出")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出调试报告", "", "文本文件 (*.txt);;JSON文件 (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.export_json_report(file_path)
                else:
                    self.export_text_report(file_path)
                    
                QMessageBox.information(self, "导出", "调试报告导出成功")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {e}")
                
    def export_text_report(self, file_path: str):
        """导出文本报告"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("AI Agent Desktop 调试报告\n")
            f.write(f"生成时间: {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            
            for info in self.collected_info:
                f.write(f"=== {info.description} ===\n")
                f.write(f"时间: {info.timestamp}\n\n")
                f.write(self.format_debug_data(info.data) + "\n\n")
                
    def export_json_report(self, file_path: str):
        """导出JSON报告"""
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
                for info in self.collected_info
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
    def clear_info(self):
        """清空信息"""
        self.collected_info.clear()
        self.info_text.clear()
        self.status_label.setText("已清空")
        
    def toggle_auto_collect(self, state: int):
        """切换自动收集"""
        if state == Qt.CheckState.Checked.value:
            self.start_auto_collect()
        else:
            self.stop_auto_collect()
            
    def start_auto_collect(self):
        """开始自动收集"""
        interval = self.interval_spin.value() * 1000  # 转换为毫秒
        self.auto_collect_timer = QTimer()
        self.auto_collect_timer.timeout.connect(self.collect_debug_info)
        self.auto_collect_timer.start(interval)
        self.status_label.setText(f"自动收集已启动 (间隔: {self.interval_spin.value()}秒)")
        
    def stop_auto_collect(self):
        """停止自动收集"""
        if hasattr(self, 'auto_collect_timer'):
            self.auto_collect_timer.stop()
            self.status_label.setText("自动收集已停止")
