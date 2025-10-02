"""
问题诊断工具
提供系统问题自动诊断和解决方案
"""

import os
import sys
import traceback
import asyncio
from datetime import datetime
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

from ..core.agent_lifecycle import AgentLifecycleManager
from ..core.model_manager import ModelManager
from ..core.task_allocator import TaskAllocator
from ..utils.logger import get_log_manager
from ..utils.status_monitor import StatusMonitor


class ProblemType(Enum):
    """问题类型"""
    CONFIGURATION_ERROR = "configuration_error"
    CONNECTION_ERROR = "connection_error"
    PERFORMANCE_ISSUE = "performance_issue"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PERMISSION_ERROR = "permission_error"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class Problem:
    """问题"""
    problem_type: ProblemType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_components: List[str]
    root_cause: str
    solutions: List[str]
    diagnostic_data: Dict[str, Any]


class ProblemDiagnoser:
    """问题诊断器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        
    def diagnose_configuration(self) -> Optional[Problem]:
        """诊断配置问题"""
        try:
            from ..core.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            issues = []
            
            # 检查数据库配置
            if not config.database.path:
                issues.append("数据库路径未配置")
                
            # 检查日志配置
            if not config.logging.level:
                issues.append("日志级别未配置")
                
            # 检查A2A服务器配置
            if not config.a2a_server.host:
                issues.append("A2A服务器主机未配置")
            if not config.a2a_server.port:
                issues.append("A2A服务器端口未配置")
                
            if issues:
                return Problem(
                    problem_type=ProblemType.CONFIGURATION_ERROR,
                    severity="high",
                    description="配置不完整或错误",
                    affected_components=["配置系统"],
                    root_cause="应用配置缺少必要参数",
                    solutions=[
                        "检查配置文件完整性",
                        "验证配置参数格式",
                        "重新生成默认配置"
                    ],
                    diagnostic_data={'issues': issues, 'config_file': 'app_config.yaml'}
                )
                
        except Exception as e:
            return Problem(
                problem_type=ProblemType.CONFIGURATION_ERROR,
                severity="critical",
                description="配置加载失败",
                affected_components=["配置系统"],
                root_cause=str(e),
                solutions=[
                    "检查配置文件语法",
                    "验证配置文件权限",
                    "重新创建配置文件"
                ],
                diagnostic_data={'error': str(e)}
            )
            
        return None
        
    def diagnose_connections(self) -> Optional[Problem]:
        """诊断连接问题"""
        try:
            # 检查数据库连接
            from ..data.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            if not db_manager.test_connection():
                return Problem(
                    problem_type=ProblemType.CONNECTION_ERROR,
                    severity="critical",
                    description="数据库连接失败",
                    affected_components=["数据库", "数据存储"],
                    root_cause="无法连接到SQLite数据库",
                    solutions=[
                        "检查数据库文件路径",
                        "验证数据库文件权限",
                        "检查磁盘空间",
                        "重新创建数据库"
                    ],
                    diagnostic_data={'database_path': db_manager.db_path}
                )
                
        except Exception as e:
            return Problem(
                problem_type=ProblemType.CONNECTION_ERROR,
                severity="critical",
                description="数据库连接异常",
                affected_components=["数据库"],
                root_cause=str(e),
                solutions=[
                    "检查数据库文件完整性",
                    "验证数据库驱动",
                    "重新安装依赖包"
                ],
                diagnostic_data={'error': str(e)}
            )
            
        return None
        
    def diagnose_resources(self) -> Optional[Problem]:
        """诊断资源问题"""
        try:
            import psutil
            
            issues = []
            
            # 检查磁盘空间
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > 90:
                issues.append(f"磁盘空间不足: {disk_usage.percent}%")
                
            # 检查内存使用
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                issues.append(f"内存使用率高: {memory.percent}%")
                
            # 检查CPU使用
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                issues.append(f"CPU使用率高: {cpu_percent}%")
                
            if issues:
                return Problem(
                    problem_type=ProblemType.RESOURCE_EXHAUSTION,
                    severity="high",
                    description="系统资源紧张",
                    affected_components=["系统资源"],
                    root_cause="硬件资源使用率过高",
                    solutions=[
                        "清理磁盘空间",
                        "关闭不必要的应用",
                        "增加系统内存",
                        "优化应用配置"
                    ],
                    diagnostic_data={'issues': issues}
                )
                
        except Exception as e:
            self.logger.error(f"资源诊断失败: {e}")
            
        return None
        
    def diagnose_permissions(self) -> Optional[Problem]:
        """诊断权限问题"""
        try:
            # 检查日志目录权限
            log_dir = "logs"
            if os.path.exists(log_dir):
                if not os.access(log_dir, os.W_OK):
                    return Problem(
                        problem_type=ProblemType.PERMISSION_ERROR,
                        severity="high",
                        description="日志目录无写入权限",
                        affected_components=["日志系统"],
                        root_cause="应用无法写入日志文件",
                        solutions=[
                            "修改日志目录权限",
                            "更改日志目录位置",
                            "以管理员权限运行应用"
                        ],
                        diagnostic_data={'log_dir': log_dir}
                    )
                    
            # 检查数据库文件权限
            db_file = "data/app.db"
            if os.path.exists(db_file):
                if not os.access(db_file, os.W_OK):
                    return Problem(
                        problem_type=ProblemType.PERMISSION_ERROR,
                        severity="critical",
                        description="数据库文件无写入权限",
                        affected_components=["数据库"],
                        root_cause="应用无法写入数据库",
                        solutions=[
                            "修改数据库文件权限",
                            "更改数据库文件位置",
                            "以管理员权限运行应用"
                        ],
                        diagnostic_data={'db_file': db_file}
                    )
                    
        except Exception as e:
            self.logger.error(f"权限诊断失败: {e}")
            
        return None
        
    def diagnose_dependencies(self) -> Optional[Problem]:
        """诊断依赖问题"""
        missing_deps = []
        
        # 检查关键依赖
        try:
            import PyQt6
        except ImportError:
            missing_deps.append("PyQt6")
            
        try:
            import psutil
        except ImportError:
            missing_deps.append("psutil")
            
        try:
            import a2a
        except ImportError:
            missing_deps.append("a2a")
            
        if missing_deps:
            return Problem(
                problem_type=ProblemType.DEPENDENCY_ERROR,
                severity="critical",
                description="缺少必要依赖包",
                affected_components=["应用框架"],
                root_cause="Python依赖包未正确安装",
                solutions=[
                    "使用pip安装缺失依赖",
                    "检查Python环境",
                    "重新创建虚拟环境"
                ],
                diagnostic_data={'missing_dependencies': missing_deps}
            )
            
        return None
        
    def diagnose_all(self) -> List[Problem]:
        """诊断所有问题"""
        problems = []
        
        diagnosers = [
            self.diagnose_configuration,
            self.diagnose_connections,
            self.diagnose_resources,
            self.diagnose_permissions,
            self.diagnose_dependencies
        ]
        
        for diagnoser in diagnosers:
            problem = diagnoser()
            if problem:
                problems.append(problem)
                
        return problems


class SolutionExecutor:
    """解决方案执行器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        
    def execute_solution(self, problem: Problem, solution_index: int) -> Tuple[bool, str]:
        """执行解决方案"""
        if solution_index < 0 or solution_index >= len(problem.solutions):
            return False, "无效的解决方案索引"
            
        solution = problem.solutions[solution_index]
        
        try:
            if problem.problem_type == ProblemType.CONFIGURATION_ERROR:
                return self.fix_configuration(problem, solution)
            elif problem.problem_type == ProblemType.CONNECTION_ERROR:
                return self.fix_connection(problem, solution)
            elif problem.problem_type == ProblemType.RESOURCE_EXHAUSTION:
                return self.fix_resources(problem, solution)
            elif problem.problem_type == ProblemType.PERMISSION_ERROR:
                return self.fix_permissions(problem, solution)
            elif problem.problem_type == ProblemType.DEPENDENCY_ERROR:
                return self.fix_dependencies(problem, solution)
            else:
                return False, "未知问题类型"
                
        except Exception as e:
            return False, f"执行解决方案失败: {e}"
            
    def fix_configuration(self, problem: Problem, solution: str) -> Tuple[bool, str]:
        """修复配置问题"""
        if "重新生成默认配置" in solution:
            try:
                from ..core.config_manager import ConfigManager
                config_manager = ConfigManager()
                config_manager.create_default_config()
                return True, "默认配置已重新生成"
            except Exception as e:
                return False, f"重新生成配置失败: {e}"
                
        return False, "该解决方案需要手动执行"
        
    def fix_connection(self, problem: Problem, solution: str) -> Tuple[bool, str]:
        """修复连接问题"""
        if "重新创建数据库" in solution:
            try:
                from ..data.database_manager import DatabaseManager
                db_manager = DatabaseManager()
                db_path = db_manager.db_path
                
                # 备份现有数据库
                if os.path.exists(db_path):
                    backup_path = f"{db_path}.backup"
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    
                # 重新创建数据库
                db_manager.initialize_database()
                return True, "数据库已重新创建"
            except Exception as e:
                return False, f"重新创建数据库失败: {e}"
                
        return False, "该解决方案需要手动执行"
        
    def fix_resources(self, problem: Problem, solution: str) -> Tuple[bool, str]:
        """修复资源问题"""
        if "清理磁盘空间" in solution:
            try:
                # 清理临时文件
                import tempfile
                temp_dir = tempfile.gettempdir()
                for file in os.listdir(temp_dir):
                    if file.startswith("ai_agent_"):
                        file_path = os.path.join(temp_dir, file)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        except:
                            pass
                return True, "临时文件已清理"
            except Exception as e:
                return False, f"清理磁盘空间失败: {e}"
                
        return False, "该解决方案需要手动执行"
        
    def fix_permissions(self, problem: Problem, solution: str) -> Tuple[bool, str]:
        """修复权限问题"""
        if "修改日志目录权限" in solution:
            try:
                log_dir = "logs"
                if os.path.exists(log_dir):
                    import stat
                    os.chmod(log_dir, stat.S_IRWXU)
                    return True, "日志目录权限已修改"
                else:
                    os.makedirs(log_dir, exist_ok=True)
                    return True, "日志目录已创建"
            except Exception as e:
                return False, f"修改权限失败: {e}"
                
        return False, "该解决方案需要手动执行"
        
    def fix_dependencies(self, problem: Problem, solution: str) -> Tuple[bool, str]:
        """修复依赖问题"""
        if "使用pip安装缺失依赖" in solution:
            missing_deps = problem.diagnostic_data.get('missing_dependencies', [])
            if missing_deps:
                deps_str = " ".join(missing_deps)
                return False, f"请手动执行: pip install {deps_str}"
                
        return False, "该解决方案需要手动执行"


class ProblemDiagnoserWidget(QWidget):
    """问题诊断器组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.diagnoser = ProblemDiagnoser()
        self.solution_executor = SolutionExecutor()
        self.current_problems: List[Problem] = []
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.diagnose_btn = QPushButton("诊断问题")
        toolbar_layout.addWidget(self.diagnose_btn)
        
        self.fix_all_btn = QPushButton("自动修复")
        toolbar_layout.addWidget(self.fix_all_btn)
        
        self.export_btn = QPushButton("导出报告")
        toolbar_layout.addWidget(self.export_btn)
        
        self.clear_btn = QPushButton("清空")
        toolbar_layout.addWidget(self.clear_btn)
        
        toolbar_layout.addStretch()
        
        # 自动诊断
        self.auto_diagnose_check = QCheckBox("自动诊断")
        toolbar_layout.addWidget(self.auto_diagnose_check)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(60, 3600)
        self.interval_spin.setValue(300)
        self.interval_spin.setSuffix(" 秒")
        toolbar_layout.addWidget(QLabel("间隔:"))
        toolbar_layout.addWidget(self.interval_spin)
        
        main_layout.addLayout(toolbar_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：问题列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 问题表格
        self.problems_table = QTableWidget()
        self.problems_table.setColumnCount(4)
        self.problems_table.setHorizontalHeaderLabels([
            "问题类型", "严重程度", "描述", "状态"
        ])
        self.problems_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.problems_table)
        
        splitter.addWidget(left_widget)
        
        # 右侧：问题详情和解决方案
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 问题详情
        detail_group = QGroupBox("问题详情")
        detail_layout = QVBoxLayout(detail_group)
        
        self.problem_detail_text = QTextEdit()
        self.problem_detail_text.setReadOnly(True)
        detail_layout.addWidget(self.problem_detail_text)
        
        right_layout.addWidget(detail_group)
        
        # 解决方案
        solution_group = QGroupBox("解决方案")
        solution_layout = QVBoxLayout(solution_group)
        
        self.solutions_list = QListWidget()
        solution_layout.addWidget(self.solutions_list)
        
        # 执行解决方案按钮
        self.execute_solution_btn = QPushButton("执行选中解决方案")
        solution_layout.addWidget(self.execute_solution_btn)
        
        # 执行结果
        self.execution_result_text = QTextEdit()
        self.execution_result_text.setReadOnly(True)
        self.execution_result_text.setMaximumHeight(100)
        solution_layout.addWidget(self.execution_result_text)
        
        right_layout.addWidget(solution_group)
        
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
    def setup_connections(self):
        """设置信号连接"""
        self.diagnose_btn.clicked.connect(self.diagnose_problems)
        self.fix_all_btn.clicked.connect(self.fix_all_problems)
        self.export_btn.clicked.connect(self.export_report)
        self.clear_btn.clicked.connect(self.clear_diagnosis)
        self.auto_diagnose_check.stateChanged.connect(self.toggle_auto_diagnose)
        self.problems_table.itemSelectionChanged.connect(self.on_problem_selected)
        self.execute_solution_btn.clicked.connect(self.execute_selected_solution)
        
    def diagnose_problems(self):
        """诊断问题"""
        self.diagnose_btn.setEnabled(False)
        self.diagnose_btn.setText("诊断中...")
        QApplication.processEvents()
        
        try:
            problems = self.diagnoser.diagnose_all()
            self.current_problems = problems
            
            self.update_problems_table()
            
            if problems:
                QMessageBox.information(self, "诊断完成", 
                                      f"发现 {len(problems)} 个问题")
            else:
                QMessageBox.information(self, "诊断完成", "未发现问题")
                
        except Exception as e:
            QMessageBox.critical(self, "诊断失败", f"诊断过程出错: {e}")
            
        finally:
            self.diagnose_btn.setEnabled(True)
            self.diagnose_btn.setText("诊断问题")
            
    def update_problems_table(self):
        """更新问题表格"""
        self.problems_table.setRowCount(len(self.current_problems))
        
        for row, problem in enumerate(self.current_problems):
            # 问题类型
            self.problems_table.setItem(row, 0, QTableWidgetItem(problem.problem_type.value))
            
            # 严重程度
            severity_item = QTableWidgetItem(problem.severity)
            # 根据严重程度设置颜色
            if problem.severity == 'critical':
                severity_item.setBackground(QColor(255, 100, 100))
            elif problem.severity == 'high':
                severity_item.setBackground(QColor(255, 200, 100))
            elif problem.severity == 'medium':
                severity_item.setBackground(QColor(255, 255, 100))
            else:
                severity_item.setBackground(QColor(200, 255, 200))
            self.problems_table.setItem(row, 1, severity_item)
            
            # 描述
            self.problems_table.setItem(row, 2, QTableWidgetItem(problem.description))
            
            # 状态
            self.problems_table.setItem(row, 3, QTableWidgetItem("待处理"))
            
    def on_problem_selected(self):
        """问题选中事件"""
        selected_items = self.problems_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        if row < len(self.current_problems):
            problem = self.current_problems[row]
            self.show_problem_details(problem)
            
    def show_problem_details(self, problem: Problem):
        """显示问题详情"""
        detail_text = f"问题类型: {problem.problem_type.value}\n"
        detail_text += f"严重程度: {problem.severity}\n"
        detail_text += f"描述: {problem.description}\n\n"
        
        detail_text += "影响组件:\n"
        for component in problem.affected_components:
            detail_text += f"  - {component}\n"
            
        detail_text += f"\n根本原因: {problem.root_cause}\n\n"
        
        detail_text += "诊断数据:\n"
        for key, value in problem.diagnostic_data.items():
            detail_text += f"  {key}: {value}\n"
            
        self.problem_detail_text.setText(detail_text)
        
        # 更新解决方案列表
        self.solutions_list.clear()
        for i, solution in enumerate(problem.solutions):
            self.solutions_list.addItem(f"{i+1}. {solution}")
            
    def execute_selected_solution(self):
        """执行选中的解决方案"""
        selected_problems = self.problems_table.selectedItems()
        selected_solutions = self.solutions_list.selectedItems()
        
        if not selected_problems or not selected_solutions:
            QMessageBox.warning(self, "执行失败", "请先选择问题和解决方案")
            return
            
        problem_row = selected_problems[0].row()
        solution_row = selected_solutions[0].row()
        
        if problem_row >= len(self.current_problems):
            return
            
        problem = self.current_problems[problem_row]
        
        # 执行解决方案
        success, message = self.solution_executor.execute_solution(problem, solution_row)
        
        # 显示执行结果
        if success:
            self.execution_result_text.setText(f"✅ 执行成功: {message}")
            # 更新问题状态
            self.problems_table.setItem(problem_row, 3, QTableWidgetItem("已修复"))
        else:
            self.execution_result_text.setText(f"❌ 执行失败: {message}")
            
    def fix_all_problems(self):
        """自动修复所有问题"""
        if not self.current_problems:
            QMessageBox.information(self, "自动修复", "没有需要修复的问题")
            return
            
        fixed_count = 0
        failed_count = 0
        
        for problem_row, problem in enumerate(self.current_problems):
            # 尝试每个解决方案，直到成功或全部尝试
            for solution_row in range(len(problem.solutions)):
                success, message = self.solution_executor.execute_solution(problem, solution_row)
                if success:
                    fixed_count += 1
                    self.problems_table.setItem(problem_row, 3, QTableWidgetItem("已修复"))
                    break
                else:
                    failed_count += 1
                    
        result_text = f"自动修复完成:\n"
        result_text += f"成功修复: {fixed_count} 个问题\n"
        result_text += f"修复失败: {failed_count} 个问题"
        
        QMessageBox.information(self, "自动修复结果", result_text)
        
    def export_report(self):
        """导出报告"""
        if not self.current_problems:
            QMessageBox.information(self, "导出", "没有诊断结果可导出")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出问题诊断报告", "", "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("AI Agent Desktop 问题诊断报告\n")
                    f.write(f"生成时间: {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(f"发现 {len(self.current_problems)} 个问题:\n\n")
                    
                    for i, problem in enumerate(self.current_problems, 1):
                        f.write(f"{i}. {problem.description}\n")
                        f.write(f"   类型: {problem.problem_type.value}\n")
                        f.write(f"   严重程度: {problem.severity}\n")
                        f.write(f"   根本原因: {problem.root_cause}\n")
                        f.write(f"   影响组件: {', '.join(problem.affected_components)}\n")
                        f.write("   解决方案:\n")
                        for j, solution in enumerate(problem.solutions, 1):
                            f.write(f"     {j}. {solution}\n")
                        f.write("\n")
                        
                QMessageBox.information(self, "导出", "问题诊断报告导出成功")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {e}")
                
    def clear_diagnosis(self):
        """清空诊断"""
        self.current_problems.clear()
        self.problems_table.setRowCount(0)
        self.problem_detail_text.clear()
        self.solutions_list.clear()
        self.execution_result_text.clear()
        
    def toggle_auto_diagnose(self, state: int):
        """切换自动诊断"""
        if state == Qt.CheckState.Checked.value:
            self.start_auto_diagnose()
        else:
            self.stop_auto_diagnose()
            
    def start_auto_diagnose(self):
        """开始自动诊断"""
        interval = self.interval_spin.value() * 1000  # 转换为毫秒
        self.auto_diagnose_timer = QTimer()
        self.auto_diagnose_timer.timeout.connect(self.diagnose_problems)
        self.auto_diagnose_timer.start(interval)
        
    def stop_auto_diagnose(self):
        """停止自动诊断"""
        if hasattr(self, 'auto_diagnose_timer'):
            self.auto_diagnose_timer.stop()
