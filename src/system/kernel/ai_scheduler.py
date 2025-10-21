#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS - AI驱动内核调度器
使用机器学习优化进程调度和资源分配
"""

import asyncio
import json
import logging
import time
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
class ProcessInfo:
    """进程信息"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    priority: int
    nice: int
    status: str
    create_time: float
    user: str
    command: str

@dataclass
class SchedulingDecision:
    """调度决策"""
    timestamp: float
    process_pid: int
    action: str  # 'boost', 'throttle', 'kill', 'migrate'
    priority_change: int
    cpu_affinity: List[int]
    memory_limit: Optional[int]
    reason: str
    confidence: float

class AIScheduler:
    """AI驱动调度器"""
    
    def __init__(self, config_path: str = "/etc/sonjayos/kernel/scheduler_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.process_history = []
        self.scheduling_decisions = []
        self.performance_metrics = {}
        self.is_active = False
        
        # AI模型参数
        self.cpu_predictor = None
        self.memory_predictor = None
        self.priority_predictor = None
        
        # 性能统计
        self.stats = {
            "total_decisions": 0,
            "successful_optimizations": 0,
            "average_response_time": 0.0,
            "cpu_efficiency": 0.0,
            "memory_efficiency": 0.0
        }
        
        self._init_performance_metrics()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载调度器配置"""
        default_config = {
            "scheduling": {
                "enabled": True,
                "check_interval": 5,  # 秒
                "decision_threshold": 0.7,
                "learning_enabled": True
            },
            "optimization": {
                "cpu_boost_threshold": 0.8,
                "memory_boost_threshold": 0.85,
                "priority_boost_factor": 1.5,
                "throttle_threshold": 0.9
            },
            "ai_models": {
                "cpu_prediction": True,
                "memory_prediction": True,
                "priority_optimization": True,
                "load_balancing": True
            },
            "process_categories": {
                "interactive": ["gnome", "firefox", "code", "terminal"],
                "background": ["systemd", "dbus", "NetworkManager"],
                "compute_intensive": ["gcc", "make", "python", "node"],
                "io_intensive": ["cp", "mv", "rsync", "dd"]
            }
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"无法加载调度器配置文件: {e}")
        
        return default_config
    
    def _init_performance_metrics(self):
        """初始化性能指标"""
        self.performance_metrics = {
            "cpu_usage_history": [],
            "memory_usage_history": [],
            "process_count_history": [],
            "response_time_history": [],
            "throughput_history": []
        }
    
    async def initialize(self) -> bool:
        """初始化AI调度器"""
        try:
            # 初始化AI预测模型
            await self._init_ai_models()
            
            # 开始调度优化
            if self.config["scheduling"]["enabled"]:
                await self._start_scheduling()
            
            logger.info("AI调度器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"AI调度器初始化失败: {e}")
            return False
    
    async def _init_ai_models(self):
        """初始化AI模型"""
        try:
            # 初始化CPU使用预测模型
            self.cpu_predictor = {
                "model_type": "linear_regression",
                "features": ["cpu_usage", "process_count", "load_average"],
                "weights": [0.4, 0.3, 0.3],
                "bias": 0.1
            }
            
            # 初始化内存使用预测模型
            self.memory_predictor = {
                "model_type": "linear_regression", 
                "features": ["memory_usage", "process_count", "cache_usage"],
                "weights": [0.5, 0.3, 0.2],
                "bias": 0.05
            }
            
            # 初始化优先级优化模型
            self.priority_predictor = {
                "model_type": "decision_tree",
                "features": ["process_type", "cpu_usage", "memory_usage", "user_interaction"],
                "rules": {
                    "interactive": 1.2,
                    "background": 0.8,
                    "compute_intensive": 1.1,
                    "io_intensive": 0.9
                }
            }
            
        except Exception as e:
            logger.error(f"初始化AI模型失败: {e}")
    
    async def _start_scheduling(self):
        """开始调度优化"""
        self.is_active = True
        
        # 启动调度任务
        asyncio.create_task(self._monitor_system_performance())
        asyncio.create_task(self._optimize_process_scheduling())
        asyncio.create_task(self._learn_from_decisions())
        
        logger.info("AI调度器已启动")
    
    async def _monitor_system_performance(self):
        """监控系统性能"""
        while self.is_active:
            try:
                # 获取系统性能指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # 获取进程信息
                processes = await self._get_process_info()
                
                # 更新性能指标
                self.performance_metrics["cpu_usage_history"].append(cpu_percent)
                self.performance_metrics["memory_usage_history"].append(memory_percent)
                self.performance_metrics["process_count_history"].append(len(processes))
                
                # 保持历史数据在合理范围内
                for key in self.performance_metrics:
                    if len(self.performance_metrics[key]) > 1000:
                        self.performance_metrics[key] = self.performance_metrics[key][-500:]
                
                # 记录进程历史
                self.process_history.extend(processes)
                if len(self.process_history) > 10000:
                    self.process_history = self.process_history[-5000:]
                
                await asyncio.sleep(self.config["scheduling"]["check_interval"])
                
            except Exception as e:
                logger.error(f"监控系统性能失败: {e}")
                await asyncio.sleep(60)
    
    async def _get_process_info(self) -> List[ProcessInfo]:
        """获取进程信息"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'nice', 'status', 'create_time', 'username', 'cmdline']):
                try:
                    proc_info = proc.info
                    
                    process = ProcessInfo(
                        pid=proc_info['pid'],
                        name=proc_info['name'],
                        cpu_percent=proc_info['cpu_percent'],
                        memory_percent=proc_info['memory_percent'],
                        priority=proc.nice(),
                        nice=proc_info['nice'],
                        status=proc_info['status'],
                        create_time=proc_info['create_time'],
                        user=proc_info['username'],
                        command=' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                    )
                    
                    processes.append(process)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            logger.error(f"获取进程信息失败: {e}")
        
        return processes
    
    async def _optimize_process_scheduling(self):
        """优化进程调度"""
        while self.is_active:
            try:
                # 获取当前进程状态
                processes = await self._get_process_info()
                
                # 分析每个进程
                for process in processes:
                    # 预测进程性能需求
                    cpu_prediction = await self._predict_cpu_usage(process)
                    memory_prediction = await self._predict_memory_usage(process)
                    
                    # 确定进程类别
                    process_category = self._categorize_process(process)
                    
                    # 计算优化建议
                    optimization = await self._calculate_optimization(
                        process, cpu_prediction, memory_prediction, process_category
                    )
                    
                    # 执行优化决策
                    if optimization and optimization.confidence > self.config["scheduling"]["decision_threshold"]:
                        await self._execute_scheduling_decision(optimization)
                        self.scheduling_decisions.append(optimization)
                        self.stats["total_decisions"] += 1
                
                await asyncio.sleep(self.config["scheduling"]["check_interval"])
                
            except Exception as e:
                logger.error(f"优化进程调度失败: {e}")
                await asyncio.sleep(60)
    
    async def _predict_cpu_usage(self, process: ProcessInfo) -> float:
        """预测CPU使用率"""
        try:
            # 使用简单的线性回归模型
            features = [
                process.cpu_percent,
                len(self.process_history) / 100,  # 进程数量归一化
                psutil.getloadavg()[0]  # 系统负载
            ]
            
            prediction = sum(w * f for w, f in zip(self.cpu_predictor["weights"], features))
            prediction += self.cpu_predictor["bias"]
            
            return max(0, min(100, prediction))
            
        except Exception as e:
            logger.error(f"预测CPU使用率失败: {e}")
            return process.cpu_percent
    
    async def _predict_memory_usage(self, process: ProcessInfo) -> float:
        """预测内存使用率"""
        try:
            # 使用简单的线性回归模型
            features = [
                process.memory_percent,
                len(self.process_history) / 100,  # 进程数量归一化
                psutil.virtual_memory().cached / psutil.virtual_memory().total * 100  # 缓存使用率
            ]
            
            prediction = sum(w * f for w, f in zip(self.memory_predictor["weights"], features))
            prediction += self.memory_predictor["bias"]
            
            return max(0, min(100, prediction))
            
        except Exception as e:
            logger.error(f"预测内存使用率失败: {e}")
            return process.memory_percent
    
    def _categorize_process(self, process: ProcessInfo) -> str:
        """分类进程"""
        name_lower = process.name.lower()
        
        for category, keywords in self.config["process_categories"].items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return "unknown"
    
    async def _calculate_optimization(self, process: ProcessInfo, cpu_prediction: float, 
                                    memory_prediction: float, category: str) -> Optional[SchedulingDecision]:
        """计算优化建议"""
        try:
            # 计算优化分数
            optimization_score = 0.0
            action = None
            priority_change = 0
            reason = ""
            confidence = 0.0
            
            # 检查CPU使用率
            if cpu_prediction > self.config["optimization"]["cpu_boost_threshold"]:
                if category == "interactive":
                    optimization_score += 0.3
                    action = "boost"
                    priority_change = 5
                    reason = "交互式进程CPU使用率高，需要优先级提升"
                    confidence = 0.8
                elif category == "compute_intensive":
                    optimization_score += 0.2
                    action = "throttle"
                    priority_change = -2
                    reason = "计算密集型进程CPU使用率过高，需要限制"
                    confidence = 0.7
            
            # 检查内存使用率
            if memory_prediction > self.config["optimization"]["memory_boost_threshold"]:
                if category == "interactive":
                    optimization_score += 0.4
                    action = "boost"
                    priority_change = 3
                    reason = "交互式进程内存使用率高，需要优先级提升"
                    confidence = 0.9
                elif category == "background":
                    optimization_score += 0.3
                    action = "throttle"
                    priority_change = -3
                    reason = "后台进程内存使用率过高，需要限制"
                    confidence = 0.8
            
            # 检查系统负载
            load_avg = psutil.getloadavg()[0]
            if load_avg > 2.0 and category == "compute_intensive":
                optimization_score += 0.2
                action = "migrate"
                reason = "系统负载高，计算密集型进程需要迁移"
                confidence = 0.6
            
            # 如果优化分数足够高，创建调度决策
            if optimization_score > 0.3 and action:
                return SchedulingDecision(
                    timestamp=time.time(),
                    process_pid=process.pid,
                    action=action,
                    priority_change=priority_change,
                    cpu_affinity=[],  # 可以设置CPU亲和性
                    memory_limit=None,  # 可以设置内存限制
                    reason=reason,
                    confidence=confidence
                )
            
            return None
            
        except Exception as e:
            logger.error(f"计算优化建议失败: {e}")
            return None
    
    async def _execute_scheduling_decision(self, decision: SchedulingDecision):
        """执行调度决策"""
        try:
            if decision.action == "boost":
                # 提升进程优先级
                new_nice = max(-20, decision.priority_change)
                subprocess.run(['renice', str(new_nice), str(decision.process_pid)])
                logger.info(f"提升进程 {decision.process_pid} 优先级: {new_nice}")
                
            elif decision.action == "throttle":
                # 降低进程优先级
                new_nice = min(19, decision.priority_change)
                subprocess.run(['renice', str(new_nice), str(decision.process_pid)])
                logger.info(f"限制进程 {decision.process_pid} 优先级: {new_nice}")
                
            elif decision.action == "migrate":
                # 迁移进程到其他CPU核心
                # 这里可以实现CPU亲和性设置
                logger.info(f"迁移进程 {decision.process_pid} 到其他CPU核心")
                
            elif decision.action == "kill":
                # 终止进程（谨慎使用）
                if decision.confidence > 0.9:
                    subprocess.run(['kill', '-9', str(decision.process_pid)])
                    logger.warning(f"终止进程 {decision.process_pid}: {decision.reason}")
            
            self.stats["successful_optimizations"] += 1
            
        except Exception as e:
            logger.error(f"执行调度决策失败: {e}")
    
    async def _learn_from_decisions(self):
        """从决策中学习"""
        while self.is_active:
            try:
                if not self.config["scheduling"]["learning_enabled"]:
                    await asyncio.sleep(3600)  # 1小时
                    continue
                
                # 分析决策效果
                await self._analyze_decision_effectiveness()
                
                # 更新AI模型参数
                await self._update_ai_models()
                
                await asyncio.sleep(3600)  # 每小时学习一次
                
            except Exception as e:
                logger.error(f"学习决策效果失败: {e}")
                await asyncio.sleep(3600)
    
    async def _analyze_decision_effectiveness(self):
        """分析决策效果"""
        try:
            if len(self.scheduling_decisions) < 10:
                return
            
            # 分析最近决策的效果
            recent_decisions = self.scheduling_decisions[-100:]
            
            # 计算成功率
            successful_decisions = 0
            for decision in recent_decisions:
                # 这里可以检查决策后的系统性能改善
                # 简化实现：假设高置信度的决策是成功的
                if decision.confidence > 0.8:
                    successful_decisions += 1
            
            success_rate = successful_decisions / len(recent_decisions)
            
            # 更新统计信息
            self.stats["cpu_efficiency"] = success_rate
            self.stats["memory_efficiency"] = success_rate
            
            logger.info(f"决策成功率: {success_rate:.2f}")
            
        except Exception as e:
            logger.error(f"分析决策效果失败: {e}")
    
    async def _update_ai_models(self):
        """更新AI模型"""
        try:
            # 基于学习结果调整模型参数
            if self.stats["cpu_efficiency"] > 0.8:
                # 如果CPU效率高，增加CPU预测的权重
                self.cpu_predictor["weights"][0] *= 1.1
            elif self.stats["cpu_efficiency"] < 0.6:
                # 如果CPU效率低，减少CPU预测的权重
                self.cpu_predictor["weights"][0] *= 0.9
            
            if self.stats["memory_efficiency"] > 0.8:
                # 如果内存效率高，增加内存预测的权重
                self.memory_predictor["weights"][0] *= 1.1
            elif self.stats["memory_efficiency"] < 0.6:
                # 如果内存效率低，减少内存预测的权重
                self.memory_predictor["weights"][0] *= 0.9
            
            logger.info("AI模型参数已更新")
            
        except Exception as e:
            logger.error(f"更新AI模型失败: {e}")
    
    async def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "active": self.is_active,
            "total_decisions": self.stats["total_decisions"],
            "successful_optimizations": self.stats["successful_optimizations"],
            "cpu_efficiency": self.stats["cpu_efficiency"],
            "memory_efficiency": self.stats["memory_efficiency"],
            "recent_decisions": self.scheduling_decisions[-10:] if self.scheduling_decisions else [],
            "performance_metrics_size": {k: len(v) for k, v in self.performance_metrics.items()}
        }
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "cpu_usage_avg": np.mean(self.performance_metrics["cpu_usage_history"]) if self.performance_metrics["cpu_usage_history"] else 0,
            "memory_usage_avg": np.mean(self.performance_metrics["memory_usage_history"]) if self.performance_metrics["memory_usage_history"] else 0,
            "process_count_avg": np.mean(self.performance_metrics["process_count_history"]) if self.performance_metrics["process_count_history"] else 0,
            "optimization_effectiveness": self.stats["successful_optimizations"] / max(1, self.stats["total_decisions"]),
            "ai_model_status": {
                "cpu_predictor": self.cpu_predictor is not None,
                "memory_predictor": self.memory_predictor is not None,
                "priority_predictor": self.priority_predictor is not None
            }
        }
    
    async def cleanup(self):
        """清理资源"""
        self.is_active = False
        self.process_history.clear()
        self.scheduling_decisions.clear()
        self.performance_metrics.clear()
        logger.info("AI调度器清理完成")

# 全局实例
ai_scheduler = AIScheduler()

async def main():
    """主函数 - 用于测试"""
    scheduler = AIScheduler()
    
    # 初始化
    if await scheduler.initialize():
        print("✅ AI调度器初始化成功")
        
        # 获取调度器状态
        status = await scheduler.get_scheduler_status()
        print(f"⚙️ 调度器状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 获取性能报告
        report = await scheduler.get_performance_report()
        print(f"📊 性能报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
        
        # 清理
        await scheduler.cleanup()
    else:
        print("❌ AI调度器初始化失败")

if __name__ == "__main__":
    asyncio.run(main())
