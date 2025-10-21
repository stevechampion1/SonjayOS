#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonjayOS - AI代码补全工具
集成Llama 3.1模型提供智能代码建议和补全功能
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeCompletion:
    """代码补全建议"""
    text: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    confidence: float
    completion_type: str  # 'function', 'variable', 'import', 'snippet'
    description: str

@dataclass
class CodeContext:
    """代码上下文"""
    file_path: str
    language: str
    content: str
    cursor_line: int
    cursor_column: int
    imports: List[str]
    functions: List[str]
    variables: List[str]
    classes: List[str]

class AICodeCompletion:
    """AI代码补全类"""
    
    def __init__(self, config_path: str = "/etc/sonjayos/dev_tools/code_completion_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.completion_cache = {}
        self.language_patterns = {}
        self.code_templates = {}
        
        # 性能统计
        self.stats = {
            "total_completions": 0,
            "cache_hits": 0,
            "average_response_time": 0.0,
            "accuracy_score": 0.0
        }
        
        self._init_language_patterns()
        self._init_code_templates()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "completion": {
                "enabled": True,
                "max_suggestions": 5,
                "confidence_threshold": 0.7,
                "cache_size": 1000
            },
            "languages": {
                "python": {
                    "extensions": [".py"],
                    "keywords": ["def", "class", "import", "from", "if", "for", "while", "try", "except"],
                    "builtins": ["print", "len", "str", "int", "float", "list", "dict", "tuple", "set"]
                },
                "javascript": {
                    "extensions": [".js", ".jsx", ".ts", ".tsx"],
                    "keywords": ["function", "class", "import", "export", "if", "for", "while", "try", "catch"],
                    "builtins": ["console", "document", "window", "setTimeout", "setInterval", "fetch"]
                },
                "cpp": {
                    "extensions": [".cpp", ".c", ".h", ".hpp"],
                    "keywords": ["int", "float", "double", "char", "bool", "void", "class", "struct", "namespace"],
                    "builtins": ["cout", "cin", "endl", "string", "vector", "map", "set"]
                },
                "java": {
                    "extensions": [".java"],
                    "keywords": ["public", "private", "protected", "class", "interface", "extends", "implements"],
                    "builtins": ["System", "String", "Integer", "ArrayList", "HashMap", "Scanner"]
                }
            },
            "ai_models": {
                "primary_model": "llama3.1:8b",
                "fallback_model": "codellama:7b",
                "context_length": 2048,
                "temperature": 0.2
            }
        }
        
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"无法加载配置文件: {e}")
        
        return default_config
    
    def _init_language_patterns(self):
        """初始化语言模式"""
        self.language_patterns = {
            "python": {
                "function_pattern": r"def\s+(\w+)\s*\(",
                "class_pattern": r"class\s+(\w+)\s*[\(:]",
                "import_pattern": r"(?:from\s+(\w+)\s+)?import\s+(\w+)",
                "variable_pattern": r"(\w+)\s*=",
                "comment_pattern": r"#.*$"
            },
            "javascript": {
                "function_pattern": r"function\s+(\w+)\s*\(",
                "class_pattern": r"class\s+(\w+)\s*[{\s]",
                "import_pattern": r"import\s+(?:.*\s+from\s+)?['\"]([^'\"]+)['\"]",
                "variable_pattern": r"(?:const|let|var)\s+(\w+)",
                "comment_pattern": r"//.*$|/\*.*?\*/"
            },
            "cpp": {
                "function_pattern": r"(\w+)\s+(\w+)\s*\(",
                "class_pattern": r"class\s+(\w+)\s*[{\s]",
                "include_pattern": r"#include\s*[<\"]([^>\"]+)[>\"]",
                "variable_pattern": r"(\w+)\s+(\w+)\s*[=;]",
                "comment_pattern": r"//.*$|/\*.*?\*/"
            }
        }
    
    def _init_code_templates(self):
        """初始化代码模板"""
        self.code_templates = {
            "python": {
                "function": "def {name}({params}):\n    \"\"\"{description}\"\"\"\n    {body}",
                "class": "class {name}:\n    \"\"\"{description}\"\"\"\n    \n    def __init__(self{params}):\n        {body}",
                "import": "import {module}",
                "from_import": "from {module} import {name}",
                "if_statement": "if {condition}:\n    {body}",
                "for_loop": "for {item} in {iterable}:\n    {body}",
                "try_except": "try:\n    {body}\nexcept {exception} as {name}:\n    {handler}"
            },
            "javascript": {
                "function": "function {name}({params}) {\n    {body}\n}",
                "arrow_function": "const {name} = ({params}) => {\n    {body}\n}",
                "class": "class {name} {\n    constructor({params}) {\n        {body}\n    }\n}",
                "import": "import {name} from '{module}'",
                "if_statement": "if ({condition}) {\n    {body}\n}",
                "for_loop": "for (let {item} of {iterable}) {\n    {body}\n}",
                "try_catch": "try {\n    {body}\n} catch ({name}) {\n    {handler}\n}"
            },
            "cpp": {
                "function": "{return_type} {name}({params}) {\n    {body}\n}",
                "class": "class {name} {\npublic:\n    {name}({params});\n    ~{name}();\nprivate:\n    {members}\n};",
                "include": "#include <{header}>",
                "if_statement": "if ({condition}) {\n    {body}\n}",
                "for_loop": "for (int {item} = 0; {item} < {limit}; {item}++) {\n    {body}\n}",
                "try_catch": "try {\n    {body}\n} catch ({exception} {name}) {\n    {handler}\n}"
            }
        }
    
    async def initialize(self) -> bool:
        """初始化AI代码补全服务"""
        try:
            # 这里可以连接到AI服务
            # 目前使用基于规则的补全
            logger.info("AI代码补全服务初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def get_completions(self, context: CodeContext) -> List[CodeCompletion]:
        """获取代码补全建议"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(context)
            if cache_key in self.completion_cache:
                self.stats["cache_hits"] += 1
                return self.completion_cache[cache_key]
            
            # 分析代码上下文
            suggestions = []
            
            # 基于语言模式的补全
            language_suggestions = await self._get_language_suggestions(context)
            suggestions.extend(language_suggestions)
            
            # 基于AI模型的补全
            ai_suggestions = await self._get_ai_suggestions(context)
            suggestions.extend(ai_suggestions)
            
            # 基于代码模板的补全
            template_suggestions = await self._get_template_suggestions(context)
            suggestions.extend(template_suggestions)
            
            # 过滤和排序建议
            filtered_suggestions = self._filter_suggestions(suggestions, context)
            sorted_suggestions = self._sort_suggestions(filtered_suggestions)
            
            # 限制建议数量
            final_suggestions = sorted_suggestions[:self.config["completion"]["max_suggestions"]]
            
            # 更新缓存
            self._update_cache(cache_key, final_suggestions)
            
            # 更新统计信息
            response_time = time.time() - start_time
            self._update_stats(response_time)
            
            return final_suggestions
            
        except Exception as e:
            logger.error(f"获取代码补全失败: {e}")
            return []
    
    async def _get_language_suggestions(self, context: CodeContext) -> List[CodeCompletion]:
        """基于语言模式的补全建议"""
        suggestions = []
        language = context.language.lower()
        
        if language not in self.language_patterns:
            return suggestions
        
        patterns = self.language_patterns[language]
        
        # 分析当前行
        current_line = context.content.split('\n')[context.cursor_line - 1]
        
        # 检查是否在函数定义中
        if re.search(patterns["function_pattern"], current_line):
            suggestions.append(CodeCompletion(
                text="def ",
                start_line=context.cursor_line,
                end_line=context.cursor_line,
                start_column=context.cursor_column,
                end_column=context.cursor_column,
                confidence=0.9,
                completion_type="snippet",
                description="函数定义"
            ))
        
        # 检查是否在类定义中
        if re.search(patterns["class_pattern"], current_line):
            suggestions.append(CodeCompletion(
                text="class ",
                start_line=context.cursor_line,
                end_line=context.cursor_line,
                start_column=context.cursor_column,
                end_column=context.cursor_column,
                confidence=0.9,
                completion_type="snippet",
                description="类定义"
            ))
        
        # 检查是否在导入语句中
        if re.search(patterns["import_pattern"], current_line):
            suggestions.append(CodeCompletion(
                text="import ",
                start_line=context.cursor_line,
                end_line=context.cursor_line,
                start_column=context.cursor_column,
                end_column=context.cursor_column,
                confidence=0.8,
                completion_type="snippet",
                description="导入语句"
            ))
        
        return suggestions
    
    async def _get_ai_suggestions(self, context: CodeContext) -> List[CodeCompletion]:
        """基于AI模型的补全建议"""
        suggestions = []
        
        try:
            # 构建提示词
            prompt = self._build_completion_prompt(context)
            
            # 这里应该调用AI模型
            # 目前使用模拟数据
            ai_suggestions = [
                CodeCompletion(
                    text="print(",
                    start_line=context.cursor_line,
                    end_line=context.cursor_line,
                    start_column=context.cursor_column,
                    end_column=context.cursor_column,
                    confidence=0.8,
                    completion_type="function",
                    description="打印函数"
                ),
                CodeCompletion(
                    text="len(",
                    start_line=context.cursor_line,
                    end_line=context.cursor_line,
                    start_column=context.cursor_column,
                    end_column=context.cursor_column,
                    confidence=0.7,
                    completion_type="function",
                    description="长度函数"
                )
            ]
            
            suggestions.extend(ai_suggestions)
            
        except Exception as e:
            logger.error(f"AI建议生成失败: {e}")
        
        return suggestions
    
    async def _get_template_suggestions(self, context: CodeContext) -> List[CodeCompletion]:
        """基于代码模板的补全建议"""
        suggestions = []
        language = context.language.lower()
        
        if language not in self.code_templates:
            return suggestions
        
        templates = self.code_templates[language]
        
        # 分析当前上下文，推荐合适的模板
        current_line = context.content.split('\n')[context.cursor_line - 1]
        
        # 检查是否在函数定义中
        if "def " in current_line or "function " in current_line:
            template = templates.get("function", "")
            if template:
                suggestions.append(CodeCompletion(
                    text=template,
                    start_line=context.cursor_line,
                    end_line=context.cursor_line,
                    start_column=context.cursor_column,
                    end_column=context.cursor_column,
                    confidence=0.9,
                    completion_type="snippet",
                    description="函数模板"
                ))
        
        # 检查是否在类定义中
        if "class " in current_line:
            template = templates.get("class", "")
            if template:
                suggestions.append(CodeCompletion(
                    text=template,
                    start_line=context.cursor_line,
                    end_line=context.cursor_line,
                    start_column=context.cursor_column,
                    end_column=context.cursor_column,
                    confidence=0.9,
                    completion_type="snippet",
                    description="类模板"
                ))
        
        return suggestions
    
    def _build_completion_prompt(self, context: CodeContext) -> str:
        """构建补全提示词"""
        # 获取上下文代码
        lines = context.content.split('\n')
        start_line = max(0, context.cursor_line - 10)
        end_line = min(len(lines), context.cursor_line + 5)
        context_code = '\n'.join(lines[start_line:end_line])
        
        prompt = f"""
请为以下代码提供补全建议：

语言: {context.language}
文件: {context.file_path}

代码上下文:
{context_code}

光标位置: 第{context.cursor_line}行，第{context.cursor_column}列

请提供3-5个最相关的代码补全建议，包括：
1. 函数调用
2. 变量名
3. 导入语句
4. 代码片段

格式：
- 建议文本
- 置信度 (0-1)
- 类型 (function/variable/import/snippet)
- 描述
"""
        
        return prompt
    
    def _filter_suggestions(self, suggestions: List[CodeCompletion], context: CodeContext) -> List[CodeCompletion]:
        """过滤建议"""
        filtered = []
        threshold = self.config["completion"]["confidence_threshold"]
        
        for suggestion in suggestions:
            if suggestion.confidence >= threshold:
                # 检查是否与现有代码重复
                if not self._is_duplicate(suggestion, context):
                    filtered.append(suggestion)
        
        return filtered
    
    def _is_duplicate(self, suggestion: CodeCompletion, context: CodeContext) -> bool:
        """检查建议是否重复"""
        # 简化的重复检查
        current_line = context.content.split('\n')[context.cursor_line - 1]
        return suggestion.text.strip() in current_line
    
    def _sort_suggestions(self, suggestions: List[CodeCompletion]) -> List[CodeCompletion]:
        """排序建议"""
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _generate_cache_key(self, context: CodeContext) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{context.file_path}:{context.cursor_line}:{context.cursor_column}:{context.language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _update_cache(self, cache_key: str, suggestions: List[CodeCompletion]):
        """更新缓存"""
        if len(self.completion_cache) >= self.config["completion"]["cache_size"]:
            # 删除最旧的缓存项
            oldest_key = next(iter(self.completion_cache))
            del self.completion_cache[oldest_key]
        
        self.completion_cache[cache_key] = suggestions
    
    def _update_stats(self, response_time: float):
        """更新统计信息"""
        self.stats["total_completions"] += 1
        
        # 计算平均响应时间
        current_avg = self.stats["average_response_time"]
        total_completions = self.stats["total_completions"]
        
        new_avg = (current_avg * (total_completions - 1) + response_time) / total_completions
        self.stats["average_response_time"] = new_avg
    
    async def get_suggestions_for_word(self, word: str, context: CodeContext) -> List[str]:
        """获取单词补全建议"""
        suggestions = []
        language = context.language.lower()
        
        if language in self.config["languages"]:
            language_config = self.config["languages"][language]
            
            # 检查内置函数
            for builtin in language_config["builtins"]:
                if builtin.startswith(word.lower()):
                    suggestions.append(builtin)
            
            # 检查关键字
            for keyword in language_config["keywords"]:
                if keyword.startswith(word.lower()):
                    suggestions.append(keyword)
        
        return suggestions[:5]  # 限制数量
    
    async def get_function_signature(self, function_name: str, context: CodeContext) -> Optional[str]:
        """获取函数签名"""
        # 这里可以实现函数签名提示
        # 目前返回模拟数据
        signatures = {
            "print": "print(*values, sep=' ', end='\\n', file=sys.stdout, flush=False)",
            "len": "len(obj) -> int",
            "str": "str(object='') -> str",
            "int": "int(x=0) -> int",
            "float": "float(x=0.0) -> float"
        }
        
        return signatures.get(function_name)
    
    async def get_documentation(self, symbol: str, context: CodeContext) -> Optional[str]:
        """获取符号文档"""
        # 这里可以实现文档提示
        # 目前返回模拟数据
        docs = {
            "print": "打印值到标准输出流",
            "len": "返回对象的长度",
            "str": "将对象转换为字符串",
            "int": "将对象转换为整数",
            "float": "将对象转换为浮点数"
        }
        
        return docs.get(symbol)
    
    async def get_suggestions_for_import(self, module_name: str, context: CodeContext) -> List[str]:
        """获取导入建议"""
        suggestions = []
        
        # 常见模块
        common_modules = [
            "os", "sys", "json", "datetime", "time", "math", "random",
            "collections", "itertools", "functools", "operator"
        ]
        
        for module in common_modules:
            if module.startswith(module_name.lower()):
                suggestions.append(module)
        
        return suggestions[:5]
    
    async def get_suggestions_for_path(self, path: str, context: CodeContext) -> List[str]:
        """获取路径建议"""
        suggestions = []
        
        try:
            path_obj = Path(path)
            if path_obj.exists() and path_obj.is_dir():
                for item in path_obj.iterdir():
                    if item.name.startswith(path.split('/')[-1]):
                        suggestions.append(str(item))
        except Exception:
            pass
        
        return suggestions[:5]
    
    async def get_completion_stats(self) -> Dict[str, Any]:
        """获取补全统计信息"""
        return {
            "total_completions": self.stats["total_completions"],
            "cache_hits": self.stats["cache_hits"],
            "cache_hit_rate": self.stats["cache_hits"] / max(1, self.stats["total_completions"]),
            "average_response_time": self.stats["average_response_time"],
            "cache_size": len(self.completion_cache),
            "supported_languages": list(self.config["languages"].keys())
        }
    
    async def cleanup(self):
        """清理资源"""
        self.completion_cache.clear()
        logger.info("AI代码补全服务清理完成")

# 全局实例
ai_code_completion = AICodeCompletion()

async def main():
    """主函数 - 用于测试"""
    completion = AICodeCompletion()
    
    # 初始化
    if await completion.initialize():
        print("✅ AI代码补全服务初始化成功")
        
        # 测试代码上下文
        context = CodeContext(
            file_path="test.py",
            language="python",
            content="def hello_world():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello_world()",
            cursor_line=5,
            cursor_column=8,
            imports=["os", "sys"],
            functions=["hello_world"],
            variables=[],
            classes=[]
        )
        
        # 获取补全建议
        suggestions = await completion.get_completions(context)
        print(f"🔍 补全建议: {len(suggestions)} 个")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion.text} (置信度: {suggestion.confidence:.2f})")
            print(f"     类型: {suggestion.completion_type}")
            print(f"     描述: {suggestion.description}")
        
        # 获取统计信息
        stats = await completion.get_completion_stats()
        print(f"\n📊 统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        # 清理
        await completion.cleanup()
    else:
        print("❌ AI代码补全服务初始化失败")

if __name__ == "__main__":
    asyncio.run(main())
