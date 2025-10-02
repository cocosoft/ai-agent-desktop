"""
配置管理对话框
提供图形界面用于配置管理
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QWidget, QLabel, QLineEdit, QComboBox, QCheckBox,
                            QSpinBox, QPushButton, QTextEdit, QMessageBox,
                            QGroupBox, QFormLayout, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..core.config_manager import get_config_manager, ConfigModel
from ..core.config_model import AppConfig, DatabaseConfig, A2AServerConfig, UIConfig, ModelConfigs, LoggingConfig


class ConfigDialog(QDialog):
    """配置管理对话框"""
    
    config_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = get_config_manager()
        self.original_config = None
        self.current_config = None
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("配置管理")
        self.setMinimumSize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("应用配置管理")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 配置信息标签
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(self.info_label)
        
        # 标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个配置页
        self.create_app_tab()
        self.create_database_tab()
        self.create_a2a_tab()
        self.create_ui_tab()
        self.create_model_tab()
        self.create_logging_tab()
        self.create_validation_tab()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("保存配置")
        self.save_button.clicked.connect(self.save_config)
        self.save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; }")
        
        self.reload_button = QPushButton("重新加载")
        self.reload_button.clicked.connect(self.reload_config)
        
        self.reset_button = QPushButton("重置为默认")
        self.reset_button.clicked.connect(self.reset_to_default)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        # 更新信息显示
        self.update_info_display()
        
    def create_app_tab(self):
        """创建应用配置页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 应用名称
        self.app_name_edit = QLineEdit()
        layout.addRow("应用名称:", self.app_name_edit)
        
        # 应用版本
        self.app_version_edit = QLineEdit()
        layout.addRow("应用版本:", self.app_version_edit)
        
        # 调试模式
        self.debug_checkbox = QCheckBox("启用调试模式")
        layout.addRow(self.debug_checkbox)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addRow("日志级别:", self.log_level_combo)
        
        self.tab_widget.addTab(tab, "应用设置")
        
    def create_database_tab(self):
        """创建数据库配置页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 数据库路径
        self.db_path_edit = QLineEdit()
        layout.addRow("数据库路径:", self.db_path_edit)
        
        # 备份启用
        self.backup_enabled_checkbox = QCheckBox("启用自动备份")
        layout.addRow(self.backup_enabled_checkbox)
        
        # 备份间隔
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(60, 86400)  # 1分钟到1天
        self.backup_interval_spin.setSuffix(" 秒")
        layout.addRow("备份间隔:", self.backup_interval_spin)
        
        self.tab_widget.addTab(tab, "数据库")
        
    def create_a2a_tab(self):
        """创建A2A服务器配置页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 服务器主机
        self.a2a_host_edit = QLineEdit()
        layout.addRow("服务器主机:", self.a2a_host_edit)
        
        # 服务器端口
        self.a2a_port_spin = QSpinBox()
        self.a2a_port_spin.setRange(1, 65535)
        layout.addRow("服务器端口:", self.a2a_port_spin)
        
        # CORS启用
        self.cors_checkbox = QCheckBox("启用CORS支持")
        layout.addRow(self.cors_checkbox)
        
        # 最大工作线程
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 100)
        layout.addRow("最大工作线程:", self.max_workers_spin)
        
        self.tab_widget.addTab(tab, "A2A服务器")
        
    def create_ui_tab(self):
        """创建UI配置页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "system"])
        layout.addRow("主题:", self.theme_combo)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh-CN", "en-US"])
        layout.addRow("语言:", self.language_combo)
        
        # 自动保存
        self.auto_save_checkbox = QCheckBox("启用自动保存")
        layout.addRow(self.auto_save_checkbox)
        
        # 刷新间隔
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1000, 60000)  # 1秒到1分钟
        self.refresh_interval_spin.setSuffix(" 毫秒")
        layout.addRow("刷新间隔:", self.refresh_interval_spin)
        
        self.tab_widget.addTab(tab, "界面设置")
        
    def create_model_tab(self):
        """创建模型配置页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 模型配置路径
        self.model_path_edit = QLineEdit()
        layout.addRow("模型配置路径:", self.model_path_edit)
        
        # 自动发现
        self.auto_discover_checkbox = QCheckBox("启用自动发现")
        layout.addRow(self.auto_discover_checkbox)
        
        self.tab_widget.addTab(tab, "模型配置")
        
    def create_logging_tab(self):
        """创建日志配置页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 日志级别
        self.logging_level_combo = QComboBox()
        self.logging_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addRow("日志级别:", self.logging_level_combo)
        
        # 日志文件
        self.log_file_edit = QLineEdit()
        layout.addRow("日志文件:", self.log_file_edit)
        
        # 最大文件大小
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1024, 104857600)  # 1KB到100MB
        self.max_size_spin.setSuffix(" 字节")
        layout.addRow("最大文件大小:", self.max_size_spin)
        
        # 备份文件数量
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(0, 50)
        layout.addRow("备份文件数量:", self.backup_count_spin)
        
        self.tab_widget.addTab(tab, "日志设置")
        
    def create_validation_tab(self):
        """创建验证信息页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 验证结果区域
        validation_group = QGroupBox("配置验证结果")
        validation_layout = QVBoxLayout(validation_group)
        
        self.validation_text = QTextEdit()
        self.validation_text.setReadOnly(True)
        self.validation_text.setMaximumHeight(200)
        validation_layout.addWidget(self.validation_text)
        
        # 验证按钮
        validate_button = QPushButton("验证配置")
        validate_button.clicked.connect(self.validate_config)
        validation_layout.addWidget(validate_button)
        
        layout.addWidget(validation_group)
        
        # 配置预览区域
        preview_group = QGroupBox("配置预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        self.tab_widget.addTab(tab, "验证和预览")
        
    def load_config(self):
        """加载配置到界面"""
        try:
            self.config_manager.load_config()
            self.original_config = self.config_manager.get_config()
            self.current_config = ConfigModel.from_dict(self.original_config.to_dict())
            
            # 应用配置
            self.app_name_edit.setText(self.current_config.app.name)
            self.app_version_edit.setText(self.current_config.app.version)
            self.debug_checkbox.setChecked(self.current_config.app.debug)
            self.log_level_combo.setCurrentText(self.current_config.app.log_level)
            
            # 数据库配置
            self.db_path_edit.setText(self.current_config.database.path)
            self.backup_enabled_checkbox.setChecked(self.current_config.database.backup_enabled)
            self.backup_interval_spin.setValue(self.current_config.database.backup_interval)
            
            # A2A服务器配置
            self.a2a_host_edit.setText(self.current_config.a2a_server.host)
            self.a2a_port_spin.setValue(self.current_config.a2a_server.port)
            self.cors_checkbox.setChecked(self.current_config.a2a_server.enable_cors)
            self.max_workers_spin.setValue(self.current_config.a2a_server.max_workers)
            
            # UI配置
            self.theme_combo.setCurrentText(self.current_config.ui.theme)
            self.language_combo.setCurrentText(self.current_config.ui.language)
            self.auto_save_checkbox.setChecked(self.current_config.ui.auto_save)
            self.refresh_interval_spin.setValue(self.current_config.ui.refresh_interval)
            
            # 模型配置
            self.model_path_edit.setText(self.current_config.model_configs.path)
            self.auto_discover_checkbox.setChecked(self.current_config.model_configs.auto_discover)
            
            # 日志配置
            self.logging_level_combo.setCurrentText(self.current_config.logging.level)
            self.log_file_edit.setText(self.current_config.logging.file)
            self.max_size_spin.setValue(self.current_config.logging.max_size)
            self.backup_count_spin.setValue(self.current_config.logging.backup_count)
            
            # 更新预览
            self.update_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置失败: {e}")
            
    def save_config(self):
        """保存配置"""
        try:
            # 从界面获取配置值
            self.update_config_from_ui()
            
            # 验证配置
            errors = self.current_config.validate()
            if errors:
                error_msg = "配置验证失败:\n\n"
                for section, section_errors in errors.items():
                    error_msg += f"{section}:\n"
                    for error in section_errors:
                        error_msg += f"  - {error}\n"
                    error_msg += "\n"
                
                reply = QMessageBox.warning(self, "配置验证失败", 
                                          f"{error_msg}\n是否继续保存？",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # 保存配置
            if self.config_manager.save_config(self.current_config):
                self.original_config = self.current_config
                self.config_changed.emit()
                QMessageBox.information(self, "成功", "配置保存成功")
                self.update_info_display()
                self.update_preview()
            else:
                QMessageBox.critical(self, "错误", "配置保存失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
            
    def reload_config(self):
        """重新加载配置"""
        reply = QMessageBox.question(self, "确认", 
                                   "重新加载配置将丢失所有未保存的修改，是否继续？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.load_config()
            
    def reset_to_default(self):
        """重置为默认配置"""
        reply = QMessageBox.question(self, "确认", 
                                   "重置为默认配置将丢失所有自定义设置，是否继续？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.current_config = ConfigModel()
            self.load_config()
            
    def validate_config(self):
        """验证配置"""
        self.update_config_from_ui()
        errors = self.current_config.validate()
        
        if not errors:
            self.validation_text.setText("✓ 配置验证通过")
            self.validation_text.setStyleSheet("color: green;")
        else:
            error_text = "配置验证失败:\n\n"
            for section, section_errors in errors.items():
                error_text += f"{section}:\n"
                for error in section_errors:
                    error_text += f"  - {error}\n"
                error_text += "\n"
            
            self.validation_text.setText(error_text)
            self.validation_text.setStyleSheet("color: red;")
            
    def update_config_from_ui(self):
        """从界面更新配置对象"""
        # 应用配置
        self.current_config.app.name = self.app_name_edit.text()
        self.current_config.app.version = self.app_version_edit.text()
        self.current_config.app.debug = self.debug_checkbox.isChecked()
        self.current_config.app.log_level = self.log_level_combo.currentText()
        
        # 数据库配置
        self.current_config.database.path = self.db_path_edit.text()
        self.current_config.database.backup_enabled = self.backup_enabled_checkbox.isChecked()
        self.current_config.database.backup_interval = self.backup_interval_spin.value()
        
        # A2A服务器配置
        self.current_config.a2a_server.host = self.a2a_host_edit.text()
        self.current_config.a2a_server.port = self.a2a_port_spin.value()
        self.current_config.a2a_server.enable_cors = self.cors_checkbox.isChecked()
        self.current_config.a2a_server.max_workers = self.max_workers_spin.value()
        
        # UI配置
        self.current_config.ui.theme = self.theme_combo.currentText()
        self.current_config.ui.language = self.language_combo.currentText()
        self.current_config.ui.auto_save = self.auto_save_checkbox.isChecked()
        self.current_config.ui.refresh_interval = self.refresh_interval_spin.value()
        
        # 模型配置
        self.current_config.model_configs.path = self.model_path_edit.text()
        self.current_config.model_configs.auto_discover = self.auto_discover_checkbox.isChecked()
        
        # 日志配置
        self.current_config.logging.level = self.logging_level_combo.currentText()
        self.current_config.logging.file = self.log_file_edit.text()
        self.current_config.logging.max_size = self.max_size_spin.value()
        self.current_config.logging.backup_count = self.backup_count_spin.value()
        
    def update_info_display(self):
        """更新信息显示"""
        info = self.config_manager.get_config_info()
        status_text = f"配置文件: {info['config_path']} | "
        status_text += f"状态: {'已加载' if info['loaded'] else '未加载'} | "
        status_text += f"验证: {'通过' if info['is_valid'] else '失败'}"
        self.info_label.setText(status_text)
        
    def update_preview(self):
        """更新配置预览"""
        import yaml
        config_dict = self.current_config.to_dict()
        preview_text = yaml.dump(config_dict, default_flow_style=False, 
                               allow_unicode=True, indent=2)
        self.preview_text.setText(preview_text)


# 测试函数
def test_config_dialog():
    """测试配置对话框"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    try:
        # 初始化配置管理器
        from ..core.config_manager import init_config_manager
        init_config_manager()
        
        # 创建配置对话框
        dialog = ConfigDialog()
        dialog.show()
        
        print("配置对话框创建成功")
        return app.exec()
        
    except Exception as e:
        print(f"配置对话框测试失败: {e}")
        return 1


if __name__ == "__main__":
    test_config_dialog()
