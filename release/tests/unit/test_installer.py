"""
安装程序功能测试
测试PyInstaller打包和安装程序创建功能
"""

import pytest
import sys
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from setup import InstallerConfig, PyInstallerBuilder


class TestInstallerConfig:
    """测试安装程序配置类"""
    
    def test_installer_config_initialization(self):
        """测试安装程序配置初始化"""
        config = InstallerConfig()
        
        assert config.app_name == "AI Agent Desktop"
        assert config.app_version == "1.0.0"
        assert config.company_name == "AI Agent Desktop Team"
        assert config.copyright == "Copyright © 2025 AI Agent Desktop Team"
        assert config.system in ["windows", "darwin", "linux"]
        
        # 检查目录创建
        assert config.build_dir.exists()
        assert config.dist_dir.exists()
        assert config.spec_dir.exists()
    
    def test_get_pyinstaller_config_windows(self):
        """测试获取Windows PyInstaller配置"""
        config = InstallerConfig()
        
        with patch('platform.system', return_value='Windows'):
            with patch('platform.architecture', return_value=('64bit', 'ELF')):
                config.system = 'windows'
                pyinstaller_config = config.get_pyinstaller_config()
                
                assert pyinstaller_config["name"] == "AI Agent Desktop"
                assert pyinstaller_config["console"] is False
                assert pyinstaller_config["version"] == "1.0.0"
                assert "PyQt6.QtCore" in pyinstaller_config["hiddenimports"]
                assert "tkinter" in pyinstaller_config["excludes"]
    
    def test_get_pyinstaller_config_macos(self):
        """测试获取macOS PyInstaller配置"""
        config = InstallerConfig()
        
        with patch('platform.system', return_value='Darwin'):
            with patch('platform.architecture', return_value=('64bit', 'ELF')):
                config.system = 'darwin'
                pyinstaller_config = config.get_pyinstaller_config()
                
                assert pyinstaller_config["name"] == "AI Agent Desktop"
                assert "bundle_identifier" in pyinstaller_config
    
    def test_get_pyinstaller_config_linux(self):
        """测试获取Linux PyInstaller配置"""
        config = InstallerConfig()
        
        with patch('platform.system', return_value='Linux'):
            with patch('platform.architecture', return_value=('64bit', 'ELF')):
                config.system = 'linux'
                pyinstaller_config = config.get_pyinstaller_config()
                
                assert pyinstaller_config["name"] == "AI Agent Desktop"
                assert pyinstaller_config["icon"].endswith(".png")
    
    def test_get_data_files(self):
        """测试获取数据文件"""
        config = InstallerConfig()
        
        # 使用patch.object来模拟目录存在性检查
        with patch('pathlib.Path.exists') as mock_exists:
            with patch('pathlib.Path.glob') as mock_glob:
                # 设置exists返回True
                mock_exists.return_value = True
                
                # 模拟配置文件
                mock_config_file = Mock()
                mock_config_file.is_file.return_value = True
                mock_config_file.relative_to.return_value = Path("config/app_config.yaml")
                
                # 模拟资源文件
                mock_asset_file = Mock()
                mock_asset_file.is_file.return_value = True
                mock_asset_file.relative_to.return_value = Path("assets/icon.ico")
                
                # 模拟文档文件
                mock_doc_file = Mock()
                mock_doc_file.is_file.return_value = True
                mock_doc_file.relative_to.return_value = Path("docs/README.md")
                
                # 设置glob返回值
                mock_glob.side_effect = [
                    [mock_config_file],  # config目录
                    [mock_asset_file],   # assets目录
                    [mock_doc_file]      # docs目录
                ]
                
                data_files = config._get_data_files()
                
                assert len(data_files) == 3
                assert any("app_config.yaml" in str(file[0]) for file in data_files)
                assert any("icon.ico" in str(file[0]) for file in data_files)
                assert any("README.md" in str(file[0]) for file in data_files)


class TestPyInstallerBuilder:
    """测试PyInstaller构建器"""
    
    def setup_method(self):
        """测试方法设置"""
        self.config = InstallerConfig()
        self.builder = PyInstallerBuilder(self.config)
    
    def test_pyinstaller_builder_initialization(self):
        """测试PyInstaller构建器初始化"""
        assert self.builder.config == self.config
        expected_spec_file = self.config.spec_dir / "ai_agent_desktop.spec"
        assert self.builder.spec_file == expected_spec_file
    
    def test_generate_spec_file(self):
        """测试生成spec文件"""
        with patch('builtins.open', create=True) as mock_open:
            with patch.object(self.builder, '_generate_spec_content', return_value="spec content"):
                self.builder.generate_spec_file()
                
                # 验证文件被写入
                mock_open.assert_called_once_with(self.builder.spec_file, 'w', encoding='utf-8')
    
    def test_generate_spec_content_windows(self):
        """测试生成Windows spec文件内容"""
        self.config.system = 'windows'
        pyinstaller_config = {
            'pathex': ['/test/path'],
            'binaries': [],
            'datas': [('/test/config.yaml', 'config')],
            'hiddenimports': ['PyQt6.QtCore'],
            'hooks': [],
            'runtime_hooks': [],
            'excludes': ['tkinter'],
            'upx': True,
            'upx_exclude': [],
            'name': 'AI Agent Desktop',
            'console': False,
            'icon': '/test/icon.ico',
            'company_name': 'Test Company',
            'product_name': 'Test App',
            'version': '1.0.0',
            'copyright': 'Test Copyright'
        }
        
        with patch.object(self.config, 'get_pyinstaller_config', return_value=pyinstaller_config):
            spec_content = self.builder._generate_spec_content()
            
            assert 'AI Agent Desktop' in spec_content
            assert 'PyQt6.QtCore' in spec_content
            assert 'tkinter' in spec_content
            assert 'Windows' in spec_content
    
    @patch('subprocess.run')
    def test_build_success(self, mock_subprocess):
        """测试构建成功"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Build successful"
        mock_subprocess.return_value = mock_result
        
        with patch.object(self.builder, 'generate_spec_file'):
            self.builder.build()
            
            # 验证PyInstaller被调用
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0][0]
            assert 'PyInstaller' in call_args
            assert '--clean' in call_args
            assert '--noconfirm' in call_args
    
    @patch('subprocess.run')
    def test_build_failure(self, mock_subprocess):
        """测试构建失败"""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'cmd', 'error output')
        
        with patch.object(self.builder, 'generate_spec_file'):
            with pytest.raises(subprocess.CalledProcessError):
                self.builder.build()
    
    def test_create_windows_installer(self):
        """测试创建Windows安装程序"""
        self.config.system = 'windows'
        
        with patch('builtins.open', create=True) as mock_open:
            self.builder._create_windows_installer()
            
            # 验证安装脚本被创建
            expected_script = self.config.dist_dir / "install.bat"
            mock_open.assert_called_once_with(expected_script, 'w', encoding='utf-8')
    
    def test_create_macos_installer(self):
        """测试创建macOS安装程序"""
        self.config.system = 'darwin'
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.chmod'):
                self.builder._create_macos_installer()
                
                # 验证安装脚本被创建
                expected_script = self.config.dist_dir / "create_dmg.sh"
                mock_open.assert_called_once_with(expected_script, 'w', encoding='utf-8')
    
    def test_create_linux_installer(self):
        """测试创建Linux安装程序"""
        self.config.system = 'linux'
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.chmod'):
                self.builder._create_linux_installer()
                
                # 验证安装脚本被创建
                expected_script = self.config.dist_dir / "create_deb.sh"
                mock_open.assert_called_once_with(expected_script, 'w', encoding='utf-8')
    
    def test_create_installer_unsupported_platform(self):
        """测试创建不支持的平台安装程序"""
        self.config.system = 'unsupported'
        
        with pytest.raises(ValueError, match="不支持的操作系统: unsupported"):
            self.builder.create_installer()


class TestMainFunction:
    """测试主函数"""
    
    @patch('setup.PyInstallerBuilder')
    @patch('setup.InstallerConfig')
    def test_main_success(self, mock_config, mock_builder):
        """测试主函数成功执行"""
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_builder_instance = Mock()
        mock_builder.return_value = mock_builder_instance
        
        with patch('sys.exit') as mock_exit:
            from setup import main
            
            result = main()
            
            # 验证配置和构建器被创建
            mock_config.assert_called_once()
            mock_builder.assert_called_once_with(mock_config_instance)
            
            # 验证构建过程被调用
            mock_builder_instance.generate_spec_file.assert_called_once()
            mock_builder_instance.build.assert_called_once()
            mock_builder_instance.create_installer.assert_called_once()
            
            # 验证成功退出
            assert result == 0
    
    @patch('setup.PyInstallerBuilder')
    @patch('setup.InstallerConfig')
    def test_main_build_failure(self, mock_config, mock_builder):
        """测试主函数构建失败"""
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_builder_instance = Mock()
        mock_builder_instance.build.side_effect = Exception("Build failed")
        mock_builder.return_value = mock_builder_instance
        
        with patch('sys.exit') as mock_exit:
            from setup import main
            
            result = main()
            
            # 验证错误处理
            assert result == 1
    
    def test_main_pyinstaller_not_installed(self):
        """测试PyInstaller未安装的情况"""
        with patch.dict('sys.modules', {'PyInstaller': None}):
            with patch('builtins.print') as mock_print:
                from setup import main
                
                result = main()
                
                # 验证错误消息被打印
                mock_print.assert_any_call("错误: 未安装PyInstaller")
                mock_print.assert_any_call("请运行: pip install pyinstaller")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
