#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS - 语义搜索模块
基于Hugging Face嵌入模型实现文件语义搜索和智能分类
"""

import asyncio
import json
import logging
import numpy as np
import sqlite3
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib
import pickle

try:
    from sentence_transformers import SentenceTransformer
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("警告: sentence-transformers未安装，语义搜索功能将不可用")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果"""
    file_path: str
    similarity_score: float
    content_snippet: str
    file_type: str
    last_modified: float
    file_size: int
    metadata: Dict[str, Any]

@dataclass
class EmbeddingConfig:
    """嵌入配置"""
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    batch_size: int = 32
    max_length: int = 512
    device: str = "auto"
    cache_size: int = 10000

class SemanticSearch:
    """语义搜索类"""
    
    def __init__(self, config_path: str = "/etc/sonjayos/ai/embeddings_config.json"):
        self.config_path = config_path
        self.config = EmbeddingConfig()
        self.model = None
        self.db_path = "/var/lib/sonjayos/embeddings.db"
        self.cache = {}
        self.index_stats = {
            "total_files": 0,
            "total_embeddings": 0,
            "last_index_time": 0,
            "index_duration": 0
        }
        
        self._load_config()
        self._init_database()
    
    def _load_config(self):
        """加载配置文件"""
        default_config = {
            "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "batch_size": 32,
            "max_length": 512,
            "device": "auto",
            "cache_size": 10000,
            "supported_extensions": [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml"],
            "chunk_size": 1000,
            "overlap_size": 200
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    for key, value in user_config.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
            except Exception as e:
                logger.warning(f"无法加载配置文件: {e}")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            # 确保目录存在
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建文件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    last_modified REAL NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建嵌入表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON files (file_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON files (file_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_embeddings_file_id ON embeddings (file_id)')
            
            conn.commit()
            conn.close()
            
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
    
    async def initialize(self) -> bool:
        """初始化语义搜索服务"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers未安装，无法初始化语义搜索")
            return False
        
        try:
            # 确定设备
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if self.config.device == "auto":
                self.config.device = device
            
            logger.info(f"使用设备: {self.config.device}")
            
            # 加载模型
            logger.info(f"加载嵌入模型: {self.config.model_name}")
            self.model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device
            )
            
            # 加载统计信息
            self._load_stats()
            
            logger.info("语义搜索服务初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    def _load_stats(self):
        """加载统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取文件总数
            cursor.execute('SELECT COUNT(*) FROM files')
            self.index_stats["total_files"] = cursor.fetchone()[0]
            
            # 获取嵌入总数
            cursor.execute('SELECT COUNT(*) FROM embeddings')
            self.index_stats["total_embeddings"] = cursor.fetchone()[0]
            
            # 获取最后索引时间
            cursor.execute('SELECT MAX(created_at) FROM files')
            result = cursor.fetchone()[0]
            if result:
                self.index_stats["last_index_time"] = result
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"加载统计信息失败: {e}")
    
    async def index_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """索引目录中的文件"""
        start_time = time.time()
        indexed_files = 0
        skipped_files = 0
        errors = []
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"目录不存在: {directory_path}")
            
            # 获取所有文件
            if recursive:
                files = list(directory.rglob("*"))
            else:
                files = list(directory.iterdir())
            
            # 过滤文件
            supported_extensions = [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".xml"]
            files = [f for f in files if f.is_file() and f.suffix.lower() in supported_extensions]
            
            logger.info(f"找到 {len(files)} 个文件需要索引")
            
            # 批量处理文件
            for file_path in files:
                try:
                    if await self._index_file(file_path):
                        indexed_files += 1
                    else:
                        skipped_files += 1
                        
                except Exception as e:
                    error_msg = f"索引文件失败 {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # 更新统计信息
            self.index_stats["total_files"] += indexed_files
            self.index_stats["last_index_time"] = time.time()
            self.index_stats["index_duration"] = time.time() - start_time
            
            logger.info(f"索引完成: {indexed_files} 个文件已索引, {skipped_files} 个文件跳过")
            
            return {
                "indexed_files": indexed_files,
                "skipped_files": skipped_files,
                "errors": errors,
                "duration": self.index_stats["index_duration"]
            }
            
        except Exception as e:
            logger.error(f"索引目录失败: {e}")
            return {"error": str(e)}
    
    async def _index_file(self, file_path: Path) -> bool:
        """索引单个文件"""
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_path)
            
            # 检查文件是否已存在且未更改
            if self._is_file_unchanged(file_path, file_hash):
                return False
            
            # 读取文件内容
            content = self._read_file_content(file_path)
            if not content:
                return False
            
            # 分块处理
            chunks = self._split_content(content)
            
            # 生成嵌入
            embeddings = await self._generate_embeddings(chunks)
            
            # 保存到数据库
            await self._save_file_embeddings(file_path, file_hash, content, chunks, embeddings)
            
            return True
            
        except Exception as e:
            logger.error(f"索引文件失败 {file_path}: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""
    
    def _is_file_unchanged(self, file_path: Path, file_hash: str) -> bool:
        """检查文件是否未更改"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT file_hash FROM files WHERE file_path = ?',
                (str(file_path),)
            )
            result = cursor.fetchone()
            
            conn.close()
            
            return result and result[0] == file_hash
            
        except Exception:
            return False
    
    def _read_file_content(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            logger.warning(f"无法读取文件 {file_path}，跳过")
            return ""
            
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return ""
    
    def _split_content(self, content: str) -> List[str]:
        """分割内容为块"""
        chunk_size = 1000
        overlap_size = 200
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end]
            
            # 尝试在句号或换行符处分割
            if end < len(content):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                split_point = max(last_period, last_newline)
                
                if split_point > start + chunk_size // 2:
                    chunk = chunk[:split_point + 1]
                    end = start + split_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap_size
            
        return [chunk for chunk in chunks if chunk.strip()]
    
    async def _generate_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
        """生成嵌入向量"""
        try:
            # 批量处理
            embeddings = []
            batch_size = self.config.batch_size
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch,
                    convert_to_tensor=True,
                    show_progress_bar=False
                )
                
                # 转换为numpy数组
                if hasattr(batch_embeddings, 'cpu'):
                    batch_embeddings = batch_embeddings.cpu().numpy()
                
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"生成嵌入失败: {e}")
            return []
    
    async def _save_file_embeddings(self, file_path: Path, file_hash: str, content: str, 
                                   chunks: List[str], embeddings: List[np.ndarray]):
        """保存文件嵌入到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除旧记录
            cursor.execute('DELETE FROM files WHERE file_path = ?', (str(file_path),))
            
            # 插入文件记录
            cursor.execute('''
                INSERT INTO files (file_path, file_hash, file_type, file_size, last_modified, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(file_path),
                file_hash,
                file_path.suffix.lower(),
                file_path.stat().st_size,
                file_path.stat().st_mtime,
                hashlib.md5(content.encode()).hexdigest()
            ))
            
            file_id = cursor.lastrowid
            
            # 插入嵌入记录
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_blob = pickle.dumps(embedding)
                cursor.execute('''
                    INSERT INTO embeddings (file_id, chunk_index, content, embedding)
                    VALUES (?, ?, ?, ?)
                ''', (file_id, i, chunk, embedding_blob))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存嵌入失败: {e}")
            raise
    
    async def search(self, query: str, limit: int = 10, min_similarity: float = 0.3) -> List[SearchResult]:
        """语义搜索"""
        try:
            # 生成查询嵌入
            query_embedding = self.model.encode([query], convert_to_tensor=True)
            if hasattr(query_embedding, 'cpu'):
                query_embedding = query_embedding.cpu().numpy()[0]
            
            # 从数据库获取所有嵌入
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT f.file_path, f.file_type, f.file_size, f.last_modified, 
                       e.chunk_index, e.content, e.embedding
                FROM files f
                JOIN embeddings e ON f.id = e.file_id
            ''')
            
            results = []
            
            for row in cursor.fetchall():
                file_path, file_type, file_size, last_modified, chunk_index, content, embedding_blob = row
                
                # 反序列化嵌入
                embedding = pickle.loads(embedding_blob)
                
                # 计算相似度
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                
                if similarity >= min_similarity:
                    results.append(SearchResult(
                        file_path=file_path,
                        similarity_score=float(similarity),
                        content_snippet=content[:200] + "..." if len(content) > 200 else content,
                        file_type=file_type,
                        last_modified=last_modified,
                        file_size=file_size,
                        metadata={"chunk_index": chunk_index}
                    ))
            
            conn.close()
            
            # 按相似度排序
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def get_similar_files(self, file_path: str, limit: int = 5) -> List[SearchResult]:
        """获取相似文件"""
        try:
            # 获取文件的嵌入
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.embedding, e.content
                FROM files f
                JOIN embeddings e ON f.id = e.file_id
                WHERE f.file_path = ?
                LIMIT 1
            ''', (file_path,))
            
            result = cursor.fetchone()
            if not result:
                return []
            
            embedding_blob, content = result
            embedding = pickle.loads(embedding_blob)
            
            # 搜索相似文件
            cursor.execute('''
                SELECT f.file_path, f.file_type, f.file_size, f.last_modified,
                       e.chunk_index, e.content, e.embedding
                FROM files f
                JOIN embeddings e ON f.id = e.file_id
                WHERE f.file_path != ?
            ''', (file_path,))
            
            results = []
            
            for row in cursor.fetchall():
                other_file_path, file_type, file_size, last_modified, chunk_index, other_content, other_embedding_blob = row
                
                other_embedding = pickle.loads(other_embedding_blob)
                
                # 计算相似度
                similarity = np.dot(embedding, other_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(other_embedding)
                )
                
                results.append(SearchResult(
                    file_path=other_file_path,
                    similarity_score=float(similarity),
                    content_snippet=other_content[:200] + "..." if len(other_content) > 200 else other_content,
                    file_type=file_type,
                    last_modified=last_modified,
                    file_size=file_size,
                    metadata={"chunk_index": chunk_index}
                ))
            
            conn.close()
            
            # 按相似度排序
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"获取相似文件失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "model_loaded": self.model is not None,
            "database_path": self.db_path,
            "index_stats": self.index_stats,
            "cache_size": len(self.cache)
        }
    
    def cleanup(self):
        """清理资源"""
        self.cache.clear()
        self.model = None
        logger.info("语义搜索服务清理完成")

# 全局实例
semantic_search = SemanticSearch()

async def main():
    """主函数 - 用于测试"""
    search = SemanticSearch()
    
    # 初始化
    if await search.initialize():
        print("✅ 语义搜索服务初始化成功")
        
        # 索引测试目录
        test_dir = "/tmp/sonjayos_test"
        Path(test_dir).mkdir(exist_ok=True)
        
        # 创建测试文件
        test_files = [
            ("AI技术发展.md", "人工智能技术正在快速发展，深度学习、机器学习等技术不断突破。"),
            ("操作系统设计.py", "class OperatingSystem:\n    def __init__(self):\n        self.kernel = Kernel()"),
            ("用户界面设计.txt", "用户界面设计需要考虑用户体验，包括易用性、美观性和功能性。")
        ]
        
        for filename, content in test_files:
            with open(Path(test_dir) / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 索引目录
        result = await search.index_directory(test_dir)
        print(f"📁 索引结果: {result}")
        
        # 测试搜索
        queries = ["人工智能", "操作系统", "用户界面"]
        
        for query in queries:
            print(f"\n🔍 搜索: {query}")
            results = await search.search(query, limit=3)
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.file_path} (相似度: {result.similarity_score:.3f})")
                print(f"     内容: {result.content_snippet}")
        
        # 获取统计信息
        stats = search.get_stats()
        print(f"\n📊 统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        # 清理
        search.cleanup()
    else:
        print("❌ 语义搜索服务初始化失败")

if __name__ == "__main__":
    asyncio.run(main())
