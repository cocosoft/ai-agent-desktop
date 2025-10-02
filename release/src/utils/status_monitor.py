"""
应用状态监控器
负责监控应用的各种状态指标和性能数据
"""

import time
import threading
import psutil
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import deque

# 在测试模式下使用模拟日志函数
if __name__ == "__main__":
    def log_info(message: str):
        print(f"INFO: {message}")
    
    def log_performance(operation: str, duration_ms: float, details: str = ""):
        print(f"PERF: {operation} - {duration_ms:.2f}ms - {details}")
    
    def log_error(message: str, error: Exception = None):
        print(f"ERROR: {message}")
        if error:
            print(f"Error details: {error}")
else:
    from .logger import log_info, log_performance, log_error


class StatusMonitor:
    """应用状态监控器类"""
    
    def __init__(self):
        """初始化状态监控器"""
        self.metrics: Dict[str, Any] = {}
        self.history: Dict[str, deque] = {}
        self.alerts: Dict[str, bool] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        self.update_callbacks: Dict[str, Callable] = {}
        
        # 初始化指标
        self._initialize_metrics()
        self._initialize_history()
    
    def _initialize_metrics(self):
        """初始化监控指标"""
        self.metrics = {
            # 系统指标
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_io': {'sent': 0, 'recv': 0},
            
            # 应用指标
            'app_uptime': 0,
            'database_connections': 0,
            'active_agents': 0,
            'pending_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            
            # 性能指标
            'response_time': 0.0,
            'throughput': 0.0,
            'error_rate': 0.0,
            
            # 自定义指标
            'custom_metrics': {}
        }
    
    def _initialize_history(self):
        """初始化历史数据"""
        history_size = 100  # 保留最近100个数据点
        
        for metric in self.metrics.keys():
            if metric != 'custom_metrics':
                self.history[metric] = deque(maxlen=history_size)
        
        # 自定义指标的历史数据在添加时初始化
        self.history['custom_metrics'] = {}
    
    def start_monitoring(self, interval: float = 5.0):
        """
        开始监控
        
        Args:
            interval: 监控间隔（秒）
        """
        if self.is_monitoring:
            log_info("状态监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        log_info(f"状态监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        
        log_info("状态监控已停止")
    
    def _monitoring_loop(self, interval: float):
        """监控循环"""
        start_time = time.time()
        
        while self.is_monitoring:
            try:
                # 更新系统指标
                self._update_system_metrics()
                
                # 更新应用指标
                self._update_application_metrics()
                
                # 检查警报条件
                self._check_alerts()
                
                # 调用更新回调
                self._call_update_callbacks()
                
                # 记录性能日志
                self._log_performance_metrics()
                
            except Exception as e:
                log_error("状态监控更新失败", e)
            
            # 等待下一个监控周期
            time.sleep(interval)
    
    def _update_system_metrics(self):
        """更新系统指标"""
        try:
            # CPU使用率
            self.metrics['cpu_usage'] = psutil.cpu_percent(interval=0.1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'] = memory.percent
            
            # 磁盘使用率（使用应用所在磁盘）
            disk = psutil.disk_usage('.')
            self.metrics['disk_usage'] = disk.percent
            
            # 网络IO
            net_io = psutil.net_io_counters()
            self.metrics['network_io'] = {
                'sent': net_io.bytes_sent,
                'recv': net_io.bytes_recv
            }
            
            # 保存历史数据
            self._save_metric_history('cpu_usage')
            self._save_metric_history('memory_usage')
            self._save_metric_history('disk_usage')
            
        except Exception as e:
            log_error("更新系统指标失败", e)
    
    def _update_application_metrics(self):
        """更新应用指标"""
        try:
            # 应用运行时间
            if 'app_start_time' in self.metrics:
                self.metrics['app_uptime'] = time.time() - self.metrics['app_start_time']
            
            # 这里可以添加更多应用特定的指标更新逻辑
            # 例如：数据库连接数、活跃代理数等
            
            # 保存历史数据
            self._save_metric_history('app_uptime')
            
        except Exception as e:
            log_error("更新应用指标失败", e)
    
    def _save_metric_history(self, metric_name: str):
        """保存指标历史数据"""
        if metric_name in self.metrics and metric_name in self.history:
            timestamp = datetime.now()
            value = self.metrics[metric_name]
            self.history[metric_name].append((timestamp, value))
    
    def _check_alerts(self):
        """检查警报条件"""
        # CPU使用率警报
        if self.metrics['cpu_usage'] > 80.0 and not self.alerts.get('high_cpu', False):
            self.alerts['high_cpu'] = True
            log_info(f"CPU使用率过高: {self.metrics['cpu_usage']:.1f}%")
        
        elif self.metrics['cpu_usage'] <= 80.0 and self.alerts.get('high_cpu', False):
            self.alerts['high_cpu'] = False
            log_info("CPU使用率恢复正常")
        
        # 内存使用率警报
        if self.metrics['memory_usage'] > 85.0 and not self.alerts.get('high_memory', False):
            self.alerts['high_memory'] = True
            log_info(f"内存使用率过高: {self.metrics['memory_usage']:.1f}%")
        
        elif self.metrics['memory_usage'] <= 85.0 and self.alerts.get('high_memory', False):
            self.alerts['high_memory'] = False
            log_info("内存使用率恢复正常")
    
    def _call_update_callbacks(self):
        """调用更新回调函数"""
        for callback_name, callback in self.update_callbacks.items():
            try:
                callback(self.metrics)
            except Exception as e:
                log_error(f"状态监控回调函数执行失败: {callback_name}", e)
    
    def _log_performance_metrics(self):
        """记录性能指标日志"""
        # 每10次记录一次性能日志
        if len(self.history['cpu_usage']) % 10 == 0:
            log_performance(
                "SYSTEM_METRICS",
                0,  # 这里不记录具体耗时，只是定期记录
                f"CPU: {self.metrics['cpu_usage']:.1f}%, "
                f"内存: {self.metrics['memory_usage']:.1f}%, "
                f"磁盘: {self.metrics['disk_usage']:.1f}%"
            )
    
    def set_app_start_time(self):
        """设置应用启动时间"""
        self.metrics['app_start_time'] = time.time()
    
    def update_custom_metric(self, name: str, value: Any):
        """
        更新自定义指标
        
        Args:
            name: 指标名称
            value: 指标值
        """
        self.metrics['custom_metrics'][name] = value
        
        # 初始化历史数据（如果需要）
        if name not in self.history['custom_metrics']:
            self.history['custom_metrics'][name] = deque(maxlen=100)
        
        # 保存历史数据
        timestamp = datetime.now()
        self.history['custom_metrics'][name].append((timestamp, value))
    
    def get_metric(self, name: str) -> Any:
        """
        获取指标值
        
        Args:
            name: 指标名称
            
        Returns:
            指标值，如果不存在返回None
        """
        if name in self.metrics:
            return self.metrics[name]
        elif name in self.metrics['custom_metrics']:
            return self.metrics['custom_metrics'][name]
        else:
            return None
    
    def get_metric_history(self, name: str, hours: int = 24) -> list:
        """
        获取指标历史数据
        
        Args:
            name: 指标名称
            hours: 小时数，返回指定小时内的数据
            
        Returns:
            历史数据列表
        """
        if name not in self.history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history_data = []
        
        for timestamp, value in self.history[name]:
            if timestamp >= cutoff_time:
                history_data.append({
                    'timestamp': timestamp,
                    'value': value
                })
        
        return history_data
    
    def get_metric_statistics(self, name: str, hours: int = 24) -> Dict[str, Any]:
        """
        获取指标统计信息
        
        Args:
            name: 指标名称
            hours: 小时数，统计指定小时内的数据
            
        Returns:
            统计信息字典
        """
        history_data = self.get_metric_history(name, hours)
        
        if not history_data:
            return {}
        
        values = [item['value'] for item in history_data]
        
        return {
            'count': len(values),
            'min': min(values) if values else 0,
            'max': max(values) if values else 0,
            'avg': sum(values) / len(values) if values else 0,
            'latest': values[-1] if values else 0
        }
    
    def register_update_callback(self, name: str, callback: Callable):
        """
        注册指标更新回调函数
        
        Args:
            name: 回调函数名称
            callback: 回调函数，接收metrics字典作为参数
        """
        self.update_callbacks[name] = callback
        log_info(f"注册状态监控回调函数: {name}")
    
    def unregister_update_callback(self, name: str):
        """取消注册回调函数"""
        if name in self.update_callbacks:
            del self.update_callbacks[name]
            log_info(f"取消注册状态监控回调函数: {name}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            健康状态字典
        """
        return {
            'cpu_healthy': self.metrics['cpu_usage'] < 80.0,
            'memory_healthy': self.metrics['memory_usage'] < 85.0,
            'disk_healthy': self.metrics['disk_usage'] < 90.0,
            'overall_healthy': (
                self.metrics['cpu_usage'] < 80.0 and
                self.metrics['memory_usage'] < 85.0 and
                self.metrics['disk_usage'] < 90.0
            ),
            'alerts': self.alerts
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成状态报告
        
        Returns:
            状态报告字典
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                'cpu_usage': self.metrics['cpu_usage'],
                'memory_usage': self.metrics['memory_usage'],
                'disk_usage': self.metrics['disk_usage'],
                'app_uptime': self.metrics['app_uptime']
            },
            'health_status': self.get_system_health(),
            'statistics': {
                'cpu': self.get_metric_statistics('cpu_usage', 1),  # 最近1小时
                'memory': self.get_metric_statistics('memory_usage', 1),
                'disk': self.get_metric_statistics('disk_usage', 1)
            }
        }


# 全局状态监控器实例
_status_monitor: Optional[StatusMonitor] = None


def init_status_monitor() -> StatusMonitor:
    """
    初始化全局状态监控器
    
    Returns:
        StatusMonitor实例
    """
    global _status_monitor
    _status_monitor = StatusMonitor()
    return _status_monitor


def get_status_monitor() -> StatusMonitor:
    """
    获取全局状态监控器
    
    Returns:
        StatusMonitor实例
        
    Raises:
        RuntimeError: 状态监控器未初始化
    """
    global _status_monitor
    
    if _status_monitor is None:
        _status_monitor = StatusMonitor()
    
    return _status_monitor


def start_monitoring(interval: float = 5.0):
    """开始监控（便捷函数）"""
    get_status_monitor().start_monitoring(interval)


def stop_monitoring():
    """停止监控（便捷函数）"""
    get_status_monitor().stop_monitoring()


def update_custom_metric(name: str, value: Any):
    """更新自定义指标（便捷函数）"""
    get_status_monitor().update_custom_metric(name, value)


def get_system_health() -> Dict[str, Any]:
    """获取系统健康状态（便捷函数）"""
    return get_status_monitor().get_system_health()


def generate_report() -> Dict[str, Any]:
    """生成状态报告（便捷函数）"""
    return get_status_monitor().generate_report()


# 测试函数
def test_status_monitor():
    """测试状态监控器"""
    try:
        # 初始化状态监控器
        monitor = init_status_monitor()
        
        # 设置应用启动时间
        monitor.set_app_start_time()
        
        # 启动监控
        monitor.start_monitoring(interval=2.0)
        
        # 等待几秒钟收集数据
        import time
        time.sleep(6)
        
        # 获取系统健康状态
        health = monitor.get_system_health()
        print(f"系统健康状态: {health}")
        
        # 生成报告
        report = monitor.generate_report()
        print(f"状态报告: {report}")
        
        # 停止监控
        monitor.stop_monitoring()
        
        print("✓ 状态监控器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 状态监控器测试失败: {e}")
        return False


if __name__ == "__main__":
    test_status_monitor()
