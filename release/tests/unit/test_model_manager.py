"""
模型管理器单元测试
测试模型管理器的核心功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.core.model_manager import (
    ModelManager, ModelInstance, LoadBalanceStrategy
)
from src.adapters.base_adapter import (
    ModelType, ModelStatus, ModelResponse
)
from src.core.model_config import ModelConfig, ModelProvider


class TestModelManager:
    """模型管理器测试类"""
    
    @pytest.fixture
    def mock_configs(self):
        """创建模拟配置"""
        ollama_config = ModelConfig(
            name="llama2",
            model_type=ModelType.OLLAMA,
            base_url="http://localhost:11434",
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
        
        openai_config = ModelConfig(
            name="gpt-3.5-turbo",
            model_type=ModelType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
        
        return [ollama_config, openai_config]
    
    @pytest.fixture
    def manager(self):
        """创建模型管理器实例"""
        return ModelManager()
    
    @pytest.mark.asyncio
    async def test_initialization(self, manager):
        """测试初始化"""
        await manager.initialize()
        
        # 验证初始化状态
        assert manager._health_check_task is not None
        assert len(manager._models) == 0
        assert len(manager._model_groups) == 0
        
        # 测试关闭
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_register_model(self, manager, mock_configs):
        """测试注册模型"""
        config = mock_configs[0]
        
        # 模拟适配器创建
        mock_adapter = AsyncMock()
        mock_adapter.status = ModelStatus.DISCONNECTED
        
        with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
            mock_factory.return_value = mock_adapter
            
            # 注册模型
            result = manager.register_model(config)
            
            # 验证结果
            assert result is True
            assert config.id in manager._models
            assert "text_models" in manager._model_groups
            assert config.id in manager._model_groups["text_models"]
            
            # 验证模型实例
            instance = manager._models[config.id]
            assert instance.config == config
            assert instance.adapter == mock_adapter
            assert instance.status == ModelStatus.DISCONNECTED
            assert instance.total_requests == 0
            assert instance.error_count == 0
    
    @pytest.mark.asyncio
    async def test_register_duplicate_model(self, manager, mock_configs):
        """测试注册重复模型"""
        config = mock_configs[0]
        
        # 模拟适配器创建
        mock_adapter = AsyncMock()
        
        with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
            mock_factory.return_value = mock_adapter
            
            # 第一次注册
            result1 = manager.register_model(config)
            assert result1 is True
            
            # 第二次注册相同模型
            result2 = manager.register_model(config)
            assert result2 is False
    
    @pytest.mark.asyncio
    async def test_unregister_model(self, manager, mock_configs):
        """测试注销模型"""
        config = mock_configs[0]
        
        # 模拟适配器创建
        mock_adapter = AsyncMock()
        
        with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
            mock_factory.return_value = mock_adapter
            
            # 注册模型
            manager.register_model(config)
            
            # 注销模型
            result = manager.unregister_model(config.id)
            
            # 验证结果
            assert result is True
            assert config.id not in manager._models
            assert config.id not in manager._model_groups["text_models"]
    
    @pytest.mark.asyncio
    async def test_unregister_nonexistent_model(self, manager):
        """测试注销不存在的模型"""
        result = manager.unregister_model("nonexistent")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_connect_all(self, manager, mock_configs):
        """测试连接所有模型"""
        # 注册多个模型
        for config in mock_configs:
            mock_adapter = AsyncMock()
            mock_adapter.connect.return_value = True
            mock_adapter.status = ModelStatus.CONNECTED
            
            with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
                mock_factory.return_value = mock_adapter
                manager.register_model(config)
        
        # 连接所有模型
        results = await manager.connect_all()
        
        # 验证结果
        assert len(results) == len(mock_configs)
        for config in mock_configs:
            assert results[config.id] is True
            assert manager._models[config.id].status == ModelStatus.CONNECTED
            assert manager._models[config.id].is_healthy is True
    
    @pytest.mark.asyncio
    async def test_disconnect_all(self, manager, mock_configs):
        """测试断开所有模型连接"""
        # 注册并连接模型
        for config in mock_configs:
            mock_adapter = AsyncMock()
            mock_adapter.connect.return_value = True
            
            with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
                mock_factory.return_value = mock_adapter
                manager.register_model(config)
        
        await manager.connect_all()
        
        # 断开所有连接
        await manager.disconnect_all()
        
        # 验证结果
        for config in mock_configs:
            assert manager._models[config.id].status == ModelStatus.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self, manager, mock_configs):
        """测试成功生成文本"""
        config = mock_configs[0]
        
        # 模拟适配器和响应
        mock_adapter = AsyncMock()
        mock_adapter.connect.return_value = True
        mock_adapter.health_check.return_value = True
        mock_adapter.generate_text.return_value = ModelResponse(
            content="这是一个测试回复",
            model="llama2",
            usage={"total_tokens": 10},
            finish_reason="stop",
            response_time=1.0
        )
        
        with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
            mock_factory.return_value = mock_adapter
            manager.register_model(config)
        
        # 连接模型
        await manager.connect_all()
        
        # 生成文本
        response = await manager.generate_text("测试提示", "text_models")
        
        # 验证结果
        assert response.content == "这是一个测试回复"
        assert response.model == "llama2"
        assert response.error is None
        
        # 验证统计更新
        instance = manager._models[config.id]
        assert instance.total_requests == 1
        assert instance.avg_response_time > 0
    
    @pytest.mark.asyncio
    async def test_generate_text_no_available_models(self, manager):
        """测试没有可用模型时的文本生成"""
        response = await manager.generate_text("测试提示", "nonexistent_group")
        
        # 验证结果
        assert response.content == ""
        assert response.error is not None
        assert "没有可用的模型" in response.error
    
    @pytest.mark.asyncio
    async def test_set_load_balance_strategy(self, manager):
        """测试设置负载均衡策略"""
        # 测试轮询策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.ROUND_ROBIN)
        assert manager._load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN
        
        # 测试最少负载策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.LEAST_LOADED)
        assert manager._load_balance_strategy == LoadBalanceStrategy.LEAST_LOADED
        
        # 测试随机策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.RANDOM)
        assert manager._load_balance_strategy == LoadBalanceStrategy.RANDOM
        
        # 测试优先级策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.PRIORITY)
        assert manager._load_balance_strategy == LoadBalanceStrategy.PRIORITY
    
    @pytest.mark.asyncio
    async def test_get_model_status(self, manager, mock_configs):
        """测试获取模型状态"""
        config = mock_configs[0]
        
        mock_adapter = AsyncMock()
        with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
            mock_factory.return_value = mock_adapter
            manager.register_model(config)
        
        # 获取模型状态
        instance = manager.get_model_status(config.id)
        
        # 验证结果
        assert instance is not None
        assert instance.config == config
        assert instance.adapter == mock_adapter
    
    def test_get_all_models(self, manager, mock_configs):
        """测试获取所有模型"""
        # 注册多个模型
        for config in mock_configs:
            mock_adapter = AsyncMock()
            with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
                mock_factory.return_value = mock_adapter
                manager.register_model(config)
        
        # 获取所有模型
        models = manager.get_all_models()
        
        # 验证结果
        assert len(models) == len(mock_configs)
        model_ids = [model.config.id for model in models]
        for config in mock_configs:
            assert config.id in model_ids
    
    def test_get_model_groups(self, manager, mock_configs):
        """测试获取模型组"""
        # 注册多个模型到同一组
        for config in mock_configs:
            mock_adapter = AsyncMock()
            with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
                mock_factory.return_value = mock_adapter
                manager.register_model(config)
        
        # 获取模型组
        groups = manager.get_model_groups()
        
        # 验证结果
        assert "text_models" in groups
        assert len(groups["text_models"]) == len(mock_configs)
        for config in mock_configs:
            assert config.id in groups["text_models"]
    
    def test_get_performance_stats(self, manager, mock_configs):
        """测试获取性能统计"""
        # 初始状态
        stats = manager.get_performance_stats()
        assert stats["total_models"] == 0
        assert stats["healthy_models"] == 0
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0
        assert stats["failed_requests"] == 0
        assert stats["success_rate"] == 0
        
        # 注册模型后
        for config in mock_configs:
            mock_adapter = AsyncMock()
            with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
                mock_factory.return_value = mock_adapter
                manager.register_model(config)
        
        stats = manager.get_performance_stats()
        assert stats["total_models"] == len(mock_configs)
        assert stats["healthy_models"] == 0  # 模型未连接
    
    @pytest.mark.asyncio
    async def test_load_balance_strategies(self, manager, mock_configs):
        """测试负载均衡策略"""
        # 注册多个模型
        for config in mock_configs:
            mock_adapter = AsyncMock()
            mock_adapter.connect.return_value = True
            mock_adapter.health_check.return_value = True
            
            with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
                mock_factory.return_value = mock_adapter
                manager.register_model(config)
        
        # 连接所有模型
        await manager.connect_all()
        
        # 测试轮询策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.ROUND_ROBIN)
        model1 = await manager._select_model("text_models")
        model2 = await manager._select_model("text_models")
        
        # 轮询应该选择不同的模型
        assert model1 != model2
        
        # 测试最少负载策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.LEAST_LOADED)
        model = await manager._select_model("text_models")
        assert model in [config.id for config in mock_configs]
        
        # 测试随机策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.RANDOM)
        model = await manager._select_model("text_models")
        assert model in [config.id for config in mock_configs]
    
    @pytest.mark.asyncio
    async def test_health_check_loop(self, manager, mock_configs):
        """测试健康检查循环"""
        config = mock_configs[0]
        
        # 模拟适配器
        mock_adapter = AsyncMock()
        mock_adapter.connect.return_value = True
        mock_adapter.health_check.return_value = True
        
        with patch('src.core.model_manager.AdapterFactory.create_adapter') as mock_factory:
            mock_factory.return_value = mock_adapter
            manager.register_model(config)
        
        # 初始化管理器
        await manager.initialize()
        
        # 执行一次健康检查
        await manager._perform_health_check()
        
        # 验证模型状态
        instance = manager._models[config.id]
        assert instance.is_healthy is True
        assert instance.status == ModelStatus.CONNECTED
        
        # 关闭管理器
        await manager.shutdown()


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
