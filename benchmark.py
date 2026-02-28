"""
OCR引擎性能基准测试
用于比较不同OCR引擎在身份证识别上的性能
"""

import time
import json
from pathlib import Path
from typing import List, Dict
import numpy as np
import cv2

from id_card_recognizer import IDCardRecognizer
from ocr_engines import list_engines


class OCRBenchmark:
    """OCR基准测试"""
    
    def __init__(self, engines: List[str] = None, use_gpu: bool = False):
        """
        初始化基准测试
        
        Args:
            engines: 要测试的引擎列表
            use_gpu: 是否使用GPU
        """
        self.engines = engines or list_engines()
        self.use_gpu = use_gpu
        self.results = {}
        
    def run_benchmark(self, image_paths: List[str], 
                      num_runs: int = 3) -> Dict:
        """
        运行基准测试
        
        Args:
            image_paths: 测试图像路径列表
            num_runs: 每张图像运行次数
            
        Returns:
            测试结果
        """
        results = {}
        
        for engine in self.engines:
            print(f"\n正在测试 {engine}...")
            print("-" * 40)
            
            try:
                recognizer = IDCardRecognizer(engine=engine, use_gpu=self.use_gpu)
                
                engine_results = {
                    "times": [],
                    "confidences": [],
                    "successes": 0,
                    "failures": 0,
                    "errors": []
                }
                
                for img_path in image_paths:
                    for run in range(num_runs):
                        try:
                            start = time.time()
                            info = recognizer.recognize(img_path)
                            elapsed = (time.time() - start) * 1000
                            
                            engine_results["times"].append(elapsed)
                            engine_results["confidences"].append(info.confidence)
                            engine_results["successes"] += 1
                            
                        except Exception as e:
                            engine_results["failures"] += 1
                            engine_results["errors"].append(str(e))
                
                # 计算统计数据
                times = engine_results["times"]
                confs = engine_results["confidences"]
                
                results[engine] = {
                    "avg_time_ms": np.mean(times) if times else 0,
                    "min_time_ms": np.min(times) if times else 0,
                    "max_time_ms": np.max(times) if times else 0,
                    "std_time_ms": np.std(times) if times else 0,
                    "avg_confidence": np.mean(confs) if confs else 0,
                    "success_rate": engine_results["successes"] / (engine_results["successes"] + engine_results["failures"]) if (engine_results["successes"] + engine_results["failures"]) > 0 else 0,
                    "total_tests": engine_results["successes"] + engine_results["failures"],
                    "errors": engine_results["errors"][:5]  # 只保留前5个错误
                }
                
                print(f"  平均耗时: {results[engine]['avg_time_ms']:.2f}ms")
                print(f"  平均置信度: {results[engine]['avg_confidence']:.3f}")
                print(f"  成功率: {results[engine]['success_rate']*100:.1f}%")
                
            except Exception as e:
                results[engine] = {
                    "error": str(e),
                    "success_rate": 0
                }
                print(f"  引擎初始化失败: {e}")
        
        self.results = results
        return results
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("OCR引擎性能对比摘要")
        print("=" * 80)
        
        # 表头
        print(f"{'引擎':<15} {'平均耗时(ms)':<15} {'置信度':<12} {'成功率':<12} {'状态':<10}")
        print("-" * 80)
        
        for engine, result in self.results.items():
            if "error" in result and result.get("avg_time_ms", 0) == 0:
                print(f"{engine:<15} {'N/A':<15} {'N/A':<12} {'N/A':<12} {'失败':<10}")
            else:
                status = "✓" if result["success_rate"] > 0.8 else "⚠"
                print(f"{engine:<15} {result['avg_time_ms']:<15.2f} {result['avg_confidence']:<12.3f} {result['success_rate']*100:<11.1f}% {status:<10}")
        
        print("-" * 80)
        
        # 找出最佳引擎
        best_speed = min(
            (e for e, r in self.results.items() if r.get("avg_time_ms", float('inf')) > 0),
            key=lambda e: self.results[e]["avg_time_ms"],
            default=None
        )
        best_accuracy = max(
            (e for e, r in self.results.items() if r.get("avg_confidence", 0) > 0),
            key=lambda e: self.results[e]["avg_confidence"],
            default=None
        )
        
        if best_speed:
            print(f"\n速度最快: {best_speed} ({self.results[best_speed]['avg_time_ms']:.2f}ms)")
        if best_accuracy:
            print(f"准确率最高: {best_accuracy} ({self.results[best_accuracy]['avg_confidence']:.3f})")
    
    def save_results(self, output_path: str = "benchmark_results.json"):
        """保存测试结果到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n测试结果已保存到: {output_path}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR引擎基准测试")
    parser.add_argument("images", nargs="+", help="测试图像路径")
    parser.add_argument("-n", "--num-runs", type=int, default=3,
                       help="每张图像运行次数 (默认: 3)")
    parser.add_argument("-e", "--engines", nargs="+",
                       help="要测试的引擎列表")
    parser.add_argument("--gpu", action="store_true",
                       help="使用GPU加速")
    parser.add_argument("-o", "--output", default="benchmark_results.json",
                       help="结果输出文件")
    
    args = parser.parse_args()
    
    # 检查文件
    valid_images = [p for p in args.images if Path(p).exists()]
    if not valid_images:
        print("没有找到有效的测试图像")
        return
    
    print(f"测试图像数量: {len(valid_images)}")
    print(f"每张图像运行次数: {args.num_runs}")
    print(f"GPU模式: {'开启' if args.gpu else '关闭'}")
    
    # 运行测试
    benchmark = OCRBenchmark(engines=args.engines, use_gpu=args.gpu)
    benchmark.run_benchmark(valid_images, num_runs=args.num_runs)
    benchmark.print_summary()
    benchmark.save_results(args.output)


if __name__ == "__main__":
    main()
