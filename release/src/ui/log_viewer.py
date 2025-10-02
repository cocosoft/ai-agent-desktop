"""
高级日志查看器
提供实时日志查看、过滤、搜索、分析等功能
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
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


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry:
    """日志条目"""
    
    def __init__(self, timestamp: datetime, level: LogLevel, logger: str, 
                 message: str, extra_data: Optional[Dict] = None):
        self.timestamp = timestamp
        self.level = level
        self.logger = logger
        self.message = message
        self.extra_data = extra_data or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'logger': self.logger,
            'message': self.message,
            'extra_data': self.extra_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """从字典创建"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            level=LogLevel(data['level']),
            logger=data['logger'],
            message=data['message'],
            extra_data=data.get('extra_data', {})
        )


class LogFilter:
    """日志过滤器"""
    
    def __init__(self):
        self.levels: List[LogLevel] = []
        self.loggers: List[str] = []
        self.keywords: List[str] = []
        self.time_range: Optional[Tuple[datetime, datetime]] = None
        self.regex_pattern: Optional[str] = None
        
    def matches(self, entry: LogEntry) -> bool:
        """检查日志条目是否匹配过滤器"""
        # 级别过滤
        if self.levels and entry.level not in self.levels:
            return False
            
        # 日志器过滤
        if self.loggers and entry.logger not in self.loggers:
            return False
            
        # 时间范围过滤
        if self.time_range:
            start, end = self.time_range
            if not (start <= entry.timestamp <= end):
                return False
                
        # 关键词过滤
        if self.keywords:
            if not any(keyword.lower() in entry.message.lower() for keyword in self.keywords):
                return False
                
        # 正则表达式过滤
        if self.regex_pattern:
            try:
                if not re.search(self.regex_pattern, entry.message):
                    return False
            except re.error:
                # 正则表达式错误时跳过正则过滤
                pass
                
        return True


class LogParser:
    """日志解析器"""
    
    @staticmethod
    def parse_log_line(line: str) -> Optional[LogEntry]:
        """解析单行日志"""
        try:
            # 尝试解析JSON格式日志
            if line.strip().startswith('{'):
                data = json.loads(line)
                return LogEntry.from_dict(data)
            
            # 解析标准格式日志: [时间] [级别] [日志器] 消息
            pattern = r'\[(.*?)\] \[(.*?)\] \[(.*?)\] (.*)'
            match = re.match(pattern, line)
            if match:
                timestamp_str, level_str, logger, message = match.groups()
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    timestamp = datetime.now()
                    
                try:
                    level = LogLevel(level_str)
                except ValueError:
                    level = LogLevel.INFO
                    
                return LogEntry(timestamp, level, logger, message)
                
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass
            
        return None
    
    @staticmethod
    def parse_log_file(file_path: str) -> List[LogEntry]:
        """解析日志文件"""
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = LogParser.parse_log_line(line.strip())
                    if entry:
                        entries.append(entry)
        except Exception as e:
            print(f"解析日志文件失败: {e}")
            
        return entries


class LogStatistics:
    """日志统计"""
    
    def __init__(self, entries: List[LogEntry]):
        self.entries = entries
        self._calculate_statistics()
        
    def _calculate_statistics(self):
        """计算统计信息"""
        self.level_counts = {}
        self.logger_counts = {}
        self.hourly_counts = {}
        self.total_count = len(self.entries)
        
        for entry in self.entries:
            # 级别统计
            self.level_counts[entry.level] = self.level_counts.get(entry.level, 0) + 1
            
            # 日志器统计
            self.logger_counts[entry.logger] = self.logger_counts.get(entry.logger, 0) + 1
            
            # 小时统计
            hour = entry.timestamp.hour
            self.hourly_counts[hour] = self.hourly_counts.get(hour, 0) + 1
            
    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            'total_count': self.total_count,
            'level_counts': {level.value: count for level, count in self.level_counts.items()},
            'logger_counts': self.logger_counts,
            'hourly_counts': self.hourly_counts,
            'time_range': {
                'start': min(entry.timestamp for entry in self.entries) if self.entries else None,
                'end': max(entry.timestamp for entry in self.entries) if self.entries else None
            }
        }


class LogSearchThread(QThread):
    """日志搜索线程"""
    
    search_completed = pyqtSignal(list)
    
    def __init__(self, entries: List[LogEntry], filter_obj: LogFilter):
        super().__init__()
        self.entries = entries
        self.filter_obj = filter_obj
        
    def run(self):
        """执行搜索"""
        filtered_entries = []
        for entry in self.entries:
            if self.filter_obj.matches(entry):
                filtered_entries.append(entry)
                
        self.search_completed.emit(filtered_entries)


class LogViewerWidget(QWidget):
    """日志查看器主组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: List[LogEntry] = []
        self.filtered_entries: List[LogEntry] = []
        self.current_filter = LogFilter()
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 文件操作
        self.open_btn = QPushButton("打开日志文件")
        toolbar_layout.addWidget(self.open_btn)
        
        self.refresh_btn = QPushButton("刷新")
        toolbar_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("清空")
        toolbar_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addStretch()
        
        # 实时监控
        self.realtime_check = QCheckBox("实时监控")
        toolbar_layout.addWidget(self.realtime_check)
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：过滤面板
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 级别过滤
        level_group = QGroupBox("级别过滤")
        level_layout = QVBoxLayout(level_group)
        
        self.level_checks = {}
        for level in LogLevel:
            check = QCheckBox(level.value)
            check.setChecked(True)
            self.level_checks[level] = check
            level_layout.addWidget(check)
            
        left_layout.addWidget(level_group)
        
        # 日志器过滤
        logger_group = QGroupBox("日志器过滤")
        logger_layout = QVBoxLayout(logger_group)
        
        self.logger_list = QListWidget()
        logger_layout.addWidget(self.logger_list)
        
        left_layout.addWidget(logger_group)
        
        # 时间过滤
        time_group = QGroupBox("时间过滤")
        time_layout = QGridLayout(time_group)
        
        time_layout.addWidget(QLabel("开始时间:"), 0, 0)
        self.start_time_edit = QLineEdit()
        self.start_time_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        time_layout.addWidget(self.start_time_edit, 0, 1)
        
        time_layout.addWidget(QLabel("结束时间:"), 1, 0)
        self.end_time_edit = QLineEdit()
        self.end_time_edit.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        time_layout.addWidget(self.end_time_edit, 1, 1)
        
        left_layout.addWidget(time_group)
        
        # 关键词过滤
        keyword_group = QGroupBox("关键词过滤")
        keyword_layout = QVBoxLayout(keyword_group)
        
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("输入关键词，用空格分隔")
        keyword_layout.addWidget(self.keyword_edit)
        
        left_layout.addWidget(keyword_group)
        
        # 正则过滤
        regex_group = QGroupBox("正则表达式")
        regex_layout = QVBoxLayout(regex_group)
        
        self.regex_edit = QLineEdit()
        self.regex_edit.setPlaceholderText("输入正则表达式")
        regex_layout.addWidget(self.regex_edit)
        
        left_layout.addWidget(regex_group)
        
        # 应用过滤按钮
        self.apply_filter_btn = QPushButton("应用过滤")
        left_layout.addWidget(self.apply_filter_btn)
        
        left_layout.addStretch()
        
        splitter.addWidget(left_widget)
        
        # 右侧：日志显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("在日志中搜索...")
        search_layout.addWidget(self.search_edit)
        
        self.search_btn = QPushButton("搜索")
        search_layout.addWidget(self.search_btn)
        
        search_layout.addStretch()
        right_layout.addLayout(search_layout)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        right_layout.addWidget(self.log_text)
        
        # 状态栏
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.count_label = QLabel("0 条日志")
        status_layout.addWidget(self.count_label)
        
        right_layout.addLayout(status_layout)
        
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
    def setup_connections(self):
        """设置信号连接"""
        self.open_btn.clicked.connect(self.open_log_file)
        self.refresh_btn.clicked.connect(self.refresh_logs)
        self.clear_btn.clicked.connect(self.clear_logs)
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.search_btn.clicked.connect(self.search_logs)
        self.realtime_check.stateChanged.connect(self.toggle_realtime_monitoring)
        
        # 级别过滤变化
        for check in self.level_checks.values():
            check.stateChanged.connect(self.on_filter_changed)
            
        # 搜索框回车
        self.search_edit.returnPressed.connect(self.search_logs)
        
    def open_log_file(self):
        """打开日志文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择日志文件", "", "日志文件 (*.log *.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.load_log_file(file_path)
            
    def load_log_file(self, file_path: str):
        """加载日志文件"""
        self.status_label.setText(f"正在加载: {file_path}")
        QApplication.processEvents()
        
        entries = LogParser.parse_log_file(file_path)
        self.entries = entries
        self.filtered_entries = entries
        
        self.update_log_display()
        self.update_logger_list()
        self.update_status()
        
    def refresh_logs(self):
        """刷新日志"""
        if hasattr(self, 'current_file_path'):
            self.load_log_file(self.current_file_path)
            
    def clear_logs(self):
        """清空日志"""
        self.entries.clear()
        self.filtered_entries.clear()
        self.log_text.clear()
        self.update_status()
        
    def apply_filter(self):
        """应用过滤器"""
        # 更新过滤器
        self.update_filter()
        
        # 执行过滤
        self.filter_logs()
        
    def update_filter(self):
        """更新过滤器配置"""
        # 级别过滤
        self.current_filter.levels = [
            level for level, check in self.level_checks.items() 
            if check.isChecked()
        ]
        
        # 日志器过滤
        selected_loggers = [
            item.text() for item in self.logger_list.selectedItems()
        ]
        self.current_filter.loggers = selected_loggers
        
        # 时间过滤
        start_text = self.start_time_edit.text().strip()
        end_text = self.end_time_edit.text().strip()
        
        if start_text or end_text:
            try:
                start_time = datetime.fromisoformat(start_text) if start_text else None
                end_time = datetime.fromisoformat(end_text) if end_text else None
                self.current_filter.time_range = (start_time, end_time)
            except ValueError:
                QMessageBox.warning(self, "错误", "时间格式不正确")
                self.current_filter.time_range = None
        else:
            self.current_filter.time_range = None
            
        # 关键词过滤
        keyword_text = self.keyword_edit.text().strip()
        self.current_filter.keywords = keyword_text.split() if keyword_text else []
        
        # 正则过滤
        regex_text = self.regex_edit.text().strip()
        self.current_filter.regex_pattern = regex_text if regex_text else None
        
    def filter_logs(self):
        """过滤日志"""
        self.status_label.setText("正在过滤...")
        QApplication.processEvents()
        
        # 使用线程进行过滤
        self.search_thread = LogSearchThread(self.entries, self.current_filter)
        self.search_thread.search_completed.connect(self.on_filter_completed)
        self.search_thread.start()
        
    def on_filter_completed(self, filtered_entries: List[LogEntry]):
        """过滤完成"""
        self.filtered_entries = filtered_entries
        self.update_log_display()
        self.update_status()
        
    def search_logs(self):
        """搜索日志"""
        search_text = self.search_edit.text().strip()
        if not search_text:
            return
            
        # 在过滤后的日志中搜索
        search_filter = LogFilter()
        search_filter.keywords = [search_text]
        
        matching_entries = [
            entry for entry in self.filtered_entries 
            if search_filter.matches(entry)
        ]
        
        if matching_entries:
            self.highlight_search_results(matching_entries, search_text)
        else:
            QMessageBox.information(self, "搜索", "未找到匹配的日志")
            
    def highlight_search_results(self, entries: List[LogEntry], search_text: str):
        """高亮显示搜索结果"""
        # 保存当前文本
        current_text = self.log_text.toPlainText()
        
        # 清除之前的高亮
        self.log_text.setPlainText(current_text)
        
        # 高亮匹配文本
        cursor = self.log_text.textCursor()
        format = cursor.charFormat()
        format.setBackground(QColor(255, 255, 0))  # 黄色背景
        
        for entry in entries:
            # 查找日志文本中的匹配位置
            entry_text = self.format_log_entry(entry)
            start_pos = current_text.find(entry_text)
            if start_pos != -1:
                # 在匹配的条目中高亮搜索文本
                entry_start = entry_text.find(search_text)
                if entry_start != -1:
                    cursor.setPosition(start_pos + entry_start)
                    cursor.setPosition(start_pos + entry_start + len(search_text), QTextCursor.MoveMode.KeepAnchor)
                    cursor.setCharFormat(format)
                    
        # 滚动到第一个匹配项
        if entries:
            first_entry = self.format_log_entry(entries[0])
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.insertText("")  # 触发滚动
            
    def update_log_display(self):
        """更新日志显示"""
        self.log_text.clear()
        
        for entry in self.filtered_entries:
            log_line = self.format_log_entry(entry)
            self.log_text.append(log_line)
            
    def format_log_entry(self, entry: LogEntry) -> str:
        """格式化日志条目"""
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据级别设置颜色
        level_color = {
            LogLevel.DEBUG: "gray",
            LogLevel.INFO: "black",
            LogLevel.WARNING: "orange",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "darkred"
        }.get(entry.level, "black")
        
        return f"[{timestamp}] [{entry.level.value}] [{entry.logger}] {entry.message}"
        
    def update_logger_list(self):
        """更新日志器列表"""
        self.logger_list.clear()
        
        loggers = set(entry.logger for entry in self.entries)
        for logger in sorted(loggers):
            item = QListWidgetItem(logger)
            item.setCheckState(Qt.CheckState.Checked)
            self.logger_list.addItem(item)
            
    def update_status(self):
        """更新状态"""
        total_count = len(self.entries)
        filtered_count = len(self.filtered_entries)
        
        self.count_label.setText(f"{filtered_count}/{total_count} 条日志")
        
        if filtered_count == total_count:
            self.status_label.setText("就绪")
        else:
            self.status_label.setText(f"已过滤: {filtered_count}/{total_count}")
            
    def on_filter_changed(self):
        """过滤器变化"""
        # 自动应用过滤
        self.apply_filter()
        
    def toggle_realtime_monitoring(self, state: int):
        """切换实时监控"""
        if state == Qt.CheckState.Checked.value:
            self.start_realtime_monitoring()
        else:
            self.stop_realtime_monitoring()
            
    def start_realtime_monitoring(self):
        """开始实时监控"""
        # 这里可以添加实时监控逻辑
        # 例如监控日志文件的变化
        self.status_label.setText("实时监控已启动")
        
    def stop_realtime_monitoring(self):
        """停止实时监控"""
        self.status_label.setText("实时监控已停止")
        
    def export_logs(self):
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for entry in self.filtered_entries:
                        f.write(self.format_log_entry(entry) + '\n')
                QMessageBox.information(self, "导出", "日志导出成功")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {e}")
                
    def show_statistics(self):
        """显示统计信息"""
        if not self.entries:
            QMessageBox.information(self, "统计", "没有日志数据")
            return
            
        stats = LogStatistics(self.entries).get_summary()
        
        stats_text = f"日志统计:\n\n"
        stats_text += f"总条数: {stats['total_count']}\n\n"
        
        stats_text += "级别统计:\n"
        for level, count in stats['level_counts'].items():
            stats_text += f"  {level}: {count}\n"
            
        stats_text += "\n日志器统计:\n"
        for logger, count in sorted(stats['logger_counts'].items(), key=lambda x: x[1], reverse=True)[:10]:
            stats_text += f"  {logger}: {count}\n"
            
        QMessageBox.information(self, "日志统计", stats_text)
