#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: yyc3_code_agent.py
description: YYC³ CodeGeeX4 Agent - 基于 CodeGeeX4 的智能代码助手
author: YanYuCloudCube Team <admin@0379.email>
version: v1.0.0
created: 2026-04-06
updated: 2026-04-06
status: active
tags: [agent],[codegeex4],[code-generation]
category: agent
language: zh-CN
priority: high
"""

import sys
import os

try:
    from langchain_ollama import ChatOllama
except ImportError:
    print("❌ 错误: 未安装 langchain-ollama")
    print("请运行: pip install langchain-ollama")
    sys.exit(1)

class YYC3CodeAgent:
    """YYC³ CodeGeeX4 Agent"""
    
    def __init__(self, model="codegeex4", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.7,
        )
    
    def generate_code(self, prompt):
        """生成代码"""
        response = self.llm.invoke(prompt)
        return response.content
    
    def explain_code(self, code):
        """解释代码"""
        prompt = f"""请解释以下代码的功能和原理：

```
{code}
```"""
        response = self.llm.invoke(prompt)
        return response.content
    
    def debug_code(self, code, error=None):
        """调试代码"""
        if error:
            prompt = f"""请分析以下代码的错误并提供修复方案：

代码：
```
{code}
```

错误信息：
```
{error}
```"""
        else:
            prompt = f"""请分析以下代码的潜在问题并提供优化建议：

```
{code}
```"""
        
        response = self.llm.invoke(prompt)
        return response.content
    
    def chat(self, message):
        """对话"""
        response = self.llm.invoke(message)
        return response.content

def test_agent():
    """测试 Agent"""
    print("\n" + "="*60)
    print("🧪 YYC³ CodeGeeX4 Agent 测试")
    print("="*60)
    
    agent = YYC3CodeAgent()
    
    print("\n📝 测试 1: 代码生成")
    print("-"*60)
    code = agent.generate_code("写一个 Python 函数实现快速排序")
    print(code[:200] + "..." if len(code) > 200 else code)
    
    print("\n📖 测试 2: 代码解释")
    print("-"*60)
    explanation = agent.explain_code("def quicksort(arr): return arr if len(arr) <= 1 else quicksort([x for x in arr[1:] if x < arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x >= arr[0]])")
    print(explanation[:200] + "..." if len(explanation) > 200 else explanation)
    
    print("\n✅ 测试完成")

def interactive_mode():
    """交互模式"""
    print("\n" + "="*60)
    print("🎯 YYC³ CodeGeeX4 Agent 交互模式")
    print("="*60)
    print("输入 'quit' 或 'exit' 退出")
    print("-"*60)
    
    agent = YYC3CodeAgent()
    
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            response = agent.chat(user_input)
            print(f"\n🤖 CodeGeeX4: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_agent()
        elif command == "interactive":
            interactive_mode()
        else:
            print(f"未知命令: {command}")
            print_usage()
    else:
        print_usage()

def print_usage():
    """打印用法"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           YYC³ CodeGeeX4 Agent v1.0                          ║
╚══════════════════════════════════════════════════════════════╝

用法:
  python yyc3_code_agent.py test        # 运行测试
  python yyc3_code_agent.py interactive  # 交互模式

示例:
  # 生成代码
  python yyc3_code_agent.py interactive
  👤 您: 写一个 Python 函数实现二分查找
  
  # 解释代码
  👤 您: 解释这段代码: def foo(): pass
""")

if __name__ == "__main__":
    main()
