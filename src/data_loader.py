import os
from datasets import load_dataset

# 【重要】如果你在国内，取消下面这行的注释，使用 HF 镜像站加速下载
# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

def get_humaneval_data():
    """
    加载 OpenAI HumanEval 数据集
    返回: 一个包含所有题目的列表 (List[Dict])
    """
    print("⏳ 正在从 Hugging Face 加载 HumanEval 数据集...")
    
    try:
        # split="test" 是必须的，因为 HumanEval 只有测试集
        dataset = load_dataset("openai_humaneval", split="test")
        
        problems = []
        for item in dataset:
            # 将 HF 的 Dataset 对象转换为标准的 Python 字典，方便后续处理
            problem = {
                'task_id': item['task_id'],           # 题目ID, 如 'HumanEval/0'
                'prompt': item['prompt'],             # 输入给模型的题目描述
                'entry_point': item['entry_point'],   # 函数名
                'test': item['test'],                 # 测试用例代码
                'canonical_solution': item['canonical_solution'] # 参考答案
            }
            problems.append(problem)
            
        print(f"✅ 成功加载 {len(problems)} 道题目。")
        return problems
    
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return []

# --- 单元测试代码 ---
# 这段代码只有直接运行此文件时才会执行，被其他文件 import 时不会执行
if __name__ == "__main__":
    data = get_humaneval_data()
    
    if data:
        print("\n--- 示例题目预览 (第一题) ---")
        print(f"题目ID: {data[0]['task_id']}")
        print(f"函数名: {data[0]['entry_point']}")
        print("-" * 20)
        print(f"Prompt (喂给模型的内容):\n{data[0]['prompt']}")
        print("-" * 20)
        print("测试用例片段 (用于验证):\n" + data[0]['test'][:100] + "...")