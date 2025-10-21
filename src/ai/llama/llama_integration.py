#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS - Llama 3.1 模型集成模块
提供本地AI推理服务，支持自然语言处理和系统交互
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import requests
import psutil
from pydantic import BaseModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """AI模型配置"""
    name: str
    size: str
    memory_usage: int  # MB
    inference_speed: float  # tokens/second
    quality_score: float  # 0-1

class LlamaRequest(BaseModel):
    """Llama请求模型"""
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    stream: bool = False

class LlamaResponse(BaseModel):
    """Llama响应模型"""
    response: str
    tokens_used: int
    inference_time: float
    model_used: str

class LlamaIntegration:
    """Llama 3.1 模型集成类"""
    
    def __init__(self, config_path: str = "/etc/sonjayos/ai/llama_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.current_model = None
        self.ollama_process = None
        self.model_cache = {}
        self.performance_metrics = {
            "total_requests": 0,
            "average_response_time": 0.0,
            "cache_hit_rate": 0.0
        }
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "models": {
                "llama3.1-8b": {
                    "name": "llama3.1:8b",
                    "size": "8B",
                    "memory_usage": 8000,
                    "inference_speed": 50.0,
                    "quality_score": 0.85
                },
                "llama3.1-70b": {
                    "name": "llama3.1:70b", 
                    "size": "70B",
                    "memory_usage": 40000,
                    "inference_speed": 15.0,
                    "quality_score": 0.95
                }
            },
            "default_model": "llama3.1-8b",
            "ollama_host": "http://localhost:11434",
            "max_memory_usage": 0.8,  # 80% of available RAM
            "cache_size": 1000,
            "auto_model_switching": True
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"无法加载配置文件: {e}")
                
        return default_config
    
    async def initialize(self) -> bool:
        """初始化AI服务"""
        try:
            # 检查Ollama是否运行
            if not await self._check_ollama_status():
                logger.info("启动Ollama服务...")
                await self._start_ollama()
                
            # 加载默认模型
            default_model = self.config["default_model"]
            await self._load_model(default_model)
            
            logger.info("Llama集成初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def _check_ollama_status(self) -> bool:
        """检查Ollama服务状态"""
        try:
            response = requests.get(f"{self.config['ollama_host']}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def _start_ollama(self):
        """启动Ollama服务"""
        try:
            # 检查系统资源
            available_memory = psutil.virtual_memory().available / (1024**3)  # GB
            if available_memory < 8:
                logger.warning("可用内存不足，建议至少8GB内存")
            
            # 启动Ollama进程
            self.ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服务启动
            for _ in range(30):  # 最多等待30秒
                if await self._check_ollama_status():
                    break
                await asyncio.sleep(1)
            else:
                raise Exception("Ollama服务启动超时")
                
        except Exception as e:
            logger.error(f"启动Ollama失败: {e}")
            raise
    
    async def _load_model(self, model_name: str) -> bool:
        """加载指定的AI模型"""
        try:
            model_config = self.config["models"].get(model_name)
            if not model_config:
                logger.error(f"未找到模型配置: {model_name}")
                return False
            
            # 检查内存是否足够
            if not self._check_memory_availability(model_config["memory_usage"]):
                logger.warning(f"内存不足，无法加载模型: {model_name}")
                return False
            
            # 拉取模型（如果不存在）
            await self._pull_model(model_config["name"])
            
            self.current_model = model_name
            logger.info(f"模型加载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False
    
    async def _pull_model(self, model_name: str):
        """拉取模型文件"""
        try:
            response = requests.post(
                f"{self.config['ollama_host']}/api/pull",
                json={"name": model_name},
                timeout=300  # 5分钟超时
            )
            response.raise_for_status()
            logger.info(f"模型拉取完成: {model_name}")
        except Exception as e:
            logger.error(f"拉取模型失败: {e}")
            raise
    
    def _check_memory_availability(self, required_memory: int) -> bool:
        """检查内存可用性"""
        available_memory = psutil.virtual_memory().available / (1024**2)  # MB
        max_usage = psutil.virtual_memory().total * self.config["max_memory_usage"] / (1024**2)
        
        return available_memory >= required_memory and required_memory <= max_usage
    
    async def generate_response(self, request: LlamaRequest) -> LlamaResponse:
        """生成AI响应"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(request)
            if cache_key in self.model_cache:
                cached_response = self.model_cache[cache_key]
                self.performance_metrics["cache_hit_rate"] += 1
                logger.info("使用缓存响应")
                return cached_response
            
            # 自动模型切换
            if self.config["auto_model_switching"]:
                await self._auto_switch_model(request)
            
            # 发送请求到Ollama
            response_data = await self._send_ollama_request(request)
            
            # 计算性能指标
            inference_time = time.time() - start_time
            tokens_used = len(response_data["response"].split())
            
            # 创建响应对象
            response = LlamaResponse(
                response=response_data["response"],
                tokens_used=tokens_used,
                inference_time=inference_time,
                model_used=self.current_model
            )
            
            # 更新缓存
            self._update_cache(cache_key, response)
            
            # 更新性能指标
            self._update_performance_metrics(inference_time)
            
            return response
            
        except Exception as e:
            logger.error(f"生成响应失败: {e}")
            raise
    
    async def _auto_switch_model(self, request: LlamaRequest):
        """根据请求自动切换模型"""
        prompt_length = len(request.prompt.split())
        
        # 根据提示长度和复杂度选择模型
        if prompt_length > 1000 or "复杂" in request.prompt:
            target_model = "llama3.1-70b"
        else:
            target_model = "llama3.1-8b"
        
        if target_model != self.current_model:
            await self._load_model(target_model)
    
    async def _send_ollama_request(self, request: LlamaRequest) -> Dict[str, Any]:
        """发送请求到Ollama API"""
        payload = {
            "model": self.config["models"][self.current_model]["name"],
            "prompt": request.prompt,
            "stream": request.stream,
            "options": {
                "num_predict": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p
            }
        }
        
        response = requests.post(
            f"{self.config['ollama_host']}/api/generate",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        return response.json()
    
    def _generate_cache_key(self, request: LlamaRequest) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{request.prompt}_{request.max_tokens}_{request.temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _update_cache(self, cache_key: str, response: LlamaResponse):
        """更新缓存"""
        if len(self.model_cache) >= self.config["cache_size"]:
            # 删除最旧的缓存项
            oldest_key = next(iter(self.model_cache))
            del self.model_cache[oldest_key]
        
        self.model_cache[cache_key] = response
    
    def _update_performance_metrics(self, inference_time: float):
        """更新性能指标"""
        self.performance_metrics["total_requests"] += 1
        current_avg = self.performance_metrics["average_response_time"]
        total_requests = self.performance_metrics["total_requests"]
        
        # 计算新的平均响应时间
        new_avg = (current_avg * (total_requests - 1) + inference_time) / total_requests
        self.performance_metrics["average_response_time"] = new_avg
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "current_model": self.current_model,
            "available_models": list(self.config["models"].keys()),
            "memory_usage": psutil.virtual_memory().percent,
            "cache_size": len(self.model_cache),
            "performance_metrics": self.performance_metrics,
            "ollama_status": await self._check_ollama_status()
        }
    
    async def cleanup(self):
        """清理资源"""
        if self.ollama_process:
            self.ollama_process.terminate()
            self.ollama_process.wait()
        
        self.model_cache.clear()
        logger.info("Llama集成清理完成")

# 全局实例
llama_integration = LlamaIntegration()

async def main():
    """主函数 - 用于测试"""
    integration = LlamaIntegration()
    
    # 初始化
    if await integration.initialize():
        print("✅ Llama集成初始化成功")
        
        # 测试请求
        test_request = LlamaRequest(
            prompt="你好，请介绍一下SonjayOS操作系统的主要特点。",
            max_tokens=200
        )
        
        response = await integration.generate_response(test_request)
        print(f"🤖 AI响应: {response.response}")
        print(f"⏱️ 推理时间: {response.inference_time:.2f}秒")
        print(f"🔢 使用令牌: {response.tokens_used}")
        
        # 系统状态
        status = await integration.get_system_status()
        print(f"📊 系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 清理
        await integration.cleanup()
    else:
        print("❌ Llama集成初始化失败")

if __name__ == "__main__":
    asyncio.run(main())
