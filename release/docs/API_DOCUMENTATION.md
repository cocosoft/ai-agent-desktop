# AI Agent Desktop API 文档

## 概述

本文档描述了AI Agent Desktop应用的API接口和开发接口。这些API主要用于内部模块间的通信和外部扩展开发。

## 核心API接口

### 配置管理API

#### ConfigManager 类

**功能**: 管理应用配置的加载、保存和验证

**主要方法**:
```python
class ConfigManager:
    def load_config(self, config_path: str = None) -> ConfigModel:
        """加载配置文件"""
        
    def save_config(self, config: ConfigModel, config_path: str = None) -> bool:
        """保存配置到文件"""
        
    def validate_config(self, config: ConfigModel) -> ValidationResult:
        """验证配置有效性"""
        
    def get_config_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        
    def update_config_section(self, section: str, data: Dict[str, Any]) -> bool:
        """更新配置节"""
```

**使用示例**:
```python
from src.core.config_manager import ConfigManager

# 加载配置
config_manager = ConfigManager()
config = config_manager.load_config()

# 获取数据库配置
db_config = config_manager.get_config_section("database")
print(f"数据库路径: {db_config['path']}")

# 更新配置
config_manager.update_config_section("ui", {"theme": "dark"})
config_manager.save_config(config)
```

### 模型管理API

#### ModelManager 类

**功能**: 统一管理AI模型调用和负载均衡

**主要方法**:
```python
class ModelManager:
    async def initialize(self) -> bool:
        """初始化模型管理器"""
        
    async def get_available_models(self) -> List[ModelInfo]:
        """获取可用模型列表"""
        
    async def generate_text(
        self, 
        prompt: str, 
        model_name: str = None,
        parameters: Dict[str, Any] = None
    ) -> TextGenerationResult:
        """文本生成"""
        
    async def test_model_connection(self, model_name: str) -> ConnectionTestResult:
        """测试模型连接"""
        
    def get_model_performance(self, model_name: str) -> ModelPerformance:
        """获取模型性能统计"""
```

**使用示例**:
```python
from src.core.model_manager import ModelManager

# 初始化模型管理器
model_manager = ModelManager()
await model_manager.initialize()

# 获取可用模型
models = await model_manager.get_available_models()
for model in models:
    print(f"模型: {model.name}, 状态: {model.status}")

# 文本生成
result = await model_manager.generate_text(
    prompt="请解释什么是人工智能",
    model_name="gpt-4"
)
print(f"生成结果: {result.text}")
```

### 能力管理API

#### CapabilityRegistry 类

**功能**: 管理AI能力注册和发现

**主要方法**:
```python
class CapabilityRegistry:
    def register_capability(self, capability: Capability) -> bool:
        """注册能力"""
        
    def unregister_capability(self, capability_id: str) -> bool:
        """注销能力"""
        
    def get_capabilities(self, filters: Dict[str, Any] = None) -> List[Capability]:
        """获取能力列表"""
        
    def get_capability_by_id(self, capability_id: str) -> Optional[Capability]:
        """根据ID获取能力"""
        
    def discover_capabilities(self, model_name: str) -> DiscoveryResult:
        """发现模型能力"""
```

**使用示例**:
```python
from src.core.capability_registry import CapabilityRegistry

# 创建能力注册表
registry = CapabilityRegistry()

# 获取所有文本生成能力
text_capabilities = registry.get_capabilities({"type": "text_generation"})
for cap in text_capabilities:
    print(f"能力: {cap.name}, 描述: {cap.description}")

# 发现模型能力
result = registry.discover_capabilities("gpt-4")
print(f"发现的能力数量: {len(result.capabilities)}")
```

### 代理管理API

#### AgentManager 类

**功能**: 管理AI代理的创建、启动和监控

**主要方法**:
```python
class AgentManager:
    def create_agent(self, config: AgentConfig) -> AgentInstance:
        """创建代理"""
        
    def start_agent(self, agent_id: str) -> bool:
        """启动代理"""
        
    def stop_agent(self, agent_id: str) -> bool:
        """停止代理"""
        
    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """获取代理状态"""
        
    def get_agent_performance(self, agent_id: str) -> AgentPerformance:
        """获取代理性能统计"""
        
    def send_task_to_agent(
        self, 
        agent_id: str, 
        task: Task
    ) -> TaskResult:
        """向代理发送任务"""
```

**使用示例**:
```python
from src.core.agent_manager import AgentManager
from src.core.agent_config import AgentConfig

# 创建代理管理器
agent_manager = AgentManager()

# 创建代理配置
agent_config = AgentConfig(
    name="问答助手",
    description="用于回答用户问题的AI代理",
    capabilities=["text_generation", "qa"]
)

# 创建代理
agent = agent_manager.create_agent(agent_config)
print(f"代理创建成功，ID: {agent.id}")

# 启动代理
if agent_manager.start_agent(agent.id):
    print("代理启动成功")
    
# 获取代理状态
status = agent_manager.get_agent_status(agent.id)
print(f"代理状态: {status.state}")
```

### 任务系统API

#### TaskManager 类

**功能**: 管理任务的发送、执行和结果收集

**主要方法**:
```python
class TaskManager:
    def create_task(self, task_data: Dict[str, Any]) -> Task:
        """创建任务"""
        
    def submit_task(self, task: Task, agent_id: str = None) -> str:
        """提交任务"""
        
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        
    def get_task_result(self, task_id: str) -> TaskResult:
        """获取任务结果"""
        
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        
    def get_task_history(
        self, 
        filters: Dict[str, Any] = None
    ) -> List[TaskRecord]:
        """获取任务历史"""
```

**使用示例**:
```python
from src.core.task_manager import TaskManager

# 创建任务管理器
task_manager = TaskManager()

# 创建任务
task = task_manager.create_task({
    "type": "text_generation",
    "content": "请写一篇关于人工智能的短文",
    "parameters": {
        "max_tokens": 500,
        "temperature": 0.7
    }
})

# 提交任务
task_id = task_manager.submit_task(task)
print(f"任务提交成功，ID: {task_id}")

# 检查任务状态
status = task_manager.get_task_status(task_id)
print(f"任务状态: {status.state}")

# 获取任务结果
result = task_manager.get_task_result(task_id)
print(f"任务结果: {result.output}")
```

## 数据模型

### ConfigModel 类

**功能**: 应用配置数据模型

**属性**:
```python
class ConfigModel:
    app: AppConfig
    database: DatabaseConfig
    a2a_server: A2AServerConfig
    ui: UIConfig
    model_configs: Dict[str, ModelConfig]
    logging: LoggingConfig
```

### AgentConfig 类

**功能**: 代理配置数据模型

**属性**:
```python
class AgentConfig:
    id: str
    name: str
    description: str
    capabilities: List[str]
    model_mappings: Dict[str, str]  # capability -> model
    priority: int
    auto_start: bool
    created_at: datetime
    updated_at: datetime
```

### Task 类

**功能**: 任务数据模型

**属性**:
```python
class Task:
    id: str
    type: str  # text_generation, code_generation, etc.
    content: str
    parameters: Dict[str, Any]
    priority: int  # 1-4: 低、正常、高、紧急
    created_at: datetime
    status: TaskStatus
```

### Capability 类

**功能**: 能力数据模型

**属性**:
```python
class Capability:
    id: str
    name: str
    description: str
    type: str
    category: str
    parameters: Dict[str, Any]
    test_cases: List[TestCase]
    performance_metrics: PerformanceMetrics
```

## 错误处理

### 自定义异常类

```python
class AIAgentDesktopError(Exception):
    """基础异常类"""
    pass

class ConfigError(AIAgentDesktopError):
    """配置错误"""
    pass

class ModelConnectionError(AIAgentDesktopError):
    """模型连接错误"""
    pass

class AgentError(AIAgentDesktopError):
    """代理错误"""
    pass

class TaskError(AIAgentDesktopError):
    """任务错误"""
    pass
```

### 错误处理示例

```python
from src.utils.error_handler import ErrorHandler

try:
    # 执行可能出错的操作
    result = await model_manager.generate_text(prompt)
except ModelConnectionError as e:
    # 处理模型连接错误
    ErrorHandler.handle_error(e, "模型连接失败")
except TaskError as e:
    # 处理任务错误
    ErrorHandler.handle_error(e, "任务执行失败")
except Exception as e:
    # 处理其他错误
    ErrorHandler.handle_error(e, "未知错误")
```

## 扩展开发

### 自定义模型适配器

**基础接口**:
```python
from src.adapters.base_adapter import BaseAdapter

class CustomModelAdapter(BaseAdapter):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        
    async def initialize(self) -> bool:
        """初始化适配器"""
        pass
        
    async def generate_text(
        self, 
        prompt: str, 
        parameters: Dict[str, Any] = None
    ) -> TextGenerationResult:
        """文本生成"""
        pass
        
    async def test_connection(self) -> ConnectionTestResult:
        """测试连接"""
        pass
```

**使用示例**:
```python
# 创建自定义适配器
class MyCustomAdapter(BaseAdapter):
    async def generate_text(self, prompt: str, parameters=None):
        # 实现自定义文本生成逻辑
        return TextGenerationResult(
            text="这是自定义模型的生成结果",
            tokens_used=100,
            model_name=self.config.name
        )

# 注册自定义适配器
from src.core.model_manager import ModelManager
model_manager.register_adapter("my_custom_model", MyCustomAdapter)
```

### 自定义能力

**创建自定义能力**:
```python
from src.core.capability import Capability

# 定义自定义能力
custom_capability = Capability(
    id="custom_analysis",
    name="自定义分析",
    description="执行自定义数据分析",
    type="analysis",
    category="custom",
    parameters={
        "analysis_type": {"type": "str", "required": True},
        "depth": {"type": "int", "default": 1}
    }
)

# 注册能力
from src.core.capability_registry import CapabilityRegistry
registry = CapabilityRegistry()
registry.register_capability(custom_capability)
```

## 性能监控

### 性能指标收集

```python
from src.utils.performance_analyzer import PerformanceAnalyzer

# 创建性能分析器
analyzer = PerformanceAnalyzer()

# 开始监控
analyzer.start_monitoring()

# 记录性能指标
analyzer.record_metric("model_response_time", response_time)
analyzer.record_metric("task_completion_rate", completion_rate)

# 获取性能报告
report = analyzer.generate_report()
print(f"平均响应时间: {report.avg_response_time}ms")
print(f"任务成功率: {report.success_rate}%")
```

### 资源使用监控

```python
from src.utils.status_monitor import StatusMonitor

# 创建状态监控器
monitor = StatusMonitor()

# 获取系统资源使用
system_status = monitor.get_system_status()
print(f"CPU使用率: {system_status.cpu_usage}%")
print(f"内存使用: {system_status.memory_usage}MB")

# 获取应用状态
app_status = monitor.get_application_status()
print(f"活跃代理数: {app_status.active_agents}")
print(f"队列任务数: {app_status.queued_tasks}")
```

## 日志系统

### 日志记录

```python
from src.utils.logger import Logger

# 创建日志记录器
logger = Logger.get_logger("my_module")

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 带上下文的日志记录
logger.info("任务执行完成", extra={
    "task_id": task_id,
    "execution_time": execution_time,
    "success": True
})
```

### 日志配置

```python
# 配置日志级别和格式
from src.utils.logger import LogManager

log_manager = LogManager()
log_manager.set_log_level("DEBUG")
log_manager.set_log_format("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 添加日志处理器
log_manager.add_file_handler("app.log")
log_manager.add_console_handler()
```

## 最佳实践

### 异步编程

```python
import asyncio
from src.utils.async_utils import run_async

# 使用异步函数
async def process_multiple_tasks(tasks):
    results = await asyncio.gather(
        *[task_manager.submit_task(task) for task in tasks],
        return_exceptions=True
    )
    return results

# 在同步代码中运行异步函数
results = run_async(process_multiple_tasks(tasks))
```

### 错误处理最佳实践

```python
# 使用上下文管理器处理资源
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_agent(agent_id):
    try:
        agent_manager.start_agent(agent_id)
        yield agent_id
    finally:
        agent_manager.stop_agent(agent_id)

# 使用上下文管理器
async with managed_agent(agent_id) as agent:
    result = await agent_manager.send_task_to_agent(agent, task)
```

### 性能优化建议

1. **批量操作**: 使用批量API减少网络请求
2. **连接池**: 重用数据库和模型连接
3. **缓存**: 缓存频繁访问的数据
4. **异步处理**: 使用异步操作提高并发性能
5. **资源监控**: 定期监控资源使用情况

---

**版本**: 1.0.0  
**最后更新**: 2025年10月2日  
**版权所有**: © 2025 AI Agent Desktop Team
