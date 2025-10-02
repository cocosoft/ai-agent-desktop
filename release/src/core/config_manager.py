"""
配置管理器
负责配置文件的读写、验证和管理
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .config_model import ConfigModel


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 使用默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / 'config' / 'app_config.yaml'
        else:
            self.config_path = Path(config_path)
        
        self._config: Optional[ConfigModel] = None
        self._backup_enabled = True
        self._auto_save = True
        self._logger = self._setup_logger()
        
        # 确保配置目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('ConfigManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_config(self) -> ConfigModel:
        """
        加载配置文件
        
        Returns:
            配置模型实例
            
        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML解析错误
            ValueError: 配置验证失败
        """
        try:
            if not self.config_path.exists():
                self._logger.warning(f"配置文件不存在，创建默认配置: {self.config_path}")
                return self.create_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            if config_dict is None:
                raise ValueError("配置文件为空")
            
            # 创建配置模型
            self._config = ConfigModel.from_dict(config_dict)
            
            # 验证配置
            errors = self._config.validate()
            if errors:
                error_msg = "配置验证失败:\n"
                for section, section_errors in errors.items():
                    error_msg += f"  {section}: {', '.join(section_errors)}\n"
                raise ValueError(error_msg)
            
            self._logger.info(f"配置文件加载成功: {self.config_path}")
            return self._config
            
        except yaml.YAMLError as e:
            self._logger.error(f"YAML解析错误: {e}")
            raise
        except Exception as e:
            self._logger.error(f"加载配置文件失败: {e}")
            raise
    
    def save_config(self, config: Optional[ConfigModel] = None, 
                   backup: bool = True) -> bool:
        """
        保存配置文件
        
        Args:
            config: 要保存的配置模型，如果为None则使用当前配置
            backup: 是否创建备份
            
        Returns:
            保存是否成功
        """
        try:
            if config is None:
                if self._config is None:
                    raise ValueError("没有配置可保存")
                config = self._config
            
            # 创建备份
            if backup and self._backup_enabled:
                self._create_backup()
            
            # 转换为字典并保存
            config_dict = config.to_dict()
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            self._config = config
            self._logger.info(f"配置文件保存成功: {self.config_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"保存配置文件失败: {e}")
            return False
    
    def create_default_config(self) -> ConfigModel:
        """
        创建默认配置
        
        Returns:
            默认配置模型
        """
        self._config = ConfigModel()
        self.save_config(backup=False)
        self._logger.info("创建默认配置文件")
        return self._config
    
    def _create_backup(self):
        """创建配置文件备份"""
        if not self.config_path.exists():
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_path.parent / f"{self.config_path.stem}_backup_{timestamp}{self.config_path.suffix}"
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as source:
                with open(backup_path, 'w', encoding='utf-8') as target:
                    target.write(source.read())
            self._logger.info(f"配置文件备份创建成功: {backup_path}")
        except Exception as e:
            self._logger.warning(f"创建备份失败: {e}")
    
    def get_config(self) -> ConfigModel:
        """
        获取当前配置
        
        Returns:
            当前配置模型
            
        Raises:
            RuntimeError: 配置未加载
        """
        if self._config is None:
            raise RuntimeError("配置未加载，请先调用load_config()")
        return self._config
    
    def update_config(self, section: str, updates: Dict[str, Any]) -> bool:
        """
        更新配置的特定部分
        
        Args:
            section: 配置节名称
            updates: 要更新的键值对
            
        Returns:
            更新是否成功
        """
        try:
            if self._config is None:
                raise RuntimeError("配置未加载")
            
            # 获取当前配置字典
            config_dict = self._config.to_dict()
            
            if section not in config_dict:
                raise ValueError(f"配置节不存在: {section}")
            
            # 更新配置
            for key, value in updates.items():
                if key in config_dict[section]:
                    config_dict[section][key] = value
                else:
                    self._logger.warning(f"忽略不存在的配置项: {section}.{key}")
            
            # 重新创建配置模型
            self._config = ConfigModel.from_dict(config_dict)
            
            # 自动保存
            if self._auto_save:
                return self.save_config()
            
            return True
            
        except Exception as e:
            self._logger.error(f"更新配置失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, List[str]]:
        """
        验证当前配置
        
        Returns:
            验证错误字典，空字典表示验证通过
        """
        if self._config is None:
            return {"general": ["配置未加载"]}
        return self._config.validate()
    
    def is_config_valid(self) -> bool:
        """检查当前配置是否有效"""
        errors = self.validate_config()
        return len(errors) == 0
    
    def reload_config(self) -> ConfigModel:
        """重新加载配置文件"""
        self._config = None
        return self.load_config()
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息摘要"""
        if self._config is None:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "config_path": str(self.config_path),
            "is_valid": self.is_config_valid(),
            "app_name": self._config.app.name,
            "app_version": self._config.app.version,
            "sections": list(self._config.to_dict().keys())
        }
    
    def set_auto_save(self, enabled: bool):
        """设置自动保存功能"""
        self._auto_save = enabled
        self._logger.info(f"自动保存设置为: {enabled}")
    
    def set_backup_enabled(self, enabled: bool):
        """设置备份功能"""
        self._backup_enabled = enabled
        self._logger.info(f"备份功能设置为: {enabled}")


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def init_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """
    初始化全局配置管理器
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ConfigManager实例
    """
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器
    
    Returns:
        ConfigManager实例
        
    Raises:
        RuntimeError: 配置管理器未初始化
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = init_config_manager()
    
    return _config_manager


def load_config() -> ConfigModel:
    """
    加载配置（便捷函数）
    
    Returns:
        配置模型实例
    """
    manager = get_config_manager()
    return manager.load_config()


def save_config(config: Optional[ConfigModel] = None) -> bool:
    """
    保存配置（便捷函数）
    
    Args:
        config: 要保存的配置模型
        
    Returns:
        保存是否成功
    """
    manager = get_config_manager()
    return manager.save_config(config)


def get_config() -> ConfigModel:
    """
    获取当前配置（便捷函数）
    
    Returns:
        当前配置模型
    """
    manager = get_config_manager()
    return manager.get_config()


# 测试函数
def test_config_manager():
    """测试配置管理器"""
    try:
        # 初始化配置管理器
        manager = init_config_manager()
        
        # 加载配置
        config = manager.load_config()
        print("✓ 配置加载成功")
        
        # 获取配置信息
        info = manager.get_config_info()
        print("配置信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 验证配置
        if manager.is_config_valid():
            print("✓ 配置验证通过")
        else:
            print("❌ 配置验证失败")
        
        # 测试更新配置
        success = manager.update_config("app", {"debug": True})
        if success:
            print("✓ 配置更新成功")
        else:
            print("❌ 配置更新失败")
        
        return True
        
    except Exception as e:
        print(f"配置管理器测试失败: {e}")
        return False


if __name__ == "__main__":
    test_config_manager()
