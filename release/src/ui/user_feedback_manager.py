"""
用户反馈管理器
用于收集用户反馈、改进界面布局、优化操作流程、添加帮助提示和完善错误信息
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class FeedbackEncoder(json.JSONEncoder):
    """自定义JSON编码器，用于处理枚举类型"""
    
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QComboBox, QPushButton, QCheckBox, QMessageBox, QProgressBar,
    QWidget, QTabWidget, QFormLayout, QSpinBox, QSlider
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from src.utils.logger import get_log_manager
from src.utils.config_loader import init_config_loader


class FeedbackType(Enum):
    """反馈类型枚举"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    UI_IMPROVEMENT = "ui_improvement"
    PERFORMANCE_ISSUE = "performance_issue"
    GENERAL_FEEDBACK = "general_feedback"


class FeedbackPriority(Enum):
    """反馈优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UserFeedback:
    """用户反馈数据类"""
    feedback_id: str
    feedback_type: FeedbackType
    title: str
    description: str
    priority: FeedbackPriority
    user_email: str = ""
    screenshots: List[str] = None
    system_info: Dict[str, Any] = None
    created_at: str = ""
    status: str = "new"
    
    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
        if self.system_info is None:
            self.system_info = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class UserFeedbackManager:
    """用户反馈管理器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        self.config_manager = init_config_loader()
        self.feedback_file = "data/user_feedback.json"
        self.feedback_data: List[UserFeedback] = []
        
        # 创建反馈目录
        os.makedirs("data", exist_ok=True)
        
        # 加载现有反馈
        self.load_feedback()
    
    def load_feedback(self):
        """加载用户反馈数据"""
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_data = [
                        UserFeedback(**item) for item in data
                    ]
                self.logger.info(f"已加载 {len(self.feedback_data)} 条用户反馈")
            else:
                self.feedback_data = []
                self.logger.info("用户反馈文件不存在，创建新文件")
        except Exception as e:
            self.logger.error(f"加载用户反馈失败: {e}")
            self.feedback_data = []
    
    def save_feedback(self):
        """保存用户反馈数据"""
        try:
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [asdict(feedback) for feedback in self.feedback_data],
                    f, 
                    ensure_ascii=False, 
                    indent=2,
                    cls=FeedbackEncoder
                )
            self.logger.info("用户反馈已保存")
        except Exception as e:
            self.logger.error(f"保存用户反馈失败: {e}")
    
    def submit_feedback(self, feedback: UserFeedback) -> bool:
        """提交用户反馈"""
        try:
            # 生成唯一ID
            feedback.feedback_id = f"feedback_{int(time.time())}_{len(self.feedback_data)}"
            
            # 添加系统信息
            feedback.system_info = self._get_system_info()
            
            # 添加到数据列表
            self.feedback_data.append(feedback)
            
            # 保存到文件
            self.save_feedback()
            
            self.logger.info(f"用户反馈已提交: {feedback.title}")
            return True
        except Exception as e:
            self.logger.error(f"提交用户反馈失败: {e}")
            return False
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        stats = {
            "total_feedback": len(self.feedback_data),
            "by_type": {},
            "by_priority": {},
            "by_status": {}
        }
        
        for feedback in self.feedback_data:
            # 按类型统计
            f_type = feedback.feedback_type.value
            stats["by_type"][f_type] = stats["by_type"].get(f_type, 0) + 1
            
            # 按优先级统计
            f_priority = feedback.priority.value
            stats["by_priority"][f_priority] = stats["by_priority"].get(f_priority, 0) + 1
            
            # 按状态统计
            f_status = feedback.status
            stats["by_status"][f_status] = stats["by_status"].get(f_status, 0) + 1
        
        return stats
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "app_version": "1.0.0",  # 应该从配置中获取
            "timestamp": datetime.now().isoformat()
        }


class FeedbackDialog(QDialog):
    """用户反馈对话框"""
    
    feedback_submitted = pyqtSignal(UserFeedback)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.feedback_manager = UserFeedbackManager()
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("用户反馈")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # 反馈类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("反馈类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Bug报告", "功能请求", "界面改进", "性能问题", "一般反馈"
        ])
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 优先级选择
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("优先级:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["低", "中", "高", "紧急"])
        priority_layout.addWidget(self.priority_combo)
        priority_layout.addStretch()
        layout.addLayout(priority_layout)
        
        # 标题输入
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("标题:"))
        self.title_edit = QTextEdit()
        self.title_edit.setMaximumHeight(30)
        self.title_edit.setPlaceholderText("请输入反馈标题...")
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)
        
        # 描述输入
        layout.addWidget(QLabel("详细描述:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("请详细描述您的问题或建议...")
        layout.addWidget(self.description_edit)
        
        # 邮箱输入
        email_layout = QHBoxLayout()
        email_layout.addWidget(QLabel("邮箱 (可选):"))
        self.email_edit = QTextEdit()
        self.email_edit.setMaximumHeight(30)
        self.email_edit.setPlaceholderText("请输入您的邮箱以便我们回复...")
        email_layout.addWidget(self.email_edit)
        layout.addLayout(email_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.submit_btn = QPushButton("提交反馈")
        self.submit_btn.clicked.connect(self.submit_feedback)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def submit_feedback(self):
        """提交反馈"""
        # 获取输入数据
        feedback_type_map = {
            0: FeedbackType.BUG_REPORT,
            1: FeedbackType.FEATURE_REQUEST,
            2: FeedbackType.UI_IMPROVEMENT,
            3: FeedbackType.PERFORMANCE_ISSUE,
            4: FeedbackType.GENERAL_FEEDBACK
        }
        
        priority_map = {
            0: FeedbackPriority.LOW,
            1: FeedbackPriority.MEDIUM,
            2: FeedbackPriority.HIGH,
            3: FeedbackPriority.CRITICAL
        }
        
        feedback_type = feedback_type_map[self.type_combo.currentIndex()]
        priority = priority_map[self.priority_combo.currentIndex()]
        title = self.title_edit.toPlainText().strip()
        description = self.description_edit.toPlainText().strip()
        email = self.email_edit.toPlainText().strip()
        
        # 验证输入
        if not title:
            QMessageBox.warning(self, "输入错误", "请输入反馈标题")
            return
        
        if not description:
            QMessageBox.warning(self, "输入错误", "请输入详细描述")
            return
        
        # 创建反馈对象
        feedback = UserFeedback(
            feedback_id="",
            feedback_type=feedback_type,
            title=title,
            description=description,
            priority=priority,
            user_email=email
        )
        
        # 提交反馈
        if self.feedback_manager.submit_feedback(feedback):
            QMessageBox.information(self, "提交成功", "感谢您的反馈！")
            self.feedback_submitted.emit(feedback)
            self.accept()
        else:
            QMessageBox.critical(self, "提交失败", "反馈提交失败，请稍后重试")


class HelpTooltipManager:
    """帮助提示管理器"""
    
    def __init__(self):
        self.tooltips = {
            # 主界面帮助提示
            "main_window": {
                "title": "AI代理管理应用",
                "content": "这是一个AI代理管理应用，您可以在这里创建和管理AI代理，配置模型能力，监控代理性能。"
            },
            
            # 代理管理帮助提示
            "agent_management": {
                "title": "代理管理",
                "content": "在这里您可以创建、编辑、启动和停止AI代理。每个代理可以配置不同的能力和模型。"
            },
            
            # 能力管理帮助提示
            "capability_management": {
                "title": "能力管理",
                "content": "管理AI模型的能力，包括文本生成、代码生成、翻译等。您可以测试和配置不同的能力。"
            },
            
            # 模型管理帮助提示
            "model_management": {
                "title": "模型管理",
                "content": "配置和管理AI模型，包括Ollama、OpenAI等。您可以设置API密钥和模型参数。"
            },
            
            # 配置管理帮助提示
            "config_management": {
                "title": "配置管理",
                "content": "配置应用的各种设置，包括主题、快捷键、数据导入导出等。"
            }
        }
    
    def get_tooltip(self, key: str) -> Dict[str, str]:
        """获取帮助提示"""
        return self.tooltips.get(key, {
            "title": "帮助",
            "content": "暂无帮助信息"
        })


class ErrorMessageManager:
    """错误信息管理器"""
    
    def __init__(self):
        self.error_messages = {
            # 数据库错误
            "database_connection_failed": {
                "title": "数据库连接失败",
                "message": "无法连接到数据库，请检查数据库文件是否被占用或损坏。",
                "suggestion": "请尝试重启应用或检查数据库文件权限。"
            },
            
            # 网络错误
            "network_connection_failed": {
                "title": "网络连接失败",
                "message": "无法连接到服务器，请检查网络连接。",
                "suggestion": "请检查您的网络连接，或稍后重试。"
            },
            
            # 模型连接错误
            "model_connection_failed": {
                "title": "模型连接失败",
                "message": "无法连接到AI模型服务。",
                "suggestion": "请检查模型服务是否运行，或检查API密钥是否正确。"
            },
            
            # 配置错误
            "config_validation_failed": {
                "title": "配置验证失败",
                "message": "配置文件存在错误，无法加载应用配置。",
                "suggestion": "请检查配置文件格式，或恢复默认配置。"
            },
            
            # 权限错误
            "permission_denied": {
                "title": "权限不足",
                "message": "没有足够的权限执行此操作。",
                "suggestion": "请以管理员身份运行应用，或检查文件权限。"
            }
        }
    
    def get_error_message(self, error_key: str, details: str = "") -> Dict[str, str]:
        """获取错误信息"""
        error_info = self.error_messages.get(error_key, {
            "title": "未知错误",
            "message": "发生了一个未知错误。",
            "suggestion": "请尝试重启应用或联系技术支持。"
        })
        
        if details:
            error_info["message"] += f"\n\n详细信息: {details}"
        
        return error_info


class UserExperienceOptimizer:
    """用户体验优化器"""
    
    def __init__(self):
        self.feedback_manager = UserFeedbackManager()
        self.help_tooltip_manager = HelpTooltipManager()
        self.error_message_manager = ErrorMessageManager()
        self.logger = get_log_manager().logger
        
        # 用户体验指标
        self.user_metrics = {
            "session_start_time": None,
            "operations_count": 0,
            "errors_count": 0,
            "feedback_count": 0
        }
    
    def start_user_session(self):
        """开始用户会话"""
        self.user_metrics["session_start_time"] = datetime.now()
        self.user_metrics["operations_count"] = 0
        self.user_metrics["errors_count"] = 0
        self.logger.info("用户会话已开始")
    
    def end_user_session(self):
        """结束用户会话"""
        session_duration = datetime.now() - self.user_metrics["session_start_time"]
        self.logger.info(
            f"用户会话结束 - 操作次数: {self.user_metrics['operations_count']}, "
            f"错误次数: {self.user_metrics['errors_count']}, "
            f"会话时长: {session_duration}"
        )
    
    def record_operation(self, operation_name: str):
        """记录用户操作"""
        self.user_metrics["operations_count"] += 1
        self.logger.debug(f"用户操作: {operation_name}")
    
    def record_error(self, error_type: str, error_details: str = ""):
        """记录错误"""
        self.user_metrics["errors_count"] += 1
        error_info = self.error_message_manager.get_error_message(error_type, error_details)
        self.logger.error(f"用户错误: {error_info['title']} - {error_details}")
    
    def record_feedback(self, feedback_type: FeedbackType):
        """记录反馈"""
        self.user_metrics["feedback_count"] += 1
        self.logger.info(f"用户反馈: {feedback_type.value}")
    
    def get_user_experience_score(self) -> float:
        """计算用户体验评分"""
        if self.user_metrics["operations_count"] == 0:
            return 100.0
        
        error_rate = self.user_metrics["errors_count"] / self.user_metrics["operations_count"]
        feedback_rate = self.user_metrics["feedback_count"] / self.user_metrics["operations_count"]
        
        # 基础评分 (100分)
        score = 100.0
        
        # 错误率扣分 (每个错误扣10分)
        score -= error_rate * 100 * 10
        
        # 反馈率加分 (每个反馈加5分)
        score += feedback_rate * 100 * 5
        
        # 确保评分在0-100之间
        return max(0.0, min(100.0, score))
    
    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        # 基于错误率的建议
        if self.user_metrics["errors_count"] > 0:
            error_rate = self.user_metrics["errors_count"] / self.user_metrics["operations_count"]
            if error_rate > 0.1:
                suggestions.append("错误率较高，建议改进错误处理和用户提示")
            elif error_rate > 0.05:
                suggestions.append("错误率适中，建议优化常见错误场景")
        
        # 基于反馈的建议
        if self.user_metrics["feedback_count"] == 0:
            suggestions.append("用户反馈较少，建议增加反馈收集机制")
        
        # 基于操作次数的建议
        if self.user_metrics["operations_count"] < 10:
            suggestions.append("用户操作较少，建议优化新手引导")
        
        if not suggestions:
            suggestions.append("用户体验良好，继续保持")
        
        return suggestions


# 全局用户体验优化器实例
global_ux_optimizer: Optional[UserExperienceOptimizer] = None


def get_ux_optimizer() -> UserExperienceOptimizer:
    """获取全局用户体验优化器实例"""
    global global_ux_optimizer
    if global_ux_optimizer is None:
        global_ux_optimizer = UserExperienceOptimizer()
    return global_ux_optimizer


def show_feedback_dialog(parent=None):
    """显示反馈对话框"""
    dialog = FeedbackDialog(parent)
    return dialog.exec()
