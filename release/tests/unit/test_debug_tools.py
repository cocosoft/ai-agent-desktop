"""
调试工具测试
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ui.log_viewer import LogViewerWidget, LogEntry, LogLevel, LogParser
from src.ui.debug_collector import DebugCollectorWidget, DebugInfoCollector, DebugInfoType
from src.ui.performance_analyzer import PerformanceAnalyzerWidget, PerformanceAnalyzer, PerformanceIssue
from src.ui.problem_diagnoser import ProblemDiagnoserWidget, ProblemDiagnoser, ProblemType
from src.ui.debug_tools import DebugToolsWidget


class TestLogViewer(unittest.TestCase):
    """日志查看器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.log_viewer = LogViewerWidget()
        
    def test_log_entry_creation(self):
        """测试日志条目创建"""
        timestamp = datetime.now()
        entry = LogEntry(timestamp, LogLevel.INFO, "test_logger", "测试消息")
        
        self.assertEqual(entry.level, LogLevel.INFO)
        self.assertEqual(entry.logger, "test_logger")
        self.assertEqual(entry.message, "测试消息")
        
    def test_log_entry_to_dict(self):
        """测试日志条目转字典"""
        timestamp = datetime.now()
        entry = LogEntry(timestamp, LogLevel.ERROR, "test_logger", "错误消息")
        entry_dict = entry.to_dict()
        
        self.assertEqual(entry_dict['level'], "ERROR")
        self.assertEqual(entry_dict['logger'], "test_logger")
        self.assertEqual(entry_dict['message'], "错误消息")
        
    def test_log_parser_parse_line(self):
        """测试日志解析器解析单行"""
        # 测试标准格式
        line = "[2024-01-01 10:00:00] [INFO] [main] 这是一条测试日志"
        entry = LogParser.parse_log_line(line)
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.level, LogLevel.INFO)
        self.assertEqual(entry.logger, "main")
        self.assertEqual(entry.message, "这是一条测试日志")
        
        # 测试JSON格式
        json_line = '{"timestamp": "2024-01-01T10:00:00", "level": "WARNING", "logger": "test", "message": "JSON日志"}'
        entry = LogParser.parse_log_line(json_line)
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.level, LogLevel.WARNING)
        self.assertEqual(entry.logger, "test")
        self.assertEqual(entry.message, "JSON日志")
        
    def test_log_filter_matches(self):
        """测试日志过滤器"""
        from src.ui.log_viewer import LogFilter
        
        filter_obj = LogFilter()
        filter_obj.levels = [LogLevel.ERROR, LogLevel.CRITICAL]
        
        # 创建测试条目
        error_entry = LogEntry(datetime.now(), LogLevel.ERROR, "test", "错误消息")
        info_entry = LogEntry(datetime.now(), LogLevel.INFO, "test", "信息消息")
        
        self.assertTrue(filter_obj.matches(error_entry))
        self.assertFalse(filter_obj.matches(info_entry))


class TestDebugCollector(unittest.TestCase):
    """调试信息收集器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.debug_collector = DebugCollectorWidget()
        
    @patch('src.ui.debug_collector.SystemInfoCollector.collect_system_info')
    def test_system_info_collection(self, mock_collect):
        """测试系统信息收集"""
        mock_collect.return_value = {
            'platform': {'system': 'Windows'},
            'cpu': {'usage_percent': 50.0},
            'memory': {'percent': 60.0}
        }
        
        from src.ui.debug_collector import SystemInfoCollector
        collector = SystemInfoCollector()
        info = collector.collect_system_info()
        
        self.assertIn('platform', info)
        self.assertIn('cpu', info)
        self.assertIn('memory', info)
        
    def test_debug_info_collector(self):
        """测试调试信息收集器"""
        collector = DebugInfoCollector()
        debug_infos = collector.collect_all_info()
        
        # 至少应该收集系统信息
        self.assertTrue(len(debug_infos) > 0)
        
        # 检查信息类型
        info_types = [info.info_type for info in debug_infos]
        self.assertIn(DebugInfoType.SYSTEM_INFO, info_types)
        self.assertIn(DebugInfoType.APPLICATION_INFO, info_types)


class TestPerformanceAnalyzer(unittest.TestCase):
    """性能分析器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.performance_analyzer = PerformanceAnalyzerWidget()
        
    def test_performance_issue_creation(self):
        """测试性能问题创建"""
        issue = PerformanceIssue(
            issue_type="high_response_time",
            severity="high",
            description="响应时间过高",
            affected_components=["模型调用", "任务处理"],
            recommendations=["优化代码", "增加缓存"],
            metrics={'avg_response_time': 15.5}
        )
        
        self.assertEqual(issue.severity, "high")
        self.assertEqual(len(issue.affected_components), 2)
        self.assertEqual(len(issue.recommendations), 2)
        
    def test_performance_analyzer(self):
        """测试性能分析器"""
        analyzer = PerformanceAnalyzer()
        
        # 测试高响应时间
        metrics = {'avg_response_time': 20.0, 'max_response_time': 50.0}
        issues = analyzer.analyze_performance(metrics)
        
        # 应该检测到高响应时间问题
        high_response_issues = [issue for issue in issues if issue.issue_type == "high_response_time"]
        self.assertTrue(len(high_response_issues) > 0)
        
        # 测试正常指标
        normal_metrics = {'avg_response_time': 5.0, 'success_rate': 0.95}
        issues = analyzer.analyze_performance(normal_metrics)
        
        # 正常指标不应该产生问题
        self.assertEqual(len(issues), 0)


class TestProblemDiagnoser(unittest.TestCase):
    """问题诊断器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.problem_diagnoser = ProblemDiagnoserWidget()
        
    @patch('src.ui.problem_diagnoser.ConfigManager')
    def test_configuration_diagnosis(self, mock_config_manager):
        """测试配置诊断"""
        from src.ui.problem_diagnoser import ProblemDiagnoser
        
        # 模拟配置问题
        mock_config = Mock()
        mock_config.database.path = ""
        mock_config.logging.level = ""
        mock_config.a2a_server.host = ""
        mock_config.a2a_server.port = ""
        
        mock_config_manager.return_value.get_config.return_value = mock_config
        
        diagnoser = ProblemDiagnoser()
        problem = diagnoser.diagnose_configuration()
        
        self.assertIsNotNone(problem)
        self.assertEqual(problem.problem_type, ProblemType.CONFIGURATION_ERROR)
        self.assertEqual(problem.severity, "high")
        
    @patch('src.ui.problem_diagnoser.DatabaseManager')
    def test_connection_diagnosis(self, mock_db_manager):
        """测试连接诊断"""
        from src.ui.problem_diagnoser import ProblemDiagnoser
        
        # 模拟连接失败
        mock_db_instance = Mock()
        mock_db_instance.test_connection.return_value = False
        mock_db_instance.db_path = "/test/path.db"
        mock_db_manager.return_value = mock_db_instance
        
        diagnoser = ProblemDiagnoser()
        problem = diagnoser.diagnose_connections()
        
        self.assertIsNotNone(problem)
        self.assertEqual(problem.problem_type, ProblemType.CONNECTION_ERROR)
        self.assertEqual(problem.severity, "critical")


class TestDebugToolsIntegration(unittest.TestCase):
    """调试工具集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.debug_tools = DebugToolsWidget()
        
    def test_debug_tools_initialization(self):
        """测试调试工具初始化"""
        # 检查所有组件是否已初始化
        self.assertIsNotNone(self.debug_tools.log_viewer)
        self.assertIsNotNone(self.debug_tools.debug_collector)
        self.assertIsNotNone(self.debug_tools.performance_analyzer)
        self.assertIsNotNone(self.debug_tools.problem_diagnoser)
        
        # 检查标签页数量
        self.assertEqual(self.debug_tools.tab_widget.count(), 4)
        
    def test_quick_diagnose(self):
        """测试快速诊断"""
        # 模拟各个组件的诊断方法
        with patch.object(self.debug_tools.problem_diagnoser, 'diagnose_problems') as mock_diagnose:
            with patch.object(self.debug_tools.debug_collector, 'collect_debug_info') as mock_collect:
                with patch.object(self.debug_tools.performance_analyzer, 'analyze_performance') as mock_analyze:
                    
                    self.debug_tools.quick_diagnose()
                    
                    # 验证所有方法都被调用
                    mock_diagnose.assert_called_once()
                    mock_collect.assert_called_once()
                    mock_analyze.assert_called_once()
                    
    def test_export_all_reports(self):
        """测试导出所有报告"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.ui.debug_tools.os.makedirs') as mock_makedirs:
                with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
                    
                    # 模拟各个组件有数据
                    self.debug_tools.problem_diagnoser.current_problems = [Mock()]
                    self.debug_tools.performance_analyzer.current_issues = [Mock()]
                    self.debug_tools.debug_collector.collected_info = [Mock()]
                    
                    self.debug_tools.export_all_reports()
                    
                    # 验证目录创建和文件写入
                    mock_makedirs.assert_called_once()
                    self.assertTrue(mock_open.called)


if __name__ == '__main__':
    unittest.main()
