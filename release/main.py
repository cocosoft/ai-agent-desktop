#!/usr/bin/env python3
"""
AI Agent Desktop 应用启动脚本
主程序入口点，负责应用初始化和启动
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入配置模块
try:
    from src.utils.config_loader import load_config
    from src.ui.main_window import main as ui_main
    from src.data.database_manager import initialize_database, get_database_info
    from src.utils.logger import setup_logging, init_log_manager
    from src.utils.error_handler import init_error_handler
    from src.utils.status_monitor import init_status_monitor, start_monitoring
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖已正确安装")
    sys.exit(1)


def check_environment():
    """检查运行环境"""
    print("检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return False
    
    # 检查必要的目录
    required_dirs = ['config', 'src', 'data']
    for dir_name in required_dirs:
        if not (project_root / dir_name).exists():
            print(f"错误: 缺少必要的目录 '{dir_name}'")
            return False
    
    # 检查配置文件
    config_file = project_root / 'config' / 'app_config.yaml'
    if not config_file.exists():
        print("错误: 配置文件不存在")
        return False
    
    print("✓ 环境检查通过")
    return True


def load_application_config():
    """加载应用配置"""
    try:
        # 加载配置字典
        config_dict = load_config()
        print("✓ 配置加载成功")
        
        # 将配置字典转换为ConfigModel对象
        from src.core.config_model import ConfigModel
        config = ConfigModel.from_dict(config_dict)
        return config
    except Exception as e:
        print(f"配置加载失败: {e}")
        return None


def initialize_application():
    """初始化应用"""
    print("初始化AI Agent Desktop应用...")
    
    # 检查环境
    if not check_environment():
        return False
    
    # 加载配置
    config = load_application_config()
    if not config:
        return False
    
    # 初始化日志系统
    print("初始化日志系统...")
    if not setup_logging(config):
        print("❌ 日志系统初始化失败")
        return False
    print("✓ 日志系统初始化成功")
    
    # 初始化数据库
    print("初始化数据库...")
    if not initialize_database():
        print("❌ 数据库初始化失败")
        return False
    print("✓ 数据库初始化成功")
    
    # 显示数据库信息
    db_info = get_database_info()
    print(f"数据库路径: {db_info['db_path']}")
    print(f"数据库版本: {db_info['version']}")
    print(f"数据表数量: {len(db_info['tables'])}")
    
    print("✓ 应用初始化完成")
    return True


def main():
    """应用主入口点"""
    print("=" * 50)
    print("AI Agent Desktop 启动中...")
    print("=" * 50)
    
    # 初始化应用
    if not initialize_application():
        print("应用初始化失败，程序退出")
        sys.exit(1)
    
    try:
        # 初始化异常处理器（需要在UI启动前初始化）
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        init_error_handler(app)
        
        # 初始化状态监控器
        status_monitor = init_status_monitor()
        status_monitor.set_app_start_time()
        start_monitoring(interval=10.0)  # 每10秒监控一次
        
        # 启动UI主窗口
        print("启动主窗口...")
        ui_main()
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"应用运行错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止状态监控
        from src.utils.status_monitor import stop_monitoring
        stop_monitoring()
        
        # 记录应用停止日志
        from src.utils.logger import get_log_manager
        get_log_manager().log_application_stop()
        
        print("AI Agent Desktop 已退出")


if __name__ == "__main__":
    main()
