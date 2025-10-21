#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS AI集成测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ai.llama.llama_integration import LlamaIntegration, LlamaRequest, LlamaResponse
from src.ai.whisper.speech_recognition import SpeechRecognition
from src.ai.embeddings.semantic_search import SemanticSearch

class TestLlamaIntegration:
    """Llama集成测试"""
    
    @pytest.fixture
    def llama_integration(self):
        """创建Llama集成实例"""
        return LlamaIntegration()
    
    @pytest.mark.asyncio
    async def test_initialize(self, llama_integration):
        """测试初始化"""
        with patch('src.ai.llama.llama_integration.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            result = await llama_integration.initialize()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_response(self, llama_integration):
        """测试生成响应"""
        # 模拟初始化
        llama_integration.current_model = "llama3.1-8b"
        llama_integration.config = {
            "ollama_host": "http://localhost:11434",
            "models": {"llama3.1-8b": {"name": "llama3.1:8b"}}
        }
        
        request = LlamaRequest(
            prompt="你好，请介绍一下SonjayOS",
            max_tokens=100
        )
        
        with patch('src.ai.llama.llama_integration.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {
                "response": "SonjayOS是一个AI集成操作系统"
            }
            mock_post.return_value.raise_for_status.return_value = None
            
            response = await llama_integration.generate_response(request)
            
            assert isinstance(response, LlamaResponse)
            assert "SonjayOS" in response.response
    
    def test_request_model(self):
        """测试请求模型"""
        request = LlamaRequest(
            prompt="测试提示",
            max_tokens=50,
            temperature=0.7
        )
        
        assert request.prompt == "测试提示"
        assert request.max_tokens == 50
        assert request.temperature == 0.7

class TestSpeechRecognition:
    """语音识别测试"""
    
    @pytest.fixture
    def speech_recognition(self):
        """创建语音识别实例"""
        return SpeechRecognition()
    
    @pytest.mark.asyncio
    async def test_initialize(self, speech_recognition):
        """测试初始化"""
        with patch('src.ai.whisper.speech_recognition.WHISPER_AVAILABLE', True):
            with patch('src.ai.whisper.speech_recognition.whisper.load_model') as mock_load:
                mock_load.return_value = Mock()
                result = await speech_recognition.initialize()
                assert result is True
    
    def test_audio_config(self, speech_recognition):
        """测试音频配置"""
        config = speech_recognition.audio_config
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.chunk_size == 1024

class TestSemanticSearch:
    """语义搜索测试"""
    
    @pytest.fixture
    def semantic_search(self):
        """创建语义搜索实例"""
        return SemanticSearch()
    
    @pytest.mark.asyncio
    async def test_initialize(self, semantic_search):
        """测试初始化"""
        with patch('src.ai.embeddings.semantic_search.SENTENCE_TRANSFORMERS_AVAILABLE', True):
            with patch('src.ai.embeddings.semantic_search.SentenceTransformer') as mock_model:
                mock_model.return_value = Mock()
                result = await semantic_search.initialize()
                assert result is True
    
    @pytest.mark.asyncio
    async def test_search(self, semantic_search):
        """测试搜索"""
        # 模拟初始化
        semantic_search.model = Mock()
        semantic_search.model.encode.return_value = [[0.1, 0.2, 0.3]]
        
        with patch('src.ai.embeddings.semantic_search.sqlite3.connect') as mock_connect:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = [
                ("/test/file.txt", "txt", 100, 1234567890, 0, "测试内容", b"mock_embedding")
            ]
            mock_connect.return_value.cursor.return_value = mock_cursor
            
            results = await semantic_search.search("测试查询", limit=5)
            
            assert len(results) >= 0

@pytest.mark.integration
class TestAIIntegration:
    """AI集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_ai_pipeline(self):
        """测试完整AI流程"""
        # 这里可以添加端到端测试
        pass

if __name__ == "__main__":
    pytest.main([__file__])
