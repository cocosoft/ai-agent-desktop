"""
数据库管理器
负责SQLite数据库的连接、初始化和基本操作
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 使用默认数据库路径
            project_root = Path(__file__).parent.parent.parent
            self.db_path = project_root / 'data' / 'app.db'
        else:
            self.db_path = Path(db_path)
        
        self.connection: Optional[sqlite3.Connection] = None
        self._logger = self._setup_logger()
        
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('DatabaseManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def connect(self) -> sqlite3.Connection:
        """
        连接到数据库
        
        Returns:
            SQLite连接对象
            
        Raises:
            sqlite3.Error: 数据库连接错误
        """
        try:
            self.connection = sqlite3.connect(
                str(self.db_path),
                timeout=30,
                check_same_thread=False
            )
            
            # 启用外键约束
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # 设置WAL模式以提高并发性能
            self.connection.execute("PRAGMA journal_mode = WAL")
            
            self._logger.info(f"数据库连接成功: {self.db_path}")
            return self.connection
            
        except sqlite3.Error as e:
            self._logger.error(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self._logger.info("数据库连接已关闭")
    
    def initialize_database(self) -> bool:
        """
        初始化数据库表结构
        
        Returns:
            初始化是否成功
        """
        try:
            if self.connection is None:
                self.connect()
            
            # 创建所有表
            self._create_tables()
            
            # 插入初始数据
            self._insert_initial_data()
            
            self._logger.info("数据库初始化完成")
            return True
            
        except Exception as e:
            self._logger.error(f"数据库初始化失败: {e}")
            return False
    
    def _create_tables(self):
        """创建所有数据库表"""
        tables_sql = [
            # 数据库版本表
            """
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # 模型相关表
            """
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                type VARCHAR(50) NOT NULL,
                adapter_type VARCHAR(50) NOT NULL,
                base_url VARCHAR(500),
                api_key VARCHAR(500),
                description TEXT,
                version VARCHAR(50),
                is_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS model_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                config_key VARCHAR(100) NOT NULL,
                config_value TEXT,
                config_type VARCHAR(20) DEFAULT 'string',
                description TEXT,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                UNIQUE(model_id, config_key)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS model_capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                capability_id INTEGER NOT NULL,
                score FLOAT DEFAULT 0.0,
                test_count INTEGER DEFAULT 0,
                last_tested TIMESTAMP,
                is_verified BOOLEAN DEFAULT 0,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE CASCADE,
                UNIQUE(model_id, capability_id)
            )
            """,
            
            # 能力相关表
            """
            CREATE TABLE IF NOT EXISTS capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                category VARCHAR(50) NOT NULL,
                description TEXT,
                test_script TEXT,
                expected_result TEXT,
                priority INTEGER DEFAULT 5,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS capability_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capability_id INTEGER NOT NULL,
                test_name VARCHAR(100) NOT NULL,
                test_input TEXT NOT NULL,
                expected_output TEXT,
                timeout_seconds INTEGER DEFAULT 30,
                max_retries INTEGER DEFAULT 3,
                weight FLOAT DEFAULT 1.0,
                FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE CASCADE
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                capability_id INTEGER NOT NULL,
                test_id INTEGER NOT NULL,
                test_input TEXT,
                actual_output TEXT,
                score FLOAT,
                duration_ms INTEGER,
                error_message TEXT,
                test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE CASCADE,
                FOREIGN KEY (test_id) REFERENCES capability_tests(id) ON DELETE CASCADE
            )
            """,
            
            # 代理相关表
            """
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                agent_type VARCHAR(50) DEFAULT 'general',
                template_id INTEGER,
                model_selection_strategy VARCHAR(50) DEFAULT 'auto',
                max_concurrent_tasks INTEGER DEFAULT 5,
                is_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS agent_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,
                instance_name VARCHAR(100),
                status VARCHAR(20) DEFAULT 'stopped',
                pid INTEGER,
                start_time TIMESTAMP,
                stop_time TIMESTAMP,
                last_heartbeat TIMESTAMP,
                error_count INTEGER DEFAULT 0,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS agent_capabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,
                capability_id INTEGER NOT NULL,
                priority INTEGER DEFAULT 5,
                is_required BOOLEAN DEFAULT 0,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE CASCADE,
                UNIQUE(agent_id, capability_id)
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS agent_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                priority INTEGER DEFAULT 5,
                weight FLOAT DEFAULT 1.0,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                UNIQUE(agent_id, model_id)
            )
            """,
            
            # A2A通信相关表
            """
            CREATE TABLE IF NOT EXISTS a2a_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id VARCHAR(100) UNIQUE NOT NULL,
                sender_agent_id INTEGER,
                receiver_agent_id INTEGER,
                message_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                status VARCHAR(20) DEFAULT 'sent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (sender_agent_id) REFERENCES agents(id) ON DELETE SET NULL,
                FOREIGN KEY (receiver_agent_id) REFERENCES agents(id) ON DELETE SET NULL
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS a2a_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id VARCHAR(100) UNIQUE NOT NULL,
                parent_task_id VARCHAR(100),
                agent_id INTEGER NOT NULL,
                capability_id INTEGER NOT NULL,
                input_data TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                status VARCHAR(20) DEFAULT 'pending',
                assigned_model_id INTEGER,
                result_data TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                timeout_seconds INTEGER DEFAULT 300,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                FOREIGN KEY (capability_id) REFERENCES capabilities(id) ON DELETE CASCADE,
                FOREIGN KEY (assigned_model_id) REFERENCES models(id) ON DELETE SET NULL
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS a2a_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(100),
                description TEXT,
                participant_agents TEXT,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP
            )
            """,
            
            # 系统管理表
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type VARCHAR(20) DEFAULT 'string',
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type VARCHAR(50) NOT NULL,
                event_source VARCHAR(100),
                event_data TEXT,
                user_agent VARCHAR(200),
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        # 执行所有建表语句
        for sql in tables_sql:
            self.connection.execute(sql)
        
        # 创建索引
        self._create_indexes()
        
        # 记录数据库版本
        self._set_database_version(1)
    
    def _create_indexes(self):
        """创建数据库索引"""
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_models_type ON models(type)",
            "CREATE INDEX IF NOT EXISTS idx_models_enabled ON models(is_enabled)",
            "CREATE INDEX IF NOT EXISTS idx_capabilities_category ON capabilities(category)",
            "CREATE INDEX IF NOT EXISTS idx_capabilities_active ON capabilities(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_agents_enabled ON agents(is_enabled)",
            "CREATE INDEX IF NOT EXISTS idx_agent_instances_status ON agent_instances(status)",
            "CREATE INDEX IF NOT EXISTS idx_a2a_tasks_status ON a2a_tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_a2a_tasks_priority ON a2a_tasks(priority)",
            "CREATE INDEX IF NOT EXISTS idx_a2a_messages_created ON a2a_messages(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_a2a_messages_status ON a2a_messages(status)",
            "CREATE INDEX IF NOT EXISTS idx_test_results_date ON test_results(test_date)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at)"
        ]
        
        for sql in indexes_sql:
            self.connection.execute(sql)
    
    def _insert_initial_data(self):
        """插入初始数据"""
        # 插入系统设置
        initial_settings = [
            ("app_name", "AI Agent Desktop", "string", "应用名称"),
            ("app_version", "1.0.0", "string", "应用版本"),
            ("database_version", "1", "int", "数据库版本"),
            ("auto_backup_enabled", "true", "bool", "自动备份启用"),
            ("backup_retention_days", "7", "int", "备份保留天数")
        ]
        
        for key, value, value_type, description in initial_settings:
            self.connection.execute(
                "INSERT OR REPLACE INTO system_settings (setting_key, setting_value, setting_type, description) VALUES (?, ?, ?, ?)",
                (key, value, value_type, description)
            )
        
        # 插入一些基础能力定义
        base_capabilities = [
            ("文本生成", "text", "生成文本内容的能力", "生成一段有意义的文本", "文本应该连贯、有逻辑", 8),
            ("问答", "text", "回答问题的能力", "准确回答用户提出的问题", "答案应该准确、简洁", 9),
            ("代码生成", "text", "生成代码的能力", "根据需求生成代码片段", "代码应该正确、可运行", 7),
            ("文本摘要", "text", "文本摘要能力", "对长文本进行摘要", "摘要应该准确、简洁", 6),
            ("翻译", "text", "语言翻译能力", "在不同语言之间进行翻译", "翻译应该准确、自然", 5)
        ]
        
        for name, category, description, test_script, expected_result, priority in base_capabilities:
            self.connection.execute(
                "INSERT OR IGNORE INTO capabilities (name, category, description, test_script, expected_result, priority) VALUES (?, ?, ?, ?, ?, ?)",
                (name, category, description, test_script, expected_result, priority)
            )
        
        self.connection.commit()
    
    def _set_database_version(self, version: int):
        """设置数据库版本"""
        self.connection.execute(
            "INSERT OR REPLACE INTO db_version (version) VALUES (?)",
            (version,)
        )
        self.connection.commit()
    
    def get_database_version(self) -> int:
        """获取数据库版本"""
        try:
            cursor = self.connection.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error:
            return 0
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径，如果为None则使用默认路径
            
        Returns:
            备份是否成功
        """
        try:
            if backup_path is None:
                timestamp = self._get_timestamp()
                backup_path = self.db_path.parent / f"backup_{timestamp}.db"
            
            # 使用SQLite的备份API
            backup_conn = sqlite3.connect(str(backup_path))
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            self._logger.info(f"数据库备份成功: {backup_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"数据库备份失败: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """获取时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        执行查询语句
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            cursor = self.connection.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except sqlite3.Error as e:
            self._logger.error(f"查询执行失败: {e}")
            return []
    
    def execute_update(self, sql: str, params: tuple = ()) -> bool:
        """
        执行更新语句
        
        Args:
            sql: SQL更新语句
            params: 更新参数
            
        Returns:
            执行是否成功
        """
        try:
            self.connection.execute(sql, params)
            self.connection.commit()
            return True
            
        except sqlite3.Error as e:
            self._logger.error(f"更新执行失败: {e}")
            self.connection.rollback()
            return False
    
    def get_table_info(self) -> Dict[str, Any]:
        """获取数据库表信息"""
        try:
            tables = self.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            
            table_info = {}
            for table in tables:
                table_name = table['name']
                columns = self.execute_query(f"PRAGMA table_info({table_name})")
                table_info[table_name] = {
                    'column_count': len(columns),
                    'columns': [col['name'] for col in columns]
                }
            
            return table_info
            
        except Exception as e:
            self._logger.error(f"获取表信息失败: {e}")
            return {}


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def init_database_manager(db_path: Optional[str] = None) -> DatabaseManager:
    """
    初始化全局数据库管理器
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        DatabaseManager实例
    """
    global _db_manager
    _db_manager = DatabaseManager(db_path)
    return _db_manager


def get_database_manager() -> DatabaseManager:
    """
    获取全局数据库管理器
    
    Returns:
        DatabaseManager实例
        
    Raises:
        RuntimeError: 数据库管理器未初始化
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = init_database_manager()
    
    return _db_manager


def initialize_database() -> bool:
    """
    初始化数据库（便捷函数）
    
    Returns:
        初始化是否成功
    """
    manager = get_database_manager()
    return manager.initialize_database()


def get_database_info() -> Dict[str, Any]:
    """
    获取数据库信息（便捷函数）
    
    Returns:
        数据库信息字典
    """
    manager = get_database_manager()
    return {
        "db_path": str(manager.db_path),
        "version": manager.get_database_version(),
        "tables": manager.get_table_info()
    }


# 测试函数
def test_database_manager():
    """测试数据库管理器"""
    try:
        # 初始化数据库管理器
        manager = init_database_manager()
        
        # 初始化数据库
        if manager.initialize_database():
            print("✓ 数据库初始化成功")
        else:
            print("❌ 数据库初始化失败")
            return False
        
        # 获取数据库信息
        info = get_database_info()
        print("数据库信息:")
        print(f"  路径: {info['db_path']}")
        print(f"  版本: {info['version']}")
        print(f"  表数量: {len(info['tables'])}")
        
        # 测试查询功能
        tables = manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        print(f"  表列表: {[table['name'] for table in tables]}")
        
        # 测试系统设置查询
        settings = manager.execute_query("SELECT * FROM system_settings")
        print(f"  系统设置数量: {len(settings)}")
        
        # 测试能力查询
        capabilities = manager.execute_query("SELECT * FROM capabilities")
        print(f"  基础能力数量: {len(capabilities)}")
        
        print("🎉 数据库管理器测试全部通过")
        return True
        
    except Exception as e:
        print(f"❌ 数据库管理器测试失败: {e}")
        return False


if __name__ == "__main__":
    test_database_manager()
