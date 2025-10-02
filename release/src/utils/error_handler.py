"""
全局异常处理器
负责应用的异常捕获、处理和用户友好的错误提示
"""

import sys
import traceback
from typing import Optional, Callable, Any
from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from .logger import log_error, log_audit


class ErrorHandler(QObject):
    """全局异常处理器类"""
    
    # 信号：错误发生时发出
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    
    def __init__(self, app: Optional[QApplication] = None):
        """
        初始化异常处理器
        
        Args:
            app: QApplication实例，用于显示错误对话框
        """
        super().__init__()
        self.app = app
        self._setup_exception_hook()
    
    def _setup_exception_hook(self):
        """设置全局异常钩子"""
        sys.excepthook = self.handle_uncaught_exception
    
    def handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """
        处理未捕获的异常
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
        """
        # 忽略KeyboardInterrupt异常（Ctrl+C）
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 记录错误日志
        error_message = str(exc_value) if exc_value else "未知错误"
        stack_trace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        log_error(f"未捕获异常: {error_message}", exc_value)
        
        # 发出错误信号
        self.error_occurred.emit(exc_type.__name__, error_message)
        
        # 显示错误对话框
        self.show_error_dialog(exc_type.__name__, error_message, stack_trace)
    
    def show_error_dialog(self, error_type: str, error_message: str, stack_trace: str = ""):
        """
        显示错误对话框
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
            stack_trace: 堆栈跟踪信息
        """
        if self.app is None:
            print(f"错误: {error_type}: {error_message}")
            if stack_trace:
                print(f"堆栈跟踪:\n{stack_trace}")
            return
        
        try:
            # 创建错误对话框
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("应用程序错误")
            
            # 构建错误消息
            detailed_message = f"错误类型: {error_type}\n错误信息: {error_message}"
            if stack_trace:
                detailed_message += f"\n\n堆栈跟踪:\n{stack_trace}"
            
            msg_box.setText("应用程序遇到错误，请查看详细信息。")
            msg_box.setDetailedText(detailed_message)
            
            # 添加按钮
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.addButton("复制错误信息", QMessageBox.ButtonRole.ActionRole)
            
            # 显示对话框
            result = msg_box.exec()
            
            # 处理按钮点击
            if result == 1:  # 复制错误信息按钮
                self._copy_to_clipboard(detailed_message)
                
        except Exception as e:
            # 如果显示对话框失败，回退到控制台输出
            print(f"显示错误对话框失败: {e}")
            print(f"原始错误: {error_type}: {error_message}")
            if stack_trace:
                print(f"堆栈跟踪:\n{stack_trace}")
    
    def _copy_to_clipboard(self, text: str):
        """复制文本到剪贴板"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            log_info("错误信息已复制到剪贴板")
        except Exception as e:
            log_error("复制到剪贴板失败", e)
    
    def handle_database_error(self, error: Exception, operation: str, table: str = ""):
        """
        处理数据库错误
        
        Args:
            error: 数据库异常
            operation: 数据库操作类型
            table: 涉及的数据表
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 记录错误日志
        log_error(f"数据库错误 - {operation}", error)
        log_audit("DATABASE_ERROR", "system", {
            "operation": operation,
            "table": table,
            "error_type": error_type,
            "error_message": error_message
        })
        
        # 显示用户友好的错误消息
        user_message = self._get_database_error_message(error_type, operation, table)
        self.show_user_error("数据库错误", user_message)
    
    def _get_database_error_message(self, error_type: str, operation: str, table: str) -> str:
        """获取数据库错误的用户友好消息"""
        base_message = f"数据库操作失败: {operation}"
        
        if table:
            base_message += f" (表: {table})"
        
        if "IntegrityError" in error_type:
            return f"{base_message}\n数据完整性错误，请检查输入数据。"
        elif "OperationalError" in error_type:
            return f"{base_message}\n数据库连接错误，请检查数据库状态。"
        elif "ProgrammingError" in error_type:
            return f"{base_message}\nSQL语句错误，请联系技术支持。"
        else:
            return f"{base_message}\n未知数据库错误。"
    
    def handle_network_error(self, error: Exception, operation: str, url: str = ""):
        """
        处理网络错误
        
        Args:
            error: 网络异常
            operation: 网络操作类型
            url: 涉及的URL
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 记录错误日志
        log_error(f"网络错误 - {operation}", error)
        log_audit("NETWORK_ERROR", "system", {
            "operation": operation,
            "url": url,
            "error_type": error_type,
            "error_message": error_message
        })
        
        # 显示用户友好的错误消息
        user_message = self._get_network_error_message(error_type, operation, url)
        self.show_user_error("网络错误", user_message)
    
    def _get_network_error_message(self, error_type: str, operation: str, url: str) -> str:
        """获取网络错误的用户友好消息"""
        base_message = f"网络操作失败: {operation}"
        
        if url:
            base_message += f" (URL: {url})"
        
        if "ConnectionError" in error_type:
            return f"{base_message}\n网络连接失败，请检查网络设置。"
        elif "Timeout" in error_type:
            return f"{base_message}\n请求超时，请稍后重试。"
        elif "HTTPError" in error_type:
            return f"{base_message}\n服务器返回错误，请检查URL和参数。"
        else:
            return f"{base_message}\n未知网络错误。"
    
    def handle_model_error(self, error: Exception, operation: str, model_name: str = ""):
        """
        处理模型错误
        
        Args:
            error: 模型异常
            operation: 模型操作类型
            model_name: 涉及的模型名称
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # 记录错误日志
        log_error(f"模型错误 - {operation}", error)
        log_audit("MODEL_ERROR", "system", {
            "operation": operation,
            "model_name": model_name,
            "error_type": error_type,
            "error_message": error_message
        })
        
        # 显示用户友好的错误消息
        user_message = self._get_model_error_message(error_type, operation, model_name)
        self.show_user_error("模型错误", user_message)
    
    def _get_model_error_message(self, error_type: str, operation: str, model_name: str) -> str:
        """获取模型错误的用户友好消息"""
        base_message = f"模型操作失败: {operation}"
        
        if model_name:
            base_message += f" (模型: {model_name})"
        
        if "ModelNotFound" in error_type:
            return f"{base_message}\n模型不存在或未正确配置。"
        elif "ModelLoadError" in error_type:
            return f"{base_message}\n模型加载失败，请检查模型文件。"
        elif "InferenceError" in error_type:
            return f"{base_message}\n模型推理失败，请检查输入数据。"
        else:
            return f"{base_message}\n未知模型错误。"
    
    def show_user_error(self, title: str, message: str, detailed_message: str = ""):
        """
        显示用户友好的错误消息
        
        Args:
            title: 错误标题
            message: 错误消息
            detailed_message: 详细错误信息
        """
        if self.app is None:
            print(f"{title}: {message}")
            if detailed_message:
                print(f"详细信息: {detailed_message}")
            return
        
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            
            if detailed_message:
                msg_box.setDetailedText(detailed_message)
            
            msg_box.exec()
            
        except Exception as e:
            print(f"显示错误对话框失败: {e}")
            print(f"{title}: {message}")
            if detailed_message:
                print(f"详细信息: {detailed_message}")
    
    def show_user_info(self, title: str, message: str):
        """
        显示用户信息消息
        
        Args:
            title: 信息标题
            message: 信息消息
        """
        if self.app is None:
            print(f"{title}: {message}")
            return
        
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
            
        except Exception as e:
            print(f"显示信息对话框失败: {e}")
            print(f"{title}: {message}")
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        安全执行函数，捕获并处理异常
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果，如果出错返回None
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_uncaught_exception(type(e), e, e.__traceback__)
            return None


# 全局异常处理器实例
_error_handler: Optional[ErrorHandler] = None


def init_error_handler(app: Optional[QApplication] = None) -> ErrorHandler:
    """
    初始化全局异常处理器
    
    Args:
        app: QApplication实例
        
    Returns:
        ErrorHandler实例
    """
    global _error_handler
    _error_handler = ErrorHandler(app)
    return _error_handler


def get_error_handler() -> ErrorHandler:
    """
    获取全局异常处理器
    
    Returns:
        ErrorHandler实例
        
    Raises:
        RuntimeError: 异常处理器未初始化
    """
    global _error_handler
    
    if _error_handler is None:
        _error_handler = ErrorHandler()
    
    return _error_handler


def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """
    安全执行函数（便捷函数）
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果，如果出错返回None
    """
    return get_error_handler().safe_execute(func, *args, **kwargs)


def show_error(title: str, message: str, detailed_message: str = ""):
    """显示错误消息（便捷函数）"""
    get_error_handler().show_user_error(title, message, detailed_message)


def show_info(title: str, message: str):
    """显示信息消息（便捷函数）"""
    get_error_handler().show_user_info(title, message)


# 测试函数
def test_error_handler():
    """测试异常处理器"""
    try:
        # 创建测试应用
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        
        # 初始化异常处理器
        handler = init_error_handler(app)
        
        # 测试各种错误处理
        print("测试错误处理功能...")
        
        # 测试数据库错误处理
        class MockDatabaseError(Exception):
            pass
        
        try:
            raise MockDatabaseError("模拟数据库连接失败")
        except Exception as e:
            handler.handle_database_error(e, "CONNECT", "users")
        
        # 测试网络错误处理
        class MockNetworkError(Exception):
            pass
        
        try:
            raise MockNetworkError("模拟网络超时")
        except Exception as e:
            handler.handle_network_error(e, "REQUEST", "https://api.example.com")
        
        # 测试模型错误处理
        class MockModelError(Exception):
            pass
        
        try:
            raise MockModelError("模拟模型加载失败")
        except Exception as e:
            handler.handle_model_error(e, "LOAD", "gpt-4")
        
        print("✓ 异常处理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 异常处理器测试失败: {e}")
        return False


if __name__ == "__main__":
    test_error_handler()


# 导入日志函数（避免循环导入）
def log_info(message: str):
    """记录信息日志"""
    from .logger import log_info as _log_info
    _log_info(message)
