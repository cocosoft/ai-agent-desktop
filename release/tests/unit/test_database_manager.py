"""
数据库管理器单元测试
测试 DatabaseManager 类的功能
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.data.database_manager import DatabaseManager


class TestDatabaseManager:
    """测试数据库管理器类"""
    
    def test_database_manager_initialization(self):
        """测试数据库管理器初始化"""
        # 使用临时文件进行测试
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            # 测试正常初始化
            db_manager = DatabaseManager(temp_db_path)
            assert db_manager.db_path == temp_db_path
            assert db_manager.connection is None
            
            # 测试数据库文件创建
            assert os.path.exists(temp_db_path)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_connection(self):
        """测试数据库连接管理"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            db_manager = DatabaseManager(temp_db_path)
            
            # 测试连接建立
            db_manager.connect()
            assert db_manager.connection is not None
            assert isinstance(db_manager.connection, sqlite3.Connection)
            
            # 测试重复连接
            original_connection = db_manager.connection
            db_manager.connect()  # 应该不会创建新连接
            assert db_manager.connection is original_connection
            
            # 测试断开连接
            db_manager.disconnect()
            assert db_manager.connection is None
            
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_context_manager(self):
        """测试数据库管理器的上下文管理器"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            # 测试上下文管理器
            with DatabaseManager(temp_db_path) as db_manager:
                assert db_manager.connection is not None
                # 在上下文中应该可以执行查询
                cursor = db_manager.connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result == (1,)
            
            # 离开上下文后连接应该关闭
            assert db_manager.connection is None
            
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_table_creation(self):
        """测试数据库表创建"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with DatabaseManager(temp_db_path) as db_manager:
                # 测试初始化表
                db_manager.initialize_tables()
                
                # 验证表是否存在
                cursor = db_manager.connection.cursor()
                
                # 检查核心表
                tables_to_check = [
                    'agents', 'agent_instances', 'capabilities', 
                    'models', 'tasks', 'logs'
                ]
                
                for table in tables_to_check:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    result = cursor.fetchone()
                    assert result is not None, f"Table {table} should exist"
                
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_backup_restore(self):
        """测试数据库备份和恢复"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        with tempfile.NamedTemporaryFile(suffix='.backup.db', delete=False) as backup_db:
            backup_db_path = backup_db.name
        
        try:
            # 创建初始数据库
            with DatabaseManager(temp_db_path) as db_manager:
                db_manager.initialize_tables()
                # 添加一些测试数据
                cursor = db_manager.connection.cursor()
                cursor.execute("INSERT INTO agents (name, description, status) VALUES (?, ?, ?)", 
                             ("Test Agent", "Test Description", "active"))
                db_manager.connection.commit()
            
            # 测试备份
            with DatabaseManager(temp_db_path) as db_manager:
                success = db_manager.backup_database(backup_db_path)
                assert success is True
                assert os.path.exists(backup_db_path)
            
            # 测试恢复
            with DatabaseManager(backup_db_path) as restored_db:
                cursor = restored_db.connection.cursor()
                cursor.execute("SELECT name, description, status FROM agents")
                result = cursor.fetchone()
                assert result == ("Test Agent", "Test Description", "active")
            
        finally:
            for path in [temp_db_path, backup_db_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_database_manager_error_handling(self):
        """测试数据库错误处理"""
        # 测试无效数据库路径
        with pytest.raises(sqlite3.OperationalError):
            db_manager = DatabaseManager("/invalid/path/database.db")
            db_manager.connect()
        
        # 测试无效SQL查询
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with DatabaseManager(temp_db_path) as db_manager:
                db_manager.initialize_tables()
                
                # 测试无效查询
                cursor = db_manager.connection.cursor()
                with pytest.raises(sqlite3.OperationalError):
                    cursor.execute("INVALID SQL STATEMENT")
                
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_transaction_handling(self):
        """测试数据库事务处理"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with DatabaseManager(temp_db_path) as db_manager:
                db_manager.initialize_tables()
                
                # 测试事务提交
                cursor = db_manager.connection.cursor()
                cursor.execute("INSERT INTO agents (name, description, status) VALUES (?, ?, ?)", 
                             ("Agent 1", "Description 1", "active"))
                db_manager.connection.commit()
                
                # 验证数据已提交
                cursor.execute("SELECT name FROM agents WHERE name = ?", ("Agent 1",))
                result = cursor.fetchone()
                assert result is not None
                
                # 测试事务回滚
                cursor.execute("INSERT INTO agents (name, description, status) VALUES (?, ?, ?)", 
                             ("Agent 2", "Description 2", "active"))
                db_manager.connection.rollback()
                
                # 验证数据未提交
                cursor.execute("SELECT name FROM agents WHERE name = ?", ("Agent 2",))
                result = cursor.fetchone()
                assert result is None
                
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_performance(self):
        """测试数据库性能"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with DatabaseManager(temp_db_path) as db_manager:
                db_manager.initialize_tables()
                
                # 测试批量插入性能
                cursor = db_manager.connection.cursor()
                
                # 插入100条记录
                test_data = [
                    (f"Agent {i}", f"Description {i}", "active") 
                    for i in range(100)
                ]
                
                cursor.executemany(
                    "INSERT INTO agents (name, description, status) VALUES (?, ?, ?)",
                    test_data
                )
                db_manager.connection.commit()
                
                # 验证插入的数据
                cursor.execute("SELECT COUNT(*) FROM agents")
                count = cursor.fetchone()[0]
                assert count == 100
                
                # 测试查询性能
                cursor.execute("SELECT * FROM agents WHERE name LIKE 'Agent%'")
                results = cursor.fetchall()
                assert len(results) == 100
                
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


class TestDatabaseManagerIntegration:
    """测试数据库管理器集成功能"""
    
    def test_database_manager_with_real_data(self):
        """测试数据库管理器与真实数据"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            with DatabaseManager(temp_db_path) as db_manager:
                # 初始化所有表
                db_manager.initialize_tables()
                
                # 模拟完整的应用数据流
                cursor = db_manager.connection.cursor()
                
                # 1. 创建代理
                cursor.execute("""
                    INSERT INTO agents (name, description, agent_type, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                """, ("Translation Agent", "Handles translation tasks", "translation", "active"))
                
                agent_id = cursor.lastrowid
                
                # 2. 创建能力
                cursor.execute("""
                    INSERT INTO capabilities (name, description, capability_type, parameters, output_type, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("text_translation", "Translate text between languages", "translation", 
                      '{"source_language": "str", "target_language": "str", "text": "str"}', 
                      "str", "active"))
                
                capability_id = cursor.lastrowid
                
                # 3. 创建代理能力映射
                cursor.execute("""
                    INSERT INTO agent_capabilities (agent_id, capability_id, priority, enabled)
                    VALUES (?, ?, ?, ?)
                """, (agent_id, capability_id, 1, 1))
                
                # 4. 创建任务
                cursor.execute("""
                    INSERT INTO tasks (name, description, task_type, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                """, ("Translate document", "Translate English to Chinese", "translation", "pending"))
                
                task_id = cursor.lastrowid
                
                # 5. 创建任务分配
                cursor.execute("""
                    INSERT INTO task_assignments (task_id, agent_id, assigned_at, status)
                    VALUES (?, ?, datetime('now'), ?)
                """, (task_id, agent_id, "assigned"))
                
                db_manager.connection.commit()
                
                # 验证数据完整性
                cursor.execute("""
                    SELECT a.name, c.name, t.name, ta.status
                    FROM agents a
                    JOIN agent_capabilities ac ON a.id = ac.agent_id
                    JOIN capabilities c ON ac.capability_id = c.id
                    JOIN task_assignments ta ON a.id = ta.agent_id
                    JOIN tasks t ON ta.task_id = t.id
                    WHERE a.id = ?
                """, (agent_id,))
                
                result = cursor.fetchone()
                assert result is not None
                assert result[0] == "Translation Agent"
                assert result[1] == "text_translation"
                assert result[2] == "Translate document"
                assert result[3] == "assigned"
                
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_concurrent_access(self):
        """测试数据库并发访问"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            # 创建第一个连接
            db1 = DatabaseManager(temp_db_path)
            db1.connect()
            db1.initialize_tables()
            
            # 创建第二个连接
            db2 = DatabaseManager(temp_db_path)
            db2.connect()
            
            # 在两个连接上执行操作
            cursor1 = db1.connection.cursor()
            cursor2 = db2.connection.cursor()
            
            # 连接1插入数据
            cursor1.execute("INSERT INTO agents (name, description, status) VALUES (?, ?, ?)", 
                          ("Agent from DB1", "Description", "active"))
            db1.connection.commit()
            
            # 连接2应该能看到数据
            cursor2.execute("SELECT name FROM agents WHERE name = ?", ("Agent from DB1",))
            result = cursor2.fetchone()
            assert result is not None
            assert result[0] == "Agent from DB1"
            
            # 清理
            db1.disconnect()
            db2.disconnect()
            
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
