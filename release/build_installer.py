#!/usr/bin/env python3
"""
AI Agent Desktop 安装程序打包脚本
支持跨平台打包：Windows、macOS、Linux
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

class InstallerBuilder:
    """安装程序构建器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        
    def clean_build_dirs(self):
        """清理构建目录"""
        print("清理构建目录...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(exist_ok=True)
    
    def create_spec_file(self, platform_name):
        """创建PyInstaller spec文件"""
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent

# 添加项目路径
sys.path.insert(0, str(project_root))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 配置文件
        ('config/*.yaml', 'config'),
        ('config/model_configs/*.yaml', 'config/model_configs'),
        
        # 文档
        ('docs/*.md', 'docs'),
        
        # 数据目录
        ('data/', 'data'),
        
        # 日志目录
        ('logs/', 'logs'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'yaml',
        'aiohttp',
        'aiohttp.client',
        'asyncio',
        'sqlite3',
        'json',
        'logging',
        'pathlib',
        'typing',
        'dataclasses',
        'enum',
        'collections',
        'threading',
        'concurrent.futures',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 排除不必要的模块
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'numpy',
    'pandas',
    'tensorflow',
    'torch',
    'PIL',
    'PIL._imaging',
    'PyQt5',
    'PySide2',
    'PySide6',
]

for exclude in excludes:
    if exclude in a.binaries:
        a.binaries.remove(exclude)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI_Agent_Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 如果是Windows，创建单文件可执行文件
if platform.system() == 'Windows':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='AI_Agent_Desktop',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        runtime_tmpdir=None,
        console=False,
        icon=str(project_root / 'assets' / 'app_icon.ico') if (project_root / 'assets' / 'app_icon.ico').exists() else None,
    )
'''
        
        spec_file = self.project_root / f"ai_agent_desktop_{platform_name}.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        return spec_file
    
    def build_windows_installer(self):
        """构建Windows安装程序"""
        print("构建Windows安装程序...")
        
        # 创建spec文件
        spec_file = self.create_spec_file("windows")
        
        # 使用PyInstaller构建
        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name', 'AI_Agent_Desktop',
            '--icon', str(self.project_root / 'assets' / 'app_icon.ico') if (self.project_root / 'assets' / 'app_icon.ico').exists() else '',
            '--add-data', f'{self.project_root / "config"};config',
            '--add-data', f'{self.project_root / "config" / "model_configs"};config/model_configs',
            '--add-data', f'{self.project_root / "docs"};docs',
            '--add-data', f'{self.project_root / "data"};data',
            '--add-data', f'{self.project_root / "logs"};logs',
            '--hidden-import', 'PyQt6',
            '--hidden-import', 'PyQt6.QtWidgets',
            '--hidden-import', 'PyQt6.QtCore',
            '--hidden-import', 'PyQt6.QtGui',
            '--hidden-import', 'yaml',
            '--hidden-import', 'aiohttp',
            '--hidden-import', 'aiohttp.client',
            '--exclude-module', 'tkinter',
            '--exclude-module', 'matplotlib',
            '--exclude-module', 'numpy',
            str(self.project_root / 'main.py')
        ]
        
        # 过滤空参数
        cmd = [arg for arg in cmd if arg]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("✅ Windows安装程序构建成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ Windows安装程序构建失败: {e}")
            return False
        
        # 创建安装程序包
        installer_dir = self.dist_dir / "windows"
        installer_dir.mkdir(exist_ok=True)
        
        # 复制可执行文件
        exe_file = self.dist_dir / "AI_Agent_Desktop.exe"
        if exe_file.exists():
            shutil.copy2(exe_file, installer_dir / "AI_Agent_Desktop_Setup_v1.0.0.exe")
            print(f"✅ Windows安装程序已创建: {installer_dir / 'AI_Agent_Desktop_Setup_v1.0.0.exe'}")
        else:
            print("❌ 可执行文件未找到")
            return False
        
        return True
    
    def build_macos_app(self):
        """构建macOS应用"""
        print("构建macOS应用...")
        
        cmd = [
            'pyinstaller',
            '--windowed',
            '--name', 'AI Agent Desktop',
            '--icon', str(self.project_root / 'assets' / 'app_icon.icns') if (self.project_root / 'assets' / 'app_icon.icns').exists() else '',
            '--add-data', f'{self.project_root / "config"}:config',
            '--add-data', f'{self.project_root / "config" / "model_configs"}:config/model_configs',
            '--add-data', f'{self.project_root / "docs"}:docs',
            '--add-data', f'{self.project_root / "data"}:data',
            '--add-data', f'{self.project_root / "logs"}:logs',
            '--osx-bundle-identifier', 'com.aidesktop.aiagent',
            str(self.project_root / 'main.py')
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("✅ macOS应用构建成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ macOS应用构建失败: {e}")
            return False
        
        # 创建DMG包
        app_dir = self.dist_dir / "AI Agent Desktop.app"
        dmg_dir = self.dist_dir / "macos"
        dmg_dir.mkdir(exist_ok=True)
        
        if app_dir.exists():
            # 这里可以使用create-dmg工具创建DMG文件
            # 暂时先复制应用目录
            shutil.copytree(app_dir, dmg_dir / "AI Agent Desktop.app", dirs_exist_ok=True)
            print(f"✅ macOS应用已创建: {dmg_dir / 'AI Agent Desktop.app'}")
        else:
            print("❌ 应用目录未找到")
            return False
        
        return True
    
    def build_linux_appimage(self):
        """构建Linux AppImage"""
        print("构建Linux AppImage...")
        
        cmd = [
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name', 'ai_agent_desktop',
            '--add-data', f'{self.project_root / "config"}:config',
            '--add-data', f'{self.project_root / "config" / "model_configs"}:config/model_configs',
            '--add-data', f'{self.project_root / "docs"}:docs',
            '--add-data', f'{self.project_root / "data"}:data',
            '--add-data', f'{self.project_root / "logs"}:logs',
            str(self.project_root / 'main.py')
        ]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("✅ Linux应用构建成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ Linux应用构建失败: {e}")
            return False
        
        # 创建AppImage（需要linuxdeploy工具）
        linux_dir = self.dist_dir / "linux"
        linux_dir.mkdir(exist_ok=True)
        
        exe_file = self.dist_dir / "ai_agent_desktop"
        if exe_file.exists():
            shutil.copy2(exe_file, linux_dir / "AI_Agent_Desktop_v1.0.0.AppImage")
            print(f"✅ Linux AppImage已创建: {linux_dir / 'AI_Agent_Desktop_v1.0.0.AppImage'}")
        else:
            print("❌ 可执行文件未找到")
            return False
        
        return True
    
    def create_release_package(self):
        """创建发布包"""
        print("创建发布包...")
        
        release_dir = self.project_root / "release"
        release_dir.mkdir(exist_ok=True)
        
        # 复制文档
        docs_to_copy = [
            'README.md',
            'CHANGELOG.md',
            'RELEASE_NOTES.md',
            'requirements.txt',
            'LICENSE'
        ]
        
        for doc_file in docs_to_copy:
            src = self.project_root / doc_file
            if src.exists():
                shutil.copy2(src, release_dir / doc_file)
        
        # 复制源码
        src_dir = release_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # 复制源代码文件
        for item in self.project_root.iterdir():
            if item.is_file() and item.suffix in ['.py', '.yaml', '.md', '.txt']:
                shutil.copy2(item, src_dir / item.name)
            elif item.is_dir() and item.name in ['src', 'config', 'docs']:
                shutil.copytree(item, src_dir / item.name, dirs_exist_ok=True)
        
        print("✅ 发布包已创建")
        return True
    
    def build_all(self):
        """构建所有平台的安装程序"""
        print("开始构建AI Agent Desktop安装程序...")
        print(f"项目根目录: {self.project_root}")
        
        # 清理构建目录
        self.clean_build_dirs()
        
        # 检查PyInstaller是否安装
        try:
            import PyInstaller
            print(f"✅ PyInstaller版本: {PyInstaller.__version__}")
        except ImportError:
            print("❌ PyInstaller未安装，请先安装: pip install pyinstaller")
            return False
        
        # 根据当前平台构建
        current_platform = platform.system()
        success = True
        
        if current_platform == "Windows":
            success = self.build_windows_installer()
        elif current_platform == "Darwin":  # macOS
            success = self.build_macos_app()
        elif current_platform == "Linux":
            success = self.build_linux_appimage()
        else:
            print(f"❌ 不支持的操作系统: {current_platform}")
            return False
        
        # 创建发布包
        if success:
            self.create_release_package()
        
        print("\n" + "="*50)
        if success:
            print("🎉 安装程序构建完成！")
            print(f"安装程序位置: {self.dist_dir}")
            print(f"发布包位置: {self.project_root / 'release'}")
        else:
            print("❌ 安装程序构建失败")
        
        return success

def main():
    """主函数"""
    builder = InstallerBuilder()
    success = builder.build_all()
    
    if success:
        print("\n📦 发布文件清单:")
        print("1. Windows: AI_Agent_Desktop_Setup_v1.0.0.exe")
        print("2. macOS: AI_Agent_Desktop_v1.0.0.dmg (应用包)")
        print("3. Linux: AI_Agent_Desktop_v1.0.0.AppImage")
        print("4. 源码包: release/ 目录")
        print("\n🚀 准备发布！")
    else:
        print("\n❌ 构建失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
