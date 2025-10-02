"""
日志管理器
负责应用的结构化日志记录和管理
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

# 在测试模式下使用模拟配置类
if __name__ == "__main__":
    # 模拟配置类用于测试
    class ConfigModel:
        def __init__(self):
            self.logging = None
else:
    from ..core.config_model import ConfigModel


class LogManager:
    """日志管理器类"""
    
    def __init__(self, config: Optional[ConfigModel] = None):
        """
        初始化日志管理器
        
        Args:
            config: 应用配置对象
        """
        self.config = config
        self.logger: Optional[logging.Logger] = None
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        # 创建根日志记录器
        self.logger = logging.getLogger('ai_agent_desktop')
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if self.logger.handlers:
            return
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（如果配置了日志文件）
        if self.config and self.config.logging:
            self._setup_file_handler(formatter)
        
        # 添加自定义日志级别
        self._add_custom_levels()
    
    def _setup_file_handler(self, formatter: logging.Formatter):
        """设置文件处理器"""
        try:
            log_config = self.config.logging
            log_dir = Path(log_config.file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_config.file,
                maxBytes=log_config.max_size * 1024 * 1024,  # MB to bytes
                backupCount=log_config.backup_count
            )
            file_handler.setLevel(getattr(logging, log_config.level.upper()))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"设置文件日志处理器失败: {e}")
    
    def _add_custom_levels(self):
        """添加自定义日志级别"""
        # 添加AUDIT级别（介于INFO和WARNING之间）
        AUDIT_LEVEL = 25
        logging.addLevelName(AUDIT_LEVEL, 'AUDIT')
        
        def audit(self, message, *args, **kwargs):
            if self.isEnabledFor(AUDIT_LEVEL):
                self._log(AUDIT_LEVEL, message, args, **kwargs)
        
        logging.Logger.audit = audit
    
    def setup_from_config(self, config: ConfigModel):
        """
        根据配置重新设置日志系统
        
        Args:
            config: 应用配置对象
        """
        self.config = config
        
        # 清除现有处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 重新设置日志系统
        self._setup_logger()
    
    def log_application_start(self):
        """记录应用启动日志"""
        if self.logger:
            self.logger.info("=" * 50)
            self.logger.info("AI Agent Desktop 应用启动")
            self.logger.info("=" * 50)
            
            # 记录系统信息
            self.logger.info(f"Python版本: {sys.version}")
            self.logger.info(f"工作目录: {os.getcwd()}")
            
            if self.config:
                self.logger.info(f"应用版本: {self.config.app.version}")
                self.logger.info(f"调试模式: {self.config.app.debug}")
    
    def log_application_stop(self):
        """记录应用停止日志"""
        if self.logger:
            self.logger.info("=" * 50)
            self.logger.info("AI Agent Desktop 应用停止")
            self.logger.info("=" * 50)
    
    def log_database_operation(self, operation: str, table: str, details: str = ""):
        """记录数据库操作日志"""
        if self.logger:
            message = f"数据库操作 - {operation} - 表: {table}"
            if details:
                message += f" - {details}"
            self.logger.info(message)
    
    def log_model_operation(self, operation: str, model_name: str, details: str = ""):
        """记录模型操作日志"""
        if self.logger:
            message = f"模型操作 - {operation} - 模型: {model_name}"
            if details:
                message += f" - {details}"
            self.logger.info(message)
    
    def log_agent_operation(self, operation: str, agent_name: str, details: str = ""):
        """记录代理操作日志"""
        if self.logger:
            message = f"代理操作 - {operation} - 代理: {agent_name}"
            if details:
                message += f" - {details}"
            self.logger.info(message)
    
    def log_a2a_operation(self, operation: str, message_type: str, details: str = ""):
        """记录A2A操作日志"""
        if self.logger:
            message = f"A2A操作 - {operation} - 类型: {message_type}"
            if details:
                message += f" - {details}"
            self.logger.info(message)
    
    def log_audit_event(self, event_type: str, user: str = "system", details: Dict[str, Any] = None):
        """记录审计事件"""
        if self.logger:
            audit_data = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user": user,
                "details": details or {}
            }
            
            self.logger.audit(f"审计事件 - {event_type} - 用户: {user} - 详情: {json.dumps(audit_data, ensure_ascii=False)}")
    
    def log_error(self, error_type: str, error_message: str, stack_trace: str = ""):
        """记录错误日志"""
        if self.logger:
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace
            }
            
            self.logger.error(f"错误 - {error_type}: {error_message}")
            if stack_trace:
                self.logger.debug(f"错误堆栈: {stack_trace}")
    
    def log_performance(self, operation: str, duration_ms: float, details: str = ""):
        """记录性能日志"""
        if self.logger:
            message = f"性能 - {operation} - 耗时: {duration_ms:.2f}ms"
            if details:
                message += f" - {details}"
            self.logger.info(message)
    
    def get_log_file_path(self) -> Optional[str]:
        """获取日志文件路径"""
        if self.config and self.config.logging:
            return self.config.logging.file
        return None
    
    def get_log_level(self) -> str:
        """获取当前日志级别"""
        if self.config and self.config.logging:
            return self.config.logging.level
        return "INFO"


# 全局日志管理器实例
_log_manager: Optional[LogManager] = None


def init_log_manager(config: Optional[ConfigModel] = None) -> LogManager:
    """
    初始化全局日志管理器
    
    Args:
        config: 应用配置对象
        
    Returns:
        LogManager实例
    """
    global _log_manager
    _log_manager = LogManager(config)
    return _log_manager


def get_log_manager() -> LogManager:
    """
    获取全局日志管理器
    
    Returns:
        LogManager实例
        
    Raises:
        RuntimeError: 日志管理器未初始化
    """
    global _log_manager
    
    if _log_manager is None:
        _log_manager = LogManager()
    
    return _log_manager


def setup_logging(config: ConfigModel) -> bool:
    """
    设置日志系统（便捷函数）
    
    Args:
        config: 应用配置对象
        
    Returns:
        设置是否成功
    """
    try:
        manager = get_log_manager()
        manager.setup_from_config(config)
        manager.log_application_start()
        return True
    except Exception as e:
        print(f"设置日志系统失败: {e}")
        return False


def log_info(message: str):
    """记录信息日志"""
    get_log_manager().logger.info(message)


def log_error(message: str, error: Optional[Exception] = None):
    """记录错误日志"""
    if error:
        stack_trace = getattr(error, '__traceback__', None)
        if stack_trace:
            import traceback
            stack_trace_str = traceback.format_exc()
        else:
            stack_trace_str = str(error)
        
        get_log_manager().log_error(type(error).__name__, message, stack_trace_str)
    else:
        get_log_manager().log_error("GeneralError", message)


def log_warning(message: str):
    """记录警告日志"""
    get_log_manager().logger.warning(message)


def log_debug(message: str):
    """记录调试日志"""
    get_log_manager().logger.debug(message)


def log_audit(event_type: str, user: str = "system", details: Dict[str, Any] = None):
    """记录审计日志"""
    get_log_manager().log_audit_event(event_type, user, details)


def log_performance(operation: str, duration_ms: float, details: str = ""):
    """记录性能日志"""
    get_log_manager().log_performance(operation, duration_ms, details)


# 测试函数
def test_log_manager():
    """测试日志管理器"""
    try:
        # 创建临时配置类（避免导入问题）
        class LoggingConfig:
            def __init__(self, level="INFO", file="logs/app.log", max_size=10, backup_count=5):
                self.level = level
                self.file = file
                self.max_size = max_size
                self.backup_count = backup_count
        
        class AppConfig:
            def __init__(self):
                self.version = "1.0.0"
                self.debug = False
        
        class ConfigModel:
            def __init__(self):
                self.logging = LoggingConfig()
                self.app = AppConfig()
        
        # 创建配置
        config = ConfigModel()
        config.logging = LoggingConfig(
            level="DEBUG",
            file="test_logs/app.log",
            max_size=10,
            backup_count=5
        )
        
        # 初始化日志管理器
        manager = init_log_manager(config)
        
        # 测试各种日志级别
        manager.logger.debug("调试日志测试")
        manager.logger.info("信息日志测试")
        manager.logger.warning("警告日志测试")
        manager.logger.error("错误日志测试")
        
        # 测试自定义日志方法
        manager.log_application_start()
        manager.log_database_operation("SELECT", "users", "查询用户列表")
        manager.log_model_operation("LOAD", "gpt-4", "加载模型成功")
        manager.log_agent_operation("START", "chat_agent", "启动聊天代理")
        manager.log_a2a_operation("SEND", "TASK", "发送任务消息")
        manager.log_audit_event("USER_LOGIN", "admin", {"ip": "192.168.1.1"})
        manager.log_performance("DATABASE_QUERY", 125.5, "用户查询")
        
        manager.log_application_stop()
        
        print("✓ 日志管理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 日志管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_log_manager()
