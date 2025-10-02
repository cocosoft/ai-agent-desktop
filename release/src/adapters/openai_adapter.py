"""
OpenAI模型适配器
实现与OpenAI API的通信和文本生成功能
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


class OpenAIAdapter(BaseAdapter):
    """OpenAI模型适配器"""
    
    def __init__(self, config: ModelConfig):
        """
        初始化OpenAI适配器
        
        Args:
            config: 模型配置
        """
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None
        self._api_key: Optional[str] = config.api_key
        self._base_url = config.base_url.rstrip('/')
        
        # OpenAI特定配置
        self._openai_timeout = config.timeout
        self._organization: Optional[str] = None
        self._project: Optional[str] = None
        
        # 使用量监控
        self._total_tokens_used = 0
        self._total_cost = 0.0
        
    async def connect(self) -> bool:
        """
        连接到OpenAI服务
        
        Returns:
            连接是否成功
        """
        start_time = time.time()
        
        try:
            self.update_status(ModelStatus.CONNECTING, "正在连接OpenAI服务")
            
            # 检查API密钥
            if not self._api_key:
                error_msg = "OpenAI API密钥未配置"
                log_error(f"OpenAI连接失败: {error_msg}")
                self.update_status(ModelStatus.ERROR, error_msg)
                return False
            
            # 创建HTTP客户端
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self._api_key}',
                'User-Agent': 'AI-Agent-Desktop/1.0'
            }
            
            # 添加组织和项目头（如果配置了）
            if self._organization:
                headers['OpenAI-Organization'] = self._organization
            if self._project:
                headers['OpenAI-Project'] = self._project
            
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._openai_timeout,
                headers=headers
            )
            
            # 测试连接
            await self._test_connection()
            
            connection_time = time.time() - start_time
            log_info(f"OpenAI连接成功: {self.config.name} ({connection_time:.2f}s)")
            self.update_status(ModelStatus.CONNECTED, "连接成功")
            
            return True
            
        except Exception as e:
            connection_time = time.time() - start_time
            error_msg = f"OpenAI连接失败: {str(e)}"
            log_error(f"OpenAI连接失败: {self.config.name}", e)
            self.update_status(ModelStatus.ERROR, error_msg)
            return False
    
    async def disconnect(self):
        """断开与OpenAI服务的连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
        
        self.update_status(ModelStatus.DISCONNECTED, "手动断开连接")
        log_info(f"OpenAI连接已断开: {self.config.name}")
    
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
                raise RuntimeError("OpenAI客户端未连接")
            
            # 构建请求参数
            request_data = self._build_chat_request(prompt, **kwargs)
            
            # 发送请求
            response = await self._client.post("/v1/chat/completions", json=request_data)
            response.raise_for_status()
            
            result = response.json()
            
            # 解析响应
            model_response = self._parse_chat_response(result, start_time)
            
            # 更新使用量统计
            self._update_usage_stats(model_response.usage)
            
            return model_response
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"文本生成失败: {str(e)}"
            log_error(f"OpenAI文本生成失败: {self.config.name}", e)
            
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
                raise RuntimeError("OpenAI客户端未连接")
            
            # 构建请求参数
            request_data = self._build_chat_request(prompt, **kwargs)
            request_data["stream"] = True
            
            # 发送流式请求
            async with self._client.stream("POST", "/v1/chat/completions", json=request_data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        data_line = line[6:]  # 移除 "data: " 前缀
                        
                        if data_line == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_line)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    callback(delta["content"])
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            error_msg = f"流式生成失败: {str(e)}"
            log_error(f"OpenAI流式生成失败: {self.config.name}", e)
            raise
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            OpenAI服务是否健康
        """
        try:
            if not self._client:
                return False
            
            # 发送简单的测试请求
            test_prompt = "请回复'健康检查成功'"
            response = await self.safe_generate_text(test_prompt, max_tokens=10)
            
            if response.error:
                self.update_status(ModelStatus.ERROR, f"健康检查失败: {response.error}")
                return False
            
            self.update_status(ModelStatus.CONNECTED, "健康检查通过")
            return True
            
        except Exception as e:
            self.update_status(ModelStatus.ERROR, f"健康检查失败: {str(e)}")
            return False
    
    async def list_models(self) -> List[str]:
        """
        获取可用的OpenAI模型列表
        
        Returns:
            可用模型名称列表
        """
        try:
            if not self._client:
                raise RuntimeError("OpenAI客户端未连接")
            
            response = await self._client.get("/v1/models")
            response.raise_for_status()
            
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            
            # 过滤出聊天模型
            chat_models = [model for model in models if "gpt" in model.lower()]
            
            log_info(f"获取到 {len(chat_models)} 个OpenAI聊天模型")
            return chat_models
            
        except Exception as e:
            log_error("获取OpenAI模型列表失败", e)
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取使用量统计
        
        Returns:
            使用量统计字典
        """
        return {
            "total_tokens": self._total_tokens_used,
            "total_cost": self._total_cost,
            "estimated_cost": self._estimate_cost()
        }
    
    def update_api_key(self, api_key: str):
        """
        更新API密钥
        
        Args:
            api_key: 新的API密钥
        """
        self._api_key = api_key
        log_info("OpenAI API密钥已更新")
        
        # 如果已连接，需要重新连接
        if self._client and self.status == ModelStatus.CONNECTED:
            asyncio.create_task(self._reconnect())
    
    def _build_chat_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        构建聊天请求
        
        Args:
            prompt: 输入提示
            **kwargs: 额外参数
            
        Returns:
            请求数据字典
        """
        messages = []
        
        # 添加系统提示
        system_prompt = kwargs.get('system_prompt', self.config.system_prompt)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加用户消息
        messages.append({"role": "user", "content": prompt})
        
        request_data = {
            "model": self.config.name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "top_p": kwargs.get('top_p', self.config.top_p),
            "frequency_penalty": kwargs.get('frequency_penalty', self.config.frequency_penalty),
            "presence_penalty": kwargs.get('presence_penalty', self.config.presence_penalty),
            "stream": False
        }
        
        # 添加自定义参数
        custom_params = kwargs.get('custom_parameters', self.config.custom_parameters)
        if custom_params:
            request_data.update(custom_params)
        
        return request_data
    
    def _parse_chat_response(self, result: Dict[str, Any], start_time: float) -> ModelResponse:
        """
        解析聊天响应
        
        Args:
            result: API响应结果
            start_time: 请求开始时间
            
        Returns:
            模型响应对象
        """
        choices = result.get("choices", [])
        if not choices:
            raise ValueError("API响应中没有choices字段")
        
        choice = choices[0]
        message = choice.get("message", {})
        
        usage = result.get("usage", {})
        finish_reason = choice.get("finish_reason", "stop")
        
        return ModelResponse(
            content=message.get("content", ""),
            model=result.get("model", self.config.name),
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            finish_reason=finish_reason,
            response_time=time.time() - start_time
        )
    
    def _update_usage_stats(self, usage: Dict[str, int]):
        """
        更新使用量统计
        
        Args:
            usage: 使用量信息
        """
        total_tokens = usage.get("total_tokens", 0)
        self._total_tokens_used += total_tokens
        
        # 简单的成本估算（基于GPT-4定价）
        cost_per_1k_tokens = 0.03  # 假设每1000个token 0.03美元
        self._total_cost += (total_tokens / 1000) * cost_per_1k_tokens
    
    def _estimate_cost(self) -> float:
        """
        估算当前使用量的成本
        
        Returns:
            估算的成本（美元）
        """
        return self._total_cost
    
    async def _test_connection(self):
        """测试连接"""
        try:
            # 尝试获取模型列表来测试连接
            models = await self.list_models()
            if not models:
                raise ValueError("无法获取模型列表")
            
            # 检查配置的模型是否在可用模型中
            if self.config.name not in models:
                log_warning(f"模型 {self.config.name} 可能不在可用模型列表中")
                
        except Exception as e:
            raise RuntimeError(f"连接测试失败: {str(e)}")
    
    async def _reconnect(self):
        """重新连接"""
        await self.disconnect()
        await asyncio.sleep(1)  # 等待1秒后重连
        await self.connect()


# 注册适配器到工厂
from .base_adapter import AdapterFactory
AdapterFactory.register_adapter(ModelType.OPENAI, OpenAIAdapter)


# 测试函数
async def test_openai_adapter():
    """测试OpenAI适配器功能"""
    try:
        # 创建测试配置
        from .base_adapter import create_model_config
        
        config = create_model_config(
            name="gpt-3.5-turbo",
            model_type=ModelType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key="test-key",  # 测试密钥
            timeout=30,
            max_tokens=100,
            temperature=0.7
        )
        
        # 创建适配器
        adapter = OpenAIAdapter(config)
        
        # 测试连接（应该失败，因为没有有效的API密钥）
        connected = await adapter.connect()
        print(f"连接测试: {'成功' if connected else '失败'}")
        
        if connected:
            # 测试获取可用模型
            models = await adapter.list_models()
            print(f"可用模型: {len(models)} 个")
            
            # 测试健康检查
            healthy = await adapter.health_check()
            print(f"健康检查: {'通过' if healthy else '失败'}")
            
            # 测试使用量统计
            usage_stats = adapter.get_usage_stats()
            print(f"使用量统计: {usage_stats}")
            
            # 测试连接断开
            await adapter.disconnect()
        
        print("✓ OpenAI适配器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI适配器测试失败: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_openai_adapter())
