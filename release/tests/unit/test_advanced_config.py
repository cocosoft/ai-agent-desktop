"""
高级配置功能测试
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ui.advanced_config_manager import (
    ThemeManager, ThemeConfig, ThemeType,
    ShortcutConfigManager, DataExportManager,
    AdvancedConfigManager
)


class TestThemeManager(unittest.TestCase):
    """主题管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.theme_manager = ThemeManager(self.mock_widget)
        
    def test_default_themes_setup(self):
        """测试默认主题设置"""
        self.assertEqual(len(self.theme_manager.available_themes), 4)
        
        # 检查关键主题是否存在
        self.assertIn("light", self.theme_manager.available_themes)
        self.assertIn("dark", self.theme_manager.available_themes)
        self.assertIn("blue", self.theme_manager.available_themes)
        self.assertIn("green", self.theme_manager.available_themes)
        
    def test_theme_config_creation(self):
        """测试主题配置创建"""
        theme_config = ThemeConfig(
            name="测试主题",
            type=ThemeType.CUSTOM,
            primary_color=Mock(),
            secondary_color=Mock(),
            background_color=Mock(),
            text_color=Mock(),
            accent_color=Mock(),
            font_family="Arial",
            font_size=12
        )
        
        self.assertEqual(theme_config.name, "测试主题")
        self.assertEqual(theme_config.type, ThemeType.CUSTOM)
        self.assertEqual(theme_config.font_family, "Arial")
        self.assertEqual(theme_config.font_size, 12)
        
    def test_apply_theme(self):
        """测试应用主题"""
        success = self.theme_manager.apply_theme("light")
        
        self.assertTrue(success)
        self.assertIsNotNone(self.theme_manager.current_theme)
        self.assertEqual(self.theme_manager.current_theme.name, "浅色主题")
        
    def test_apply_nonexistent_theme(self):
        """测试应用不存在的主题"""
        success = self.theme_manager.apply_theme("nonexistent")
        
        self.assertFalse(success)
        self.assertIsNone(self.theme_manager.current_theme)
        
    def test_get_available_themes(self):
        """测试获取可用主题列表"""
        themes = self.theme_manager.get_available_themes()
        
        self.assertEqual(len(themes), 4)
        self.assertIn("light", themes)
        self.assertIn("dark", themes)
        
    def test_get_current_theme_info(self):
        """测试获取当前主题信息"""
        self.theme_manager.apply_theme("light")
        theme_info = self.theme_manager.get_current_theme_info()
        
        self.assertIsInstance(theme_info, dict)
        self.assertIn('name', theme_info)
        self.assertIn('type', theme_info)
        self.assertIn('primary_color', theme_info)
        
    def test_get_current_theme_info_no_theme(self):
        """测试获取当前主题信息（无主题）"""
        theme_info = self.theme_manager.get_current_theme_info()
        
        self.assertEqual(theme_info, {})
        
    def test_create_custom_theme(self):
        """测试创建自定义主题"""
        custom_theme = self.theme_manager.create_custom_theme(
            name="自定义主题",
            primary_color=Mock(),
            secondary_color=Mock(),
            background_color=Mock(),
            text_color=Mock(),
            accent_color=Mock(),
            font_family="Arial",
            font_size=14
        )
        
        self.assertEqual(custom_theme.name, "自定义主题")
        self.assertEqual(custom_theme.type, ThemeType.CUSTOM)
        self.assertEqual(custom_theme.font_family, "Arial")
        self.assertEqual(custom_theme.font_size, 14)
        
        # 检查自定义主题是否添加到可用主题中
        self.assertIn("自定义主题", self.theme_manager.available_themes)


class TestShortcutConfigManager(unittest.TestCase):
    """快捷键配置管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.shortcut_manager = ShortcutConfigManager(self.mock_widget)
        
    def test_shortcut_configs_loading(self):
        """测试快捷键配置加载"""
        self.assertEqual(len(self.shortcut_manager.shortcut_configs), 8)
        
        # 检查关键快捷键配置是否存在
        self.assertIn('new_agent', self.shortcut_manager.shortcut_configs)
        self.assertIn('save_config', self.shortcut_manager.shortcut_configs)
        self.assertIn('reload_config', self.shortcut_manager.shortcut_configs)
        
    def test_update_shortcut(self):
        """测试更新快捷键"""
        success = self.shortcut_manager.update_shortcut('new_agent', 'Ctrl+Shift+N')
        
        self.assertTrue(success)
        self.assertEqual(self.shortcut_manager.shortcut_configs['new_agent']['current_shortcut'], 'Ctrl+Shift+N')
        
    def test_update_nonexistent_shortcut(self):
        """测试更新不存在的快捷键"""
        success = self.shortcut_manager.update_shortcut('nonexistent', 'Ctrl+X')
        
        self.assertFalse(success)
        
    def test_reset_shortcut(self):
        """测试重置快捷键"""
        # 先修改快捷键
        self.shortcut_manager.update_shortcut('new_agent', 'Ctrl+Shift+N')
        
        # 然后重置
        success = self.shortcut_manager.reset_shortcut('new_agent')
        
        self.assertTrue(success)
        self.assertEqual(self.shortcut_manager.shortcut_configs['new_agent']['current_shortcut'], 'Ctrl+N')
        
    def test_reset_nonexistent_shortcut(self):
        """测试重置不存在的快捷键"""
        success = self.shortcut_manager.reset_shortcut('nonexistent')
        
        self.assertFalse(success)
        
    def test_enable_shortcut(self):
        """测试启用/禁用快捷键"""
        success = self.shortcut_manager.enable_shortcut('new_agent', False)
        
        self.assertTrue(success)
        self.assertFalse(self.shortcut_manager.shortcut_configs['new_agent']['enabled'])
        
    def test_enable_nonexistent_shortcut(self):
        """测试启用/禁用不存在的快捷键"""
        success = self.shortcut_manager.enable_shortcut('nonexistent', False)
        
        self.assertFalse(success)
        
    def test_get_shortcut_configs(self):
        """测试获取快捷键配置"""
        configs = self.shortcut_manager.get_shortcut_configs()
        
        self.assertEqual(len(configs), 8)
        self.assertIsInstance(configs, dict)
        
        # 检查配置结构
        new_agent_config = configs['new_agent']
        self.assertIn('action', new_agent_config)
        self.assertIn('default_shortcut', new_agent_config)
        self.assertIn('current_shortcut', new_agent_config)
        self.assertIn('enabled', new_agent_config)
        self.assertIn('description', new_agent_config)


class TestDataExportManager(unittest.TestCase):
    """数据导出管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_widget = Mock()
        self.data_export_manager = DataExportManager(self.mock_widget)
        
    def test_export_agents(self):
        """测试导出代理数据"""
        agents_data = [
            {'id': 1, 'name': '测试代理1', 'status': 'active'},
            {'id': 2, 'name': '测试代理2', 'status': 'inactive'}
        ]
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            success = self.data_export_manager.export_agents(agents_data, 'test.json')
            
        self.assertTrue(success)
        
    def test_export_capabilities(self):
        """测试导出能力数据"""
        capabilities_data = [
            {'id': 1, 'name': '文本生成', 'type': 'text_generation'},
            {'id': 2, 'name': '代码生成', 'type': 'code_generation'}
        ]
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            success = self.data_export_manager.export_capabilities(capabilities_data, 'test.json')
            
        self.assertTrue(success)
        
    def test_export_templates(self):
        """测试导出模板数据"""
        templates_data = [
            {'id': 1, 'name': '问答模板', 'type': 'qa'},
            {'id': 2, 'name': '翻译模板', 'type': 'translation'}
        ]
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            success = self.data_export_manager.export_templates(templates_data, 'test.json')
            
        self.assertTrue(success)
        
    def test_export_configuration(self):
        """测试导出配置数据"""
        config_data = {
            'app': {'name': 'AI代理管理应用', 'version': '1.0.0'},
            'database': {'path': 'data/app.db'}
        }
        
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            success = self.data_export_manager.export_configuration(config_data, 'test.yaml')
            
        self.assertTrue(success)
        
    def test_import_agents(self):
        """测试导入代理数据"""
        agents_data = [
            {'id': 1, 'name': '测试代理1', 'status': 'active'},
            {'id': 2, 'name': '测试代理2', 'status': 'inactive'}
        ]
        
        with patch('builtins.open', unittest.mock.mock_open(read_data='[{"id": 1, "name": "测试代理1", "status": "active"}, {"id": 2, "name": "测试代理2", "status": "inactive"}]')):
            imported_data = self.data_export_manager.import_agents('test.json')
            
        self.assertIsNotNone(imported_data)
        self.assertEqual(len(imported_data), 2)
        
    def test_import_capabilities(self):
        """测试导入能力数据"""
        with patch('builtins.open', unittest.mock.mock_open(read_data='[{"id": 1, "name": "文本生成", "type": "text_generation"}]')):
            imported_data = self.data_export_manager.import_capabilities('test.json')
            
        self.assertIsNotNone(imported_data)
        self.assertEqual(len(imported_data), 1)
        
    def test_import_templates(self):
        """测试导入模板数据"""
        with patch('builtins.open', unittest.mock.mock_open(read_data='[{"id": 1, "name": "问答模板", "type": "qa"}]')):
            imported_data = self.data_export_manager.import_templates('test.json')
            
        self.assertIsNotNone(imported_data)
        self.assertEqual(len(imported_data), 1)
        
    def test_import_configuration(self):
        """测试导入配置数据"""
        with patch('builtins.open', unittest.mock.mock_open(read_data='app:\n  name: AI代理管理应用\n  version: 1.0.0')):
            imported_data = self.data_export_manager.import_configuration('test.yaml')
            
        self.assertIsNotNone(imported_data)
        self.assertIn('app', imported_data)


class TestAdvancedConfigManager(unittest.TestCase):
    """高级配置管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_main_window = Mock()
        self.advanced_config_manager = AdvancedConfigManager(self.mock_main_window)
        
    def test_advanced_config_manager_initialization(self):
        """测试高级配置管理器初始化"""
        self.assertIsNotNone(self.advanced_config_manager.theme_manager)
        self.assertIsNotNone(self.advanced_config_manager.shortcut_manager)
        self.assertIsNotNone(self.advanced_config_manager.data_export_manager)
        
    def test_apply_theme(self):
        """测试应用主题"""
        with patch.object(self.advanced_config_manager.theme_manager, 'apply_theme') as mock_apply:
            self.advanced_config_manager.apply_theme('light')
            mock_apply.assert_called_once_with('light')
            
    def test_get_available_themes(self):
        """测试获取可用主题列表"""
        with patch.object(self.advanced_config_manager.theme_manager, 'get_available_themes') as mock_get:
            mock_get.return_value = ['light', 'dark']
            themes = self.advanced_config_manager.get_available_themes()
            
        self.assertEqual(themes, ['light', 'dark'])
        
    def test_get_current_theme_info(self):
        """测试获取当前主题信息"""
        with patch.object(self.advanced_config_manager.theme_manager, 'get_current_theme_info') as mock_get:
            mock_get.return_value = {'name': 'light', 'type': 'light'}
            theme_info = self.advanced_config_manager.get_current_theme_info()
            
        self.assertEqual(theme_info, {'name': 'light', 'type': 'light'})
        
    def test_get_shortcut_configs(self):
        """测试获取快捷键配置"""
        with patch.object(self.advanced_config_manager.shortcut_manager, 'get_shortcut_configs') as mock_get:
            mock_get.return_value = {'new_agent': {'action': '创建新代理'}}
            configs = self.advanced_config_manager.get_shortcut_configs()
            
        self.assertEqual(configs, {'new_agent': {'action': '创建新代理'}})
        
    def test_update_shortcut(self):
        """测试更新快捷键"""
        with patch.object(self.advanced_config_manager.shortcut_manager, 'update_shortcut') as mock_update:
            self.advanced_config_manager.update_shortcut('new_agent', 'Ctrl+Shift+N')
            mock_update.assert_called_once_with('new_agent', 'Ctrl+Shift+N')


if __name__ == '__main__':
    unittest.main()
