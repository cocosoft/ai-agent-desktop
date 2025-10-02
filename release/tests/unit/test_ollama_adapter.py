"""
Ollama适配器单元测试
测试Ollama适配器的基本功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json

from src.adapters.ollama_adapter import OllamaAdapter
from src.adapters.base_adapter import (
    ModelConfig, ModelType, ModelStatus, ModelResponse
)


class TestOllamaAdapter:
    """Ollama适配器测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        return ModelConfig(
            name="test-model",
            model_type=ModelType.OLLAMA,
            base_url="http://localhost:11434",
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
    
    @pytest.fixture
    def adapter(self, mock_config):
        """创建适配器实例"""
        return OllamaAdapter(mock_config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, adapter, mock_config):
        """测试初始化"""
        assert adapter.config == mock_config
        assert adapter.status == ModelStatus.DISCONNECTED
        assert adapter._client is None
        assert adapter._available_models == []
        assert adapter._model_info == {}
    
    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        """测试成功连接"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "test-model"},
                {"name": "other-model"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_show_response = Mock()
        mock_show_response.json.return_value = {
            "name": "test-model",
            "size": 1000000,
            "modified_at": "2024-01-01T00:00:00Z"
        }
        mock_show_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # 模拟API调用
            mock_client.get.return_value = mock_response
            mock_client.post.return_value = mock_show_response
            
            # 执行连接
            result = await adapter.connect()
            
            # 验证结果
            assert result is True
            assert adapter.status == ModelStatus.CONNECTED
            assert adapter._client is mock_client
            assert "test-model" in adapter._available_models
    
    @pytest.mark.asyncio
    async def test_connect_model_unavailable(self, adapter):
        """测试连接时模型不可用"""
        # 模拟HTTP响应（模型列表不包含配置的模型）
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "other-model"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.get.return_value = mock_response
            
            # 执行连接
            result = await adapter.connect()
            
            # 验证结果
            assert result is False
            assert adapter.status == ModelStatus.UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, adapter):
        """测试连接失败"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.get.side_effect = Exception("Connection failed")
            
            # 执行连接
            result = await adapter.connect()
            
            # 验证结果
            assert result is False
            # 连接失败时，由于无法获取模型列表，状态会变为UNAVAILABLE
            assert adapter.status == ModelStatus.UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_disconnect(self, adapter):
        """测试断开连接"""
        # 先设置一个模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 执行断开连接
        await adapter.disconnect()
        
        # 验证结果
        assert adapter._client is None
        assert adapter.status == ModelStatus.DISCONNECTED
        mock_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, adapter):
        """测试成功生成文本"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟生成响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "这是一个测试回复",
            "model": "test-model",
            "prompt_eval_count": 10,
            "eval_count": 20,
            "done_reason": "stop"
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        # 执行文本生成
        result = await adapter.generate_text("测试提示")
        
        # 验证结果
        assert isinstance(result, ModelResponse)
        assert result.content == "这是一个测试回复"
        assert result.model == "test-model"
        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 20
        assert result.usage["total_tokens"] == 30
        assert result.finish_reason == "stop"
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_generate_text_failure(self, adapter):
        """测试生成文本失败"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟生成失败
        mock_client.post.side_effect = Exception("Generation failed")
        
        # 执行文本生成
        result = await adapter.generate_text("测试提示")
        
        # 验证结果
        assert isinstance(result, ModelResponse)
        assert result.content == ""
        assert result.error is not None
        assert "Generation failed" in result.error
    
    @pytest.mark.asyncio
    async def test_generate_stream(self, adapter):
        """测试流式生成文本"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟流式响应
        mock_stream_response = AsyncMock()
        mock_stream_response.raise_for_status.return_value = None
        
        # 模拟流数据
        stream_data = [
            '{"response": "这是", "done": false}',
            '{"response": "一个", "done": false}',
            '{"response": "测试", "done": false}',
            '{"response": "回复", "done": true}'
        ]
        mock_stream_response.aiter_lines.return_value = stream_data
        
        # 正确模拟异步上下文管理器
        mock_client.stream.return_value.__aenter__.return_value = mock_stream_response
        mock_client.stream.return_value.__aexit__.return_value = None
        
        # 收集回调调用的结果
        callback_results = []
        
        def mock_callback(text):
            callback_results.append(text)
        
        # 执行流式生成
        await adapter.generate_stream("测试提示", mock_callback)
        
        # 验证结果
        assert callback_results == ["这是", "一个", "测试", "回复"]
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, adapter):
        """测试健康检查成功"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        adapter._available_models = ["test-model"]
        
        # 模拟健康检查响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "test-model"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        
        # 执行健康检查
        result = await adapter.health_check()
        
        # 验证结果
        assert result is True
        assert adapter.status == ModelStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, adapter):
        """测试健康检查失败"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟健康检查失败
        mock_client.get.side_effect = Exception("Health check failed")
        
        # 执行健康检查
        result = await adapter.health_check()
        
        # 验证结果
        assert result is False
        assert adapter.status == ModelStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, adapter):
        """测试获取可用模型"""
        # 设置模拟客户端和模型列表
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter._available_models = ["model1", "model2", "model3"]
        
        # 模拟刷新可用模型列表（不实际调用API）
        with patch.object(adapter, '_refresh_available_models') as mock_refresh:
            mock_refresh.return_value = None
            
            # 执行获取可用模型
            models = await adapter.get_available_models()
            
            # 验证结果
            assert models == ["model1", "model2", "model3"]
            mock_refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_pull_model_success(self, adapter):
        """测试成功拉取模型"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟拉取响应
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        # 执行模型拉取
        result = await adapter.pull_model("new-model")
        
        # 验证结果
        assert result["success"] is True
        assert result["model"] == "new-model"
    
    @pytest.mark.asyncio
    async def test_pull_model_failure(self, adapter):
        """测试拉取模型失败"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟拉取失败
        mock_client.post.side_effect = Exception("Pull failed")
        
        # 执行模型拉取
        result = await adapter.pull_model("new-model")
        
        # 验证结果
        assert result["success"] is False
        assert "Pull failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_delete_model_success(self, adapter):
        """测试成功删除模型"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟删除响应
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_client.delete.return_value = mock_response
        
        # 执行模型删除
        result = await adapter.delete_model("old-model")
        
        # 验证结果
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_model_failure(self, adapter):
        """测试删除模型失败"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟删除失败
        mock_client.delete.side_effect = Exception("Delete failed")
        
        # 执行模型删除
        result = await adapter.delete_model("old-model")
        
        # 验证结果
        assert result is False
    
    def test_build_generation_params(self, adapter):
        """测试构建生成参数"""
        # 测试默认参数
        params = adapter._build_generation_params()
        assert "options" in params
        assert params["options"]["temperature"] == 0.7
        assert params["options"]["num_predict"] == 100
        
        # 测试自定义参数
        custom_params = adapter._build_generation_params(
            temperature=0.5,
            max_tokens=200,
            system_prompt="你是一个助手"
        )
        assert custom_params["options"]["temperature"] == 0.5
        assert custom_params["options"]["num_predict"] == 200
        assert custom_params["system"] == "你是一个助手"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
