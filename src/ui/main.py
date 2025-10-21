#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS UI服务主程序
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

from src.ui.themes.adaptive_theme import AdaptiveTheme

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
                logging.FileHandler('/tmp/sonjayos-ui-dev.log')
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
                logging.FileHandler(log_dir / 'ui.log'),
                logging.StreamHandler() if debug else logging.NullHandler()
            ]
        )

class UIService:
    """UI服务主类"""
    
    def __init__(self, dev_mode=False, hot_reload=False, debug=False):
        self.dev_mode = dev_mode
        self.hot_reload = hot_reload
        self.debug = debug
        self.services = {}
        self.is_running = False
        
        # 设置环境变量
        os.environ['SONJAYOS_DEV_MODE'] = str(dev_mode)
        os.environ['SONJAYOS_HOT_RELOAD'] = str(hot_reload)
        os.environ['SONJAYOS_DEBUG'] = str(debug)
        
        logger = logging.getLogger(__name__)
        logger.info(f"UI服务初始化 - 开发模式: {dev_mode}, 热重载: {hot_reload}, 调试: {debug}")
    
    async def initialize_services(self):
        """初始化UI服务"""
        logger = logging.getLogger(__name__)
        
        try:
            if self.dev_mode:
                logger.info("初始化开发模式UI服务")
                await self._init_dev_services()
            else:
                logger.info("初始化生产模式UI服务")
                await self._init_prod_services()
            
            logger.info("UI服务初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"UI服务初始化失败: {e}")
            return False
    
    async def _init_dev_services(self):
        """初始化开发模式服务"""
        # 开发模式下的自适应主题（简化版）
        self.services['theme'] = MockAdaptiveTheme()
        
        # 开发模式下的GNOME扩展（模拟）
        self.services['gnome'] = MockGNOMEExtension()
        
        logger = logging.getLogger(__name__)
        logger.info("开发模式UI服务初始化完成")
    
    async def _init_prod_services(self):
        """初始化生产模式服务"""
        # 真实的自适应主题
        self.services['theme'] = AdaptiveTheme()
        await self.services['theme'].initialize()
        
        # 真实的GNOME扩展
        self.services['gnome'] = RealGNOMEExtension()
        await self.services['gnome'].initialize()
        
        logger = logging.getLogger(__name__)
        logger.info("生产模式UI服务初始化完成")
    
    async def start(self):
        """启动UI服务"""
        logger = logging.getLogger(__name__)
        
        if not await self.initialize_services():
            logger.error("服务初始化失败，无法启动")
            return False
        
        self.is_running = True
        logger.info("UI服务已启动")
        
        # 开发模式下的额外功能
        if self.dev_mode:
            await self._start_dev_features()
        
        return True
    
    async def _start_dev_features(self):
        """启动开发模式功能"""
        logger = logging.getLogger(__name__)
        logger.info("启动开发模式功能...")
        
        # 启动热重载监控
        if self.hot_reload:
            await self._start_hot_reload()
        
        # 启动主题预览
        await self._start_theme_preview()
    
    async def _start_hot_reload(self):
        """启动热重载"""
        logger = logging.getLogger(__name__)
        logger.info("启动热重载监控...")
        
        # 监控UI文件变化
        import watchdog
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class UIChangeHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path.endswith(('.js', '.css', '.html')):
                    logger.info(f"UI文件变化: {event.src_path}")
                    # 这里可以触发UI重载
        
        observer = Observer()
        observer.schedule(UIChangeHandler(), 'src/ui/', recursive=True)
        observer.start()
        
        self.observer = observer
    
    async def _start_theme_preview(self):
        """启动主题预览"""
        logger = logging.getLogger(__name__)
        logger.info("启动主题预览...")
        
        # 开发模式下可以预览不同主题
        if hasattr(self.services['theme'], 'preview_theme'):
            await self.services['theme'].preview_theme('light_work')
    
    async def stop(self):
        """停止UI服务"""
        logger = logging.getLogger(__name__)
        
        # 停止热重载监控
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
        
        # 停止所有服务
        for name, service in self.services.items():
            if hasattr(service, 'cleanup'):
                await service.cleanup()
            logger.info(f"服务 {name} 已停止")
        
        self.is_running = False
        logger.info("UI服务已停止")
    
    async def get_status(self):
        """获取服务状态"""
        return {
            "running": self.is_running,
            "dev_mode": self.dev_mode,
            "hot_reload": self.hot_reload,
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
class MockAdaptiveTheme:
    """模拟自适应主题"""
    
    async def initialize(self):
        return True
    
    async def get_current_theme(self):
        return {
            "name": "light_work",
            "background": "#FFFFFF",
            "accent_color": "#2196F3",
            "text_color": "#212121"
        }
    
    async def switch_theme(self, theme_name):
        logger = logging.getLogger(__name__)
        logger.info(f"[模拟] 切换主题到: {theme_name}")
        return True
    
    async def cleanup(self):
        pass

class MockGNOMEExtension:
    """模拟GNOME扩展"""
    
    async def initialize(self):
        return True
    
    async def enable_extension(self, extension_id):
        logger = logging.getLogger(__name__)
        logger.info(f"[模拟] 启用GNOME扩展: {extension_id}")
        return True
    
    async def disable_extension(self, extension_id):
        logger = logging.getLogger(__name__)
        logger.info(f"[模拟] 禁用GNOME扩展: {extension_id}")
        return True
    
    async def cleanup(self):
        pass

class RealGNOMEExtension:
    """真实GNOME扩展"""
    
    async def initialize(self):
        # 这里可以集成真实的GNOME扩展管理
        return True
    
    async def enable_extension(self, extension_id):
        # 真实的GNOME扩展启用逻辑
        return True
    
    async def disable_extension(self, extension_id):
        # 真实的GNOME扩展禁用逻辑
        return True
    
    async def cleanup(self):
        pass

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='SonjayOS UI服务')
    parser.add_argument('--dev-mode', action='store_true', help='开发模式')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    parser.add_argument('--hot-reload', action='store_true', help='热重载')
    parser.add_argument('--port', type=int, default=8001, help='服务端口')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(debug=args.debug, dev_mode=args.dev_mode)
    
    # 创建UI服务
    ui_service = UIService(
        dev_mode=args.dev_mode,
        hot_reload=args.hot_reload,
        debug=args.debug
    )
    
    try:
        # 启动服务
        if await ui_service.start():
            logger = logging.getLogger(__name__)
            logger.info("UI服务启动成功")
            
            # 开发模式下显示状态
            if args.dev_mode:
                status = await ui_service.get_status()
                logger.info(f"服务状态: {status}")
            
            # 保持服务运行
            while ui_service.is_running:
                await asyncio.sleep(1)
        else:
            logger.error("UI服务启动失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    except Exception as e:
        logger.error(f"服务运行错误: {e}")
    finally:
        await ui_service.stop()

if __name__ == "__main__":
    asyncio.run(main())
