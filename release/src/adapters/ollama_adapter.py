"""
Ollama模型适配器
实现与Ollama本地模型的通信和文本生成功能
"""

import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
import httpx
from pathlib import Path

from .base_adapter import (
    BaseAdapter, ModelConfig, ModelResponse, ModelStatus, 
    ModelType, log_info, log_error, log_performance, safe_execute
)


class OllamaAdapter(BaseAdapter):
    """Ollama模型适配器"""
    
    def __init__(self, config: ModelConfig):
        """
        初始化Ollama适配器
        
        Args:
            config: 模型配置
        """
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None
        self._available_models: List[str] = []
        self._model_info: Dict[str, Any] = {}
        
        # Ollama特定配置
        self._ollama_timeout = config.timeout
        self._base_url = config.base_url.rstrip('/')
        
    async def connect(self) -> bool:
        """
        连接到Ollama服务
        
        Returns:
            连接是否成功
        """
        start_time = time.time()
        
        try:
            self.update_status(ModelStatus.CONNECTING, "正在连接Ollama服务")
            
            # 创建HTTP客户端
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._ollama_timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'AI-Agent-Desktop/1.0'
                }
            )
            
            # 测试连接并获取可用模型
            await self._refresh_available_models()
            
            # 检查配置的模型是否可用
            if self.config.name not in self._available_models:
                log_error(f"模型 {self.config.name} 在Ollama中不可用")
                self.update_status(ModelStatus.UNAVAILABLE, f"模型 {self.config.name} 不可用")
                return False
            
            # 获取模型详细信息
            await self._get_model_info(self.config.name)
            
            connection_time = time.time() - start_time
            log_info(f"Ollama连接成功: {self.config.name} ({connection_time:.2f}s)")
            self.update_status(ModelStatus.CONNECTED, "连接成功")
            
            return True
            
        except Exception as e:
            connection_time = time.time() - start_time
            error_msg = f"Ollama连接失败: {str(e)}"
            log_error(f"Ollama连接失败: {self.config.name}", e)
            self.update_status(ModelStatus.ERROR, error_msg)
            return False
    
    async def disconnect(self):
        """断开与Ollama服务的连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self.update_status(ModelStatus.DISCONNECTED, "手动断开连接")
        log_info(f"Ollama连接已断开: {self.config.name}")
    
    async def generate_text(self, prompt: str, **kwargs) -> ModelResponse:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            模型响应
        """
        start_time = time.time()
        
        try:
            if not self._client:
                raise RuntimeError("Ollama客户端未连接")
            
            # 构建请求参数
            request_data = {
                "model": self.config.name,
                "prompt": prompt,
                "stream": False
            }
            
            # 合并配置参数
            request_data.update(self._build_generation_params(**kwargs))
            
            # 发送请求
            response = await self._client.post("/api/generate", json=request_data)
            response.raise_for_status()
            
            result = response.json()
            
            # 构建响应对象
            model_response = ModelResponse(
                content=result.get("response", ""),
                model=result.get("model", self.config.name),
                usage={
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                },
                finish_reason=result.get("done_reason", "stop"),
                response_time=time.time() - start_time
            )
            
            return model_response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"文本生成失败: {str(e)}"
            log_error(f"Ollama文本生成失败: {self.config.name}", e)
            
            return ModelResponse(
                content="",
                model=self.config.name,
                usage={},
                finish_reason="error",
                response_time=response_time,
                error=error_msg
            )
    
    async def generate_stream(self, prompt: str, callback: Callable[[str], None], **kwargs):
        """
        流式生成文本
        
        Args:
            prompt: 输入提示
            callback: 回调函数，接收生成的文本片段
            **kwargs: 额外参数
        """
        try:
            if not self._client:
                raise RuntimeError("Ollama客户端未连接")
            
            # 构建请求参数
            request_data = {
                "model": self.config.name,
                "prompt": prompt,
                "stream": True
            }
            
            # 合并配置参数
            request_data.update(self._build_generation_params(**kwargs))
            
            # 发送流式请求
            async with self._client.stream("POST", "/api/generate", json=request_data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                callback(data["response"])
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            error_msg = f"流式生成失败: {str(e)}"
            log_error(f"Ollama流式生成失败: {self.config.name}", e)
            raise
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            Ollama服务是否健康
        """
        try:
            if not self._client:
                return False
            
            # 检查连接状态
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            
            # 更新可用模型列表
            await self._refresh_available_models()
            
            # 检查配置的模型是否仍然可用
            if self.config.name not in self._available_models:
                self.update_status(ModelStatus.UNAVAILABLE, "模型不再可用")
                return False
            
            self.update_status(ModelStatus.CONNECTED, "健康检查通过")
            return True
            
        except Exception as e:
            self.update_status(ModelStatus.ERROR, f"健康检查失败: {str(e)}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """
        获取可用的Ollama模型列表
        
        Returns:
            可用模型名称列表
        """
        await self._refresh_available_models()
        return self._available_models.copy()
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型详细信息
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型信息字典
        """
        if model_name not in self._model_info:
            await self._get_model_info(model_name)
        
        return self._model_info.get(model_name, {})
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        拉取模型到本地
        
        Args:
            model_name: 模型名称
            
        Returns:
            拉取结果
        """
        try:
            if not self._client:
                raise RuntimeError("Ollama客户端未连接")
            
            request_data = {
                "name": model_name,
                "stream": False
            }
            
            response = await self._client.post("/api/pull", json=request_data)
            response.raise_for_status()
            
            result = response.json()
            log_info(f"模型拉取完成: {model_name}")
            
            # 刷新可用模型列表
            await self._refresh_available_models()
            
            return {
                "success": True,
                "status": "completed",
                "model": model_name
            }
            
        except Exception as e:
            error_msg = f"模型拉取失败: {str(e)}"
            log_error(f"Ollama模型拉取失败: {model_name}", e)
            
            return {
                "success": False,
                "error": error_msg,
                "model": model_name
            }
    
    async def delete_model(self, model_name: str) -> bool:
        """
        删除本地模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            删除是否成功
        """
        try:
            if not self._client:
                raise RuntimeError("Ollama客户端未连接")
            
            request_data = {
                "name": model_name
            }
            
            response = await self._client.delete("/api/delete", json=request_data)
            response.raise_for_status()
            
            log_info(f"模型删除成功: {model_name}")
            
            # 刷新可用模型列表
            await self._refresh_available_models()
            
            return True
            
        except Exception as e:
            error_msg = f"模型删除失败: {str(e)}"
            log_error(f"Ollama模型删除失败: {model_name}", e)
            return False
    
    def _build_generation_params(self, **kwargs) -> Dict[str, Any]:
        """
        构建生成参数
        
        Args:
            **kwargs: 额外参数
            
        Returns:
            生成参数字典
        """
        params = {
            "options": {
                "temperature": kwargs.get('temperature', self.config.temperature),
                "top_p": kwargs.get('top_p', self.config.top_p),
                "top_k": kwargs.get('top_k', 40),
                "num_predict": kwargs.get('max_tokens', self.config.max_tokens),
                "repeat_penalty": kwargs.get('frequency_penalty', self.config.frequency_penalty) + 1.0,
                "presence_penalty": kwargs.get('presence_penalty', self.config.presence_penalty),
            }
        }
        
        # 添加系统提示
        system_prompt = kwargs.get('system_prompt', self.config.system_prompt)
        if system_prompt:
            params["system"] = system_prompt
        
        # 添加自定义参数
        custom_params = kwargs.get('custom_parameters', self.config.custom_parameters)
        if custom_params:
            params["options"].update(custom_params)
        
        return params
    
    async def _refresh_available_models(self):
        """刷新可用模型列表"""
        try:
            if not self._client:
                return
            
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            
            data = response.json()
            self._available_models = [model["name"] for model in data.get("models", [])]
            
            log_info(f"刷新可用模型列表: {len(self._available_models)} 个模型")
            
        except Exception as e:
            log_error("刷新可用模型列表失败", e)
            self._available_models = []
    
    async def _get_model_info(self, model_name: str):
        """获取模型详细信息"""
        try:
            if not self._client:
                return
            
            request_data = {
                "name": model_name
            }
            
            response = await self._client.post("/api/show", json=request_data)
            response.raise_for_status()
            
            info = response.json()
            self._model_info[model_name] = info
            
        except Exception as e:
            log_error(f"获取模型信息失败: {model_name}", e)
            self._model_info[model_name] = {}


# 注册适配器到工厂
from .base_adapter import AdapterFactory
AdapterFactory.register_adapter(ModelType.OLLAMA, OllamaAdapter)


# 测试函数
async def test_ollama_adapter():
    """测试Ollama适配器功能"""
    try:
        # 创建测试配置
        from .base_adapter import create_model_config
        
        config = create_model_config(
            name="llama2",  # 假设本地有llama2模型
            model_type=ModelType.OLLAMA,
            base_url="http://localhost:11434",
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
        
        # 创建适配器
        adapter = OllamaAdapter(config)
        
        # 测试连接
        connected = await adapter.connect()
        print(f"连接测试: {'成功' if connected else '失败'}")
        
        if connected:
            # 测试获取可用模型
            models = await adapter.get_available_models()
            print(f"可用模型: {models}")
            
            # 测试健康检查
            healthy = await adapter.health_check()
            print(f"健康检查: {'通过' if healthy else '失败'}")
            
            # 测试文本生成
            test_prompt = "请用中文简单介绍一下你自己"
            response = await adapter.safe_generate_text(test_prompt)
            print(f"文本生成测试: {response.content}")
            
            # 测试连接断开
            await adapter.disconnect()
        
        print("✓ Ollama适配器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ Ollama适配器测试失败: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ollama_adapter())
