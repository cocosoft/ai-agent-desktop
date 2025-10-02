"""
配置管理系统测试
测试配置数据模型、配置管理器和配置界面的功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
import yaml


def test_config_model():
    """测试配置数据模型"""
    try:
        # 导入配置模型
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.core.config_model import ConfigModel, AppConfig, DatabaseConfig, A2AServerConfig
        
        print("开始测试配置数据模型...")
        
        # 测试默认配置创建
        config = ConfigModel()
        print("✓ 默认配置创建成功")
        
        # 测试配置验证
        errors = config.validate()
        if errors:
            print("❌ 默认配置验证失败:")
            for section, section_errors in errors.items():
                print(f"  {section}: {', '.join(section_errors)}")
            return False
        else:
            print("✓ 默认配置验证通过")
        
        # 测试字典转换
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "app" in config_dict
        assert "database" in config_dict
        assert "a2a_server" in config_dict
        print("✓ 字典转换成功")
        
        # 测试从字典创建
        new_config = ConfigModel.from_dict(config_dict)
        assert new_config.app.name == config.app.name
        assert new_config.database.path == config.database.path
        print("✓ 从字典创建成功")
        
        # 测试配置验证失败情况
        invalid_config = ConfigModel()
        invalid_config.app.name = ""  # 无效的应用名称
        invalid_config.database.backup_interval = 30  # 无效的备份间隔
        
        errors = invalid_config.validate()
        assert "app" in errors
        assert "database" in errors
        print("✓ 无效配置验证正确")
        
        print("🎉 配置数据模型测试全部通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置数据模型测试失败: {e}")
        return False


def test_config_manager():
    """测试配置管理器"""
    try:
        # 创建临时目录用于测试
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "test_config.yaml"
        
        print(f"开始测试配置管理器，使用临时目录: {temp_dir}")
        
        # 导入配置管理器
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.core.config_manager import ConfigManager, ConfigModel
        
        # 创建配置管理器
        manager = ConfigManager(str(config_path))
        print("✓ 配置管理器创建成功")
        
        # 测试创建默认配置
        config = manager.create_default_config()
        assert config is not None
        assert config_path.exists()
        print("✓ 默认配置创建成功")
        
        # 测试加载配置
        loaded_config = manager.load_config()
        assert loaded_config.app.name == "AI Agent Desktop"
        print("✓ 配置加载成功")
        
        # 测试配置信息获取
        info = manager.get_config_info()
        assert info["loaded"] == True
        assert info["is_valid"] == True
        print("✓ 配置信息获取成功")
        
        # 测试配置更新
        success = manager.update_config("app", {"debug": True})
        assert success == True
        assert manager.get_config().app.debug == True
        print("✓ 配置更新成功")
        
        # 测试配置验证
        errors = manager.validate_config()
        assert len(errors) == 0
        print("✓ 配置验证成功")
        
        # 测试重新加载
        reloaded_config = manager.reload_config()
        assert reloaded_config is not None
        print("✓ 配置重新加载成功")
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        print("🎉 配置管理器测试全部通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        # 清理临时目录（如果存在）
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return False


def test_config_dialog_import():
    """测试配置对话框导入"""
    try:
        print("开始测试配置对话框导入...")
        
        # 导入配置对话框
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.ui.config_dialog import ConfigDialog
        
        # 检查对话框类是否存在
        assert ConfigDialog is not None
        print("✓ 配置对话框导入成功")
        
        # 检查对话框类的方法
        assert hasattr(ConfigDialog, 'load_config')
        assert hasattr(ConfigDialog, 'save_config')
        assert hasattr(ConfigDialog, 'validate_config')
        print("✓ 配置对话框方法检查通过")
        
        print("🎉 配置对话框导入测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置对话框导入测试失败: {e}")
        return False


def test_config_file_operations():
    """测试配置文件操作"""
    try:
        # 创建临时目录用于测试
        temp_dir = tempfile.mkdtemp()
        config_path = Path(temp_dir) / "test_operations.yaml"
        
        print(f"开始测试配置文件操作，使用临时目录: {temp_dir}")
        
        # 导入配置管理器
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.core.config_manager import ConfigManager
        
        # 创建配置管理器
        manager = ConfigManager(str(config_path))
        
        # 测试配置文件不存在时的处理
        if config_path.exists():
            config_path.unlink()
        
        config = manager.load_config()  # 应该创建默认配置
        assert config_path.exists()
        print("✓ 配置文件不存在时自动创建默认配置")
        
        # 测试配置文件内容
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = yaml.safe_load(f)
        
        assert config_content is not None
        assert "app" in config_content
        assert config_content["app"]["name"] == "AI Agent Desktop"
        print("✓ 配置文件内容正确")
        
        # 测试备份功能
        manager.set_backup_enabled(True)
        manager.save_config()
        
        # 检查备份文件是否创建
        backup_files = list(config_path.parent.glob("*_backup_*.yaml"))
        assert len(backup_files) > 0
        print("✓ 配置文件备份功能正常")
        
        # 测试无效配置文件处理
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content")
        
        try:
            manager.reload_config()
            print("❌ 无效配置文件处理失败 - 应该抛出异常")
            return False
        except:
            print("✓ 无效配置文件正确处理")
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        print("🎉 配置文件操作测试全部通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置文件操作测试失败: {e}")
        # 清理临时目录（如果存在）
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return False


def run_all_tests():
    """运行所有配置系统测试"""
    print("=" * 60)
    print("开始测试配置管理系统")
    print("=" * 60)
    
    tests = [
        ("配置数据模型", test_config_model),
        ("配置管理器", test_config_manager),
        ("配置对话框导入", test_config_dialog_import),
        ("配置文件操作", test_config_file_operations)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 测试: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                failed += 1
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        print("🎉 所有配置管理系统测试通过！")
        return True
    else:
        print("❌ 部分测试失败，需要检查")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
