"""
AI Agent Desktop 应用安装程序配置
用于PyInstaller打包和安装程序创建
"""

import os
import sys
import platform
from pathlib import Path
import subprocess
import shutil
from typing import List, Dict, Any


class InstallerConfig:
    """安装程序配置类"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.app_name = "AI Agent Desktop"
        self.app_version = "1.0.0"
        self.company_name = "AI Agent Desktop Team"
        self.copyright = "Copyright © 2025 AI Agent Desktop Team"
        
        # 平台特定配置
        self.system = platform.system().lower()
        self.architecture = platform.architecture()[0]
        
        # 输出目录
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.spec_dir = self.project_root / "spec"
        
        # 创建必要的目录
        self._create_directories()
    
    def _create_directories(self):
        """创建必要的目录"""
        for directory in [self.build_dir, self.dist_dir, self.spec_dir]:
            directory.mkdir(exist_ok=True)
    
    def get_pyinstaller_config(self) -> Dict[str, Any]:
        """获取PyInstaller配置"""
        if self.system == "windows":
            return self._get_windows_config()
        elif self.system == "darwin":
            return self._get_macos_config()
        elif self.system == "linux":
            return self._get_linux_config()
        else:
            raise ValueError(f"不支持的操作系统: {self.system}")
    
    def _get_windows_config(self) -> Dict[str, Any]:
        """获取Windows配置"""
        return {
            "name": f"{self.app_name}",
            "console": False,
            "icon": str(self.project_root / "assets" / "app_icon.ico"),
            "version": self.app_version,
            "company_name": self.company_name,
            "copyright": self.copyright,
            "product_name": self.app_name,
            "onefile": False,
            "hiddenimports": [
                "PyQt6.QtCore",
                "PyQt6.QtGui", 
                "PyQt6.QtWidgets",
                "PyQt6.QtNetwork",
                "yaml",
                "sqlite3",
                "psutil",
                "platformdirs",
                "aiohttp",
                "asyncio",
                "json",
                "logging",
                "pathlib",
                "typing",
                "dataclasses",
                "enum"
            ],
            "datas": self._get_data_files(),
            "binaries": [],
            "pathex": [str(self.project_root)],
            "hooks": [],
            "runtime_hooks": [],
            "excludes": [
                "tkinter",
                "test",
                "unittest",
                "pytest",
                "distutils",
                "setuptools",
                "pip",
                "wheel",
                "venv",
                "virtualenv"
            ],
            "optimize": 2,
            "upx": True,
            "upx_exclude": [],
            "collect_submodules": {
                "PyQt6": True,
                "yaml": True,
                "psutil": True
            }
        }
    
    def _get_macos_config(self) -> Dict[str, Any]:
        """获取macOS配置"""
        config = self._get_windows_config()
        config["icon"] = str(self.project_root / "assets" / "app_icon.icns")
        config["bundle_identifier"] = f"com.{self.company_name.lower().replace(' ', '')}.{self.app_name.lower().replace(' ', '')}"
        return config
    
    def _get_linux_config(self) -> Dict[str, Any]:
        """获取Linux配置"""
        config = self._get_windows_config()
        config["icon"] = str(self.project_root / "assets" / "app_icon.png")
        return config
    
    def _get_data_files(self) -> List[tuple]:
        """获取数据文件列表"""
        data_files = []
        
        # 配置文件
        config_dir = self.project_root / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("**/*"):
                if config_file.is_file():
                    relative_path = config_file.relative_to(self.project_root)
                    data_files.append((str(config_file), str(relative_path.parent)))
        
        # 资源文件
        assets_dir = self.project_root / "assets"
        if assets_dir.exists():
            for asset_file in assets_dir.glob("**/*"):
                if asset_file.is_file():
                    relative_path = asset_file.relative_to(self.project_root)
                    data_files.append((str(asset_file), str(relative_path.parent)))
        
        # 文档文件
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.glob("**/*.md"):
                if doc_file.is_file():
                    relative_path = doc_file.relative_to(self.project_root)
                    data_files.append((str(doc_file), str(relative_path.parent)))
        
        return data_files


class PyInstallerBuilder:
    """PyInstaller构建器"""
    
    def __init__(self, config: InstallerConfig):
        self.config = config
        self.spec_file = self.config.spec_dir / f"{self.config.app_name.replace(' ', '_').lower()}.spec"
    
    def generate_spec_file(self):
        """生成PyInstaller spec文件"""
        spec_content = self._generate_spec_content()
        
        with open(self.spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✓ 已生成spec文件: {self.spec_file}")
    
    def _generate_spec_content(self) -> str:
        """生成spec文件内容"""
        pyinstaller_config = self.config.get_pyinstaller_config()
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

block_cipher = None

a = Analysis(
    ['{self.config.project_root / "main.py"}'],
    pathex={pyinstaller_config['pathex']},
    binaries={pyinstaller_config['binaries']},
    datas={pyinstaller_config['datas']},
    hiddenimports={pyinstaller_config['hiddenimports']},
    hookspath={pyinstaller_config['hooks']},
    hooksconfig={{}},
    runtime_hooks={pyinstaller_config['runtime_hooks']},
    excludes={pyinstaller_config['excludes']},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{pyinstaller_config["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={pyinstaller_config['upx']},
    upx_exclude={pyinstaller_config['upx_exclude']},
    runtime_tmpdir=None,
    console={pyinstaller_config['console']},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{pyinstaller_config["icon"]}' if os.path.exists('{pyinstaller_config["icon"]}') else None,
)

# Windows特定配置
if sys.platform == 'win32':
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringTable,
        StringStruct,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )
    
        version_info = VSVersionInfo(
            ffi=FixedFileInfo(
                filevers=({self.config.app_version.split('.')[0]}, {self.config.app_version.split('.')[1]}, {self.config.app_version.split('.')[2]}, 0),
                prodvers=({self.config.app_version.split('.')[0]}, {self.config.app_version.split('.')[1]}, {self.config.app_version.split('.')[2]}, 0),
            mask=0x3f,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0)
        ),
        kids=[
            StringFileInfo([
                StringTable(
                    '040904b0',
                    [
                        StringStruct('CompanyName', '{pyinstaller_config["company_name"]}'),
                        StringStruct('FileDescription', '{pyinstaller_config["product_name"]}'),
                        StringStruct('FileVersion', '{pyinstaller_config["version"]}'),
                        StringStruct('InternalName', '{pyinstaller_config["name"]}'),
                        StringStruct('LegalCopyright', '{pyinstaller_config["copyright"]}'),
                        StringStruct('OriginalFilename', '{pyinstaller_config["name"]}.exe'),
                        StringStruct('ProductName', '{pyinstaller_config["product_name"]}'),
                        StringStruct('ProductVersion', '{pyinstaller_config["version"]}'),
                    ]
                )
            ]),
            VarFileInfo([VarStruct('Translation', [0x409, 1200])])
        ]
    )
    
    exe.version = version_info
'''
        return spec_content
    
    def build(self):
        """构建应用"""
        print(f"开始构建 {self.config.app_name}...")
        
        # 生成spec文件
        self.generate_spec_file()
        
        # 运行PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(self.spec_file)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✓ 构建成功完成")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"✗ 构建失败: {e}")
            print(e.stderr)
            raise
    
    def create_installer(self):
        """创建安装程序"""
        if self.config.system == "windows":
            self._create_windows_installer()
        elif self.config.system == "darwin":
            self._create_macos_installer()
        elif self.config.system == "linux":
            self._create_linux_installer()
        else:
            raise ValueError(f"不支持的操作系统: {self.config.system}")
    
    def _create_windows_installer(self):
        """创建Windows安装程序"""
        print("创建Windows安装程序...")
        
        # 这里可以使用Inno Setup或NSIS创建安装程序
        # 目前先创建简单的批处理安装脚本
        
        installer_script = self.config.dist_dir / "install.bat"
        installer_content = f'''@echo off
echo 正在安装 {self.config.app_name} {self.config.app_version}...
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 需要管理员权限来安装应用
    echo 请以管理员身份运行此脚本
    pause
    exit /b 1
)

REM 创建开始菜单快捷方式
set "START_MENU_DIR=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{self.config.app_name}"
if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"

REM 创建桌面快捷方式
set "DESKTOP_DIR=%USERPROFILE%\\Desktop"

REM 复制可执行文件到程序目录
set "PROGRAM_DIR=%PROGRAMFILES%\\{self.config.app_name}"
if not exist "%PROGRAM_DIR%" mkdir "%PROGRAM_DIR%"

xcopy "{self.config.app_name}\\*" "%PROGRAM_DIR%\\" /E /Y /I

REM 创建快捷方式
echo 创建快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\\{self.config.app_name}.lnk'); $Shortcut.TargetPath = '%PROGRAM_DIR%\\{self.config.app_name}.exe'; $Shortcut.WorkingDirectory = '%PROGRAM_DIR%'; $Shortcut.Save()"
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_DIR%\\{self.config.app_name}.lnk'); $Shortcut.TargetPath = '%PROGRAM_DIR%\\{self.config.app_name}.exe'; $Shortcut.WorkingDirectory = '%PROGRAM_DIR%'; $Shortcut.Save()"

echo.
echo 安装完成！
echo 应用已安装到: %PROGRAM_DIR%
echo 开始菜单快捷方式已创建
echo 桌面快捷方式已创建
echo.
pause
'''

        with open(installer_script, 'w', encoding='utf-8') as f:
            f.write(installer_content)
        
        print(f"✓ 已创建Windows安装脚本: {installer_script}")
    
    def _create_macos_installer(self):
        """创建macOS安装程序"""
        print("创建macOS安装程序...")
        
        # 创建DMG安装脚本
        installer_script = self.config.dist_dir / "create_dmg.sh"
        installer_content = f'''#!/bin/bash
echo "Creating macOS installer for {self.config.app_name}..."

# 创建DMG文件
DMG_NAME="{self.config.app_name.replace(' ', '_')}_{self.config.app_version}.dmg"
VOLUME_NAME="{self.config.app_name}"
APP_NAME="{self.config.app_name}.app"

# 检查应用是否存在
if [ ! -d "$APP_NAME" ]; then
    echo "Error: Application bundle not found: $APP_NAME"
    exit 1
fi

# 创建临时目录
TEMP_DIR="temp_dmg"
mkdir -p "$TEMP_DIR"

# 复制应用到临时目录
cp -R "$APP_NAME" "$TEMP_DIR/"

# 创建Applications链接
ln -s /Applications "$TEMP_DIR/Applications"

# 创建DMG
hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_NAME"

# 清理临时文件
rm -rf "$TEMP_DIR"

echo "DMG created: $DMG_NAME"
'''

        with open(installer_script, 'w', encoding='utf-8') as f:
            f.write(installer_content)
        
        # 设置执行权限
        os.chmod(installer_script, 0o755)
        
        print(f"✓ 已创建macOS安装脚本: {installer_script}")
    
    def _create_linux_installer(self):
        """创建Linux安装程序"""
        print("创建Linux安装程序...")
        
        # 创建DEB包安装脚本
        installer_script = self.config.dist_dir / "create_deb.sh"
        installer_content = f'''#!/bin/bash
echo "Creating Linux installer for {self.config.app_name}..."

# 创建DEB包目录结构
PACKAGE_NAME="{self.config.app_name.replace(' ', '-').lower()}"
VERSION="{self.config.app_version}"
ARCHITECTURE="amd64"

DEB_DIR="$PACKAGE_NAME-$VERSION"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"

# 创建控制文件
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCHITECTURE
Depends: python3, python3-pip, libqt6core6, libqt6gui6, libqt6widgets6
Maintainer: {self.config.company_name}
Description: {self.config.app_name}
 AI Agent Desktop Management Application
EOF

# 创建桌面文件
cat > "$DEB_DIR/usr/share/applications/$PACKAGE_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name={self.config.app_name}
Comment=AI Agent Desktop Management Application
Exec=/usr/bin/{self.config.app_name.replace(' ', '').lower()}
Icon=$PACKAGE_NAME
Categories=Utility;
Terminal=false
StartupNotify=true
EOF

# 复制可执行文件
cp "{self.config.app_name.replace(' ', '').lower()}" "$DEB_DIR/usr/bin/"

# 构建DEB包
dpkg-deb --build "$DEB_DIR"

# 清理
rm -rf "$DEB_DIR"

echo "DEB package created: $PACKAGE_NAME-$VERSION-$ARCHITECTURE.deb"
'''

        with open(installer_script, 'w', encoding='utf-8') as f:
            f.write(installer_content)
        
        # 设置执行权限
        os.chmod(installer_script, 0o755)
        
        print(f"✓ 已创建Linux安装脚本: {installer_script}")


def main():
    """主函数"""
    try:
        # 检查PyInstaller是否安装
        import PyInstaller
    except ImportError:
        print("错误: 未安装PyInstaller")
        print("请运行: pip install pyinstaller")
        return
    
    # 创建配置
    config = InstallerConfig()
    
    # 构建应用
    builder = PyInstallerBuilder(config)
    
    try:
        # 生成spec文件
        builder.generate_spec_file()
        
        # 构建应用
        builder.build()
        
        # 创建安装程序
        builder.create_installer()
        
        print(f"\n✓ {config.app_name} 安装程序准备完成")
        print(f"构建目录: {config.build_dir}")
        print(f"输出目录: {config.dist_dir}")
        print(f"spec文件: {builder.spec_file}")
        
    except Exception as e:
        print(f"构建过程中发生错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
