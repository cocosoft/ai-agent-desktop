"""
环境配置测试
测试第一天的项目初始化和环境搭建任务完成情况
"""

import sys
import os
import yaml
from pathlib import Path


def test_project_structure():
    """测试项目目录结构是否正确创建"""
    required_dirs = [
        'config',
        'data', 
        'docs',
        'src',
        'src/a2a',
        'src/adapters',
        'src/core',
        'src/data',
        'src/ui',
        'src/utils',
        'tests',
        'tests/fixtures',
        'tests/integration',
        'tests/unit'
    ]
    
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"目录 {dir_path} 不存在"
    
    print("✓ 项目目录结构测试通过")


def test_requirements_file():
    """测试requirements.txt文件是否存在且格式正确"""
    assert Path('requirements.txt').exists(), "requirements.txt文件不存在"
    
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'PyQt6' in content, "PyQt6依赖未在requirements.txt中"
        assert 'a2a-sdk' in content, "a2a-sdk依赖未在requirements.txt中"
        assert 'fastapi' in content, "fastapi依赖未在requirements.txt中"
    
    print("✓ requirements.txt文件测试通过")


def test_config_file():
    """测试配置文件是否存在且格式正确"""
    config_path = Path('config/app_config.yaml')
    assert config_path.exists(), "配置文件不存在"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        assert 'app' in config, "配置文件缺少app配置"
        assert 'database' in config, "配置文件缺少database配置"
        assert 'a2a_server' in config, "配置文件缺少a2a_server配置"
    
    print("✓ 配置文件测试通过")


def test_virtual_environment():
    """测试虚拟环境是否正常工作"""
    # 检查是否在虚拟环境中
    assert 'venv' in sys.prefix or 'VIRTUAL_ENV' in os.environ, "未在虚拟环境中运行"
    
    # 检查关键依赖是否已安装
    try:
        import PyQt6
        import a2a
        import fastapi
        import sqlalchemy
        import yaml
        print("✓ 虚拟环境依赖测试通过")
    except ImportError as e:
        raise AssertionError(f"依赖包导入失败: {e}")


def test_git_ignore():
    """测试.gitignore文件是否存在且内容正确"""
    gitignore_path = Path('.gitignore')
    assert gitignore_path.exists(), ".gitignore文件不存在"
    
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert '__pycache__' in content, ".gitignore缺少Python缓存目录配置"
        assert 'venv' in content, ".gitignore缺少虚拟环境目录配置"
        assert '*.db' in content, ".gitignore缺少数据库文件配置"
    
    print("✓ .gitignore文件测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始测试第一天的任务完成情况...")
    print("=" * 50)
    
    try:
        test_project_structure()
        test_requirements_file()
        test_config_file()
        test_virtual_environment()
        test_git_ignore()
        
        print("=" * 50)
        print("🎉 所有测试通过！第一天的任务已完成")
        return True
        
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False


if __name__ == "__main__":
    # 切换到项目根目录
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
