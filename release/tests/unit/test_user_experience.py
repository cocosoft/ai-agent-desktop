"""
用户体验优化测试
测试用户反馈收集、界面布局改进、操作流程优化、帮助提示和错误信息完善功能
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch

from src.ui.user_feedback_manager import (
    UserFeedbackManager,
    UserFeedback,
    FeedbackType,
    FeedbackPriority,
    HelpTooltipManager,
    ErrorMessageManager,
    UserExperienceOptimizer
)


class TestUserFeedbackManager:
    """用户反馈管理器测试"""
    
    def setup_method(self):
        """测试方法设置"""
        # 创建临时文件用于测试
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # 创建用户反馈管理器实例
        self.feedback_manager = UserFeedbackManager()
        self.feedback_manager.feedback_file = self.temp_file.name
        self.feedback_manager.feedback_data = []
    
    def teardown_method(self):
        """测试方法清理"""
        # 删除临时文件
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_user_feedback_manager_initialization(self):
        """测试用户反馈管理器初始化"""
        assert self.feedback_manager.feedback_data == []
        assert self.feedback_manager.feedback_file == self.temp_file.name
    
    def test_load_feedback_empty_file(self):
        """测试加载空反馈文件"""
        # 确保文件存在但为空
        with open(self.temp_file.name, 'w') as f:
            f.write('')
        
        self.feedback_manager.load_feedback()
        assert self.feedback_manager.feedback_data == []
    
    def test_load_feedback_with_data(self):
        """测试加载有数据的反馈文件"""
        # 创建测试数据
        test_data = [
            {
                "feedback_id": "test_1",
                "feedback_type": "bug_report",
                "title": "测试反馈",
                "description": "这是一个测试反馈",
                "priority": "medium",
                "user_email": "test@example.com",
                "screenshots": [],
                "system_info": {},
                "created_at": "2025-01-01T00:00:00",
                "status": "new"
            }
        ]
        
        # 写入测试数据
        with open(self.temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 加载数据
        self.feedback_manager.load_feedback()
        
        # 验证数据
        assert len(self.feedback_manager.feedback_data) == 1
        feedback = self.feedback_manager.feedback_data[0]
        assert feedback.feedback_id == "test_1"
        assert feedback.title == "测试反馈"
        assert feedback.description == "这是一个测试反馈"
    
    def test_save_feedback(self):
        """测试保存反馈数据"""
        # 创建测试反馈
        feedback = UserFeedback(
            feedback_id="test_save",
            feedback_type=FeedbackType.BUG_REPORT,
            title="保存测试",
            description="测试保存功能",
            priority=FeedbackPriority.HIGH
        )
        
        # 添加反馈
        self.feedback_manager.feedback_data.append(feedback)
        
        # 保存反馈
        self.feedback_manager.save_feedback()
        
        # 验证文件内容
        with open(self.temp_file.name, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1
        assert saved_data[0]["feedback_id"] == "test_save"
        assert saved_data[0]["title"] == "保存测试"
    
    def test_submit_feedback(self):
        """测试提交反馈"""
        feedback = UserFeedback(
            feedback_id="",
            feedback_type=FeedbackType.FEATURE_REQUEST,
            title="新功能请求",
            description="希望添加新功能",
            priority=FeedbackPriority.MEDIUM,
            user_email="user@example.com"
        )
        
        # 提交反馈
        result = self.feedback_manager.submit_feedback(feedback)
        
        # 验证结果
        assert result is True
        assert len(self.feedback_manager.feedback_data) == 1
        
        saved_feedback = self.feedback_manager.feedback_data[0]
        assert saved_feedback.title == "新功能请求"
        assert saved_feedback.user_email == "user@example.com"
        assert saved_feedback.feedback_id.startswith("feedback_")
        assert saved_feedback.system_info is not None
    
    def test_get_feedback_stats(self):
        """测试获取反馈统计"""
        # 添加测试反馈数据
        feedbacks = [
            UserFeedback(
                feedback_id=f"test_{i}",
                feedback_type=FeedbackType.BUG_REPORT if i % 2 == 0 else FeedbackType.FEATURE_REQUEST,
                title=f"反馈{i}",
                description=f"描述{i}",
                priority=FeedbackPriority.HIGH if i < 2 else FeedbackPriority.LOW
            )
            for i in range(4)
        ]
        
        self.feedback_manager.feedback_data = feedbacks
        
        # 获取统计信息
        stats = self.feedback_manager.get_feedback_stats()
        
        # 验证统计信息
        assert stats["total_feedback"] == 4
        assert stats["by_type"]["bug_report"] == 2
        assert stats["by_type"]["feature_request"] == 2
        assert stats["by_priority"]["high"] == 2
        assert stats["by_priority"]["low"] == 2
        assert stats["by_status"]["new"] == 4


class TestHelpTooltipManager:
    """帮助提示管理器测试"""
    
    def test_help_tooltip_manager_initialization(self):
        """测试帮助提示管理器初始化"""
        manager = HelpTooltipManager()
        assert manager.tooltips is not None
        assert len(manager.tooltips) > 0
    
    def test_get_tooltip_existing_key(self):
        """测试获取存在的帮助提示"""
        manager = HelpTooltipManager()
        
        tooltip = manager.get_tooltip("main_window")
        
        assert tooltip["title"] == "AI代理管理应用"
        assert "AI代理管理应用" in tooltip["content"]
    
    def test_get_tooltip_non_existing_key(self):
        """测试获取不存在的帮助提示"""
        manager = HelpTooltipManager()
        
        tooltip = manager.get_tooltip("non_existing_key")
        
        assert tooltip["title"] == "帮助"
        assert tooltip["content"] == "暂无帮助信息"


class TestErrorMessageManager:
    """错误信息管理器测试"""
    
    def test_error_message_manager_initialization(self):
        """测试错误信息管理器初始化"""
        manager = ErrorMessageManager()
        assert manager.error_messages is not None
        assert len(manager.error_messages) > 0
    
    def test_get_error_message_existing_key(self):
        """测试获取存在的错误信息"""
        manager = ErrorMessageManager()
        
        error_info = manager.get_error_message("database_connection_failed")
        
        assert error_info["title"] == "数据库连接失败"
        assert "无法连接到数据库" in error_info["message"]
        assert "请尝试重启应用" in error_info["suggestion"]
    
    def test_get_error_message_with_details(self):
        """测试获取带详细信息的错误信息"""
        manager = ErrorMessageManager()
        
        error_info = manager.get_error_message("database_connection_failed", "文件被占用")
        
        assert "数据库连接失败" in error_info["title"]
        assert "文件被占用" in error_info["message"]
    
    def test_get_error_message_non_existing_key(self):
        """测试获取不存在的错误信息"""
        manager = ErrorMessageManager()
        
        error_info = manager.get_error_message("non_existing_error")
        
        assert error_info["title"] == "未知错误"
        assert "发生了一个未知错误" in error_info["message"]


class TestUserExperienceOptimizer:
    """用户体验优化器测试"""
    
    def setup_method(self):
        """测试方法设置"""
        self.ux_optimizer = UserExperienceOptimizer()
    
    def test_user_experience_optimizer_initialization(self):
        """测试用户体验优化器初始化"""
        assert self.ux_optimizer.feedback_manager is not None
        assert self.ux_optimizer.help_tooltip_manager is not None
        assert self.ux_optimizer.error_message_manager is not None
        assert self.ux_optimizer.user_metrics is not None
    
    def test_start_user_session(self):
        """测试开始用户会话"""
        self.ux_optimizer.start_user_session()
        
        assert self.ux_optimizer.user_metrics["session_start_time"] is not None
        assert self.ux_optimizer.user_metrics["operations_count"] == 0
        assert self.ux_optimizer.user_metrics["errors_count"] == 0
        assert self.ux_optimizer.user_metrics["feedback_count"] == 0
    
    def test_record_operation(self):
        """测试记录用户操作"""
        self.ux_optimizer.start_user_session()
        
        # 记录操作
        self.ux_optimizer.record_operation("创建代理")
        self.ux_optimizer.record_operation("启动代理")
        
        assert self.ux_optimizer.user_metrics["operations_count"] == 2
    
    def test_record_error(self):
        """测试记录错误"""
        self.ux_optimizer.start_user_session()
        
        # 记录错误
        self.ux_optimizer.record_error("database_connection_failed", "数据库文件被占用")
        
        assert self.ux_optimizer.user_metrics["errors_count"] == 1
    
    def test_record_feedback(self):
        """测试记录反馈"""
        self.ux_optimizer.start_user_session()
        
        # 记录反馈
        self.ux_optimizer.record_feedback(FeedbackType.BUG_REPORT)
        
        assert self.ux_optimizer.user_metrics["feedback_count"] == 1
    
    def test_get_user_experience_score_no_operations(self):
        """测试获取用户体验评分（无操作）"""
        self.ux_optimizer.start_user_session()
        
        score = self.ux_optimizer.get_user_experience_score()
        
        assert score == 100.0
    
    def test_get_user_experience_score_with_operations(self):
        """测试获取用户体验评分（有操作）"""
        self.ux_optimizer.start_user_session()
        
        # 记录一些操作和错误
        for i in range(10):
            self.ux_optimizer.record_operation(f"操作{i}")
        
        for i in range(2):
            self.ux_optimizer.record_error("test_error")
        
        self.ux_optimizer.record_feedback(FeedbackType.FEATURE_REQUEST)
        
        score = self.ux_optimizer.get_user_experience_score()
        
        # 验证评分在合理范围内
        assert 0 <= score <= 100
    
    def test_get_optimization_suggestions_no_issues(self):
        """测试获取优化建议（无问题）"""
        self.ux_optimizer.start_user_session()
        
        # 记录一些操作
        for i in range(20):
            self.ux_optimizer.record_operation(f"操作{i}")
        
        self.ux_optimizer.record_feedback(FeedbackType.GENERAL_FEEDBACK)
        
        suggestions = self.ux_optimizer.get_optimization_suggestions()
        
        assert "用户体验良好，继续保持" in suggestions
    
    def test_get_optimization_suggestions_with_high_error_rate(self):
        """测试获取优化建议（高错误率）"""
        self.ux_optimizer.start_user_session()
        
        # 记录操作和错误（高错误率）
        for i in range(10):
            self.ux_optimizer.record_operation(f"操作{i}")
        
        for i in range(3):  # 30% 错误率
            self.ux_optimizer.record_error("test_error")
        
        suggestions = self.ux_optimizer.get_optimization_suggestions()
        
        assert "错误率较高，建议改进错误处理和用户提示" in suggestions
    
    def test_get_optimization_suggestions_with_low_operations(self):
        """测试获取优化建议（低操作次数）"""
        self.ux_optimizer.start_user_session()
        
        # 记录少量操作
        for i in range(5):
            self.ux_optimizer.record_operation(f"操作{i}")
        
        suggestions = self.ux_optimizer.get_optimization_suggestions()
        
        assert "用户操作较少，建议优化新手引导" in suggestions
    
    def test_end_user_session(self):
        """测试结束用户会话"""
        self.ux_optimizer.start_user_session()
        
        # 记录一些操作
        self.ux_optimizer.record_operation("测试操作")
        self.ux_optimizer.record_error("test_error")
        
        # 结束会话
        self.ux_optimizer.end_user_session()
        
        # 验证会话数据仍然存在
        assert self.ux_optimizer.user_metrics["operations_count"] == 1
        assert self.ux_optimizer.user_metrics["errors_count"] == 1


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
