"""
代理间通信协议
实现代理间消息传递、任务分解合并、协作工作流等功能
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.agent_model import AgentInstance, AgentStatus
from ..core.task_router import Task, TaskResult, TaskPriority
from ..utils.logger import get_log_manager


class MessageType(Enum):
    """消息类型"""
    TASK_REQUEST = "task_request"           # 任务请求
    TASK_RESULT = "task_result"             # 任务结果
    STATUS_UPDATE = "status_update"         # 状态更新
    HEARTBEAT = "heartbeat"                 # 心跳
    ERROR = "error"                         # 错误
    COLLABORATION_REQUEST = "collab_request" # 协作请求
    COLLABORATION_RESPONSE = "collab_response" # 协作响应


class CollaborationType(Enum):
    """协作类型"""
    SEQUENTIAL = "sequential"      # 顺序协作
    PARALLEL = "parallel"          # 并行协作
    HIERARCHICAL = "hierarchical"  # 层次协作
    PEER_TO_PEER = "peer_to_peer"  # 对等协作


@dataclass
class AgentMessage:
    """代理间消息"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: Optional[str] = None  # None表示广播
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: TaskPriority = TaskPriority.NORMAL
    correlation_id: Optional[str] = None  # 用于关联消息


@dataclass
class CollaborationRequest:
    """协作请求"""
    request_id: str
    collaboration_type: CollaborationType
    task_description: str
    required_capabilities: List[str]
    input_data: Dict[str, Any]
    timeout: int = 60
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationResponse:
    """协作响应"""
    request_id: str
    agent_id: str
    accepted: bool
    capabilities: List[str] = field(default_factory=list)
    estimated_time: Optional[float] = None
    cost_estimate: Optional[float] = None
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    capability_id: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)  # 依赖的步骤ID
    timeout: int = 30
    retry_count: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """工作流定义"""
    workflow_id: str
    steps: List[WorkflowStep]
    collaboration_type: CollaborationType = CollaborationType.SEQUENTIAL
    max_parallel_steps: int = 3
    timeout: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """工作流结果"""
    workflow_id: str
    success: bool
    step_results: Dict[str, TaskResult] = field(default_factory=dict)
    total_execution_time: Optional[float] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class AgentCommunicationProtocol:
    """代理间通信协议"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        
        # 消息队列
        self.incoming_messages: asyncio.Queue = asyncio.Queue()
        self.outgoing_messages: asyncio.Queue = asyncio.Queue()
        
        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # 协作请求跟踪
        self.collaboration_requests: Dict[str, CollaborationRequest] = {}
        self.collaboration_responses: Dict[str, List[CollaborationResponse]] = {}
        
        # 工作流跟踪
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_results: Dict[str, WorkflowResult] = {}
        
        # 通信状态
        self.running = False
        self.communication_task: Optional[asyncio.Task] = None
        
        # 注册默认消息处理器
        self._register_default_handlers()
    
    async def start(self):
        """启动通信协议"""
        try:
            self.logger.info("启动代理间通信协议...")
            self.running = True
            self.communication_task = asyncio.create_task(self._communication_loop())
            self.logger.info("代理间通信协议启动成功")
            
        except Exception as e:
            self.logger.error(f"启动代理间通信协议失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止通信协议"""
        try:
            self.logger.info("停止代理间通信协议...")
            self.running = False
            
            if self.communication_task:
                self.communication_task.cancel()
                try:
                    await self.communication_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("代理间通信协议已停止")
            
        except Exception as e:
            self.logger.error(f"停止代理间通信协议失败: {str(e)}")
    
    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self.message_handlers[MessageType.TASK_REQUEST] = self._handle_task_request
        self.message_handlers[MessageType.TASK_RESULT] = self._handle_task_result
        self.message_handlers[MessageType.STATUS_UPDATE] = self._handle_status_update
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.ERROR] = self._handle_error
        self.message_handlers[MessageType.COLLABORATION_REQUEST] = self._handle_collaboration_request
        self.message_handlers[MessageType.COLLABORATION_RESPONSE] = self._handle_collaboration_response
    
    async def _communication_loop(self):
        """通信循环"""
        while self.running:
            try:
                # 处理传入消息
                if not self.incoming_messages.empty():
                    message = await self.incoming_messages.get()
                    await self._process_incoming_message(message)
                
                # 发送传出消息
                if not self.outgoing_messages.empty():
                    message = await self.outgoing_messages.get()
                    await self._send_message(message)
                
                # 短暂休眠避免过度占用CPU
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"通信循环错误: {str(e)}")
    
    async def _process_incoming_message(self, message: AgentMessage):
        """处理传入消息"""
        try:
            handler = self.message_handlers.get(message.message_type)
            if handler:
                await handler(message)
            else:
                self.logger.warning(f"未知消息类型: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"处理消息失败: {str(e)}")
            # 发送错误响应
            error_message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.ERROR,
                sender_id="system",
                receiver_id=message.sender_id,
                payload={
                    "error": f"处理消息失败: {str(e)}",
                    "original_message_id": message.message_id
                },
                correlation_id=message.message_id
            )
            await self.send_message(error_message)
    
    async def _send_message(self, message: AgentMessage):
        """发送消息（模拟实现）"""
        try:
            # TODO: 实际实现消息发送逻辑
            # 这里模拟消息发送到A2A服务器或其他代理
            self.logger.info(f"发送消息: {message.message_type} 从 {message.sender_id} 到 {message.receiver_id or '广播'}")
            
            # 模拟网络延迟
            await asyncio.sleep(0.01)
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
    
    async def send_message(self, message: AgentMessage):
        """发送消息到队列"""
        await self.outgoing_messages.put(message)
    
    async def receive_message(self, message: AgentMessage):
        """接收消息到队列"""
        await self.incoming_messages.put(message)
    
    async def _handle_task_request(self, message: AgentMessage):
        """处理任务请求"""
        try:
            task_data = message.payload.get("task", {})
            task = Task(
                task_id=task_data.get("task_id", str(uuid.uuid4())),
                capability_id=task_data.get("capability_id"),
                input_data=task_data.get("input_data", {}),
                priority=TaskPriority(task_data.get("priority", TaskPriority.NORMAL.value)),
                timeout=task_data.get("timeout", 60),
                metadata=task_data.get("metadata", {})
            )
            
            # TODO: 实际执行任务逻辑
            self.logger.info(f"处理任务请求: {task.task_id} 来自 {message.sender_id}")
            
            # 模拟任务执行
            result = TaskResult(
                task_id=task.task_id,
                success=True,
                output_data={"result": f"处理来自 {message.sender_id} 的任务"},
                execution_time=0.1,
                agent_id="local_agent"
            )
            
            # 发送任务结果
            result_message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.TASK_RESULT,
                sender_id="local_agent",
                receiver_id=message.sender_id,
                payload={"task_result": result.__dict__},
                correlation_id=message.message_id
            )
            await self.send_message(result_message)
            
        except Exception as e:
            self.logger.error(f"处理任务请求失败: {str(e)}")
    
    async def _handle_task_result(self, message: AgentMessage):
        """处理任务结果"""
        try:
            result_data = message.payload.get("task_result", {})
            self.logger.info(f"收到任务结果: {result_data.get('task_id')} 来自 {message.sender_id}")
            
            # TODO: 实际处理任务结果逻辑
            # 这里可以更新工作流状态或通知其他组件
            
        except Exception as e:
            self.logger.error(f"处理任务结果失败: {str(e)}")
    
    async def _handle_status_update(self, message: AgentMessage):
        """处理状态更新"""
        try:
            status_data = message.payload.get("status", {})
            self.logger.info(f"收到状态更新: {status_data} 来自 {message.sender_id}")
            
            # TODO: 实际处理状态更新逻辑
            # 这里可以更新代理状态或通知其他组件
            
        except Exception as e:
            self.logger.error(f"处理状态更新失败: {str(e)}")
    
    async def _handle_heartbeat(self, message: AgentMessage):
        """处理心跳"""
        try:
            heartbeat_data = message.payload.get("heartbeat", {})
            self.logger.debug(f"收到心跳: {heartbeat_data} 来自 {message.sender_id}")
            
            # TODO: 实际处理心跳逻辑
            # 这里可以更新代理活跃状态
            
        except Exception as e:
            self.logger.error(f"处理心跳失败: {str(e)}")
    
    async def _handle_error(self, message: AgentMessage):
        """处理错误消息"""
        try:
            error_data = message.payload.get("error", {})
            self.logger.error(f"收到错误消息: {error_data} 来自 {message.sender_id}")
            
            # TODO: 实际处理错误逻辑
            # 这里可以记录错误或通知其他组件
            
        except Exception as e:
            self.logger.error(f"处理错误消息失败: {str(e)}")
    
    async def _handle_collaboration_request(self, message: AgentMessage):
        """处理协作请求"""
        try:
            request_data = message.payload.get("collaboration_request", {})
            request = CollaborationRequest(
                request_id=request_data.get("request_id", str(uuid.uuid4())),
                collaboration_type=CollaborationType(request_data.get("collaboration_type")),
                task_description=request_data.get("task_description"),
                required_capabilities=request_data.get("required_capabilities", []),
                input_data=request_data.get("input_data", {}),
                timeout=request_data.get("timeout", 60),
                metadata=request_data.get("metadata", {})
            )
            
            self.logger.info(f"收到协作请求: {request.request_id} 来自 {message.sender_id}")
            
            # 检查本地能力是否匹配
            local_capabilities = await self._get_local_capabilities()
            matching_capabilities = [
                cap for cap in request.required_capabilities 
                if cap in local_capabilities
            ]
            
            # 发送协作响应
            response = CollaborationResponse(
                request_id=request.request_id,
                agent_id="local_agent",
                accepted=len(matching_capabilities) > 0,
                capabilities=matching_capabilities,
                estimated_time=10.0,  # 模拟估计时间
                cost_estimate=0.1,    # 模拟成本估计
                constraints={"max_concurrent_tasks": 5}
            )
            
            response_message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.COLLABORATION_RESPONSE,
                sender_id="local_agent",
                receiver_id=message.sender_id,
                payload={"collaboration_response": response.__dict__},
                correlation_id=message.message_id
            )
            await self.send_message(response_message)
            
        except Exception as e:
            self.logger.error(f"处理协作请求失败: {str(e)}")
    
    async def _handle_collaboration_response(self, message: AgentMessage):
        """处理协作响应"""
        try:
            response_data = message.payload.get("collaboration_response", {})
            response = CollaborationResponse(
                request_id=response_data.get("request_id"),
                agent_id=response_data.get("agent_id"),
                accepted=response_data.get("accepted", False),
                capabilities=response_data.get("capabilities", []),
                estimated_time=response_data.get("estimated_time"),
                cost_estimate=response_data.get("cost_estimate"),
                constraints=response_data.get("constraints", {})
            )
            
            self.logger.info(f"收到协作响应: {response.request_id} 来自 {message.sender_id}")
            
            # 记录响应
            if response.request_id not in self.collaboration_responses:
                self.collaboration_responses[response.request_id] = []
            self.collaboration_responses[response.request_id].append(response)
            
        except Exception as e:
            self.logger.error(f"处理协作响应失败: {str(e)}")
    
    async def _get_local_capabilities(self) -> List[str]:
        """获取本地能力列表（模拟实现）"""
        # TODO: 实际从能力管理器获取本地能力
        return ["text_generation", "code_generation", "text_summarization"]
    
    async def initiate_collaboration(self, collaboration_request: CollaborationRequest) -> str:
        """发起协作请求"""
        try:
            self.collaboration_requests[collaboration_request.request_id] = collaboration_request
            
            # 发送协作请求消息
            message = AgentMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.COLLABORATION_REQUEST,
                sender_id="local_agent",
                receiver_id=None,  # 广播
                payload={"collaboration_request": collaboration_request.__dict__}
            )
            await self.send_message(message)
            
            self.logger.info(f"发起协作请求: {collaboration_request.request_id}")
            return collaboration_request.request_id
            
        except Exception as e:
            self.logger.error(f"发起协作请求失败: {str(e)}")
            raise
    
    async def execute_workflow(self, workflow: Workflow) -> WorkflowResult:
        """执行工作流"""
        try:
            self.active_workflows[workflow.workflow_id] = workflow
            start_time = datetime.now()
            
            self.logger.info(f"开始执行工作流: {workflow.workflow_id}")
            
            # 根据协作类型执行工作流
            if workflow.collaboration_type == CollaborationType.SEQUENTIAL:
                result = await self._execute_sequential_workflow(workflow)
            elif workflow.collaboration_type == CollaborationType.PARALLEL:
                result = await self._execute_parallel_workflow(workflow)
            elif workflow.collaboration_type == CollaborationType.HIERARCHICAL:
                result = await self._execute_hierarchical_workflow(workflow)
            elif workflow.collaboration_type == CollaborationType.PEER_TO_PEER:
                result = await self._execute_peer_to_peer_workflow(workflow)
            else:
                raise ValueError(f"未知的协作类型: {workflow.collaboration_type}")
            
            result.total_execution_time = (datetime.now() - start_time).total_seconds()
            result.completed_at = datetime.now()
            
            self.workflow_results[workflow.workflow_id] = result
            self.logger.info(f"工作流执行完成: {workflow.workflow_id}, 成功: {result.success}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行工作流失败: {str(e)}")
            result = WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=False,
                error_message=f"执行工作流失败: {str(e)}"
            )
            self.workflow_results[workflow.workflow_id] = result
            return result
    
    async def _execute_sequential_workflow(self, workflow: Workflow) -> WorkflowResult:
        """执行顺序工作流"""
        result = WorkflowResult(workflow_id=workflow.workflow_id, success=True)
        
        for step in workflow.steps:
            try:
                # 检查依赖是否完成
                for dep_id in step.dependencies:
                    if dep_id not in result.step_results or not result.step_results[dep_id].success:
                        raise Exception(f"依赖步骤 {dep_id} 未完成或失败")
                
                # 执行步骤
                step_result = await self._execute_workflow_step(step)
                result.step_results[step.step_id] = step_result
                
                if not step_result.success:
                    result.success = False
                    result.error_message = f"步骤 {step.step_id} 执行失败: {step_result.error_message}"
                    break
                    
            except Exception as e:
                result.success = False
                result.error_message = f"执行步骤 {step.step_id} 失败: {str(e)}"
                break
        
        return result
    
    async def _execute_parallel_workflow(self, workflow: Workflow) -> WorkflowResult:
        """执行并行工作流"""
        result = WorkflowResult(workflow_id=workflow.workflow_id, success=True)
        
        # 按依赖关系分组执行
        independent_steps = [step for step in workflow.steps if not step.dependencies]
        dependent_steps = [step for step in workflow.steps if step.dependencies]
        
        # 先执行独立步骤
        if independent_steps:
            tasks = [self._execute_workflow_step(step) for step in independent_steps]
            step_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for step, step_result in zip(independent_steps, step_results):
                if isinstance(step_result, Exception):
                    result.step_results[step.step_id] = TaskResult(
                        task_id=step.step_id,
                        success=False,
                        error_message=f"执行步骤失败: {str(step_result)}"
                    )
                    result.success = False
                else:
                    result.step_results[step.step_id] = step_result
                    if not step_result.success:
                        result.success = False
        
        # 再执行依赖步骤（简化实现）
        for step in dependent_steps:
            try:
                step_result = await self._execute_workflow_step(step)
                result.step_results[step.step_id] = step_result
                if not step_result.success:
                    result.success = False
            except Exception as e:
                result.success = False
                result.error_message = f"执行依赖步骤 {step.step_id} 失败: {str(e)}"
        
        return result
    
    async def _execute_hierarchical_workflow(self, workflow: Workflow) -> WorkflowResult:
        """执行层次工作流"""
        # 简化实现，使用顺序执行
        return await self._execute_sequential_workflow(workflow)
    
    async def _execute_peer_to_peer_workflow(self, workflow: Workflow) -> WorkflowResult:
        """执行对等工作流"""
        # 简化实现，使用并行执行
        return await self._execute_parallel_workflow(workflow)
    
    async def _execute_workflow_step(self, step: WorkflowStep) -> TaskResult:
        """执行工作流步骤"""
        try:
            # TODO: 实际执行步骤逻辑
            # 这里模拟步骤执行
            self.logger.info(f"执行工作流步骤: {step.step_id}")
            
            await asyncio.sleep(0.1)  # 模拟执行时间
            
            return TaskResult(
                task_id=step.step_id,
                success=True,
                output_data={"result": f"步骤 {step.step_id} 执行完成"},
                execution_time=0.1,
                agent_id="local_agent"
            )
            
        except Exception as e:
            self.logger.error(f"执行工作流步骤失败: {str(e)}")
            return TaskResult(
                task_id=step.step_id,
                success=False,
                error_message=f"执行步骤失败: {str(e)}"
            )
    
    async def get_collaboration_responses(self, request_id: str) -> List[CollaborationResponse]:
        """获取协作响应"""
        return self.collaboration_responses.get(request_id, [])
    
    async def get_workflow_result(self, workflow_id: str) -> Optional[WorkflowResult]:
        """获取工作流结果"""
        return self.workflow_results.get(workflow_id)
    
    def get_active_workflows(self) -> Dict[str, Workflow]:
        """获取活跃工作流"""
        return self.active_workflows.copy()
    
    def get_workflow_results(self) -> Dict[str, WorkflowResult]:
        """获取工作流结果"""
        return self.workflow_results.copy()


# 全局通信协议实例
_communication_protocol: Optional[AgentCommunicationProtocol] = None


def get_communication_protocol() -> AgentCommunicationProtocol:
    """获取全局通信协议实例"""
    global _communication_protocol
    if _communication_protocol is None:
        _communication_protocol = AgentCommunicationProtocol()
    return _communication_protocol


async def start_communication_protocol():
    """启动通信协议"""
    protocol = get_communication_protocol()
    await protocol.start()
    return protocol


async def stop_communication_protocol():
    """停止通信协议"""
    global _communication_protocol
    if _communication_protocol:
        await _communication_protocol.stop()
        _communication_protocol = None


async def send_agent_message(message: AgentMessage):
    """发送代理消息"""
    protocol = get_communication_protocol()
    await protocol.send_message(message)


async def receive_agent_message(message: AgentMessage):
    """接收代理消息"""
    protocol = get_communication_protocol()
    await protocol.receive_message(message)
