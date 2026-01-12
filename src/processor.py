import re

def extract_code(text: str) -> str:
    """
    从模型回复中提取纯净的 Python 代码。
    
    参数:
        text: 模型生成的原始字符串 (Raw Generation)
    返回:
        clean_code: 清洗后的 Python 代码字符串
    """
    if not text:
        return ""

    # 1. 尝试匹配 ```python ... ``` 代码块
    # re.DOTALL 标志让 '.' 可以匹配换行符，确保多行代码被捕获
    python_block_pattern = r"```python\s*(.*?)```"
    match = re.search(python_block_pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # 2. 如果没有 python 标签，尝试匹配通用 ``` ... ``` 代码块
    generic_block_pattern = r"```\s*(.*?)```"
    match = re.search(generic_block_pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip()

    # 3. [兜底策略] 如果没有 Markdown 标记
    # 有些模型比较懒，直接输出代码不加格式。
    # 为了防止把 "Here is the code:" 这种话也当成代码，我们可以做一个简单的启发式过滤
    # 但在 HumanEval 的场景下，通常直接返回原文即可，让后续的解释器去报错比吞掉代码好。
    return text.strip()

# --- 单元测试部分 ---
# 下面的代码只有当你直接运行 python src/processor.py 时才会执行
if __name__ == "__main__":
    print("🧪 开始测试代码提取功能...")

    # 测试用例 1: 标准 Markdown 格式
    case1 = """
    Sure, here is the solution:
    ```python
    def add(a, b):
        return a + b
    ```
    Hope it works!
    """
    assert extract_code(case1) == "def add(a, b):\n        return a + b", "测试用例 1 失败"
    print("✅ 测试用例 1 (标准格式): 通过")

    # 测试用例 2: 没有指定语言的 Markdown
    case2 = """
    ```
    def sub(a, b):
        return a - b
    ```
    """
    assert extract_code(case2) == "def sub(a, b):\n        return a - b", "测试用例 2 失败"
    print("✅ 测试用例 2 (无语言标记): 通过")

    # 测试用例 3: 纯文本 (兜底)
    case3 = "def mul(a, b):\n    return a * b"
    assert extract_code(case3) == case3, "测试用例 3 失败"
    print("✅ 测试用例 3 (纯文本): 通过")

    print("\n🎉 所有测试通过！Processor 模块准备就绪。")