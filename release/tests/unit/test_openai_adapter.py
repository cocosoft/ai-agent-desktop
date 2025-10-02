"""
OpenAI适配器单元测试
测试OpenAI适配器的基本功能
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import json

from src.adapters.openai_adapter import OpenAIAdapter
from src.adapters.base_adapter import (
    ModelConfig, ModelType, ModelStatus, ModelResponse
)


class TestOpenAIAdapter:
    """OpenAI适配器测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        return ModelConfig(
            name="gpt-3.5-turbo",
            model_type=ModelType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key="test-api-key",
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
    
    @pytest.fixture
    def adapter(self, mock_config):
        """创建适配器实例"""
        return OpenAIAdapter(mock_config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, adapter, mock_config):
        """测试初始化"""
        assert adapter.config == mock_config
        assert adapter.status == ModelStatus.DISCONNECTED
        assert adapter._client is None
        assert adapter._api_key == "test-api-key"
        assert adapter._total_tokens_used == 0
        assert adapter._total_cost == 0.0
    
    @pytest.mark.asyncio
    async def test_connect_success(self, adapter):
        """测试成功连接"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-3.5-turbo"},
                {"id": "gpt-4"},
                {"id": "text-davinci-003"}
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
            assert result is True
            assert adapter.status == ModelStatus.CONNECTED
            assert adapter._client is mock_client
    
    @pytest.mark.asyncio
    async def test_connect_no_api_key(self, adapter):
        """测试连接时没有API密钥"""
        # 移除API密钥
        adapter._api_key = None
        
        # 执行连接
        result = await adapter.connect()
        
        # 验证结果
        assert result is False
        assert adapter.status == ModelStatus.ERROR
    
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
            assert adapter.status == ModelStatus.ERROR
    
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
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "这是一个测试回复"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
        # 执行文本生成
        result = await adapter.generate_text("测试提示")
        
        # 验证结果
        assert isinstance(result, ModelResponse)
        assert result.content == "这是一个测试回复"
        assert result.model == "gpt-3.5-turbo"
        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 20
        assert result.usage["total_tokens"] == 30
        assert result.finish_reason == "stop"
        assert result.error is None
        
        # 验证使用量统计更新
        assert adapter._total_tokens_used == 30
        assert adapter._total_cost > 0
    
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
            'data: {"choices": [{"delta": {"content": "这是"}}]}',
            'data: {"choices": [{"delta": {"content": "一个"}}]}',
            'data: {"choices": [{"delta": {"content": "测试"}}]}',
            'data: {"choices": [{"delta": {"content": "回复"}}]}',
            'data: [DONE]'
        ]
        
        # 创建异步迭代器
        async def async_iter():
            for item in stream_data:
                yield item
        
        mock_stream_response.aiter_lines.return_value = async_iter()
        
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
        
        # 模拟健康检查响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "健康检查成功"
                    }
                }
            ],
            "usage": {
                "total_tokens": 10
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        
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
        mock_client.post.side_effect = Exception("Health check failed")
        
        # 执行健康检查
        result = await adapter.health_check()
        
        # 验证结果
        assert result is False
        assert adapter.status == ModelStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_list_models(self, adapter):
        """测试获取模型列表"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟模型列表响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-3.5-turbo"},
                {"id": "gpt-4"},
                {"id": "text-davinci-003"},
                {"id": "dall-e-2"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        
        # 执行获取模型列表
        models = await adapter.list_models()
        
        # 验证结果（应该只包含GPT模型）
        assert "gpt-3.5-turbo" in models
        assert "gpt-4" in models
        assert "text-davinci-003" not in models  # 非聊天模型
        assert "dall-e-2" not in models  # 非聊天模型
    
    @pytest.mark.asyncio
    async def test_list_models_failure(self, adapter):
        """测试获取模型列表失败"""
        # 设置模拟客户端
        mock_client = AsyncMock()
        adapter._client = mock_client
        adapter.status = ModelStatus.CONNECTED
        
        # 模拟获取模型列表失败
        mock_client.get.side_effect = Exception("List models failed")
        
        # 执行获取模型列表
        models = await adapter.list_models()
        
        # 验证结果
        assert models == []
    
    def test_get_usage_stats(self, adapter):
        """测试获取使用量统计"""
        # 设置一些使用量数据
        adapter._total_tokens_used = 1500
        adapter._total_cost = 0.045
        
        # 获取使用量统计
        stats = adapter.get_usage_stats()
        
        # 验证结果
        assert stats["total_tokens"] == 1500
        assert stats["total_cost"] == 0.045
        assert "estimated_cost" in stats
    
    def test_update_api_key(self, adapter):
        """测试更新API密钥"""
        # 初始状态
        original_api_key = adapter._api_key
        
        # 更新API密钥
        adapter.update_api_key("new-api-key")
        
        # 验证结果
        assert adapter._api_key == "new-api-key"
        assert adapter._api_key != original_api_key
    
    def test_build_chat_request(self, adapter):
        """测试构建聊天请求"""
        # 测试默认参数
        request_data = adapter._build_chat_request("测试提示")
        
        assert request_data["model"] == "gpt-3.5-turbo"
        assert request_data["messages"][0]["role"] == "user"
        assert request_data["messages"][0]["content"] == "测试提示"
        assert request_data["max_tokens"] == 100
        assert request_data["temperature"] == 0.7
        assert request_data["stream"] is False
        
        # 测试自定义参数
        custom_request = adapter._build_chat_request(
            "测试提示",
            system_prompt="你是一个助手",
            max_tokens=200,
            temperature=0.5
        )
        
        assert custom_request["messages"][0]["role"] == "system"
        assert custom_request["messages"][0]["content"] == "你是一个助手"
        assert custom_request["messages"][1]["role"] == "user"
        assert custom_request["max_tokens"] == 200
        assert custom_request["temperature"] == 0.5
    
    def test_parse_chat_response(self, adapter):
        """测试解析聊天响应"""
        # 模拟API响应
        api_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "这是一个测试回复"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        
        start_time = time.time()
        response = adapter._parse_chat_response(api_response, start_time)
        
        # 验证结果
        assert response.content == "这是一个测试回复"
        assert response.model == "gpt-3.5-turbo"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 30
        assert response.finish_reason == "stop"
        assert response.error is None
    
    def test_update_usage_stats(self, adapter):
        """测试更新使用量统计"""
        # 初始状态
        assert adapter._total_tokens_used == 0
        assert adapter._total_cost == 0.0
        
        # 更新使用量
        usage = {"total_tokens": 1000}
        adapter._update_usage_stats(usage)
        
        # 验证结果
        assert adapter._total_tokens_used == 1000
        assert adapter._total_cost > 0
        
        # 再次更新
        usage2 = {"total_tokens": 500}
        adapter._update_usage_stats(usage2)
        
        # 验证累计结果
        assert adapter._total_tokens_used == 1500
        assert adapter._total_cost > 0


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
