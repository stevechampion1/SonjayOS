#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS - 自适应主题系统
根据用户行为和环境自动调整桌面主题和布局
"""

import asyncio
import json
import logging
import time
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import psutil
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThemeConfig:
    """主题配置"""
    name: str
    background: str
    accent_color: str
    text_color: str
    icon_theme: str
    cursor_theme: str
    font_size: int
    opacity: float
    brightness: float
    contrast: float

@dataclass
class UserBehavior:
    """用户行为数据"""
    timestamp: float
    activity_type: str  # 'work', 'entertainment', 'reading', 'coding'
    application: str
    duration: float
    brightness_preference: float
    color_preference: str

class AdaptiveTheme:
    """自适应主题类"""
    
    def __init__(self, config_path: str = "/etc/sonjayos/ui/theme_config.json"):
        self.config_path = config_path
        self.current_theme = None
        self.user_behaviors = []
        self.environment_data = {}
        self.theme_history = []
        
        # 预定义主题
        self.themes = {
            "light_work": ThemeConfig(
                name="light_work",
                background="#FFFFFF",
                accent_color="#2196F3",
                text_color="#212121",
                icon_theme="Papirus-Light",
                cursor_theme="Adwaita",
                font_size=11,
                opacity=1.0,
                brightness=1.0,
                contrast=1.0
            ),
            "dark_work": ThemeConfig(
                name="dark_work",
                background="#1E1E1E",
                accent_color="#64B5F6",
                text_color="#FFFFFF",
                icon_theme="Papirus-Dark",
                cursor_theme="Adwaita",
                font_size=11,
                opacity=1.0,
                brightness=0.8,
                contrast=1.2
            ),
            "light_reading": ThemeConfig(
                name="light_reading",
                background="#F5F5F5",
                accent_color="#4CAF50",
                text_color="#2E2E2E",
                icon_theme="Papirus-Light",
                cursor_theme="Adwaita",
                font_size=12,
                opacity=0.95,
                brightness=1.0,
                contrast=1.1
            ),
            "dark_reading": ThemeConfig(
                name="dark_reading",
                background="#121212",
                accent_color="#81C784",
                text_color="#E0E0E0",
                icon_theme="Papirus-Dark",
                cursor_theme="Adwaita",
                font_size=12,
                opacity=0.9,
                brightness=0.7,
                contrast=1.3
            ),
            "coding": ThemeConfig(
                name="coding",
                background="#0D1117",
                accent_color="#58A6FF",
                text_color="#F0F6FC",
                icon_theme="Papirus-Dark",
                cursor_theme="Adwaita",
                font_size=10,
                opacity=1.0,
                brightness=0.6,
                contrast=1.4
            ),
            "entertainment": ThemeConfig(
                name="entertainment",
                background="#1A1A2E",
                accent_color="#FF6B6B",
                text_color="#FFFFFF",
                icon_theme="Papirus-Dark",
                cursor_theme="Adwaita",
                font_size=11,
                opacity=0.8,
                brightness=0.5,
                contrast=1.1
            )
        }
        
        self._load_config()
        self._start_monitoring()
    
    def _load_config(self):
        """加载配置文件"""
        default_config = {
            "auto_theme_switching": True,
            "learning_enabled": True,
            "brightness_adaptation": True,
            "time_based_themes": {
                "morning": "light_work",
                "afternoon": "light_work", 
                "evening": "dark_work",
                "night": "dark_reading"
            },
            "activity_themes": {
                "work": "light_work",
                "coding": "coding",
                "reading": "light_reading",
                "entertainment": "entertainment"
            },
            "environment_adaptation": {
                "brightness_threshold": 0.5,
                "contrast_threshold": 0.3
            }
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"无法加载配置文件: {e}")
        
        self.config = default_config
    
    def _start_monitoring(self):
        """开始监控用户行为和环境"""
        asyncio.create_task(self._monitor_user_activity())
        asyncio.create_task(self._monitor_environment())
        asyncio.create_task(self._learn_user_preferences())
    
    async def _monitor_user_activity(self):
        """监控用户活动"""
        while True:
            try:
                # 获取当前活动应用程序
                current_app = self._get_current_application()
                
                # 检测活动类型
                activity_type = self._detect_activity_type(current_app)
                
                # 记录用户行为
                behavior = UserBehavior(
                    timestamp=time.time(),
                    activity_type=activity_type,
                    application=current_app,
                    duration=0.0,
                    brightness_preference=self._get_brightness_preference(),
                    color_preference=self._get_color_preference()
                )
                
                self.user_behaviors.append(behavior)
                
                # 保持历史记录在合理范围内
                if len(self.user_behaviors) > 1000:
                    self.user_behaviors = self.user_behaviors[-500:]
                
                # 检查是否需要切换主题
                await self._check_theme_switch(behavior)
                
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                logger.error(f"监控用户活动失败: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_environment(self):
        """监控环境条件"""
        while True:
            try:
                # 获取环境数据
                brightness = self._get_ambient_brightness()
                time_of_day = self._get_time_of_day()
                system_load = psutil.cpu_percent()
                
                self.environment_data = {
                    "brightness": brightness,
                    "time_of_day": time_of_day,
                    "system_load": system_load,
                    "timestamp": time.time()
                }
                
                # 根据环境调整主题
                await self._adapt_to_environment()
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"监控环境失败: {e}")
                await asyncio.sleep(60)
    
    async def _learn_user_preferences(self):
        """学习用户偏好"""
        while True:
            try:
                if not self.config["learning_enabled"]:
                    await asyncio.sleep(3600)  # 1小时
                    continue
                
                # 分析用户行为模式
                patterns = self._analyze_user_patterns()
                
                # 更新主题推荐
                await self._update_theme_recommendations(patterns)
                
                await asyncio.sleep(3600)  # 每小时学习一次
                
            except Exception as e:
                logger.error(f"学习用户偏好失败: {e}")
                await asyncio.sleep(3600)
    
    def _get_current_application(self) -> str:
        """获取当前活动应用程序"""
        try:
            # 使用psutil获取活动进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'gnome' in proc.info['name'].lower():
                        return proc.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return "unknown"
        except Exception:
            return "unknown"
    
    def _detect_activity_type(self, application: str) -> str:
        """检测活动类型"""
        app_lower = application.lower()
        
        # 工作相关应用
        work_apps = ['code', 'vscode', 'sublime', 'atom', 'gedit', 'libreoffice', 'writer', 'calc']
        if any(app in app_lower for app in work_apps):
            return "work"
        
        # 编程相关应用
        coding_apps = ['code', 'vscode', 'sublime', 'atom', 'vim', 'emacs', 'terminal']
        if any(app in app_lower for app in coding_apps):
            return "coding"
        
        # 阅读相关应用
        reading_apps = ['reader', 'evince', 'okular', 'firefox', 'chrome', 'browser']
        if any(app in app_lower for app in reading_apps):
            return "reading"
        
        # 娱乐相关应用
        entertainment_apps = ['vlc', 'mpv', 'spotify', 'steam', 'game']
        if any(app in app_lower for app in entertainment_apps):
            return "entertainment"
        
        return "work"  # 默认工作模式
    
    def _get_brightness_preference(self) -> float:
        """获取用户亮度偏好"""
        try:
            # 从系统获取当前亮度设置
            result = subprocess.run(['xrandr', '--verbose'], capture_output=True, text=True)
            if 'Brightness:' in result.stdout:
                brightness_line = [line for line in result.stdout.split('\n') if 'Brightness:' in line][0]
                brightness = float(brightness_line.split('Brightness: ')[1])
                return brightness
            return 1.0
        except Exception:
            return 1.0
    
    def _get_color_preference(self) -> str:
        """获取用户颜色偏好"""
        # 基于当前主题推断颜色偏好
        if self.current_theme:
            if "dark" in self.current_theme.name:
                return "dark"
            elif "light" in self.current_theme.name:
                return "light"
        return "auto"
    
    def _get_ambient_brightness(self) -> float:
        """获取环境亮度"""
        try:
            # 尝试从传感器获取环境亮度
            # 这里使用模拟数据，实际实现需要硬件支持
            import random
            return random.uniform(0.1, 1.0)
        except Exception:
            return 0.5
    
    def _get_time_of_day(self) -> str:
        """获取时间段"""
        hour = datetime.datetime.now().hour
        
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    async def _check_theme_switch(self, behavior: UserBehavior):
        """检查是否需要切换主题"""
        if not self.config["auto_theme_switching"]:
            return
        
        # 基于活动类型选择主题
        activity_theme = self.config["activity_themes"].get(behavior.activity_type)
        if activity_theme and activity_theme != self.current_theme.name:
            await self._switch_theme(activity_theme)
            return
        
        # 基于时间选择主题
        time_theme = self.config["time_based_themes"].get(self._get_time_of_day())
        if time_theme and time_theme != self.current_theme.name:
            await self._switch_theme(time_theme)
    
    async def _adapt_to_environment(self):
        """根据环境调整主题"""
        if not self.config["brightness_adaptation"]:
            return
        
        brightness = self.environment_data.get("brightness", 0.5)
        threshold = self.config["environment_adaptation"]["brightness_threshold"]
        
        # 根据环境亮度调整主题
        if brightness < threshold and "light" in self.current_theme.name:
            # 环境较暗，切换到深色主题
            dark_theme = self.current_theme.name.replace("light", "dark")
            if dark_theme in self.themes:
                await self._switch_theme(dark_theme)
        elif brightness >= threshold and "dark" in self.current_theme.name:
            # 环境较亮，切换到浅色主题
            light_theme = self.current_theme.name.replace("dark", "light")
            if light_theme in self.themes:
                await self._switch_theme(light_theme)
    
    def _analyze_user_patterns(self) -> Dict[str, Any]:
        """分析用户行为模式"""
        if len(self.user_behaviors) < 10:
            return {}
        
        # 分析活动类型分布
        activity_counts = {}
        for behavior in self.user_behaviors[-100:]:  # 最近100个行为
            activity_counts[behavior.activity_type] = activity_counts.get(behavior.activity_type, 0) + 1
        
        # 分析时间模式
        time_patterns = {}
        for behavior in self.user_behaviors[-100:]:
            hour = datetime.datetime.fromtimestamp(behavior.timestamp).hour
            time_slot = f"{hour//4*4}-{(hour//4+1)*4}"
            time_patterns[time_slot] = time_patterns.get(time_slot, {})
            time_patterns[time_slot][behavior.activity_type] = time_patterns[time_slot].get(behavior.activity_type, 0) + 1
        
        # 分析亮度偏好
        brightness_preferences = [b.brightness_preference for b in self.user_behaviors[-50:]]
        avg_brightness = sum(brightness_preferences) / len(brightness_preferences) if brightness_preferences else 0.5
        
        return {
            "activity_distribution": activity_counts,
            "time_patterns": time_patterns,
            "brightness_preference": avg_brightness,
            "most_common_activity": max(activity_counts, key=activity_counts.get) if activity_counts else "work"
        }
    
    async def _update_theme_recommendations(self, patterns: Dict[str, Any]):
        """更新主题推荐"""
        if not patterns:
            return
        
        # 基于用户模式更新配置
        most_common_activity = patterns.get("most_common_activity", "work")
        brightness_pref = patterns.get("brightness_preference", 0.5)
        
        # 更新活动主题映射
        if most_common_activity in patterns["activity_distribution"]:
            self.config["activity_themes"][most_common_activity] = self._recommend_theme_for_activity(most_common_activity, brightness_pref)
    
    def _recommend_theme_for_activity(self, activity: str, brightness_pref: float) -> str:
        """为活动推荐主题"""
        if brightness_pref > 0.7:
            return f"light_{activity}"
        else:
            return f"dark_{activity}"
    
    async def _switch_theme(self, theme_name: str):
        """切换主题"""
        if theme_name not in self.themes:
            logger.warning(f"主题不存在: {theme_name}")
            return
        
        try:
            theme = self.themes[theme_name]
            self.current_theme = theme
            
            # 应用主题设置
            await self._apply_theme(theme)
            
            # 记录主题历史
            self.theme_history.append({
                "theme": theme_name,
                "timestamp": time.time(),
                "reason": "auto_switch"
            })
            
            logger.info(f"主题已切换为: {theme_name}")
            
        except Exception as e:
            logger.error(f"切换主题失败: {e}")
    
    async def _apply_theme(self, theme: ThemeConfig):
        """应用主题设置"""
        try:
            # 应用GNOME主题
            await self._apply_gnome_theme(theme)
            
            # 应用图标主题
            await self._apply_icon_theme(theme)
            
            # 应用光标主题
            await self._apply_cursor_theme(theme)
            
            # 应用字体设置
            await self._apply_font_settings(theme)
            
            # 应用亮度设置
            await self._apply_brightness_settings(theme)
            
        except Exception as e:
            logger.error(f"应用主题失败: {e}")
    
    async def _apply_gnome_theme(self, theme: ThemeConfig):
        """应用GNOME主题"""
        try:
            # 设置GTK主题
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'gtk-theme', theme.name])
            
            # 设置Shell主题
            subprocess.run(['gsettings', 'set', 'org.gnome.shell.extensions.user-theme', 'name', theme.name])
            
        except Exception as e:
            logger.error(f"应用GNOME主题失败: {e}")
    
    async def _apply_icon_theme(self, theme: ThemeConfig):
        """应用图标主题"""
        try:
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'icon-theme', theme.icon_theme])
        except Exception as e:
            logger.error(f"应用图标主题失败: {e}")
    
    async def _apply_cursor_theme(self, theme: ThemeConfig):
        """应用光标主题"""
        try:
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'cursor-theme', theme.cursor_theme])
        except Exception as e:
            logger.error(f"应用光标主题失败: {e}")
    
    async def _apply_font_settings(self, theme: ThemeConfig):
        """应用字体设置"""
        try:
            font_name = f"Ubuntu {theme.font_size}"
            subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'font-name', font_name])
        except Exception as e:
            logger.error(f"应用字体设置失败: {e}")
    
    async def _apply_brightness_settings(self, theme: ThemeConfig):
        """应用亮度设置"""
        try:
            # 设置显示器亮度
            brightness_percent = int(theme.brightness * 100)
            subprocess.run(['xrandr', '--output', 'eDP-1', '--brightness', str(theme.brightness)])
            
        except Exception as e:
            logger.error(f"应用亮度设置失败: {e}")
    
    async def get_current_theme(self) -> Optional[ThemeConfig]:
        """获取当前主题"""
        return self.current_theme
    
    async def get_theme_recommendations(self) -> List[str]:
        """获取主题推荐"""
        if not self.user_behaviors:
            return list(self.themes.keys())
        
        patterns = self._analyze_user_patterns()
        recommendations = []
        
        # 基于用户行为推荐
        most_common_activity = patterns.get("most_common_activity", "work")
        brightness_pref = patterns.get("brightness_preference", 0.5)
        
        if brightness_pref > 0.7:
            recommendations.append(f"light_{most_common_activity}")
        else:
            recommendations.append(f"dark_{most_common_activity}")
        
        # 基于时间推荐
        time_of_day = self._get_time_of_day()
        time_theme = self.config["time_based_themes"].get(time_of_day)
        if time_theme:
            recommendations.append(time_theme)
        
        return list(set(recommendations))
    
    async def get_theme_stats(self) -> Dict[str, Any]:
        """获取主题统计信息"""
        return {
            "current_theme": self.current_theme.name if self.current_theme else None,
            "available_themes": list(self.themes.keys()),
            "theme_history_count": len(self.theme_history),
            "user_behaviors_count": len(self.user_behaviors),
            "environment_data": self.environment_data,
            "learning_enabled": self.config["learning_enabled"]
        }
    
    async def cleanup(self):
        """清理资源"""
        self.user_behaviors.clear()
        self.theme_history.clear()
        self.environment_data.clear()
        logger.info("自适应主题系统清理完成")

# 全局实例
adaptive_theme = AdaptiveTheme()

async def main():
    """主函数 - 用于测试"""
    theme_system = AdaptiveTheme()
    
    print("✅ 自适应主题系统初始化成功")
    
    # 获取当前主题
    current_theme = await theme_system.get_current_theme()
    if current_theme:
        print(f"🎨 当前主题: {current_theme.name}")
    
    # 获取主题推荐
    recommendations = await theme_system.get_theme_recommendations()
    print(f"💡 主题推荐: {recommendations}")
    
    # 获取统计信息
    stats = await theme_system.get_theme_stats()
    print(f"📊 统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    # 测试主题切换
    print("\n🔄 测试主题切换...")
    await theme_system._switch_theme("dark_work")
    
    # 清理
    await theme_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
