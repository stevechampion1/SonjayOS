#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS - AI驱动安全模块
提供智能威胁检测、异常行为监控和数据保护功能
"""

import asyncio
import json
import logging
import time
import hashlib
import psutil
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """安全事件"""
    timestamp: float
    event_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    source: str
    description: str
    details: Dict[str, Any]
    risk_score: float  # 0-1

@dataclass
class ThreatPattern:
    """威胁模式"""
    pattern_id: str
    name: str
    description: str
    indicators: List[str]
    risk_level: str
    mitigation: str

class AISecurity:
    """AI驱动安全系统"""
    
    def __init__(self, config_path: str = "/etc/sonjayos/security/ai_security_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.security_events = []
        self.threat_patterns = []
        self.behavior_baseline = {}
        self.anomaly_detector = None
        self.is_monitoring = False
        
        # 性能统计
        self.stats = {
            "total_events": 0,
            "threats_detected": 0,
            "false_positives": 0,
            "response_time_avg": 0.0
        }
        
        self._init_threat_patterns()
        self._init_behavior_baseline()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载安全配置"""
        default_config = {
            "monitoring": {
                "enabled": True,
                "check_interval": 30,  # 秒
                "log_retention_days": 30
            },
            "threat_detection": {
                "cpu_threshold": 80.0,
                "memory_threshold": 85.0,
                "network_threshold": 1000,  # MB
                "file_access_threshold": 1000,  # 文件/分钟
                "process_threshold": 200  # 进程数
            },
            "ai_models": {
                "anomaly_detection": True,
                "behavior_analysis": True,
                "threat_classification": True
            },
            "alerts": {
                "email_notifications": False,
                "desktop_notifications": True,
                "log_file": "/var/log/sonjayos/security.log"
            },
            "encryption": {
                "enabled": True,
                "algorithm": "AES-256",
                "key_rotation_days": 30
            }
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"无法加载安全配置文件: {e}")
        
        return default_config
    
    def _init_threat_patterns(self):
        """初始化威胁模式"""
        self.threat_patterns = [
            ThreatPattern(
                pattern_id="cpu_anomaly",
                name="CPU异常使用",
                description="CPU使用率异常高，可能表示恶意软件或挖矿程序",
                indicators=["cpu_usage > 80%", "sustained_high_cpu"],
                risk_level="medium",
                mitigation="检查进程列表，终止可疑进程"
            ),
            ThreatPattern(
                pattern_id="memory_anomaly",
                name="内存异常使用",
                description="内存使用率异常高，可能表示内存泄漏或恶意软件",
                indicators=["memory_usage > 85%", "memory_leak"],
                risk_level="medium",
                mitigation="检查内存使用情况，重启相关服务"
            ),
            ThreatPattern(
                pattern_id="network_anomaly",
                name="网络异常活动",
                description="网络流量异常，可能表示数据泄露或DDoS攻击",
                indicators=["high_network_usage", "unusual_connections"],
                risk_level="high",
                mitigation="检查网络连接，阻止可疑IP"
            ),
            ThreatPattern(
                pattern_id="file_access_anomaly",
                name="文件访问异常",
                description="文件访问频率异常高，可能表示数据窃取",
                indicators=["high_file_access_rate", "sensitive_file_access"],
                risk_level="high",
                mitigation="检查文件访问日志，限制敏感文件权限"
            ),
            ThreatPattern(
                pattern_id="process_anomaly",
                name="进程异常",
                description="异常进程活动，可能表示恶意软件执行",
                indicators=["unknown_processes", "suspicious_process_names"],
                risk_level="critical",
                mitigation="终止可疑进程，扫描系统"
            ),
            ThreatPattern(
                pattern_id="login_anomaly",
                name="登录异常",
                description="异常登录活动，可能表示账户被攻击",
                indicators=["failed_logins", "unusual_login_times", "multiple_ips"],
                risk_level="high",
                mitigation="检查登录日志，加强认证"
            )
        ]
    
    def _init_behavior_baseline(self):
        """初始化行为基线"""
        self.behavior_baseline = {
            "cpu_usage": [],
            "memory_usage": [],
            "network_usage": [],
            "file_access_rate": [],
            "process_count": [],
            "login_attempts": []
        }
    
    async def initialize(self) -> bool:
        """初始化安全系统"""
        try:
            # 创建日志目录
            log_dir = Path("/var/log/sonjayos")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 初始化异常检测器
            await self._init_anomaly_detector()
            
            # 开始监控
            if self.config["monitoring"]["enabled"]:
                await self._start_monitoring()
            
            logger.info("AI安全系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"安全系统初始化失败: {e}")
            return False
    
    async def _init_anomaly_detector(self):
        """初始化异常检测器"""
        try:
            # 这里可以集成机器学习模型进行异常检测
            # 目前使用基于统计的方法
            self.anomaly_detector = {
                "cpu_threshold": self.config["threat_detection"]["cpu_threshold"],
                "memory_threshold": self.config["threat_detection"]["memory_threshold"],
                "network_threshold": self.config["threat_detection"]["network_threshold"],
                "file_access_threshold": self.config["threat_detection"]["file_access_threshold"],
                "process_threshold": self.config["threat_detection"]["process_threshold"]
            }
            
        except Exception as e:
            logger.error(f"初始化异常检测器失败: {e}")
    
    async def _start_monitoring(self):
        """开始安全监控"""
        self.is_monitoring = True
        
        # 启动监控任务
        asyncio.create_task(self._monitor_system_resources())
        asyncio.create_task(self._monitor_network_activity())
        asyncio.create_task(self._monitor_file_access())
        asyncio.create_task(self._monitor_processes())
        asyncio.create_task(self._monitor_login_activity())
        asyncio.create_task(self._analyze_behavior_patterns())
        
        logger.info("安全监控已启动")
    
    async def _monitor_system_resources(self):
        """监控系统资源"""
        while self.is_monitoring:
            try:
                # 获取CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # 获取内存使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # 检查阈值
                if cpu_percent > self.anomaly_detector["cpu_threshold"]:
                    await self._detect_threat("cpu_anomaly", {
                        "cpu_usage": cpu_percent,
                        "threshold": self.anomaly_detector["cpu_threshold"]
                    })
                
                if memory_percent > self.anomaly_detector["memory_threshold"]:
                    await self._detect_threat("memory_anomaly", {
                        "memory_usage": memory_percent,
                        "threshold": self.anomaly_detector["memory_threshold"]
                    })
                
                # 更新基线
                self.behavior_baseline["cpu_usage"].append(cpu_percent)
                self.behavior_baseline["memory_usage"].append(memory_percent)
                
                # 保持基线数据在合理范围内
                for key in ["cpu_usage", "memory_usage"]:
                    if len(self.behavior_baseline[key]) > 1000:
                        self.behavior_baseline[key] = self.behavior_baseline[key][-500:]
                
                await asyncio.sleep(self.config["monitoring"]["check_interval"])
                
            except Exception as e:
                logger.error(f"监控系统资源失败: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_network_activity(self):
        """监控网络活动"""
        while self.is_monitoring:
            try:
                # 获取网络统计信息
                net_io = psutil.net_io_counters()
                network_usage = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # MB
                
                # 检查网络使用量
                if network_usage > self.anomaly_detector["network_threshold"]:
                    await self._detect_threat("network_anomaly", {
                        "network_usage": network_usage,
                        "threshold": self.anomaly_detector["network_threshold"]
                    })
                
                # 检查网络连接
                connections = psutil.net_connections()
                suspicious_connections = []
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED':
                        # 检查可疑端口
                        if conn.laddr.port in [22, 23, 3389, 5900]:  # SSH, Telnet, RDP, VNC
                            suspicious_connections.append(conn)
                
                if len(suspicious_connections) > 10:  # 超过10个可疑连接
                    await self._detect_threat("network_anomaly", {
                        "suspicious_connections": len(suspicious_connections),
                        "connections": suspicious_connections
                    })
                
                # 更新基线
                self.behavior_baseline["network_usage"].append(network_usage)
                
                await asyncio.sleep(self.config["monitoring"]["check_interval"])
                
            except Exception as e:
                logger.error(f"监控网络活动失败: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_file_access(self):
        """监控文件访问"""
        while self.is_monitoring:
            try:
                # 获取文件访问统计
                file_access_count = 0
                sensitive_files = ["/etc/passwd", "/etc/shadow", "/etc/sudoers"]
                
                # 检查敏感文件访问
                for file_path in sensitive_files:
                    if Path(file_path).exists():
                        # 这里可以检查文件访问日志
                        pass
                
                # 模拟文件访问监控
                file_access_count = len(list(Path("/tmp").glob("*")))
                
                if file_access_count > self.anomaly_detector["file_access_threshold"]:
                    await self._detect_threat("file_access_anomaly", {
                        "file_access_count": file_access_count,
                        "threshold": self.anomaly_detector["file_access_threshold"]
                    })
                
                # 更新基线
                self.behavior_baseline["file_access_rate"].append(file_access_count)
                
                await asyncio.sleep(self.config["monitoring"]["check_interval"])
                
            except Exception as e:
                logger.error(f"监控文件访问失败: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_processes(self):
        """监控进程活动"""
        while self.is_monitoring:
            try:
                # 获取进程列表
                processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
                process_count = len(processes)
                
                # 检查进程数量
                if process_count > self.anomaly_detector["process_threshold"]:
                    await self._detect_threat("process_anomaly", {
                        "process_count": process_count,
                        "threshold": self.anomaly_detector["process_threshold"]
                    })
                
                # 检查可疑进程
                suspicious_processes = []
                suspicious_names = ["miner", "crypto", "bitcoin", "monero", "xmrig", "cpuminer"]
                
                for proc in processes:
                    try:
                        proc_info = proc.info
                        proc_name = proc_info['name'].lower()
                        
                        # 检查可疑进程名
                        if any(suspicious in proc_name for suspicious in suspicious_names):
                            suspicious_processes.append(proc_info)
                        
                        # 检查高CPU/内存使用进程
                        if (proc_info['cpu_percent'] > 50 or 
                            proc_info['memory_percent'] > 20):
                            suspicious_processes.append(proc_info)
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if suspicious_processes:
                    await self._detect_threat("process_anomaly", {
                        "suspicious_processes": suspicious_processes,
                        "count": len(suspicious_processes)
                    })
                
                # 更新基线
                self.behavior_baseline["process_count"].append(process_count)
                
                await asyncio.sleep(self.config["monitoring"]["check_interval"])
                
            except Exception as e:
                logger.error(f"监控进程活动失败: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_login_activity(self):
        """监控登录活动"""
        while self.is_monitoring:
            try:
                # 检查登录日志
                # 这里可以解析/var/log/auth.log等文件
                # 目前使用模拟数据
                failed_logins = 0
                unusual_logins = 0
                
                # 模拟登录监控
                if time.time() % 300 < 30:  # 每5分钟模拟一次检查
                    failed_logins = np.random.randint(0, 5)
                    unusual_logins = np.random.randint(0, 3)
                
                if failed_logins > 3:
                    await self._detect_threat("login_anomaly", {
                        "failed_logins": failed_logins,
                        "type": "brute_force"
                    })
                
                if unusual_logins > 2:
                    await self._detect_threat("login_anomaly", {
                        "unusual_logins": unusual_logins,
                        "type": "suspicious_activity"
                    })
                
                # 更新基线
                self.behavior_baseline["login_attempts"].append(failed_logins + unusual_logins)
                
                await asyncio.sleep(self.config["monitoring"]["check_interval"])
                
            except Exception as e:
                logger.error(f"监控登录活动失败: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_behavior_patterns(self):
        """分析行为模式"""
        while self.is_monitoring:
            try:
                # 分析行为基线，检测异常模式
                for metric, values in self.behavior_baseline.items():
                    if len(values) > 10:
                        # 计算统计指标
                        mean_val = np.mean(values)
                        std_val = np.std(values)
                        
                        # 检测异常值
                        for i, value in enumerate(values[-10:]):  # 检查最近10个值
                            if abs(value - mean_val) > 2 * std_val:
                                await self._detect_threat(f"{metric}_anomaly", {
                                    "metric": metric,
                                    "value": value,
                                    "mean": mean_val,
                                    "std": std_val,
                                    "z_score": abs(value - mean_val) / std_val
                                })
                
                await asyncio.sleep(300)  # 每5分钟分析一次
                
            except Exception as e:
                logger.error(f"分析行为模式失败: {e}")
                await asyncio.sleep(300)
    
    async def _detect_threat(self, threat_type: str, details: Dict[str, Any]):
        """检测威胁"""
        try:
            # 查找威胁模式
            pattern = next((p for p in self.threat_patterns if p.pattern_id == threat_type), None)
            
            if not pattern:
                logger.warning(f"未知威胁类型: {threat_type}")
                return
            
            # 计算风险评分
            risk_score = self._calculate_risk_score(threat_type, details)
            
            # 创建安全事件
            event = SecurityEvent(
                timestamp=time.time(),
                event_type=threat_type,
                severity=self._get_severity(risk_score),
                source="ai_security",
                description=pattern.description,
                details=details,
                risk_score=risk_score
            )
            
            # 记录事件
            self.security_events.append(event)
            self.stats["total_events"] += 1
            self.stats["threats_detected"] += 1
            
            # 记录日志
            await self._log_security_event(event)
            
            # 发送警报
            await self._send_alert(event)
            
            # 执行缓解措施
            await self._execute_mitigation(event, pattern)
            
            logger.warning(f"检测到威胁: {threat_type}, 风险评分: {risk_score:.2f}")
            
        except Exception as e:
            logger.error(f"威胁检测失败: {e}")
    
    def _calculate_risk_score(self, threat_type: str, details: Dict[str, Any]) -> float:
        """计算风险评分"""
        base_scores = {
            "cpu_anomaly": 0.6,
            "memory_anomaly": 0.5,
            "network_anomaly": 0.8,
            "file_access_anomaly": 0.7,
            "process_anomaly": 0.9,
            "login_anomaly": 0.8
        }
        
        base_score = base_scores.get(threat_type, 0.5)
        
        # 根据详细信息调整评分
        if "cpu_usage" in details:
            cpu_usage = details["cpu_usage"]
            if cpu_usage > 95:
                base_score += 0.2
            elif cpu_usage > 90:
                base_score += 0.1
        
        if "memory_usage" in details:
            memory_usage = details["memory_usage"]
            if memory_usage > 95:
                base_score += 0.2
            elif memory_usage > 90:
                base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _get_severity(self, risk_score: float) -> str:
        """获取严重程度"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    async def _log_security_event(self, event: SecurityEvent):
        """记录安全事件"""
        try:
            log_entry = {
                "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
                "event_type": event.event_type,
                "severity": event.severity,
                "source": event.source,
                "description": event.description,
                "risk_score": event.risk_score,
                "details": event.details
            }
            
            # 写入日志文件
            log_file = self.config["alerts"]["log_file"]
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
        except Exception as e:
            logger.error(f"记录安全事件失败: {e}")
    
    async def _send_alert(self, event: SecurityEvent):
        """发送警报"""
        try:
            if self.config["alerts"]["desktop_notifications"]:
                # 发送桌面通知
                subprocess.run([
                    'notify-send',
                    f'SonjayOS安全警报 - {event.severity.upper()}',
                    f'{event.description}\n风险评分: {event.risk_score:.2f}',
                    '--urgency=critical' if event.severity == 'critical' else '--urgency=normal'
                ])
            
            if self.config["alerts"]["email_notifications"]:
                # 发送邮件通知
                await self._send_email_alert(event)
                
        except Exception as e:
            logger.error(f"发送警报失败: {e}")
    
    async def _send_email_alert(self, event: SecurityEvent):
        """发送邮件警报"""
        # 这里可以实现邮件发送功能
        pass
    
    async def _execute_mitigation(self, event: SecurityEvent, pattern: ThreatPattern):
        """执行缓解措施"""
        try:
            if event.severity in ["high", "critical"]:
                if event.event_type == "process_anomaly":
                    # 终止可疑进程
                    await self._terminate_suspicious_processes(event.details.get("suspicious_processes", []))
                
                elif event.event_type == "network_anomaly":
                    # 阻止可疑网络连接
                    await self._block_suspicious_connections(event.details.get("suspicious_connections", []))
                
                elif event.event_type == "login_anomaly":
                    # 加强认证
                    await self._strengthen_authentication()
            
            logger.info(f"执行缓解措施: {pattern.mitigation}")
            
        except Exception as e:
            logger.error(f"执行缓解措施失败: {e}")
    
    async def _terminate_suspicious_processes(self, processes: List[Dict[str, Any]]):
        """终止可疑进程"""
        for proc_info in processes:
            try:
                pid = proc_info['pid']
                subprocess.run(['kill', '-9', str(pid)])
                logger.info(f"已终止可疑进程: PID {pid}")
            except Exception as e:
                logger.error(f"终止进程失败: {e}")
    
    async def _block_suspicious_connections(self, connections: List[Any]):
        """阻止可疑连接"""
        # 这里可以实现网络连接阻止功能
        pass
    
    async def _strengthen_authentication(self):
        """加强认证"""
        # 这里可以实现认证加强功能
        pass
    
    async def get_security_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        return {
            "monitoring_enabled": self.is_monitoring,
            "total_events": self.stats["total_events"],
            "threats_detected": self.stats["threats_detected"],
            "recent_events": self.security_events[-10:] if self.security_events else [],
            "behavior_baseline_size": {k: len(v) for k, v in self.behavior_baseline.items()},
            "threat_patterns_count": len(self.threat_patterns)
        }
    
    async def get_threat_report(self, hours: int = 24) -> Dict[str, Any]:
        """获取威胁报告"""
        cutoff_time = time.time() - (hours * 3600)
        recent_events = [e for e in self.security_events if e.timestamp >= cutoff_time]
        
        # 统计威胁类型
        threat_counts = {}
        severity_counts = {}
        
        for event in recent_events:
            threat_counts[event.event_type] = threat_counts.get(event.event_type, 0) + 1
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
        
        return {
            "time_range_hours": hours,
            "total_events": len(recent_events),
            "threat_type_distribution": threat_counts,
            "severity_distribution": severity_counts,
            "average_risk_score": np.mean([e.risk_score for e in recent_events]) if recent_events else 0,
            "events": recent_events
        }
    
    async def cleanup(self):
        """清理资源"""
        self.is_monitoring = False
        self.security_events.clear()
        self.behavior_baseline.clear()
        logger.info("AI安全系统清理完成")

# 全局实例
ai_security = AISecurity()

async def main():
    """主函数 - 用于测试"""
    security = AISecurity()
    
    # 初始化
    if await security.initialize():
        print("✅ AI安全系统初始化成功")
        
        # 获取安全状态
        status = await security.get_security_status()
        print(f"🔒 安全状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 获取威胁报告
        report = await security.get_threat_report(24)
        print(f"📊 威胁报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
        
        # 清理
        await security.cleanup()
    else:
        print("❌ AI安全系统初始化失败")

if __name__ == "__main__":
    asyncio.run(main())
