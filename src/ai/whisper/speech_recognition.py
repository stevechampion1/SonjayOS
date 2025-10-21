#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS - Whisper语音识别模块
提供实时语音转文本功能，支持多语言和噪声环境
"""

import asyncio
import logging
import numpy as np
import pyaudio
import wave
import threading
import queue
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path
import json

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("警告: Whisper未安装，语音识别功能将不可用")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """音频配置"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: int = pyaudio.paInt16
    device_index: Optional[int] = None

@dataclass
class RecognitionConfig:
    """识别配置"""
    language: str = "zh"  # 中文
    model_size: str = "base"  # tiny, base, small, medium, large
    temperature: float = 0.0
    beam_size: int = 5
    best_of: int = 5
    patience: float = 1.0
    length_penalty: float = 1.0
    suppress_tokens: str = "-1"
    initial_prompt: Optional[str] = None
    word_timestamps: bool = False
    condition_on_previous_text: bool = True
    fp16: bool = True
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6

class SpeechRecognition:
    """语音识别类"""
    
    def __init__(self, config_path: str = "/etc/sonjayos/ai/whisper_config.json"):
        self.config_path = config_path
        self.audio_config = AudioConfig()
        self.recognition_config = RecognitionConfig()
        self.model = None
        self.audio = None
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recognition_queue = queue.Queue()
        self.callbacks = []
        self.recording_thread = None
        self.processing_thread = None
        
        # 性能统计
        self.stats = {
            "total_audio_duration": 0.0,
            "total_processing_time": 0.0,
            "recognition_accuracy": 0.0,
            "average_latency": 0.0
        }
        
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        default_config = {
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "chunk_size": 1024,
                "device_index": None
            },
            "recognition": {
                "language": "zh",
                "model_size": "base",
                "temperature": 0.0,
                "beam_size": 5,
                "word_timestamps": False
            },
            "performance": {
                "max_audio_length": 30,  # 秒
                "vad_threshold": 0.5,    # 语音活动检测阈值
                "silence_timeout": 2.0   # 静音超时
            }
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 更新配置
                    if "audio" in user_config:
                        for key, value in user_config["audio"].items():
                            setattr(self.audio_config, key, value)
                    if "recognition" in user_config:
                        for key, value in user_config["recognition"].items():
                            setattr(self.recognition_config, key, value)
            except Exception as e:
                logger.warning(f"无法加载配置文件: {e}")
    
    async def initialize(self) -> bool:
        """初始化语音识别服务"""
        if not WHISPER_AVAILABLE:
            logger.error("Whisper未安装，无法初始化语音识别")
            return False
        
        try:
            # 检查CUDA可用性
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"使用设备: {device}")
            
            # 加载Whisper模型
            logger.info(f"加载Whisper模型: {self.recognition_config.model_size}")
            self.model = whisper.load_model(
                self.recognition_config.model_size,
                device=device
            )
            
            # 初始化音频系统
            self.audio = pyaudio.PyAudio()
            
            # 列出可用音频设备
            self._list_audio_devices()
            
            logger.info("语音识别服务初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    def _list_audio_devices(self):
        """列出可用音频设备"""
        logger.info("可用音频设备:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                logger.info(f"  {i}: {info['name']} (输入通道: {info['maxInputChannels']})")
    
    def add_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """添加识别结果回调函数"""
        self.callbacks.append(callback)
    
    def start_listening(self) -> bool:
        """开始监听语音"""
        if self.is_recording:
            logger.warning("已经在监听中")
            return False
        
        try:
            # 创建音频流
            self.stream = self.audio.open(
                format=self.audio_config.format,
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                input=True,
                input_device_index=self.audio_config.device_index,
                frames_per_buffer=self.audio_config.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            
            # 启动录音线程
            self.recording_thread = threading.Thread(target=self._recording_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            # 启动处理线程
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            logger.info("开始语音监听")
            return True
            
        except Exception as e:
            logger.error(f"启动监听失败: {e}")
            return False
    
    def stop_listening(self):
        """停止监听语音"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        logger.info("停止语音监听")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调函数"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def _recording_loop(self):
        """录音循环"""
        audio_buffer = []
        silence_frames = 0
        max_silence_frames = int(self.audio_config.sample_rate * 2.0 / self.audio_config.chunk_size)
        
        while self.is_recording:
            try:
                # 获取音频数据
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get(timeout=0.1)
                    audio_buffer.append(audio_data)
                    silence_frames = 0
                else:
                    silence_frames += 1
                
                # 检查静音超时
                if silence_frames > max_silence_frames and len(audio_buffer) > 0:
                    # 处理音频缓冲区
                    audio_array = np.frombuffer(b''.join(audio_buffer), dtype=np.int16)
                    self.recognition_queue.put(audio_array)
                    audio_buffer = []
                    silence_frames = 0
                
                # 检查缓冲区大小
                if len(audio_buffer) > 100:  # 防止内存溢出
                    audio_array = np.frombuffer(b''.join(audio_buffer), dtype=np.int16)
                    self.recognition_queue.put(audio_array)
                    audio_buffer = []
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"录音循环错误: {e}")
                break
    
    def _processing_loop(self):
        """处理循环"""
        while self.is_recording:
            try:
                if not self.recognition_queue.empty():
                    audio_array = self.recognition_queue.get(timeout=1.0)
                    
                    # 语音活动检测
                    if self._detect_speech_activity(audio_array):
                        # 转换为浮点数
                        audio_float = audio_array.astype(np.float32) / 32768.0
                        
                        # 识别语音
                        start_time = time.time()
                        result = self._recognize_audio(audio_float)
                        processing_time = time.time() - start_time
                        
                        # 更新统计信息
                        self._update_stats(len(audio_float) / self.audio_config.sample_rate, processing_time)
                        
                        # 调用回调函数
                        if result and result.strip():
                            for callback in self.callbacks:
                                try:
                                    callback(result, {
                                        "confidence": getattr(result, 'confidence', 0.0),
                                        "processing_time": processing_time,
                                        "timestamp": time.time()
                                    })
                                except Exception as e:
                                    logger.error(f"回调函数错误: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"处理循环错误: {e}")
                break
    
    def _detect_speech_activity(self, audio_array: np.ndarray) -> bool:
        """语音活动检测"""
        # 计算RMS能量
        rms = np.sqrt(np.mean(audio_array**2))
        
        # 简单的阈值检测
        threshold = 0.01  # 可配置
        return rms > threshold
    
    def _recognize_audio(self, audio_array: np.ndarray) -> str:
        """识别音频"""
        try:
            # 预处理音频
            audio_array = whisper.pad_or_trim(audio_array)
            
            # 生成mel频谱图
            mel = whisper.log_mel_spectrogram(audio_array).to(self.model.device)
            
            # 解码
            options = whisper.DecodingOptions(
                language=self.recognition_config.language,
                temperature=self.recognition_config.temperature,
                beam_size=self.recognition_config.beam_size,
                best_of=self.recognition_config.best_of,
                patience=self.recognition_config.patience,
                length_penalty=self.recognition_config.length_penalty,
                suppress_tokens=self.recognition_config.suppress_tokens,
                initial_prompt=self.recognition_config.initial_prompt,
                condition_on_previous_text=self.recognition_config.condition_on_previous_text,
                fp16=self.recognition_config.fp16,
                compression_ratio_threshold=self.recognition_config.compression_ratio_threshold,
                logprob_threshold=self.recognition_config.logprob_threshold,
                no_speech_threshold=self.recognition_config.no_speech_threshold
            )
            
            result = whisper.decode(self.model, mel, options)
            
            return result.text
            
        except Exception as e:
            logger.error(f"语音识别错误: {e}")
            return ""
    
    def _update_stats(self, audio_duration: float, processing_time: float):
        """更新统计信息"""
        self.stats["total_audio_duration"] += audio_duration
        self.stats["total_processing_time"] += processing_time
        
        # 计算平均延迟
        if self.stats["total_audio_duration"] > 0:
            self.stats["average_latency"] = (
                self.stats["total_processing_time"] / 
                self.stats["total_audio_duration"]
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "is_recording": self.is_recording,
            "model_loaded": self.model is not None,
            "audio_device_count": self.audio.get_device_count() if self.audio else 0,
            "queue_sizes": {
                "audio_queue": self.audio_queue.qsize(),
                "recognition_queue": self.recognition_queue.qsize()
            },
            "performance_stats": self.stats
        }
    
    def cleanup(self):
        """清理资源"""
        self.stop_listening()
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
        
        self.model = None
        logger.info("语音识别服务清理完成")

# 全局实例
speech_recognition = SpeechRecognition()

def on_recognition_result(text: str, metadata: Dict[str, Any]):
    """识别结果回调示例"""
    print(f"🎤 识别结果: {text}")
    print(f"📊 元数据: {metadata}")

async def main():
    """主函数 - 用于测试"""
    recognition = SpeechRecognition()
    
    # 初始化
    if await recognition.initialize():
        print("✅ 语音识别服务初始化成功")
        
        # 添加回调
        recognition.add_callback(on_recognition_result)
        
        # 开始监听
        if recognition.start_listening():
            print("🎤 开始语音监听，请说话...")
            print("按Ctrl+C停止")
            
            try:
                while True:
                    await asyncio.sleep(1)
                    stats = recognition.get_stats()
                    print(f"📊 状态: {stats}")
            except KeyboardInterrupt:
                print("\n⏹️ 停止监听")
            finally:
                recognition.cleanup()
        else:
            print("❌ 启动监听失败")
    else:
        print("❌ 语音识别服务初始化失败")

if __name__ == "__main__":
    asyncio.run(main())
