import multiprocessing
import sys
import io

# 设置超时时间 (秒)
TIMEOUT_SECONDS = 30

def _temp_run(code, result_queue):
    """
    这是一个在子进程中运行的函数。
    它会尝试执行传入的代码字符串。
    """
    try:
        # 1. 捕获 stdout/stderr，防止控制台被打印刷屏
        # 虽然我们要运行代码，但不希望它乱打印东西干扰主程序
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()

        # 2. 创建一个新的全局命名空间字典
        # 这样代码运行产生变量不会污染主进程
        exec_globals = {}
        
        # 3. 执行代码
        # exec() 是 Python 内置的动态执行函数
        exec(code, exec_globals)
        
        # 4. 如果没报错，就是通过
        result_queue.put("Passed")
        
    except AssertionError:
        # 如果触发了 assert 错误，说明测试没通过
        result_queue.put("Failed: Assertion Error")
    except Exception as e:
        # 其他运行时错误 (如 SyntaxError, TypeError)
        result_queue.put(f"Failed: {type(e).__name__}: {str(e)}")
    finally:
        # 恢复标准输出
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

def evaluate_code(code: str, test_code: str, entry_point: str) -> str:
    """
    核心评估函数
    :param code: 模型生成的函数代码
    :param test_code: HumanEval 提供的测试代码 (通常包含 check 函数)
    :param entry_point: 待测函数的名称 (如 "has_close_elements")
    :return: 结果字符串 ("Passed", "Failed...", "Timeout")
    """
    
    # --- 1. 组装“三明治”代码 ---
    # 必须引入 typing 库，因为 HumanEval 很多题目依赖 List, Tuple 等
    header = "from typing import *\nimport math\nimport hashlib\n\n"
    
    # 触发器：HumanEval 的测试通常定义了一个 check(candidate) 函数
    # 我们需要手动调用它： check(你的函数名)
    execution_trigger = f"\ncheck({entry_point})"
    
    full_code = header + code + "\n" + test_code + "\n" + execution_trigger
    
    # --- 2. 在子进程中运行 ---
    # 使用 Queue 来获取子进程的结果
    queue = multiprocessing.Queue()
    
    # 创建子进程
    p = multiprocessing.Process(target=_temp_run, args=(full_code, queue))
    p.start()
    
    # 等待子进程结束，或者超时
    p.join(TIMEOUT_SECONDS)
    
    if p.is_alive():
        # 如果还在跑，说明超时了 (可能是死循环)
        p.terminate()
        p.join() # 确保资源释放
        return "Timeout"
    
    if not queue.empty():
        return queue.get()
    else:
        # 子进程意外退出（极少见）
        return "Failed: Unknown Error"

# --- 单元测试 ---
if __name__ == "__main__":
    print("🧪 开始测试沙盒环境...")

    # 模拟一个正确的代码
    correct_code = """
def add(a, b):
    return a + b
"""
    # 模拟测试用例
    test_case = """
def check(candidate):
    assert candidate(1, 1) == 2
    assert candidate(2, 3) == 5
"""
    entry = "add"
    
    print(f"测试 1 (正确代码): {evaluate_code(correct_code, test_case, entry)}")

    # 模拟一个死循环代码
    infinite_loop_code = """
def add(a, b):
    while True:
        pass
"""
    print(f"测试 2 (死循环): {evaluate_code(infinite_loop_code, test_case, entry)}")
    
    # 模拟一个逻辑错误代码
    wrong_code = """
def add(a, b):
    return a - b
"""
    print(f"测试 3 (错误代码): {evaluate_code(wrong_code, test_case, entry)}")