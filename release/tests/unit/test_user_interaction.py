"""
用户交互功能测试
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ui.user_interaction_manager import (
    ShortcutManager, ShortcutAction, ShortcutConfig,
    DragDropManager, ContextMenuManager, PerformanceOptimizer,
    UserInteractionManager, InteractionOptimizer
)
from src.ui.operation_optimizer import (
    SmartTipManager, BatchOperationManager, OperationWizard,
    AnimationManager, OperationFlowOptimizer, QuickActionManager,
    OperationType
)


class TestShortcutManager(unittest.TestCase):
    """快捷键管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.shortcut_manager = ShortcutManager(self.mock_widget)
        
    def test_shortcut_config_creation(self):
        """测试快捷键配置创建"""
        config = ShortcutConfig(
            ShortcutAction.NEW_AGENT,
            Mock(),
            "创建新代理"
        )
        
        self.assertEqual(config.action, ShortcutAction.NEW_AGENT)
        self.assertEqual(config.description, "创建新代理")
        self.assertTrue(config.enabled)
        
    def test_default_shortcuts_setup(self):
        """测试默认快捷键设置"""
        self.assertEqual(len(self.shortcut_manager.shortcut_configs), 10)
        
        # 检查关键快捷键是否存在
        actions = [config.action for config in self.shortcut_manager.shortcut_configs]
        self.assertIn(ShortcutAction.NEW_AGENT, actions)
        self.assertIn(ShortcutAction.OPEN_DEBUG_TOOLS, actions)
        self.assertIn(ShortcutAction.SAVE_CONFIG, actions)
        
    def test_register_shortcut(self):
        """测试注册快捷键"""
        callback = Mock()
        success = self.shortcut_manager.register_shortcut(ShortcutAction.NEW_AGENT, callback)
        
        self.assertTrue(success)
        self.assertIn(ShortcutAction.NEW_AGENT, self.shortcut_manager.shortcuts)
        
    def test_unregister_shortcut(self):
        """测试取消注册快捷键"""
        callback = Mock()
        self.shortcut_manager.register_shortcut(ShortcutAction.NEW_AGENT, callback)
        self.shortcut_manager.unregister_shortcut(ShortcutAction.NEW_AGENT)
        
        self.assertNotIn(ShortcutAction.NEW_AGENT, self.shortcut_manager.shortcuts)
        
    def test_get_shortcut_list(self):
        """测试获取快捷键列表"""
        shortcut_list = self.shortcut_manager.get_shortcut_list()
        
        self.assertEqual(len(shortcut_list), 10)
        self.assertIsInstance(shortcut_list[0], dict)
        self.assertIn('action', shortcut_list[0])
        self.assertIn('key_sequence', shortcut_list[0])
        self.assertIn('description', shortcut_list[0])


class TestDragDropManager(unittest.TestCase):
    """拖拽管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.drag_drop_manager = DragDropManager(self.mock_widget)
        
    def test_setup_drag_drop(self):
        """测试拖拽设置"""
        self.drag_drop_manager.setup_drag_drop()
        self.mock_widget.setAcceptDrops.assert_called_once_with(True)
        
    def test_enable_drag_drop(self):
        """测试启用拖拽"""
        self.drag_drop_manager.enable_drag_drop()
        self.mock_widget.setAcceptDrops.assert_called_once_with(True)
        
    def test_disable_drag_drop(self):
        """测试禁用拖拽"""
        self.drag_drop_manager.disable_drag_drop()
        self.mock_widget.setAcceptDrops.assert_called_once_with(False)


class TestContextMenuManager(unittest.TestCase):
    """上下文菜单管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.context_menu_manager = ContextMenuManager(self.mock_widget)
        
    def test_create_context_menu(self):
        """测试创建上下文菜单"""
        menu = self.context_menu_manager.create_context_menu("test_menu", "测试菜单")
        
        self.assertIsNotNone(menu)
        self.assertIn("test_menu", self.context_menu_manager.context_menus)
        
    def test_add_menu_action(self):
        """测试添加菜单动作"""
        callback = Mock()
        action = self.context_menu_manager.add_menu_action(
            "test_menu", "测试动作", callback
        )
        
        self.assertIsNotNone(action)
        self.assertIn("test_menu", self.context_menu_manager.context_menus)
        
    def test_add_menu_separator(self):
        """测试添加菜单分隔符"""
        self.context_menu_manager.create_context_menu("test_menu")
        self.context_menu_manager.add_menu_separator("test_menu")
        
        # 验证分隔符已添加
        self.assertIn("test_menu", self.context_menu_manager.context_menus)


class TestPerformanceOptimizer(unittest.TestCase):
    """性能优化器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.performance_optimizer = PerformanceOptimizer()
        
    def test_optimize_table_performance(self):
        """测试表格性能优化"""
        mock_table = Mock()
        self.performance_optimizer.optimize_table_performance(mock_table)
        
        # 验证表格优化选项设置
        mock_table.setSortingEnabled.assert_called_once_with(False)
        mock_table.setAlternatingRowColors.assert_called_once_with(True)
        
    def test_optimize_tree_performance(self):
        """测试树形控件性能优化"""
        mock_tree = Mock()
        self.performance_optimizer.optimize_tree_performance(mock_tree)
        
        mock_tree.setSortingEnabled.assert_called_once_with(False)
        mock_tree.setAlternatingRowColors.assert_called_once_with(True)


class TestSmartTipManager(unittest.TestCase):
    """智能提示管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.smart_tip_manager = SmartTipManager(self.mock_widget)
        
    def test_enable_disable_tips(self):
        """测试启用禁用提示"""
        self.smart_tip_manager.enable_tips()
        self.assertTrue(self.smart_tip_manager.tips_enabled)
        
        self.smart_tip_manager.disable_tips()
        self.assertFalse(self.smart_tip_manager.tips_enabled)
        
    @patch('src.ui.operation_optimizer.QToolTip.showText')
    def test_show_context_tip(self, mock_show_text):
        """测试显示上下文提示"""
        mock_widget = Mock()
        mock_widget.objectName.return_value = "test_widget"
        mock_widget.rect.return_value = Mock()
        mock_widget.mapToGlobal.return_value = Mock()
        
        self.smart_tip_manager.show_context_tip(mock_widget, "测试提示", 3000)
        
        # 验证提示历史记录
        self.assertEqual(len(self.smart_tip_manager.tip_history), 1)
        self.assertEqual(self.smart_tip_manager.tip_history[0]['tip_text'], "测试提示")
        
        # 验证工具提示显示
        mock_show_text.assert_called_once()


class TestBatchOperationManager(unittest.TestCase):
    """批量操作管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.batch_operation_manager = BatchOperationManager(self.mock_widget)
        
    def test_batch_operations_setup(self):
        """测试批量操作设置"""
        self.assertEqual(len(self.batch_operation_manager.batch_operations), 5)
        
        # 检查关键批量操作是否存在
        self.assertIn('start_all_agents', self.batch_operation_manager.batch_operations)
        self.assertIn('stop_all_agents', self.batch_operation_manager.batch_operations)
        self.assertIn('test_all_capabilities', self.batch_operation_manager.batch_operations)
        
    @patch('src.ui.operation_optimizer.QProgressDialog')
    @patch('src.ui.operation_optimizer.QApplication.processEvents')
    def test_start_all_agents(self, mock_process_events, mock_progress_dialog):
        """测试启动所有代理"""
        mock_dialog_instance = Mock()
        mock_progress_dialog.return_value = mock_dialog_instance
        
        self.batch_operation_manager.start_all_agents()
        
        # 验证进度对话框创建和显示
        mock_progress_dialog.assert_called_once()
        mock_dialog_instance.show.assert_called_once()
        mock_dialog_instance.setValue.assert_called()


class TestOperationWizard(unittest.TestCase):
    """操作向导测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.operation_wizard = OperationWizard(self.mock_widget)
        
    def test_create_agent_creation_wizard(self):
        """测试创建代理创建向导"""
        wizard = self.operation_wizard.create_agent_creation_wizard()
        
        self.assertIsNotNone(wizard)
        self.assertEqual(wizard.windowTitle(), "代理创建向导")
        self.assertEqual(wizard.pageCount(), 4)  # 4个页面


class TestAnimationManager(unittest.TestCase):
    """动画管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.animation_manager = AnimationManager()
        
    def test_enable_disable_animations(self):
        """测试启用禁用动画"""
        self.animation_manager.enable_animations()
        self.assertTrue(self.animation_manager.animations_enabled)
        
        self.animation_manager.disable_animations()
        self.assertFalse(self.animation_manager.animations_enabled)


class TestQuickActionManager(unittest.TestCase):
    """快速操作管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.quick_action_manager = QuickActionManager(self.mock_widget)
        
    def test_quick_actions_setup(self):
        """测试快速操作设置"""
        self.assertEqual(len(self.quick_action_manager.quick_actions), 4)
        
        # 检查关键快速操作是否存在
        self.assertIn('quick_create_agent', self.quick_action_manager.quick_actions)
        self.assertIn('quick_test_capability', self.quick_action_manager.quick_actions)
        self.assertIn('quick_export_report', self.quick_action_manager.quick_actions)


class TestUserInteractionIntegration(unittest.TestCase):
    """用户交互集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_main_window = Mock()
        self.user_interaction_manager = UserInteractionManager(self.mock_main_window)
        
    def test_user_interaction_manager_initialization(self):
        """测试用户交互管理器初始化"""
        self.assertIsNotNone(self.user_interaction_manager.shortcut_manager)
        self.assertIsNotNone(self.user_interaction_manager.context_menu_manager)
        self.assertIsNotNone(self.user_interaction_manager.performance_optimizer)
        
    def test_setup_global_shortcuts(self):
        """测试设置全局快捷键"""
        self.user_interaction_manager.setup_global_shortcuts()
        
        # 验证快捷键已注册
        self.assertGreater(len(self.user_interaction_manager.shortcut_manager.shortcuts), 0)
        
    def test_setup_context_menus(self):
        """测试设置上下文菜单"""
        self.user_interaction_manager.setup_context_menus()
        
        # 验证上下文菜单已创建
        self.assertIn("agent_list", self.user_interaction_manager.context_menu_manager.context_menus)
        self.assertIn("capability_list", self.user_interaction_manager.context_menu_manager.context_menus)


if __name__ == '__main__':
    unittest.main()
