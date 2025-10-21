#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS AI服务主程序
支持开发模式和生产模式
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ai.llama.llama_integration import LlamaIntegration
from src.ai.whisper.speech_recognition import SpeechRecognition
from src.ai.embeddings.semantic_search import SemanticSearch

# 配置日志
def setup_logging(debug=False, dev_mode=False):
    """设置日志配置"""
    level = logging.DEBUG if debug else logging.INFO
    
    # 开发模式使用控制台输出
    if dev_mode:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/tmp/sonjayos-ai-dev.log')
            ]
        )
    else:
        # 生产模式使用文件输出
        log_dir = Path('/var/log/sonjayos')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'ai.log'),
                logging.StreamHandler() if debug else logging.NullHandler()
            ]
        )

class AIService:
    """AI服务主类"""
    
    def __init__(self, dev_mode=False, mock_ai=False, debug=False):
        self.dev_mode = dev_mode
        self.mock_ai = mock_ai
        self.debug = debug
        self.services = {}
        self.is_running = False
        
        # 设置环境变量
        os.environ['SONJAYOS_DEV_MODE'] = str(dev_mode)
        os.environ['SONJAYOS_MOCK_AI'] = str(mock_ai)
        os.environ['SONJAYOS_DEBUG'] = str(debug)
        
        logger = logging.getLogger(__name__)
        logger.info(f"AI服务初始化 - 开发模式: {dev_mode}, 模拟AI: {mock_ai}, 调试: {debug}")
    
    async def initialize_services(self):
        """初始化AI服务"""
        logger = logging.getLogger(__name__)
        
        try:
            if self.mock_ai:
                logger.info("使用模拟AI服务")
                await self._init_mock_services()
            else:
                logger.info("初始化真实AI服务")
                await self._init_real_services()
            
            logger.info("AI服务初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"AI服务初始化失败: {e}")
            return False
    
    async def _init_mock_services(self):
        """初始化模拟服务"""
        # 模拟Llama集成
        self.services['llama'] = MockLlamaIntegration()
        
        # 模拟语音识别
        self.services['whisper'] = MockSpeechRecognition()
        
        # 模拟语义搜索
        self.services['embeddings'] = MockSemanticSearch()
        
        logger = logging.getLogger(__name__)
        logger.info("模拟AI服务初始化完成")
    
    async def _init_real_services(self):
        """初始化真实服务"""
        # 初始化Llama集成
        self.services['llama'] = LlamaIntegration()
        await self.services['llama'].initialize()
        
        # 初始化语音识别
        self.services['whisper'] = SpeechRecognition()
        await self.services['whisper'].initialize()
        
        # 初始化语义搜索
        self.services['embeddings'] = SemanticSearch()
        await self.services['embeddings'].initialize()
        
        logger = logging.getLogger(__name__)
        logger.info("真实AI服务初始化完成")
    
    async def start(self):
        """启动AI服务"""
        logger = logging.getLogger(__name__)
        
        if not await self.initialize_services():
            logger.error("服务初始化失败，无法启动")
            return False
        
        self.is_running = True
        logger.info("AI服务已启动")
        
        # 开发模式下的额外功能
        if self.dev_mode:
            await self._start_dev_features()
        
        return True
    
    async def _start_dev_features(self):
        """启动开发模式功能"""
        logger = logging.getLogger(__name__)
        logger.info("启动开发模式功能...")
        
        # 启动性能监控
        if os.environ.get('SONJAYOS_PROFILING', 'false').lower() == 'true':
            await self._start_profiling()
        
        # 启动热重载监控
        if os.environ.get('SONJAYOS_HOT_RELOAD', 'false').lower() == 'true':
            await self._start_hot_reload()
    
    async def _start_profiling(self):
        """启动性能分析"""
        logger = logging.getLogger(__name__)
        logger.info("启动性能分析...")
        
        # 这里可以集成性能分析工具
        # 如memory_profiler, line_profiler等
    
    async def _start_hot_reload(self):
        """启动热重载"""
        logger = logging.getLogger(__name__)
        logger.info("启动热重载监控...")
        
        # 这里可以集成文件监控工具
        # 如watchdog等
    
    async def stop(self):
        """停止AI服务"""
        logger = logging.getLogger(__name__)
        
        # 停止所有服务
        for name, service in self.services.items():
            if hasattr(service, 'cleanup'):
                await service.cleanup()
            logger.info(f"服务 {name} 已停止")
        
        self.is_running = False
        logger.info("AI服务已停止")
    
    async def get_status(self):
        """获取服务状态"""
        return {
            "running": self.is_running,
            "dev_mode": self.dev_mode,
            "mock_ai": self.mock_ai,
            "debug": self.debug,
            "services": {
                name: {
                    "initialized": hasattr(service, 'get_stats'),
                    "status": "running" if hasattr(service, 'get_stats') else "stopped"
                }
                for name, service in self.services.items()
            }
        }

# 模拟服务类
class MockLlamaIntegration:
    """模拟Llama集成"""
    
    async def initialize(self):
        return True
    
    async def generate_response(self, request):
        return {
            "response": f"[模拟] AI响应: {request.get('prompt', '')}",
            "tokens_used": 50,
            "inference_time": 0.1,
            "model_used": "mock-llama"
        }
    
    async def cleanup(self):
        pass

class MockSpeechRecognition:
    """模拟语音识别"""
    
    async def initialize(self):
        return True
    
    async def recognize_audio(self, audio_data):
        return "[模拟] 语音识别结果"
    
    async def cleanup(self):
        pass

class MockSemanticSearch:
    """模拟语义搜索"""
    
    async def initialize(self):
        return True
    
    async def search(self, query, limit=10):
        return [
            {
                "file_path": "/mock/file1.txt",
                "similarity_score": 0.9,
                "content_snippet": f"[模拟] 搜索结果: {query}",
                "file_type": ".txt"
            }
        ]
    
    async def cleanup(self):
        pass

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SonjayOS AI服务')
    parser.add_argument('--dev-mode', action='store_true', help='开发模式')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--mock-ai', action='store_true', help='使用模拟AI服务')
    parser.add_argument('--port', type=int, default=8000, help='服务端口')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(debug=args.debug, dev_mode=args.dev_mode)
    
    # 创建AI服务
    ai_service = AIService(
        dev_mode=args.dev_mode,
        mock_ai=args.mock_ai,
        debug=args.debug
    )
    
    try:
        # 启动服务
        if await ai_service.start():
            logger = logging.getLogger(__name__)
            logger.info("AI服务启动成功")
            
            # 开发模式下显示状态
            if args.dev_mode:
                status = await ai_service.get_status()
                logger.info(f"服务状态: {status}")
            
            # 保持服务运行
            while ai_service.is_running:
                await asyncio.sleep(1)
        else:
            logger.error("AI服务启动失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    except Exception as e:
        logger.error(f"服务运行错误: {e}")
    finally:
        await ai_service.stop()

if __name__ == "__main__":
    asyncio.run(main())
