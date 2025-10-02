"""
代理生命周期管理
负责代理的自动启动、健康检查、故障恢复等生命周期管理功能
"""

import asyncio
import time
import threading
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from .agent_model import AgentRegistry, AgentInstance, AgentStatus, AgentConfig
from ..utils.logger import get_log_manager


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"  # 健康
    WARNING = "warning"  # 警告
    CRITICAL = "critical"  # 严重
    UNKNOWN = "unknown"  # 未知


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    message: str
    timestamp: float
    response_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float
    memory_mb: float
    disk_mb: float
    network_rx_mb: float
    network_tx_mb: float
    timestamp: float


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.logger = get_log_manager().logger
    
    async def check_agent_health(self, agent_instance: AgentInstance) -> HealthCheckResult:
        """检查代理健康状态"""
        try:
            start_time = time.time()
            
            # 基础状态检查
            if agent_instance.status == AgentStatus.ERROR:
                return HealthCheckResult(
                    status=HealthStatus.CRITICAL,
                    message="代理处于错误状态",
                    timestamp=start_time,
                    response_time=time.time() - start_time
                )
            
            if agent_instance.status == AgentStatus.STOPPED:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message="代理已停止",
                    timestamp=start_time,
                    response_time=time.time() - start_time
                )
            
            # 模拟健康检查（实际项目中需要实现具体的检查逻辑）
            if agent_instance.status == AgentStatus.RUNNING:
                # 模拟响应时间检查
                response_time = time.time() - start_time
                
                if response_time < 0.1:
                    status = HealthStatus.HEALTHY
                    message = "代理运行正常"
                elif response_time < 1.0:
                    status = HealthStatus.WARNING
                    message = f"代理响应较慢: {response_time:.2f}s"
                else:
                    status = HealthStatus.CRITICAL
                    message = f"代理响应超时: {response_time:.2f}s"
                
                return HealthCheckResult(
                    status=status,
                    message=message,
                    timestamp=start_time,
                    response_time=response_time
                )
            
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"未知状态: {agent_instance.status.value}",
                timestamp=start_time,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {str(e)}")
            return HealthCheckResult(
                status=HealthStatus.CRITICAL,
                message=f"健康检查异常: {str(e)}",
                timestamp=time.time(),
                error=str(e)
            )
    
    async def check_all_agents(self) -> Dict[str, HealthCheckResult]:
        """检查所有代理的健康状态"""
        results = {}
        agents = self.agent_registry.list_agents()
        
        for agent_config in agents:
            # 获取代理的所有实例
            agent_instances = self.agent_registry.get_agent_instances(agent_config.agent_id)
            if agent_instances:
                # 只检查第一个实例（简化实现）
                agent_instance = agent_instances[0]
                result = await self.check_agent_health(agent_instance)
                results[agent_config.agent_id] = result
        
        return results


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.logger = get_log_manager().logger
        self.resource_history: Dict[str, List[ResourceUsage]] = {}
    
    def get_system_resources(self) -> ResourceUsage:
        """获取系统资源使用情况（简化版本）"""
        # 实际项目中应该使用psutil等库获取真实资源数据
        current_time = time.time()
        
        return ResourceUsage(
            cpu_percent=25.0,  # 模拟25% CPU使用率
            memory_mb=512.0,   # 模拟512MB内存使用
            disk_mb=1024.0,    # 模拟1GB磁盘使用
            network_rx_mb=10.0,  # 模拟10MB网络接收
            network_tx_mb=5.0,   # 模拟5MB网络发送
            timestamp=current_time
        )
    
    def get_agent_resources(self, agent_instance: AgentInstance) -> ResourceUsage:
        """获取代理资源使用情况（简化版本）"""
        # 实际项目中应该从代理实例获取真实资源数据
        current_time = time.time()
        
        # 模拟基于代理状态的资源使用
        if agent_instance.status == AgentStatus.RUNNING:
            cpu = 15.0
            memory = 256.0
        elif agent_instance.status == AgentStatus.STARTING:
            cpu = 5.0
            memory = 128.0
        else:
            cpu = 0.0
            memory = 0.0
        
        return ResourceUsage(
            cpu_percent=cpu,
            memory_mb=memory,
            disk_mb=50.0,  # 模拟50MB磁盘使用
            network_rx_mb=2.0,
            network_tx_mb=1.0,
            timestamp=current_time
        )
    
    def record_resource_usage(self, agent_id: str, usage: ResourceUsage):
        """记录资源使用历史"""
        if agent_id not in self.resource_history:
            self.resource_history[agent_id] = []
        
        self.resource_history[agent_id].append(usage)
        
        # 保持最近100条记录
        if len(self.resource_history[agent_id]) > 100:
            self.resource_history[agent_id] = self.resource_history[agent_id][-100:]
    
    def get_resource_trend(self, agent_id: str, hours: int = 1) -> Optional[ResourceUsage]:
        """获取资源使用趋势"""
        if agent_id not in self.resource_history:
            return None
        
        history = self.resource_history[agent_id]
        cutoff_time = time.time() - (hours * 3600)
        
        recent_usage = [u for u in history if u.timestamp >= cutoff_time]
        if not recent_usage:
            return None
        
        # 计算平均值
        avg_cpu = sum(u.cpu_percent for u in recent_usage) / len(recent_usage)
        avg_memory = sum(u.memory_mb for u in recent_usage) / len(recent_usage)
        avg_disk = sum(u.disk_mb for u in recent_usage) / len(recent_usage)
        
        return ResourceUsage(
            cpu_percent=avg_cpu,
            memory_mb=avg_memory,
            disk_mb=avg_disk,
            network_rx_mb=0.0,
            network_tx_mb=0.0,
            timestamp=time.time()
        )


class AutoStarter:
    """自动启动器"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.logger = get_log_manager().logger
        self.auto_start_enabled = True
    
    def enable_auto_start(self):
        """启用自动启动"""
        self.auto_start_enabled = True
        self.logger.info("自动启动已启用")
    
    def disable_auto_start(self):
        """禁用自动启动"""
        self.auto_start_enabled = False
        self.logger.info("自动启动已禁用")
    
    async def auto_start_agents(self):
        """自动启动需要启动的代理"""
        if not self.auto_start_enabled:
            return
        
        agents = self.agent_registry.list_agents()
        started_count = 0
        
        for agent_config in agents:
            if agent_config.auto_start:
                # 获取代理的所有实例
                agent_instances = self.agent_registry.get_agent_instances(agent_config.agent_id)
                if agent_instances:
                    # 只检查第一个实例（简化实现）
                    agent_instance = agent_instances[0]
                    if agent_instance.status == AgentStatus.STOPPED:
                        try:
                            success = await self.agent_registry.start_agent(agent_config.agent_id)
                            if success:
                                started_count += 1
                                self.logger.info(f"自动启动代理: {agent_config.name}")
                            else:
                                self.logger.warning(f"自动启动代理失败: {agent_config.name}")
                        except Exception as e:
                            self.logger.error(f"自动启动代理异常: {agent_config.name}, 错误: {str(e)}")
        
        if started_count > 0:
            self.logger.info(f"自动启动了 {started_count} 个代理")


class FaultRecovery:
    """故障恢复"""
    
    def __init__(self, agent_registry: AgentRegistry, health_checker: HealthChecker):
        self.agent_registry = agent_registry
        self.health_checker = health_checker
        self.logger = get_log_manager().logger
        self.recovery_enabled = True
        self.max_restart_attempts = 3
        self.restart_attempts: Dict[str, int] = {}
    
    def enable_recovery(self):
        """启用故障恢复"""
        self.recovery_enabled = True
        self.logger.info("故障恢复已启用")
    
    def disable_recovery(self):
        """禁用故障恢复"""
        self.recovery_enabled = False
        self.logger.info("故障恢复已禁用")
    
    async def handle_fault(self, agent_instance: AgentInstance, health_result: HealthCheckResult):
        """处理代理故障"""
        if not self.recovery_enabled:
            return
        
        agent_id = agent_instance.agent_config.agent_id
        
        if health_result.status == HealthStatus.CRITICAL:
            # 严重故障，尝试重启
            await self._attempt_restart(agent_instance)
        elif health_result.status == HealthStatus.WARNING:
            # 警告状态，记录但不立即处理
            self.logger.warning(f"代理 {agent_instance.agent_config.name} 处于警告状态: {health_result.message}")
    
    async def _attempt_restart(self, agent_instance: AgentInstance):
        """尝试重启代理"""
        agent_id = agent_instance.agent_config.agent_id
        agent_name = agent_instance.agent_config.name
        
        # 获取重启尝试次数
        attempts = self.restart_attempts.get(agent_id, 0)
        
        if attempts >= self.max_restart_attempts:
            self.logger.error(f"代理 {agent_name} 已达到最大重启次数 ({self.max_restart_attempts})，停止自动重启")
            return
        
        try:
            self.logger.info(f"尝试重启代理 {agent_name} (第 {attempts + 1} 次尝试)")
            
            # 先停止代理
            await self.agent_registry.stop_agent(agent_id)
            
            # 等待一段时间
            await asyncio.sleep(2)
            
            # 重新启动代理
            success = await self.agent_registry.start_agent(agent_id)
            
            if success:
                self.logger.info(f"代理 {agent_name} 重启成功")
                # 重置重启计数
                self.restart_attempts[agent_id] = 0
            else:
                self.logger.warning(f"代理 {agent_name} 重启失败")
                # 增加重启计数
                self.restart_attempts[agent_id] = attempts + 1
                
        except Exception as e:
            self.logger.error(f"代理 {agent_name} 重启异常: {str(e)}")
            self.restart_attempts[agent_id] = attempts + 1
    
    def reset_restart_attempts(self, agent_id: str):
        """重置代理的重启尝试计数"""
        if agent_id in self.restart_attempts:
            del self.restart_attempts[agent_id]


class AgentLifecycleManager:
    """代理生命周期管理器"""
    
    def __init__(self, agent_registry: AgentRegistry):
        self.agent_registry = agent_registry
        self.health_checker = HealthChecker(agent_registry)
        self.resource_monitor = ResourceMonitor()
        self.auto_starter = AutoStarter(agent_registry)
        self.fault_recovery = FaultRecovery(agent_registry, self.health_checker)
        
        self.logger = get_log_manager().logger
        self.running = False
        self.monitoring_interval = 30  # 监控间隔（秒）
        self.health_check_interval = 60  # 健康检查间隔（秒）
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable] = []
    
    def start_monitoring(self):
        """开始监控"""
        if self.running:
            self.logger.warning("生命周期监控已在运行")
            return
        
        self.running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("代理生命周期监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.running:
            self.logger.warning("生命周期监控未在运行")
            return
        
        self.running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
        self.logger.info("代理生命周期监控已停止")
    
    async def _monitoring_loop(self):
        """监控循环"""
        last_health_check = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # 自动启动检查
                await self.auto_starter.auto_start_agents()
                
                # 定期健康检查
                if current_time - last_health_check >= self.health_check_interval:
                    health_results = await self.health_checker.check_all_agents()
                    await self._process_health_results(health_results)
                    last_health_check = current_time
                
                # 资源监控
                await self._monitor_resources()
                
                # 等待下一个监控周期
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环异常: {str(e)}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _process_health_results(self, health_results: Dict[str, HealthCheckResult]):
        """处理健康检查结果"""
        for agent_id, result in health_results.items():
            # 获取代理的所有实例
            agent_instances = self.agent_registry.get_agent_instances(agent_id)
            if agent_instances:
                # 只处理第一个实例（简化实现）
                agent_instance = agent_instances[0]
                # 记录健康状态
                agent_instance.health_status = result.status.value
                agent_instance.last_health_check = result.timestamp
                
                # 处理故障
                if result.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                    await self.fault_recovery.handle_fault(agent_instance, result)
                
                # 触发回调
                for callback in self._callbacks:
                    try:
                        callback(agent_instance, result)
                    except Exception as e:
                        self.logger.error(f"健康检查回调异常: {str(e)}")
    
    async def _monitor_resources(self):
        """监控资源使用"""
        agents = self.agent_registry.list_agents()
        
        for agent_config in agents:
            # 获取代理的所有实例
            agent_instances = self.agent_registry.get_agent_instances(agent_config.agent_id)
            if agent_instances:
                # 只监控第一个实例（简化实现）
                agent_instance = agent_instances[0]
                resource_usage = self.resource_monitor.get_agent_resources(agent_instance)
                self.resource_monitor.record_resource_usage(agent_config.agent_id, resource_usage)
                
                # 更新代理实例的资源使用信息
                agent_instance.cpu_usage = resource_usage.cpu_percent
                agent_instance.memory_usage = resource_usage.memory_mb / 1024 * 100  # 转换为百分比
                agent_instance.disk_usage = resource_usage.disk_mb / 1024 * 100  # 转换为百分比
    
    def add_health_callback(self, callback: Callable):
        """添加健康检查回调"""
        self._callbacks.append(callback)
    
    def remove_health_callback(self, callback: Callable):
        """移除健康检查回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        agents = self.agent_registry.list_agents()
        
        total_agents = len(agents)
        running_agents = 0
        healthy_agents = 0
        warning_agents = 0
        critical_agents = 0
        
        for agent_config in agents:
            # 获取代理的所有实例
            agent_instances = self.agent_registry.get_agent_instances(agent_config.agent_id)
            if agent_instances:
                # 只检查第一个实例（简化实现）
                agent_instance = agent_instances[0]
                if agent_instance.status == AgentStatus.RUNNING:
                    running_agents += 1
                
                if hasattr(agent_instance, 'health_status'):
                    if agent_instance.health_status == HealthStatus.HEALTHY.value:
                        healthy_agents += 1
                    elif agent_instance.health_status == HealthStatus.WARNING.value:
                        warning_agents += 1
                    elif agent_instance.health_status == HealthStatus.CRITICAL.value:
                        critical_agents += 1
        
        return {
            "total_agents": total_agents,
            "running_agents": running_agents,
            "healthy_agents": healthy_agents,
            "warning_agents": warning_agents,
            "critical_agents": critical_agents,
            "auto_start_enabled": self.auto_starter.auto_start_enabled,
            "recovery_enabled": self.fault_recovery.recovery_enabled,
            "monitoring_running": self.running
        }


# 全局生命周期管理器实例
_lifecycle_manager: Optional[AgentLifecycleManager] = None


def get_lifecycle_manager(agent_registry: AgentRegistry) -> AgentLifecycleManager:
    """获取全局生命周期管理器实例"""
    global _lifecycle_manager
    if _lifecycle_manager is None:
        _lifecycle_manager = AgentLifecycleManager(agent_registry)
    return _lifecycle_manager


def start_global_monitoring(agent_registry: AgentRegistry):
    """启动全局监控"""
    manager = get_lifecycle_manager(agent_registry)
    manager.start_monitoring()


def stop_global_monitoring():
    """停止全局监控"""
    global _lifecycle_manager
    if _lifecycle_manager:
        _lifecycle_manager.stop_monitoring()


def get_global_system_status() -> Optional[Dict]:
    """获取全局系统状态"""
    global _lifecycle_manager
    if _lifecycle_manager:
        return _lifecycle_manager.get_system_status()
    return None


# 使用示例
async def demo_lifecycle_manager():
    """演示生命周期管理器使用"""
    from .agent_model import AgentRegistry
    
    # 创建代理注册表
    agent_registry = AgentRegistry()
    
    # 获取生命周期管理器
    lifecycle_manager = get_lifecycle_manager(agent_registry)
    
    # 添加健康检查回调
    def health_callback(agent_instance: AgentInstance, result: HealthCheckResult):
        print(f"代理 {agent_instance.agent_config.name} 健康状态: {result.status.value} - {result.message}")
    
    lifecycle_manager.add_health_callback(health_callback)
    
    # 启动监控
    lifecycle_manager.start_monitoring()
    
    print("生命周期监控已启动")
    
    # 模拟运行一段时间
    await asyncio.sleep(120)
    
    # 获取系统状态
    status = lifecycle_manager.get_system_status()
    print(f"系统状态: {status}")
    
    # 停止监控
    lifecycle_manager.stop_monitoring()
    print("生命周期监控已停止")


if __name__ == "__main__":
    asyncio.run(demo_lifecycle_manager())
