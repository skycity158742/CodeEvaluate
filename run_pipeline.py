import json
import os
import time
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 导入模块
from src.data_loader import get_humaneval_data
from src.generator import generate_one_completion
from src.processor import extract_code
from src.evaluator import evaluate_code

OUTPUT_FILE = "results/humaneval_results.jsonl"

# --- 并发设置 ---
MAX_WORKERS = 5  # 同时处理 5 道题 (建议不要设置太大，防止触发 API 限流)

def process_one_problem(problem):
    task_id = problem['task_id']
    prompt = problem['prompt']
    entry_point = problem['entry_point']
    test_case = problem['test']
    
    # 1. 生成
    start_gen = time.time()
    try:
        raw_completion = generate_one_completion(prompt)
    except Exception:
        raw_completion = ""
    gen_time = time.time() - start_gen
    
    # 2. 清洗
    clean_code = extract_code(raw_completion)
    
    if not clean_code:
        return {
            "task_id": task_id, "prompt": prompt, "completion": "", 
            "clean_code": "", "status": "API_Error", "gen_time": "0.00s"
        }

    # --- 🛠️ 逻辑简化：优先信任模型输出的完整代码 🛠️ ---
    
    # 检查模型是否听话地输出了 "def 函数名"
    if f"def {entry_point}" in clean_code:
        # 完美情况：模型输出了完整的函数，直接用它的
        # 注意：这里我们甚至不需要再拼 import，因为提示词要求模型自己写 import
        final_code_to_test = clean_code
    else:
        # 兜底情况：模型还是只输出了函数体（虽然概率很低，但防一手）
        # 这种情况下，我们简单粗暴地拼接
        final_code_to_test = prompt + "\n" + clean_code

    # ----------------------------------------------------
    
    # 3. 验证
    status = evaluate_code(final_code_to_test, test_case, entry_point)
    
    return {
        "task_id": task_id,
        "prompt": prompt,
        "completion": raw_completion,
        "clean_code": clean_code, 
        "final_code": final_code_to_test, 
        "status": status,
        "gen_time": f"{gen_time:.2f}s"
    }

def main(num_samples=None):
    # 1. 加载数据
    problems = get_humaneval_data()
    if num_samples:
        print(f"⚠️ 测试模式: 仅运行前 {num_samples} 道题目...")
        problems = problems[:num_samples]
    
    # 清空或创建结果文件
    open(OUTPUT_FILE, "w", encoding="utf-8").close()
    
    results = []
    passed_count = 0
    total = len(problems)
    
    print(f"🚀 开始评估流程 (并发数: {MAX_WORKERS})...")
    
    # 2. 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_problem = {executor.submit(process_one_problem, p): p for p in problems}
        
        # 使用 tqdm 显示进度，as_completed 会在某个任务完成时立刻返回
        for future in tqdm(as_completed(future_to_problem), total=total, desc="Evaluating"):
            try:
                result = future.result()
                
                # 写入文件
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                
                if result["status"] == "Passed":
                    passed_count += 1
                    
                # 可以在这里打印一下耗时太久的任务，看看是不是 API 的锅
                print(f"完成 {result['task_id']}，耗时: {result['gen_time']}，结果: {result['status']}")
                
            except Exception as e:
                print(f"❌ 处理某道题时发生异常: {e}")

    # 3. 统计
    accuracy = (passed_count / total) * 100
    print("\n" + "="*40)
    print(f"📊 评估结束!")
    print(f"总题目数: {total}")
    print(f"通过数量: {passed_count}")
    print(f"Pass@1 准确率: {accuracy:.2f}%")
    print("="*40)
    print(f"详细结果已保存至: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    # 建议先跑 10 道题试试速度
    main(num_samples=10)