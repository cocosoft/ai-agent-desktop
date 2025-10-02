"""
端到端工作流集成测试
测试完整的应用工作流程，包括多代理协作、任务分配、错误处理等场景
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from src.core.agent_model import AgentConfig, AgentInstance
from src.core.capability_model import Capability, CapabilityRegistry
from src.core.task_router import TaskRouter, Task, TaskPriority
from src.data.database_manager import DatabaseManager
from src.core.model_manager import ModelManager
from src.adapters.base_adapter import BaseAdapter, ModelConfig, ModelResponse


class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    @pytest.fixture
    async def temp_database(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            db_manager = DatabaseManager(temp_db_path)
            db_manager.connect()
            db_manager.initialize_tables()
            yield db_manager
            db_manager.disconnect()
        finally:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    @pytest.fixture
    async def capability_registry(self):
        """创建能力注册表"""
        registry = CapabilityRegistry()
        
        # 注册测试能力
        text_generation = Capability(
            id="text_generation",
            name="文本生成",
            description="生成文本内容",
            capability_type="generation",
            parameters={"prompt": "str", "max_tokens": "int"},
            output_type="str",
            test_cases=[
                {
                    "input": {"prompt": "你好", "max_tokens": 50},
                    "expected_output": "你好，我是AI助手"
                }
            ]
        )
        
        code_generation = Capability(
            id="code_generation",
            name="代码生成",
            description="生成代码片段",
            capability_type="generation",
            parameters={"language": "str", "description": "str"},
            output_type="str",
            test_cases=[
                {
                    "input": {"language": "python", "description": "打印Hello World"},
                    "expected_output": "print('Hello World')"
                }
            ]
        )
        
        registry.register_capability(text_generation)
        registry.register_capability(code_generation)
        
        return registry
    
    @pytest.fixture
    async def mock_model_adapter(self):
        """创建模拟模型适配器"""
        
        class MockAdapter(BaseAdapter):
            def __init__(self, config: ModelConfig):
                super().__init__(config)
                self.responses = {
                    "你好": "你好，我是AI助手",
                    "打印Hello World": "print('Hello World')",
                    "翻译测试": "Translation test"
                }
            
            async def connect(self) -> bool:
                return True
            
            async def disconnect(self):
                pass
            
            async def generate_text(self, prompt: str, **kwargs):
                response = self.responses.get(prompt, "默认响应")
                return ModelResponse(
                    content=response,
                    model=self.config.name,
                    usage={"total_tokens": len(response)},
                    finish_reason="stop",
                    response_time=0.1
                )
            
            async def generate_stream(self, prompt: str, callback, **kwargs):
                response = self.responses.get(prompt, "默认响应")
                callback(response)
            
            async def health_check(self) -> bool:
                return True
        
        return MockAdapter
    
    @pytest.fixture
    async def model_manager(self, mock_model_adapter):
        """创建模型管理器"""
        manager = ModelManager()
        
        # 注册模拟适配器
        config1 = ModelConfig(
            name="test-model-1",
            model_type="custom",
            base_url="http://localhost:8081"
        )
        
        config2 = ModelConfig(
            name="test-model-2", 
            model_type="custom",
            base_url="http://localhost:8082"
        )
        
        adapter1 = mock_model_adapter(config1)
        adapter2 = mock_model_adapter(config2)
        
        manager.register_model("test-model-1", adapter1)
        manager.register_model("test-model-2", adapter2)
        
        return manager
    
    @pytest.mark.asyncio
    async def test_complete_agent_workflow(self, temp_database, capability_registry, model_manager):
        """测试完整的代理工作流程"""
        
        # 1. 创建代理配置
        agent_config1 = AgentConfig(
            id="translation-agent",
            name="翻译代理",
            description="处理翻译任务",
            agent_type="translation",
            capabilities=["text_generation"],
            model_mappings={
                "text_generation": [
                    {"model_id": "test-model-1", "priority": 1, "enabled": True}
                ]
            },
            auto_start=True,
            max_concurrent_tasks=5
        )
        
        agent_config2 = AgentConfig(
            id="code-agent",
            name="代码代理", 
            description="处理代码生成任务",
            agent_type="code_generation",
            capabilities=["code_generation"],
            model_mappings={
                "code_generation": [
                    {"model_id": "test-model-2", "priority": 1, "enabled": True}
                ]
            },
            auto_start=True,
            max_concurrent_tasks=3
        )
        
        # 2. 创建代理实例
        agent1 = AgentInstance(
            id="instance-1",
            config=agent_config1,
            status="active",
            performance_metrics={}
        )
        
        agent2 = AgentInstance(
            id="instance-2",
            config=agent_config2,
            status="active", 
            performance_metrics={}
        )
        
        # 3. 创建任务路由器
        task_router = TaskRouter()
        
        # 4. 测试任务分配
        text_task = Task(
            task_id="text-task-1",
            capability_id="text_generation",
            input_data={"prompt": "你好", "max_tokens": 50},
            priority=TaskPriority.NORMAL
        )
        
        code_task = Task(
            task_id="code-task-1",
            capability_id="code_generation", 
            input_data={"language": "python", "description": "打印Hello World"},
            priority=TaskPriority.NORMAL
        )
        
        # 5. 分配任务给合适的代理
        text_agent = task_router.select_agent_for_task(text_task, [agent1, agent2])
        code_agent = task_router.select_agent_for_task(code_task, [agent1, agent2])
        
        # 6. 验证任务分配正确
        assert text_agent.id == "instance-1"  # 应该分配给翻译代理
        assert code_agent.id == "instance-2"  # 应该分配给代码代理
        
        # 7. 执行任务
        text_result = await model_manager.generate_text(
            "test-model-1", 
            "你好", 
            max_tokens=50
        )
        
        code_result = await model_manager.generate_text(
            "test-model-2",
            "打印Hello World",
            language="python"
        )
        
        # 8. 验证任务结果
        assert text_result.content == "你好，我是AI助手"
        assert code_result.content == "print('Hello World')"
        
        # 9. 验证性能指标更新
        stats1 = model_manager.get_model_stats("test-model-1")
        stats2 = model_manager.get_model_stats("test-model-2")
        
        assert stats1.total_requests >= 1
        assert stats2.total_requests >= 1
    
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration(self, temp_database, capability_registry, model_manager):
        """测试多代理协作场景"""
        
        # 1. 创建协作代理
        agent_configs = [
            AgentConfig(
                id=f"agent-{i}",
                name=f"协作代理{i}",
                description=f"第{i}个协作代理",
                agent_type="collaboration",
                capabilities=["text_generation"],
                model_mappings={
                    "text_generation": [
                        {"model_id": f"test-model-{i % 2 + 1}", "priority": 1, "enabled": True}
                    ]
                },
                auto_start=True,
                max_concurrent_tasks=2
            )
            for i in range(3)
        ]
        
        agents = [
            AgentInstance(
                id=f"instance-{i}",
                config=config,
                status="active",
                performance_metrics={}
            )
            for i, config in enumerate(agent_configs)
        ]
        
        # 2. 创建任务路由器
        task_router = TaskRouter()
        
        # 3. 创建多个任务
        tasks = [
            Task(
                task_id=f"task-{i}",
                capability_id="text_generation",
                input_data={"prompt": f"任务{i}输入", "max_tokens": 50},
                priority=TaskPriority.NORMAL
            )
            for i in range(5)
        ]
        
        # 4. 分配任务给代理
        assignments = []
        for task in tasks:
            agent = task_router.select_agent_for_task(task, agents)
            assignments.append((task.task_id, agent.id))
        
        # 5. 验证任务分配均衡
        assignment_counts = {}
        for _, agent_id in assignments:
            assignment_counts[agent_id] = assignment_counts.get(agent_id, 0) + 1
        
        # 任务应该相对均衡地分配给3个代理
        assert len(assignment_counts) == 3
        for count in assignment_counts.values():
            assert count >= 1  # 每个代理至少分配到一个任务
        
        # 6. 并发执行任务
        async def execute_task(task_id, prompt):
            # 模拟任务执行
            result = await model_manager.generate_text(
                "test-model-1",  # 使用第一个模型
                prompt,
                max_tokens=50
            )
            return task_id, result.content
        
        # 并发执行所有任务
        tasks_to_execute = [
            execute_task(task.task_id, task.input_data["prompt"])
            for task in tasks
        ]
        
        results = await asyncio.gather(*tasks_to_execute)
        
        # 7. 验证所有任务都成功完成
        assert len(results) == 5
        for task_id, result in results:
            assert result == "你好，我是AI助手"  # 模拟适配器的固定响应
        
        # 8. 验证性能统计
        stats = model_manager.get_model_stats("test-model-1")
        assert stats.total_requests >= 5
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_database, capability_registry, model_manager):
        """测试错误处理和恢复机制"""
        
        # 1. 创建代理配置
        agent_config = AgentConfig(
            id="test-agent",
            name="测试代理",
            description="测试错误处理",
            agent_type="test",
            capabilities=["text_generation"],
            model_mappings={
                "text_generation": [
                    {"model_id": "test-model-1", "priority": 1, "enabled": True},
                    {"model_id": "test-model-2", "priority": 2, "enabled": True}
                ]
            },
            auto_start=True,
            max_concurrent_tasks=2
        )
        
        agent = AgentInstance(
            id="test-instance",
            config=agent_config,
            status="active",
            performance_metrics={}
        )
        
        # 2. 模拟第一个模型失败
        with patch.object(model_manager.models["test-model-1"], 'generate_text',
                         side_effect=Exception("模拟模型故障")):
            
            # 3. 尝试使用第一个模型（应该失败）
            try:
                result = await model_manager.generate_text(
                    "test-model-1",
                    "测试输入",
                    max_tokens=50
                )
                # 如果到达这里，测试失败
                assert False, "应该抛出异常"
            except Exception as e:
                assert "模拟模型故障" in str(e)
        
        # 4. 使用第二个模型（应该成功）
        result = await model_manager.generate_text(
            "test-model-2",
            "测试输入", 
            max_tokens=50
        )
        
        # 5. 验证第二个模型工作正常
        assert result.content == "你好，我是AI助手"
        
        # 6. 验证故障转移机制
        # 在实际系统中，应该自动切换到备用模型
        
        # 7. 验证错误统计
        stats1 = model_manager.get_model_stats("test-model-1")
        stats2 = model_manager.get_model_stats("test-model-2")
        
        # 第一个模型应该有失败记录
        assert stats1.failed_requests >= 1
        # 第二个模型应该有成功记录
        assert stats2.successful_requests >= 1
    
    @pytest.mark.asyncio
    async def test_performance_stress_test(self, temp_database, capability_registry, model_manager):
        """测试性能压力测试"""
        
        # 1. 创建多个代理
        num_agents = 5
        agents = []
        
        for i in range(num_agents):
            config = AgentConfig(
                id=f"stress-agent-{i}",
                name=f"压力测试代理{i}",
                description=f"第{i}个压力测试代理",
                agent_type="stress_test",
                capabilities=["text_generation"],
                model_mappings={
                    "text_generation": [
                        {"model_id": f"test-model-{i % 2 + 1}", "priority": 1, "enabled": True}
                    ]
                },
                auto_start=True,
                max_concurrent_tasks=10
            )
            
            agent = AgentInstance(
                id=f"stress-instance-{i}",
                config=config,
                status="active",
                performance_metrics={}
            )
            agents.append(agent)
        
        # 2. 创建大量任务
        num_tasks = 20
        tasks = [
            Task(
                task_id=f"stress-task-{i}",
                capability_id="text_generation",
                input_data={"prompt": f"压力测试任务{i}", "max_tokens": 50},
                priority=TaskPriority.NORMAL
            )
            for i in range(num_tasks)
        ]
        
        # 3. 并发执行所有任务
        start_time = asyncio.get_event_loop().time()
        
        async def execute_single_task(task):
            # 模拟任务执行
            model_id = f"test-model-{(int(task.task_id.split('-')[-1]) % 2) + 1}"
            result = await model_manager.generate_text(
                model_id,
                task.input_data["prompt"],
                max_tokens=50
            )
            return result
        
        # 并发执行所有任务
        results = await asyncio.gather(*[execute_single_task(task) for task in tasks])
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # 4. 验证性能指标
        assert len(results) == num_tasks
        
        # 计算吞吐量
        throughput = num_tasks / total_time
        print(f"压力测试结果: {num_tasks} 个任务在 {total_time:.2f} 秒内完成，吞吐量: {throughput:.2f} 任务/秒")
        
        # 验证吞吐量在合理范围内（模拟环境）
        assert throughput > 1.0  # 至少每秒1个任务
        
        # 5. 验证所有任务都成功完成
        for result in results:
            assert result.content == "你好，我是AI助手"
        
        # 6. 验证模型使用统计
        stats1 = model_manager.get_model_stats("test-model-1")
        stats2 = model_manager.get_model_stats("test-model-2")
        
        total_requests = stats1.total_requests + stats2.total_requests
        assert total_requests >= num_tasks
    
    @pytest.mark.asyncio
    async def test_data_persistence_and_recovery(self, temp_database, capability_registry, model_manager):
        """测试数据持久化和恢复"""
        
        # 1. 创建代理配置并保存到数据库
        agent_config = AgentConfig(
            id="persistence-agent",
            name="持久化测试代理",
            description="测试数据持久化",
            agent_type="persistence_test",
            capabilities=["text_generation"],
            model_mappings={
                "text_generation": [
                    {"model_id": "test-model-1", "priority": 1, "enabled": True}
                ]
            },
            auto_start=True,
            max_concurrent_tasks=3
        )
        
        # 2. 模拟保存到数据库
        cursor = temp_database.connection.cursor()
        cursor.execute("""
            INSERT INTO agents (id, name, description, agent_type, config, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            agent_config.id,
            agent_config.name,
            agent_config.description,
            agent_config.agent_type,
            '{"capabilities": ["text_generation"]}',  # 简化的配置
            "active"
        ))
        temp_database.connection.commit()
        
        # 3. 从数据库读取代理配置
        cursor.execute("SELECT id, name, description, agent_type, config FROM agents WHERE id = ?", 
                      (agent_config.id,))
        result = cursor.fetchone()
        
        # 4. 验证数据持久化
        assert result is not None
        assert result[0] == agent_config.id
        assert result[1] == agent_config.name
        assert result[2] == agent_config.description
        assert result[3] == agent_config.agent_type
        
        # 5. 模拟数据库故障恢复
        # 创建新的数据库连接（模拟重启）
        new_db_manager = DatabaseManager(temp_database.db_path)
        new_db_manager.connect()
        
        # 6. 验证数据恢复
        cursor = new_db_manager.connection.cursor()
        cursor.execute("SELECT id, name, description FROM agents WHERE id = ?", 
                      (agent_config.id,))
        recovered_result = cursor.fetchone()
        
        # 7. 验证数据完整恢复
        assert recovered_result is not None
        assert recovered_result[0] == agent_config.id
        assert recovered_result[1] == agent_config.name
        assert recovered_result[2] == agent_config.description
        
        # 8. 清理
        new_db_manager.disconnect()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
