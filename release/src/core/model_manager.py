"""
模型管理器
统一管理多个模型适配器，提供负载均衡、故障转移等功能
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor

from .model_config import ModelConfig
from ..adapters.base_adapter import (
    BaseAdapter, ModelType, ModelStatus, ModelResponse, 
    AdapterFactory, log_info, log_error, log_warning, log_performance
)


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"      # 轮询
    LEAST_LOADED = "least_loaded"    # 最少负载
    RANDOM = "random"                # 随机
    PRIORITY = "priority"            # 优先级


@dataclass
class ModelInstance:
    """模型实例信息"""
    config: ModelConfig
    adapter: BaseAdapter
    status: ModelStatus
    last_used: float
    total_requests: int
    error_count: int
    avg_response_time: float
    is_healthy: bool


class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        """初始化模型管理器"""
        self._models: Dict[str, ModelInstance] = {}
        self._model_groups: Dict[str, List[str]] = {}  # 模型组映射
        self._load_balance_strategy = LoadBalanceStrategy.ROUND_ROBIN
        self._current_index: Dict[str, int] = {}  # 轮询索引
        self._health_check_interval = 60  # 健康检查间隔（秒）
        self._max_retries = 3  # 最大重试次数
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=10)
        
        # 性能统计
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        
    async def initialize(self):
        """初始化模型管理器"""
        log_info("初始化模型管理器")
        
        # 启动健康检查任务
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        log_info("模型管理器初始化完成")
    
    async def shutdown(self):
        """关闭模型管理器"""
        log_info("关闭模型管理器")
        
        # 停止健康检查任务
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # 断开所有模型连接
        for model_id, instance in self._models.items():
            try:
                await instance.adapter.disconnect()
                log_info(f"已断开模型连接: {model_id}")
            except Exception as e:
                log_error(f"断开模型连接失败: {model_id}", e)
        
        # 关闭线程池
        self._executor.shutdown(wait=True)
        
        log_info("模型管理器已关闭")
    
    def register_model(self, config: ModelConfig) -> bool:
        """
        注册模型
        
        Args:
            config: 模型配置
            
        Returns:
            注册是否成功
        """
        with self._lock:
            try:
                model_id = config.id
                
                # 检查模型是否已注册
                if model_id in self._models:
                    log_warning(f"模型已注册: {model_id}")
                    return False
                
                # 创建适配器
                adapter = AdapterFactory.create_adapter(config)
                if not adapter:
                    log_error(f"创建适配器失败: {config.model_type}")
                    return False
                
                # 创建模型实例
                instance = ModelInstance(
                    config=config,
                    adapter=adapter,
                    status=ModelStatus.DISCONNECTED,
                    last_used=0,
                    total_requests=0,
                    error_count=0,
                    avg_response_time=0,
                    is_healthy=False
                )
                
                self._models[model_id] = instance
                
                # 添加到模型组
                group_name = config.group or "default"
                if group_name not in self._model_groups:
                    self._model_groups[group_name] = []
                    self._current_index[group_name] = 0
                
                self._model_groups[group_name].append(model_id)
                
                log_info(f"模型注册成功: {model_id} ({config.name})")
                return True
                
            except Exception as e:
                log_error(f"注册模型失败: {config.name}", e)
                return False
    
    def unregister_model(self, model_id: str) -> bool:
        """
        注销模型
        
        Args:
            model_id: 模型ID
            
        Returns:
            注销是否成功
        """
        with self._lock:
            try:
                if model_id not in self._models:
                    log_warning(f"模型未注册: {model_id}")
                    return False
                
                instance = self._models[model_id]
                
                # 从模型组中移除
                group_name = instance.config.group or "default"
                if group_name in self._model_groups:
                    if model_id in self._model_groups[group_name]:
                        self._model_groups[group_name].remove(model_id)
                    
                    # 如果组为空，删除组
                    if not self._model_groups[group_name]:
                        del self._model_groups[group_name]
                        if group_name in self._current_index:
                            del self._current_index[group_name]
                
                # 断开连接
                asyncio.create_task(instance.adapter.disconnect())
                
                # 移除模型
                del self._models[model_id]
                
                log_info(f"模型注销成功: {model_id}")
                return True
                
            except Exception as e:
                log_error(f"注销模型失败: {model_id}", e)
                return False
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        连接所有模型
        
        Returns:
            每个模型的连接结果
        """
        results = {}
        
        with self._lock:
            for model_id, instance in self._models.items():
                try:
                    connected = await instance.adapter.connect()
                    results[model_id] = connected
                    
                    if connected:
                        instance.status = ModelStatus.CONNECTED
                        instance.is_healthy = True
                        log_info(f"模型连接成功: {model_id}")
                    else:
                        instance.status = ModelStatus.ERROR
                        instance.is_healthy = False
                        log_error(f"模型连接失败: {model_id}")
                        
                except Exception as e:
                    results[model_id] = False
                    instance.status = ModelStatus.ERROR
                    instance.is_healthy = False
                    log_error(f"模型连接异常: {model_id}", e)
        
        return results
    
    async def disconnect_all(self):
        """断开所有模型连接"""
        with self._lock:
            for model_id, instance in self._models.items():
                try:
                    await instance.adapter.disconnect()
                    instance.status = ModelStatus.DISCONNECTED
                    log_info(f"模型断开连接: {model_id}")
                except Exception as e:
                    log_error(f"断开模型连接失败: {model_id}", e)
    
    async def generate_text(
        self, 
        prompt: str, 
        model_group: str = "default",
        **kwargs
    ) -> ModelResponse:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            model_group: 模型组名称
            **kwargs: 额外参数
            
        Returns:
            模型响应
        """
        start_time = time.time()
        self._total_requests += 1
        
        try:
            # 选择模型
            model_id = await self._select_model(model_group)
            if not model_id:
                error_msg = f"没有可用的模型: {model_group}"
                log_error(error_msg)
                self._failed_requests += 1
                return ModelResponse(
                    content="",
                    model="",
                    usage={},
                    finish_reason="error",
                    response_time=time.time() - start_time,
                    error=error_msg
                )
            
            # 获取模型实例
            instance = self._models[model_id]
            
            # 更新使用统计
            instance.last_used = time.time()
            instance.total_requests += 1
            
            # 生成文本
            response = await instance.adapter.generate_text(prompt, **kwargs)
            
            # 更新性能统计
            response_time = time.time() - start_time
            instance.avg_response_time = self._update_avg_response_time(
                instance.avg_response_time, instance.total_requests, response_time
            )
            
            if response.error:
                instance.error_count += 1
                self._failed_requests += 1
                log_error(f"文本生成失败: {model_id} - {response.error}")
            else:
                self._successful_requests += 1
                log_performance(f"文本生成成功: {model_id} ({response_time:.2f}s)")
            
            return response
            
        except Exception as e:
            self._failed_requests += 1
            error_msg = f"文本生成异常: {str(e)}"
            log_error("文本生成异常", e)
            
            return ModelResponse(
                content="",
                model="",
                usage={},
                finish_reason="error",
                response_time=time.time() - start_time,
                error=error_msg
            )
    
    async def generate_stream(
        self,
        prompt: str,
        callback: Callable[[str], None],
        model_group: str = "default",
        **kwargs
    ):
        """
        流式生成文本
        
        Args:
            prompt: 输入提示
            callback: 回调函数
            model_group: 模型组名称
            **kwargs: 额外参数
        """
        try:
            # 选择模型
            model_id = await self._select_model(model_group)
            if not model_id:
                raise RuntimeError(f"没有可用的模型: {model_group}")
            
            # 获取模型实例
            instance = self._models[model_id]
            
            # 更新使用统计
            instance.last_used = time.time()
            instance.total_requests += 1
            
            # 流式生成
            await instance.adapter.generate_stream(prompt, callback, **kwargs)
            
        except Exception as e:
            error_msg = f"流式生成异常: {str(e)}"
            log_error("流式生成异常", e)
            raise
    
    def set_load_balance_strategy(self, strategy: LoadBalanceStrategy):
        """
        设置负载均衡策略
        
        Args:
            strategy: 负载均衡策略
        """
        with self._lock:
            self._load_balance_strategy = strategy
            log_info(f"设置负载均衡策略: {strategy.value}")
    
    def get_model_status(self, model_id: str) -> Optional[ModelInstance]:
        """
        获取模型状态
        
        Args:
            model_id: 模型ID
            
        Returns:
            模型实例信息
        """
        with self._lock:
            return self._models.get(model_id)
    
    def get_all_models(self) -> List[ModelInstance]:
        """
        获取所有模型
        
        Returns:
            所有模型实例列表
        """
        with self._lock:
            return list(self._models.values())
    
    def get_model_groups(self) -> Dict[str, List[str]]:
        """
        获取模型组
        
        Returns:
            模型组映射
        """
        with self._lock:
            return self._model_groups.copy()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计
        
        Returns:
            性能统计字典
        """
        with self._lock:
            total_models = len(self._models)
            healthy_models = sum(1 for instance in self._models.values() if instance.is_healthy)
            
            return {
                "total_models": total_models,
                "healthy_models": healthy_models,
                "total_requests": self._total_requests,
                "successful_requests": self._successful_requests,
                "failed_requests": self._failed_requests,
                "success_rate": (
                    self._successful_requests / self._total_requests * 100 
                    if self._total_requests > 0 else 0
                )
            }
    
    async def _select_model(self, model_group: str) -> Optional[str]:
        """
        选择模型
        
        Args:
            model_group: 模型组名称
            
        Returns:
            选择的模型ID
        """
        with self._lock:
            if model_group not in self._model_groups:
                return None
            
            available_models = [
                model_id for model_id in self._model_groups[model_group]
                if self._models[model_id].is_healthy
            ]
            
            if not available_models:
                return None
            
            if self._load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
                return self._select_round_robin(model_group, available_models)
            elif self._load_balance_strategy == LoadBalanceStrategy.LEAST_LOADED:
                return self._select_least_loaded(available_models)
            elif self._load_balance_strategy == LoadBalanceStrategy.RANDOM:
                return self._select_random(available_models)
            elif self._load_balance_strategy == LoadBalanceStrategy.PRIORITY:
                return self._select_priority(available_models)
            else:
                return available_models[0]
    
    def _select_round_robin(self, model_group: str, available_models: List[str]) -> str:
        """轮询选择模型"""
        if model_group not in self._current_index:
            self._current_index[model_group] = 0
        
        index = self._current_index[model_group]
        selected_model = available_models[index]
        
        # 更新索引
        self._current_index[model_group] = (index + 1) % len(available_models)
        
        return selected_model
    
    def _select_least_loaded(self, available_models: List[str]) -> str:
        """选择最少负载的模型"""
        return min(
            available_models,
            key=lambda model_id: self._models[model_id].total_requests
        )
    
    def _select_random(self, available_models: List[str]) -> str:
        """随机选择模型"""
        import random
        return random.choice(available_models)
    
    def _select_priority(self, available_models: List[str]) -> str:
        """按优先级选择模型"""
        # 按配置的优先级排序
        sorted_models = sorted(
            available_models,
            key=lambda model_id: self._models[model_id].config.priority,
            reverse=True
        )
        return sorted_models[0]
    
    def _update_avg_response_time(
        self, 
        current_avg: float, 
        total_requests: int, 
        new_time: float
    ) -> float:
        """更新平均响应时间"""
        if total_requests <= 1:
            return new_time
        else:
            return (current_avg * (total_requests - 1) + new_time) / total_requests
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error("健康检查循环异常", e)
    
    async def _perform_health_check(self):
        """执行健康检查"""
        with self._lock:
            for model_id, instance in self._models.items():
                try:
                    # 如果模型已连接，执行健康检查
                    if instance.status == ModelStatus.CONNECTED:
                        is_healthy = await instance.adapter.health_check()
                        instance.is_healthy = is_healthy
                        
                        if not is_healthy:
                            log_warning(f"模型健康检查失败: {model_id}")
                            instance.status = ModelStatus.ERROR
                    else:
                        # 如果模型未连接，尝试重新连接
                        connected = await instance.adapter.connect()
                        instance.is_healthy = connected
                        instance.status = (
                            ModelStatus.CONNECTED if connected 
                            else ModelStatus.ERROR
                        )
                        
                except Exception as e:
                    log_error(f"模型健康检查异常: {model_id}", e)
                    instance.is_healthy = False
                    instance.status = ModelStatus.ERROR


# 全局模型管理器实例
_model_manager: Optional[ModelManager] = None


async def get_model_manager() -> ModelManager:
    """获取全局模型管理器实例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
        await _model_manager.initialize()
    return _model_manager


async def shutdown_model_manager():
    """关闭全局模型管理器"""
    global _model_manager
    if _model_manager:
        await _model_manager.shutdown()
        _model_manager = None


# 测试函数
async def test_model_manager():
    """测试模型管理器功能"""
    try:
        # 创建模型管理器
        manager = ModelManager()
        
        # 创建测试配置
        from ..adapters.base_adapter import create_model_config
        
        # 创建Ollama配置
        ollama_config = create_model_config(
            name="llama2",
            model_type=ModelType.OLLAMA,
            base_url="http://localhost:11434",
            timeout=30,
            max_tokens=100,
            temperature=0.7,
            group="text_models"
        )
        
        # 创建OpenAI配置
        openai_config = create_model_config(
            name="gpt-3.5-turbo",
            model_type=ModelType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=30,
            max_tokens=100,
            temperature=0.7,
            group="text_models"
        )
        
        # 注册模型
        ollama_registered = manager.register_model(ollama_config)
        openai_registered = manager.register_model(openai_config)
        
        print(f"Ollama模型注册: {'成功' if ollama_registered else '失败'}")
        print(f"OpenAI模型注册: {'成功' if openai_registered else '失败'}")
        
        # 测试连接所有模型
        connection_results = await manager.connect_all()
        print(f"连接结果: {connection_results}")
        
        # 测试获取模型状态
        models = manager.get_all_models()
        print(f"注册的模型数量: {len(models)}")
        
        # 测试获取模型组
        groups = manager.get_model_groups()
        print(f"模型组: {groups}")
        
        # 测试性能统计
        stats = manager.get_performance_stats()
        print(f"性能统计: {stats}")
        
        # 测试设置负载均衡策略
        manager.set_load_balance_strategy(LoadBalanceStrategy.ROUND_ROBIN)
        print("负载均衡策略设置成功")
        
        # 测试文本生成（由于没有真实模型，应该会失败）
        try:
            response = await manager.generate_text("测试提示")
            print(f"文本生成结果: {response.error or '成功'}")
        except Exception as e:
            print(f"文本生成测试失败（预期）: {e}")
        
        # 测试关闭管理器
        await manager.shutdown()
        print("模型管理器关闭成功")
        
        print("✓ 模型管理器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 模型管理器测试失败: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_model_manager())
