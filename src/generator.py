import os
import time
from openai import OpenAI

# =================配置区域=================
# 建议将 API Key 写入环境变量: export DEEPSEEK_API_KEY="sk-..."
# 或者直接在这里填入（注意不要把带有 Key 的代码传到公开仓库）
API_KEY = os.getenv("DEEPSEEK_API_KEY", "") 
BASE_URL = "https://api.siliconflow.cn/v1"
# =========================================

# 初始化客户端
# client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def generate_one_completion(prompt):
    """
    调用 DeepSeek 模型生成代码 (带重试机制)
    """
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="Pro/deepseek-ai/DeepSeek-V3",
                messages=[
                    {
                        "role": "system", "content": """你是一个精通Python的编程专家。你的任务是编写完整的、自包含的函数代码。
                        【严格遵守以下规则】
                        1. 必须输出完整的代码：包含所有必要的 import 语句、函数定义(def)、文档字符串(docstring)和具体的函数体实现。
                        2. 即使函数签名已给出，你也许**完整复述**一遍，不能只写函数体。
                        3. 保持缩进规范（使用4个空格）。
                        4. 代码必须包裹在 ```python 和 ``` 之间。
                        5. 不要输出任何解释、注释或测试用例，只输出代码本身。"""
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=512,
                
                # 🔥【关键修改】强制 90 秒超时
                # 如果 90s 没结果，直接抛出 APITimeoutError，触发重试
                timeout=90.0
            )
            return response.choices[0].message.content

        except Exception as e:
            # 打印简短的错误日志
            print(f"⚠️ 生成失败 (尝试 {attempt+1}/{max_retries}): {type(e).__name__} - {e}")
            
            # 如果是最后一次尝试依然失败，返回空字符串
            if attempt == max_retries - 1:
                print(f"❌ 最终放弃该题目。")
                return ""
            
            # 失败后稍微睡一秒再重试
            time.sleep(1)

    return ""

# --- 单元测试 ---
if __name__ == "__main__":
    test_prompt = "def hello_world():\n    \"\"\"Docstring\"\"\""
    print(generate_one_completion(test_prompt))