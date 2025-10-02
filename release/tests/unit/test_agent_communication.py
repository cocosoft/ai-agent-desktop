"""
代理间通信协议单元测试
测试代理间消息传递、任务分解合并、协作工作流等功能
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.core.agent_communication import (
    AgentCommunicationProtocol, AgentMessage, MessageType, CollaborationType,
    CollaborationRequest, CollaborationResponse, Workflow, WorkflowStep, 
    WorkflowResult, get_communication_protocol, start_communication_protocol, 
    stop_communication_protocol
)
from src.core.task_router import TaskResult, TaskPriority


class TestAgentCommunicationProtocol:
    """代理间通信协议测试"""
    
    @pytest.fixture
    def communication_protocol(self):
        """创建通信协议实例"""
        return AgentCommunicationProtocol()
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return AgentMessage(
            message_id="test_message",
            message_type=MessageType.TASK_REQUEST,
            sender_id="agent1",
            receiver_id="agent2",
            payload={"task": {"task_id": "test_task", "capability_id": "text_generation"}},
            priority=TaskPriority.NORMAL
        )
    
    @pytest.fixture
    def sample_collaboration_request(self):
        """创建示例协作请求"""
        return CollaborationRequest(
            request_id="test_request",
            collaboration_type=CollaborationType.SEQUENTIAL,
            task_description="测试协作任务",
            required_capabilities=["text_generation", "code_generation"],
            input_data={"text": "测试输入"},
            timeout=60
        )
    
    @pytest.fixture
    def sample_workflow(self):
        """创建示例工作流"""
        step1 = WorkflowStep(
            step_id="step1",
            capability_id="text_generation",
            input_data={"text": "步骤1输入"}
        )
        step2 = WorkflowStep(
            step_id="step2",
            capability_id="code_generation",
            input_data={"code": "步骤2输入"},
            dependencies=["step1"]
        )
        
        return Workflow(
            workflow_id="test_workflow",
            steps=[step1, step2],
            collaboration_type=CollaborationType.SEQUENTIAL
        )
    
    def test_communication_protocol_creation(self, communication_protocol):
        """测试通信协议创建"""
        assert communication_protocol is not None
        assert communication_protocol.logger is not None
        assert isinstance(communication_protocol.incoming_messages, asyncio.Queue)
        assert isinstance(communication_protocol.outgoing_messages, asyncio.Queue)
        assert len(communication_protocol.message_handlers) == 7  # 7种消息类型
        assert communication_protocol.running is False
        assert communication_protocol.communication_task is None
    
    @pytest.mark.asyncio
    async def test_send_receive_message(self, communication_protocol, sample_message):
        """测试发送和接收消息"""
        # 发送消息
        await communication_protocol.send_message(sample_message)
        assert communication_protocol.outgoing_messages.qsize() == 1
        
        # 接收消息
        await communication_protocol.receive_message(sample_message)
        assert communication_protocol.incoming_messages.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_handle_task_request(self, communication_protocol, sample_message):
        """测试处理任务请求"""
        with patch.object(communication_protocol, 'send_message') as mock_send:
            await communication_protocol._handle_task_request(sample_message)
            
            # 验证发送了任务结果消息
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            assert sent_message.message_type == MessageType.TASK_RESULT
            assert sent_message.receiver_id == sample_message.sender_id
            assert "task_result" in sent_message.payload
    
    @pytest.mark.asyncio
    async def test_handle_task_result(self, communication_protocol, sample_message):
        """测试处理任务结果"""
        sample_message.message_type = MessageType.TASK_RESULT
        sample_message.payload = {"task_result": {"task_id": "test_task", "success": True}}
        
        await communication_protocol._handle_task_result(sample_message)
        # 应该没有错误发生
    
    @pytest.mark.asyncio
    async def test_handle_status_update(self, communication_protocol, sample_message):
        """测试处理状态更新"""
        sample_message.message_type = MessageType.STATUS_UPDATE
        sample_message.payload = {"status": {"agent_id": "agent1", "status": "running"}}
        
        await communication_protocol._handle_status_update(sample_message)
        # 应该没有错误发生
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat(self, communication_protocol, sample_message):
        """测试处理心跳"""
        sample_message.message_type = MessageType.HEARTBEAT
        sample_message.payload = {"heartbeat": {"agent_id": "agent1", "timestamp": "2025-10-02"}}
        
        await communication_protocol._handle_heartbeat(sample_message)
        # 应该没有错误发生
    
    @pytest.mark.asyncio
    async def test_handle_error(self, communication_protocol, sample_message):
        """测试处理错误消息"""
        sample_message.message_type = MessageType.ERROR
        sample_message.payload = {"error": {"message": "测试错误", "code": "TEST_ERROR"}}
        
        await communication_protocol._handle_error(sample_message)
        # 应该没有错误发生
    
    @pytest.mark.asyncio
    async def test_handle_collaboration_request(self, communication_protocol, sample_message):
        """测试处理协作请求"""
        sample_message.message_type = MessageType.COLLABORATION_REQUEST
        sample_message.payload = {
            "collaboration_request": {
                "request_id": "test_request",
                "collaboration_type": "sequential",
                "task_description": "测试任务",
                "required_capabilities": ["text_generation"],
                "input_data": {"text": "测试输入"}
            }
        }
        
        with patch.object(communication_protocol, 'send_message') as mock_send:
            await communication_protocol._handle_collaboration_request(sample_message)
            
            # 验证发送了协作响应消息
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            assert sent_message.message_type == MessageType.COLLABORATION_RESPONSE
            assert sent_message.receiver_id == sample_message.sender_id
            assert "collaboration_response" in sent_message.payload
    
    @pytest.mark.asyncio
    async def test_handle_collaboration_response(self, communication_protocol, sample_message):
        """测试处理协作响应"""
        sample_message.message_type = MessageType.COLLABORATION_RESPONSE
        sample_message.payload = {
            "collaboration_response": {
                "request_id": "test_request",
                "agent_id": "agent1",
                "accepted": True,
                "capabilities": ["text_generation"]
            }
        }
        
        await communication_protocol._handle_collaboration_response(sample_message)
        
        # 验证响应已记录
        assert "test_request" in communication_protocol.collaboration_responses
        responses = communication_protocol.collaboration_responses["test_request"]
        assert len(responses) == 1
        assert responses[0].agent_id == "agent1"
        assert responses[0].accepted is True
    
    @pytest.mark.asyncio
    async def test_initiate_collaboration(self, communication_protocol, sample_collaboration_request):
        """测试发起协作请求"""
        with patch.object(communication_protocol, 'send_message') as mock_send:
            request_id = await communication_protocol.initiate_collaboration(sample_collaboration_request)
            
            # 验证请求已记录
            assert request_id == sample_collaboration_request.request_id
            assert request_id in communication_protocol.collaboration_requests
            
            # 验证发送了协作请求消息
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            assert sent_message.message_type == MessageType.COLLABORATION_REQUEST
            assert sent_message.receiver_id is None  # 广播
            assert "collaboration_request" in sent_message.payload
    
    @pytest.mark.asyncio
    async def test_execute_sequential_workflow(self, communication_protocol, sample_workflow):
        """测试执行顺序工作流"""
        result = await communication_protocol._execute_sequential_workflow(sample_workflow)
        
        assert result.workflow_id == sample_workflow.workflow_id
        assert result.success is True
        assert len(result.step_results) == 2
        assert "step1" in result.step_results
        assert "step2" in result.step_results
        assert result.step_results["step1"].success is True
        assert result.step_results["step2"].success is True
    
    @pytest.mark.asyncio
    async def test_execute_parallel_workflow(self, communication_protocol):
        """测试执行并行工作流"""
        step1 = WorkflowStep(
            step_id="step1",
            capability_id="text_generation",
            input_data={"text": "步骤1输入"}
        )
        step2 = WorkflowStep(
            step_id="step2",
            capability_id="code_generation",
            input_data={"code": "步骤2输入"}
        )
        
        workflow = Workflow(
            workflow_id="test_parallel_workflow",
            steps=[step1, step2],
            collaboration_type=CollaborationType.PARALLEL
        )
        
        result = await communication_protocol._execute_parallel_workflow(workflow)
        
        assert result.workflow_id == workflow.workflow_id
        assert result.success is True
        assert len(result.step_results) == 2
        assert "step1" in result.step_results
        assert "step2" in result.step_results
    
    @pytest.mark.asyncio
    async def test_execute_workflow_step(self, communication_protocol):
        """测试执行工作流步骤"""
        step = WorkflowStep(
            step_id="test_step",
            capability_id="text_generation",
            input_data={"text": "测试输入"}
        )
        
        result = await communication_protocol._execute_workflow_step(step)
        
        assert result.task_id == step.step_id
        assert result.success is True
        assert result.output_data is not None
        assert result.execution_time is not None
        assert result.agent_id == "local_agent"
    
    @pytest.mark.asyncio
    async def test_get_collaboration_responses(self, communication_protocol):
        """测试获取协作响应"""
        # 添加一些测试响应
        response = CollaborationResponse(
            request_id="test_request",
            agent_id="agent1",
            accepted=True,
            capabilities=["text_generation"]
        )
        communication_protocol.collaboration_responses["test_request"] = [response]
        
        responses = await communication_protocol.get_collaboration_responses("test_request")
        
        assert len(responses) == 1
        assert responses[0].agent_id == "agent1"
        assert responses[0].accepted is True
    
    @pytest.mark.asyncio
    async def test_get_workflow_result(self, communication_protocol):
        """测试获取工作流结果"""
        # 添加测试结果
        result = WorkflowResult(
            workflow_id="test_workflow",
            success=True
        )
        communication_protocol.workflow_results["test_workflow"] = result
        
        retrieved_result = await communication_protocol.get_workflow_result("test_workflow")
        
        assert retrieved_result is not None
        assert retrieved_result.workflow_id == "test_workflow"
        assert retrieved_result.success is True
    
    @pytest.mark.asyncio
    async def test_start_stop_protocol(self, communication_protocol):
        """测试启动和停止通信协议"""
        # 启动协议
        await communication_protocol.start()
        assert communication_protocol.running is True
        assert communication_protocol.communication_task is not None
        
        # 停止协议
        await communication_protocol.stop()
        assert communication_protocol.running is False


class TestGlobalFunctions:
    """全局函数测试"""
    
    def test_get_communication_protocol(self):
        """测试获取全局通信协议"""
        protocol1 = get_communication_protocol()
        protocol2 = get_communication_protocol()
        
        assert protocol1 is not None
        assert protocol2 is not None
        assert protocol1 is protocol2  # 应该是同一个实例
    
    @pytest.mark.asyncio
    async def test_start_stop_communication_protocol(self):
        """测试启动和停止全局通信协议"""
        # 使用Mock来避免实际启动协议
        with patch('src.core.agent_communication.AgentCommunicationProtocol.start') as mock_start, \
             patch('src.core.agent_communication.AgentCommunicationProtocol.stop') as mock_stop:
            
            # 测试启动
            await start_communication_protocol()
            mock_start.assert_called_once()
            
            # 测试停止
            await stop_communication_protocol()
            mock_stop.assert_called_once()


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def communication_protocol(self):
        """创建通信协议实例"""
        return AgentCommunicationProtocol()
    
    @pytest.mark.asyncio
    async def test_complete_message_workflow(self, communication_protocol):
        """测试完整消息工作流"""
        # 1. 创建任务请求消息
        task_message = AgentMessage(
            message_id="task_msg",
            message_type=MessageType.TASK_REQUEST,
            sender_id="agent1",
            receiver_id="agent2",
            payload={
                "task": {
                    "task_id": "test_task",
                    "capability_id": "text_generation",
                    "input_data": {"text": "测试输入"},
                    "priority": TaskPriority.NORMAL.value
                }
            }
        )
        
        # 2. 处理任务请求
        with patch.object(communication_protocol, 'send_message') as mock_send:
            await communication_protocol._handle_task_request(task_message)
            
            # 3. 验证发送了任务结果
            mock_send.assert_called_once()
            result_message = mock_send.call_args[0][0]
            assert result_message.message_type == MessageType.TASK_RESULT
            assert result_message.receiver_id == "agent1"
            assert result_message.correlation_id == "task_msg"
    
    @pytest.mark.asyncio
    async def test_complete_collaboration_workflow(self, communication_protocol):
        """测试完整协作工作流"""
        # 1. 创建协作请求
        collaboration_request = CollaborationRequest(
            request_id="collab_request",
            collaboration_type=CollaborationType.SEQUENTIAL,
            task_description="测试协作任务",
            required_capabilities=["text_generation", "code_generation"],
            input_data={"text": "测试输入"}
        )
        
        # 2. 发起协作请求
        with patch.object(communication_protocol, 'send_message') as mock_send:
            request_id = await communication_protocol.initiate_collaboration(collaboration_request)
            
            # 3. 验证请求已发送
            mock_send.assert_called_once()
            request_message = mock_send.call_args[0][0]
            assert request_message.message_type == MessageType.COLLABORATION_REQUEST
            assert request_message.receiver_id is None  # 广播
        
        # 4. 模拟接收协作响应
        response_message = AgentMessage(
            message_id="response_msg",
            message_type=MessageType.COLLABORATION_RESPONSE,
            sender_id="agent2",
            receiver_id="agent1",
            payload={
                "collaboration_response": {
                    "request_id": request_id,
                    "agent_id": "agent2",
                    "accepted": True,
                    "capabilities": ["text_generation"]
                }
            }
        )
        
        await communication_protocol._handle_collaboration_response(response_message)
        
        # 5. 验证响应已记录
        responses = await communication_protocol.get_collaboration_responses(request_id)
        assert len(responses) == 1
        assert responses[0].agent_id == "agent2"
        assert responses[0].accepted is True


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
