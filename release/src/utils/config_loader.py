"""
配置加载器模块
负责加载和管理应用配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 使用默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / 'config' / 'app_config.yaml'
        else:
            self.config_path = Path(config_path)
        
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                
            if self._config is None:
                raise ValueError("配置文件为空或格式错误")
                
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析错误: {e}")
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        if self._config is None:
            raise RuntimeError("配置未加载")
        return self._config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置的特定部分"""
        if self._config is None:
            raise RuntimeError("配置未加载")
        
        if section not in self._config:
            raise KeyError(f"配置节不存在: {section}")
        
        return self._config[section].copy()
    
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """获取配置的特定值"""
        try:
            section_config = self.get_section(section)
            return section_config.get(key, default)
        except KeyError:
            return default
    
    def validate_config(self) -> bool:
        """验证配置文件的完整性"""
        if self._config is None:
            return False
        
        required_sections = ['app', 'database', 'a2a_server', 'ui']
        
        for section in required_sections:
            if section not in self._config:
                return False
        
        # 验证app配置
        app_config = self._config['app']
        required_app_keys = ['name', 'version']
        for key in required_app_keys:
            if key not in app_config:
                return False
        
        return True
    
    def reload_config(self):
        """重新加载配置文件"""
        self._config = None
        self._load_config()
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息摘要"""
        if self._config is None:
            return {}
        
        return {
            'config_path': str(self.config_path),
            'sections': list(self._config.keys()),
            'is_valid': self.validate_config(),
            'app_name': self.get_value('app', 'name', 'Unknown'),
            'app_version': self.get_value('app', 'version', 'Unknown')
        }


# 全局配置加载器实例
_config_loader: Optional[ConfigLoader] = None


def init_config_loader(config_path: Optional[str] = None) -> ConfigLoader:
    """
    初始化全局配置加载器
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ConfigLoader实例
    """
    global _config_loader
    _config_loader = ConfigLoader(config_path)
    return _config_loader


def load_config() -> Dict[str, Any]:
    """
    加载配置（便捷函数）
    
    Returns:
        配置字典
        
    Raises:
        RuntimeError: 如果配置加载器未初始化
    """
    global _config_loader
    
    if _config_loader is None:
        _config_loader = init_config_loader()
    
    return _config_loader.get_config()


def get_config_section(section: str) -> Dict[str, Any]:
    """
    获取配置的特定部分
    
    Args:
        section: 配置节名称
        
    Returns:
        配置节字典
    """
    global _config_loader
    
    if _config_loader is None:
        _config_loader = init_config_loader()
    
    return _config_loader.get_section(section)


def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """
    获取配置的特定值
    
    Args:
        section: 配置节名称
        key: 配置键名
        default: 默认值
        
    Returns:
        配置值
    """
    global _config_loader
    
    if _config_loader is None:
        _config_loader = init_config_loader()
    
    return _config_loader.get_value(section, key, default)


def validate_config() -> bool:
    """验证配置文件的完整性"""
    global _config_loader
    
    if _config_loader is None:
        _config_loader = init_config_loader()
    
    return _config_loader.validate_config()


def get_config_info() -> Dict[str, Any]:
    """获取配置信息摘要"""
    global _config_loader
    
    if _config_loader is None:
        _config_loader = init_config_loader()
    
    return _config_loader.get_config_info()


# 测试函数
def test_config_loader():
    """测试配置加载器"""
    try:
        # 初始化配置加载器
        loader = init_config_loader()
        
        # 获取配置信息
        info = get_config_info()
        print("配置信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 验证配置
        if validate_config():
            print("✓ 配置验证通过")
        else:
            print("✗ 配置验证失败")
        
        # 测试获取配置值
        app_name = get_config_value('app', 'name')
        print(f"应用名称: {app_name}")
        
        return True
        
    except Exception as e:
        print(f"配置加载器测试失败: {e}")
        return False


if __name__ == "__main__":
    test_config_loader()
