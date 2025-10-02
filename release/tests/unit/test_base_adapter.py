"""
基础适配器单元测试
测试 BaseAdapter 抽象基类的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from src.adapters.base_adapter import BaseAdapter
from src.core.model_config import ModelConfig


class TestBaseAdapter:
    """测试基础适配器类"""
    
    def test_base_adapter_abstract_methods(self):
        """测试基础适配器抽象方法"""
        # 测试不能直接实例化抽象类
        with pytest.raises(TypeError):
            BaseAdapter()
    
    def test_base_adapter_subclass_implementation(self):
        """测试子类必须实现抽象方法"""
        
        class IncompleteAdapter(BaseAdapter):
            """不完整的适配器实现"""
            
            async def generate_text(self, prompt: str, **kwargs) -> str:
                return "test response"
            
            async def generate_stream(self, prompt: str, **kwargs):
                yield "test stream response"
        
        # 测试缺少必要方法
        with pytest.raises(TypeError):
            IncompleteAdapter(Mock())
    
    def test_base_adapter_interface_contract(self):
        """测试适配器接口契约"""
        
        class CompleteAdapter(BaseAdapter):
            """完整的适配器实现"""
            
            def __init__(self, config: ModelConfig):
                super().__init__(config)
                self.test_calls = []
            
            async def connect(self) -> bool:
                self.test_calls.append(('connect',))
                return True
            
            async def disconnect(self):
                self.test_calls.append(('disconnect',))
            
            async def generate_text(self, prompt: str, **kwargs):
                self.test_calls.append(('generate_text', prompt, kwargs))
                from src.adapters.base_adapter import ModelResponse
                return ModelResponse(
                    content=f"Response to: {prompt}",
                    model=self.config.name,
                    usage={"total_tokens": 10},
                    finish_reason="stop",
                    response_time=0.1
                )
            
            async def generate_stream(self, prompt: str, callback, **kwargs):
                self.test_calls.append(('generate_stream', prompt, kwargs))
                callback("Stream response to: {prompt}")
            
            async def health_check(self) -> bool:
                self.test_calls.append(('health_check',))
                return True
        
        # 测试完整实现
        config = Mock(spec=ModelConfig)
        adapter = CompleteAdapter(config)
        
        assert adapter.config == config
        assert adapter.test_calls == []
    
    @pytest.mark.asyncio
    async def test_base_adapter_method_calls(self):
        """测试适配器方法调用"""
        
        class TestAdapter(BaseAdapter):
            """测试适配器实现"""
            
            def __init__(self, config: ModelConfig):
                super().__init__(config)
                self.calls = []
            
            async def generate_text(self, prompt: str, **kwargs) -> str:
                self.calls.append(('generate_text', prompt, kwargs))
                return f"Text: {prompt}"
            
            async def generate_stream(self, prompt: str, **kwargs):
                self.calls.append(('generate_stream', prompt, kwargs))
                yield f"Stream: {prompt}"
            
            async def get_available_models(self) -> Dict[str, Any]:
                self.calls.append(('get_available_models',))
                return {"test_model": {"name": "Test Model"}}
            
            async def test_connection(self) -> bool:
                self.calls.append(('test_connection',))
                return True
            
            async def get_model_info(self) -> Dict[str, Any]:
                self.calls.append(('get_model_info',))
                return {"name": "Test Model"}
        
        config = Mock(spec=ModelConfig)
        adapter = TestAdapter(config)
        
        # 测试 generate_text
        result = await adapter.generate_text("Hello", temperature=0.7)
        assert result == "Text: Hello"
        assert ('generate_text', "Hello", {'temperature': 0.7}) in adapter.calls
        
        # 测试 generate_stream
        stream_results = []
        async for chunk in adapter.generate_stream("Stream test", max_tokens=100):
            stream_results.append(chunk)
        
        assert stream_results == ["Stream: Stream test"]
        assert ('generate_stream', "Stream test", {'max_tokens': 100}) in adapter.calls
        
        # 测试 get_available_models
        models = await adapter.get_available_models()
        assert models == {"test_model": {"name": "Test Model"}}
        assert ('get_available_models',) in adapter.calls
        
        # 测试 test_connection
        connected = await adapter.test_connection()
        assert connected is True
        assert ('test_connection',) in adapter.calls
        
        # 测试 get_model_info
        model_info = await adapter.get_model_info()
        assert model_info == {"name": "Test Model"}
        assert ('get_model_info',) in adapter.calls
    
    def test_base_adapter_error_handling(self):
        """测试适配器错误处理"""
        
        class ErrorAdapter(BaseAdapter):
            """错误处理适配器"""
            
            def __init__(self, config: ModelConfig):
                super().__init__(config)
                self.should_fail = False
            
            async def generate_text(self, prompt: str, **kwargs) -> str:
                if self.should_fail:
                    raise ConnectionError("Connection failed")
                return "Success"
            
            async def generate_stream(self, prompt: str, **kwargs):
                if self.should_fail:
                    raise RuntimeError("Stream error")
                yield "Success"
            
            async def get_available_models(self) -> Dict[str, Any]:
                if self.should_fail:
                    raise ValueError("Model error")
                return {}
            
            async def test_connection(self) -> bool:
                if self.should_fail:
                    raise ConnectionError("Connection test failed")
                return True
            
            async def get_model_info(self) -> Dict[str, Any]:
                if self.should_fail:
                    raise RuntimeError("Info error")
                return {}
        
        config = Mock(spec=ModelConfig)
        adapter = ErrorAdapter(config)
        
        # 测试正常情况
        adapter.should_fail = False
        
        # 测试错误情况
        adapter.should_fail = True
        
        # 验证错误类型
        with pytest.raises(ConnectionError):
            asyncio.run(adapter.generate_text("test"))
        
        with pytest.raises(RuntimeError):
            async def test_stream():
                async for _ in adapter.generate_stream("test"):
                    pass
            asyncio.run(test_stream())
        
        with pytest.raises(ValueError):
            asyncio.run(adapter.get_available_models())
        
        with pytest.raises(ConnectionError):
            asyncio.run(adapter.test_connection())
        
        with pytest.raises(RuntimeError):
            asyncio.run(adapter.get_model_info())
    
    def test_base_adapter_config_management(self):
        """测试适配器配置管理"""
        
        class ConfigAdapter(BaseAdapter):
            """配置管理适配器"""
            
            def __init__(self, config: ModelConfig):
                super().__init__(config)
                self.config_updates = []
            
            async def generate_text(self, prompt: str, **kwargs) -> str:
                return "response"
            
            async def generate_stream(self, prompt: str, **kwargs):
                yield "stream"
            
            async def get_available_models(self) -> Dict[str, Any]:
                return {}
            
            async def test_connection(self) -> bool:
                return True
            
            async def get_model_info(self) -> Dict[str, Any]:
                return {}
        
        # 测试配置传递
        config = Mock(spec=ModelConfig)
        config.name = "test_model"
        config.provider = "test_provider"
        
        adapter = ConfigAdapter(config)
        
        assert adapter.config.name == "test_model"
        assert adapter.config.provider == "test_provider"
        
        # 测试配置不可变性
        with pytest.raises(AttributeError):
            adapter.config = Mock()


class TestBaseAdapterIntegration:
    """测试基础适配器集成功能"""
    
    @pytest.mark.asyncio
    async def test_adapter_lifecycle(self):
        """测试适配器生命周期"""
        
        class LifecycleAdapter(BaseAdapter):
            """生命周期测试适配器"""
            
            def __init__(self, config: ModelConfig):
                super().__init__(config)
                self.lifecycle_events = []
            
            async def generate_text(self, prompt: str, **kwargs) -> str:
                self.lifecycle_events.append('generate_text')
                return "response"
            
            async def generate_stream(self, prompt: str, **kwargs):
                self.lifecycle_events.append('generate_stream')
                yield "stream"
            
            async def get_available_models(self) -> Dict[str, Any]:
                self.lifecycle_events.append('get_available_models')
                return {}
            
            async def test_connection(self) -> bool:
                self.lifecycle_events.append('test_connection')
                return True
            
            async def get_model_info(self) -> Dict[str, Any]:
                self.lifecycle_events.append('get_model_info')
                return {}
        
        config = Mock(spec=ModelConfig)
        adapter = LifecycleAdapter(config)
        
        # 执行一系列操作
        await adapter.test_connection()
        await adapter.get_available_models()
        await adapter.get_model_info()
        await adapter.generate_text("test")
        
        async for _ in adapter.generate_stream("test"):
            pass
        
        # 验证生命周期事件顺序
        expected_events = [
            'test_connection',
            'get_available_models', 
            'get_model_info',
            'generate_text',
            'generate_stream'
        ]
        
        assert adapter.lifecycle_events == expected_events
    
    @pytest.mark.asyncio
    async def test_adapter_concurrent_operations(self):
        """测试适配器并发操作"""
        
        class ConcurrentAdapter(BaseAdapter):
            """并发测试适配器"""
            
            def __init__(self, config: ModelConfig):
                super().__init__(config)
                self.concurrent_calls = 0
                self.max_concurrent = 0
            
            async def generate_text(self, prompt: str, **kwargs) -> str:
                self.concurrent_calls += 1
                self.max_concurrent = max(self.max_concurrent, self.concurrent_calls)
                await asyncio.sleep(0.01)  # 模拟处理时间
                self.concurrent_calls -= 1
                return f"Response to {prompt}"
            
            async def generate_stream(self, prompt: str, **kwargs):
                self.concurrent_calls += 1
                self.max_concurrent = max(self.max_concurrent, self.concurrent_calls)
                await asyncio.sleep(0.01)
                self.concurrent_calls -= 1
                yield f"Stream for {prompt}"
            
            async def get_available_models(self) -> Dict[str, Any]:
                return {}
            
            async def test_connection(self) -> bool:
                return True
            
            async def get_model_info(self) -> Dict[str, Any]:
                return {}
        
        config = Mock(spec=ModelConfig)
        adapter = ConcurrentAdapter(config)
        
        # 并发调用 generate_text
        tasks = [
            adapter.generate_text(f"prompt_{i}") 
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result == f"Response to prompt_{i}"
        
        # 验证并发处理
        assert adapter.max_concurrent > 1  # 应该支持并发


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
