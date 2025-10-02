"""
配置数据模型
定义应用配置的数据结构和验证规则
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml


@dataclass
class AppConfig:
    """应用基础配置"""
    name: str = "AI Agent Desktop"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    def validate(self) -> List[str]:
        """验证应用配置"""
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("应用名称不能为空")
        
        if not self.version or len(self.version.strip()) == 0:
            errors.append("应用版本不能为空")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            errors.append(f"日志级别必须是: {', '.join(valid_log_levels)}")
        
        return errors


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "data/app.db"
    backup_enabled: bool = True
    backup_interval: int = 3600  # 秒
    
    def validate(self) -> List[str]:
        """验证数据库配置"""
        errors = []
        
        if not self.path or len(self.path.strip()) == 0:
            errors.append("数据库路径不能为空")
        
        if self.backup_interval < 60:
            errors.append("备份间隔不能小于60秒")
        
        return errors
    
    def get_backup_path(self) -> str:
        """获取备份文件路径"""
        db_path = Path(self.path)
        return str(db_path.parent / f"{db_path.stem}_backup{db_path.suffix}")


@dataclass
class A2AServerConfig:
    """A2A服务器配置"""
    host: str = "localhost"
    port: int = 8000
    enable_cors: bool = True
    max_workers: int = 10
    
    def validate(self) -> List[str]:
        """验证A2A服务器配置"""
        errors = []
        
        if not self.host or len(self.host.strip()) == 0:
            errors.append("服务器主机不能为空")
        
        if self.port < 1 or self.port > 65535:
            errors.append("端口号必须在1-65535范围内")
        
        if self.max_workers < 1:
            errors.append("最大工作线程数必须大于0")
        
        return errors
    
    def get_url(self) -> str:
        """获取服务器URL"""
        return f"http://{self.host}:{self.port}"


@dataclass
class UIConfig:
    """UI配置"""
    theme: str = "dark"
    language: str = "zh-CN"
    auto_save: bool = True
    refresh_interval: int = 5000  # 毫秒
    
    def validate(self) -> List[str]:
        """验证UI配置"""
        errors = []
        
        valid_themes = ["light", "dark", "system"]
        if self.theme not in valid_themes:
            errors.append(f"主题必须是: {', '.join(valid_themes)}")
        
        valid_languages = ["zh-CN", "en-US"]
        if self.language not in valid_languages:
            errors.append(f"语言必须是: {', '.join(valid_languages)}")
        
        if self.refresh_interval < 1000:
            errors.append("刷新间隔不能小于1000毫秒")
        
        return errors


@dataclass
class ModelConfigs:
    """模型配置目录设置"""
    path: str = "config/model_configs/"
    auto_discover: bool = True
    
    def validate(self) -> List[str]:
        """验证模型配置设置"""
        errors = []
        
        if not self.path or len(self.path.strip()) == 0:
            errors.append("模型配置路径不能为空")
        
        return errors


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/app.log"
    max_size: int = 10485760  # 10MB
    backup_count: int = 5
    
    def validate(self) -> List[str]:
        """验证日志配置"""
        errors = []
        
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level not in valid_levels:
            errors.append(f"日志级别必须是: {', '.join(valid_levels)}")
        
        if self.max_size < 1024:  # 1KB
            errors.append("日志文件最大大小不能小于1KB")
        
        if self.backup_count < 0:
            errors.append("备份文件数量不能为负数")
        
        return errors


@dataclass
class ConfigModel:
    """完整的配置数据模型"""
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    a2a_server: A2AServerConfig = field(default_factory=A2AServerConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    model_configs: ModelConfigs = field(default_factory=ModelConfigs)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def validate(self) -> Dict[str, List[str]]:
        """验证所有配置"""
        errors = {}
        
        # 验证各个配置节
        app_errors = self.app.validate()
        if app_errors:
            errors["app"] = app_errors
        
        db_errors = self.database.validate()
        if db_errors:
            errors["database"] = db_errors
        
        a2a_errors = self.a2a_server.validate()
        if a2a_errors:
            errors["a2a_server"] = a2a_errors
        
        ui_errors = self.ui.validate()
        if ui_errors:
            errors["ui"] = ui_errors
        
        model_errors = self.model_configs.validate()
        if model_errors:
            errors["model_configs"] = model_errors
        
        log_errors = self.logging.validate()
        if log_errors:
            errors["logging"] = log_errors
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        errors = self.validate()
        return len(errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "app": {
                "name": self.app.name,
                "version": self.app.version,
                "debug": self.app.debug,
                "log_level": self.app.log_level
            },
            "database": {
                "path": self.database.path,
                "backup_enabled": self.database.backup_enabled,
                "backup_interval": self.database.backup_interval
            },
            "a2a_server": {
                "host": self.a2a_server.host,
                "port": self.a2a_server.port,
                "enable_cors": self.a2a_server.enable_cors,
                "max_workers": self.a2a_server.max_workers
            },
            "ui": {
                "theme": self.ui.theme,
                "language": self.ui.language,
                "auto_save": self.ui.auto_save,
                "refresh_interval": self.ui.refresh_interval
            },
            "model_configs": {
                "path": self.model_configs.path,
                "auto_discover": self.model_configs.auto_discover
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "max_size": self.logging.max_size,
                "backup_count": self.logging.backup_count
            }
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ConfigModel':
        """从字典创建配置模型"""
        config = cls()
        
        # 应用配置
        if "app" in config_dict:
            app_config = config_dict["app"]
            config.app = AppConfig(
                name=app_config.get("name", "AI Agent Desktop"),
                version=app_config.get("version", "1.0.0"),
                debug=app_config.get("debug", False),
                log_level=app_config.get("log_level", "INFO")
            )
        
        # 数据库配置
        if "database" in config_dict:
            db_config = config_dict["database"]
            config.database = DatabaseConfig(
                path=db_config.get("path", "data/app.db"),
                backup_enabled=db_config.get("backup_enabled", True),
                backup_interval=db_config.get("backup_interval", 3600)
            )
        
        # A2A服务器配置
        if "a2a_server" in config_dict:
            a2a_config = config_dict["a2a_server"]
            config.a2a_server = A2AServerConfig(
                host=a2a_config.get("host", "localhost"),
                port=a2a_config.get("port", 8000),
                enable_cors=a2a_config.get("enable_cors", True),
                max_workers=a2a_config.get("max_workers", 10)
            )
        
        # UI配置
        if "ui" in config_dict:
            ui_config = config_dict["ui"]
            config.ui = UIConfig(
                theme=ui_config.get("theme", "dark"),
                language=ui_config.get("language", "zh-CN"),
                auto_save=ui_config.get("auto_save", True),
                refresh_interval=ui_config.get("refresh_interval", 5000)
            )
        
        # 模型配置设置
        if "model_configs" in config_dict:
            model_config = config_dict["model_configs"]
            config.model_configs = ModelConfigs(
                path=model_config.get("path", "config/model_configs/"),
                auto_discover=model_config.get("auto_discover", True)
            )
        
        # 日志配置
        if "logging" in config_dict:
            log_config = config_dict["logging"]
            config.logging = LoggingConfig(
                level=log_config.get("level", "INFO"),
                file=log_config.get("file", "logs/app.log"),
                max_size=log_config.get("max_size", 10485760),
                backup_count=log_config.get("backup_count", 5)
            )
        
        return config


# 测试函数
def test_config_model():
    """测试配置模型"""
    try:
        # 创建默认配置
        config = ConfigModel()
        print("默认配置创建成功")
        
        # 验证配置
        errors = config.validate()
        if errors:
            print("配置验证失败:")
            for section, section_errors in errors.items():
                print(f"  {section}: {', '.join(section_errors)}")
        else:
            print("✓ 配置验证通过")
        
        # 测试字典转换
        config_dict = config.to_dict()
        print("✓ 字典转换成功")
        
        # 测试从字典创建
        new_config = ConfigModel.from_dict(config_dict)
        print("✓ 从字典创建成功")
        
        # 验证新配置
        if new_config.is_valid():
            print("✓ 新配置验证通过")
        else:
            print("❌ 新配置验证失败")
        
        return True
        
    except Exception as e:
        print(f"配置模型测试失败: {e}")
        return False


if __name__ == "__main__":
    test_config_model()
