"""
主窗口功能测试
测试PyQt6主窗口框架的各项功能
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def test_window_creation():
    """测试主窗口创建"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from src.ui.main_window import MainWindow
        
        # 创建主窗口
        window = MainWindow()
        
        # 验证窗口属性
        assert window.windowTitle() == "AI Agent Desktop"
        assert window.minimumSize().width() == 1200
        assert window.minimumSize().height() == 800
        
        # 验证窗口组件存在
        assert hasattr(window, 'toolbar')
        assert hasattr(window, 'tab_widget')
        assert hasattr(window, 'status_bar')
        
        print("✓ 主窗口创建测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 主窗口创建测试失败: {e}")
        return False
    finally:
        if 'window' in locals():
            window.close()


def test_menu_bar():
    """测试菜单栏功能"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from src.ui.main_window import MainWindow
        
        window = MainWindow()
        
        # 验证菜单栏存在
        menu_bar = window.menuBar()
        assert menu_bar is not None
        
        # 验证菜单项数量 - 使用正确的方法获取菜单标题
        menu_titles = []
        for action in menu_bar.actions():
            if action.menu():
                menu_titles.append(action.menu().title())
        
        expected_menus = ["文件(&F)", "视图(&V)", "帮助(&H)"]
        
        for expected_menu in expected_menus:
            assert expected_menu in menu_titles, f"菜单 {expected_menu} 不存在"
        
        print("✓ 菜单栏测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 菜单栏测试失败: {e}")
        return False
    finally:
        if 'window' in locals():
            window.close()


def test_toolbar():
    """测试工具栏功能"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from src.ui.main_window import MainWindow
        
        window = MainWindow()
        
        # 验证工具栏存在
        assert hasattr(window, 'toolbar')
        
        print("✓ 工具栏测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 工具栏测试失败: {e}")
        return False
    finally:
        if 'window' in locals():
            window.close()


def test_tab_navigation():
    """测试标签页导航功能"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from src.ui.main_window import MainWindow
        
        window = MainWindow()
        
        # 验证标签页组件存在
        assert window.tab_widget is not None
        
        # 验证标签页数量
        tab_count = window.tab_widget.count()
        assert tab_count == 4  # 应该有4个标签页
        
        # 验证标签页标题
        expected_tabs = ["代理管理", "模型管理", "能力管理", "监控"]
        for i, expected_tab in enumerate(expected_tabs):
            tab_text = window.tab_widget.tabText(i)
            assert tab_text == expected_tab, f"标签页 {i} 标题不匹配"
        
        print("✓ 标签页导航测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 标签页导航测试失败: {e}")
        return False
    finally:
        if 'window' in locals():
            window.close()


def test_status_bar():
    """测试状态栏功能"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from src.ui.main_window import MainWindow
        
        window = MainWindow()
        
        # 验证状态栏存在
        assert hasattr(window, 'status_bar')
        
        print("✓ 状态栏测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 状态栏测试失败: {e}")
        return False
    finally:
        if 'window' in locals():
            window.close()


def test_theme_applied():
    """测试主题设置"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from src.ui.main_window import MainWindow
        
        window = MainWindow()
        
        # 验证样式表已应用
        stylesheet = window.styleSheet()
        assert stylesheet is not None
        assert len(stylesheet) > 0
        
        # 验证包含关键样式规则
        assert "QMainWindow" in stylesheet
        assert "QTabWidget" in stylesheet
        assert "QTabBar" in stylesheet
        
        print("✓ 主题设置测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 主题设置测试失败: {e}")
        return False
    finally:
        if 'window' in locals():
            window.close()


def run_all_tests():
    """运行所有主窗口测试"""
    print("开始测试PyQt6主窗口框架...")
    print("=" * 50)
    
    tests = [
        test_window_creation,
        test_menu_bar,
        test_toolbar,
        test_tab_navigation,
        test_status_bar,
        test_theme_applied
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 测试异常: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"测试结果: 通过 {passed}/6, 失败 {failed}/6")
    
    if failed == 0:
        print("🎉 所有主窗口测试通过！")
        return True
    else:
        print("❌ 部分测试失败，需要检查")
        return False


if __name__ == "__main__":
    # 切换到项目根目录并添加路径
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
