"""
测试覆盖率分析工具
用于分析当前测试覆盖率并识别需要补充测试的区域
"""

import os
import sys
import json
from typing import Dict, List, Any, Set
from pathlib import Path


class TestCoverageAnalyzer:
    """测试覆盖率分析器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests" / "unit"
        
    def analyze_coverage(self) -> Dict[str, Any]:
        """分析测试覆盖率"""
        analysis = {
            "total_files": 0,
            "tested_files": 0,
            "untested_files": [],
            "coverage_percentage": 0,
            "module_breakdown": {},
            "recommendations": []
        }
        
        # 获取所有源文件
        src_files = self._get_all_src_files()
        analysis["total_files"] = len(src_files)
        
        # 获取所有测试文件
        test_files = self._get_all_test_files()
        
        # 分析每个源文件的测试覆盖情况
        tested_files = []
        untested_files = []
        
        for src_file in src_files:
            module_name = self._get_module_name(src_file)
            has_test = self._has_test_file(module_name, test_files)
            
            if has_test:
                tested_files.append(src_file)
            else:
                untested_files.append(src_file)
                
            # 模块细分统计
            module_path = str(src_file.relative_to(self.src_dir).parent)
            if module_path not in analysis["module_breakdown"]:
                analysis["module_breakdown"][module_path] = {
                    "total": 0,
                    "tested": 0,
                    "untested": 0
                }
            
            analysis["module_breakdown"][module_path]["total"] += 1
            if has_test:
                analysis["module_breakdown"][module_path]["tested"] += 1
            else:
                analysis["module_breakdown"][module_path]["untested"] += 1
        
        analysis["tested_files"] = len(tested_files)
        analysis["untested_files"] = untested_files
        
        if src_files:
            analysis["coverage_percentage"] = (len(tested_files) / len(src_files)) * 100
        
        # 生成建议
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _get_all_src_files(self) -> List[Path]:
        """获取所有源文件"""
        src_files = []
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    src_files.append(Path(root) / file)
        return src_files
    
    def _get_all_test_files(self) -> List[Path]:
        """获取所有测试文件"""
        test_files = []
        for root, dirs, files in os.walk(self.tests_dir):
            for file in files:
                if file.endswith('.py') and file.startswith('test_'):
                    test_files.append(Path(root) / file)
        return test_files
    
    def _get_module_name(self, src_file: Path) -> str:
        """获取模块名称"""
        relative_path = src_file.relative_to(self.src_dir)
        module_name = str(relative_path).replace('\\', '.').replace('/', '.').replace('.py', '')
        return module_name
    
    def _has_test_file(self, module_name: str, test_files: List[Path]) -> bool:
        """检查是否有对应的测试文件"""
        expected_test_name = f"test_{module_name.replace('.', '_')}.py"
        
        for test_file in test_files:
            if test_file.name == expected_test_name:
                return True
                
        # 检查是否有部分匹配的测试文件
        for test_file in test_files:
            if module_name.replace('.', '_') in test_file.name:
                return True
                
        return False
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 总体覆盖率建议
        coverage = analysis["coverage_percentage"]
        if coverage < 50:
            recommendations.append(f"当前测试覆盖率较低 ({coverage:.1f}%)，建议优先补充核心模块的测试")
        elif coverage < 80:
            recommendations.append(f"测试覆盖率中等 ({coverage:.1f}%)，建议补充缺失的重要功能测试")
        else:
            recommendations.append(f"测试覆盖率良好 ({coverage:.1f}%)，建议完善边缘情况和错误处理测试")
        
        # 模块级别的建议
        for module_path, stats in analysis["module_breakdown"].items():
            module_coverage = (stats["tested"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            
            if module_coverage < 50:
                recommendations.append(f"模块 '{module_path}' 测试覆盖率较低 ({module_coverage:.1f}%)，建议优先补充")
            elif module_coverage < 80:
                recommendations.append(f"模块 '{module_path}' 测试覆盖率中等 ({module_coverage:.1f}%)，建议补充重要功能测试")
        
        # 未测试文件建议
        if analysis["untested_files"]:
            untested_count = len(analysis["untested_files"])
            recommendations.append(f"有 {untested_count} 个文件没有对应的测试，建议创建相应的测试文件")
            
            # 列出前5个未测试的重要文件
            important_untested = []
            for file in analysis["untested_files"][:5]:
                file_name = str(file.relative_to(self.src_dir))
                if any(keyword in file_name for keyword in ['manager', 'adapter', 'core', 'model']):
                    important_untested.append(file_name)
            
            if important_untested:
                recommendations.append("重要未测试文件示例: " + ", ".join(important_untested))
        
        return recommendations
    
    def generate_report(self) -> str:
        """生成测试覆盖率报告"""
        analysis = self.analyze_coverage()
        
        report = []
        report.append("=" * 80)
        report.append("测试覆盖率分析报告")
        report.append("=" * 80)
        report.append("")
        
        # 总体统计
        report.append("总体统计:")
        report.append(f"  总源文件数: {analysis['total_files']}")
        report.append(f"  已测试文件数: {analysis['tested_files']}")
        report.append(f"  未测试文件数: {len(analysis['untested_files'])}")
        report.append(f"  测试覆盖率: {analysis['coverage_percentage']:.1f}%")
        report.append("")
        
        # 模块细分
        report.append("模块细分:")
        for module_path, stats in analysis["module_breakdown"].items():
            coverage = (stats["tested"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            report.append(f"  {module_path}: {stats['tested']}/{stats['total']} ({coverage:.1f}%)")
        report.append("")
        
        # 建议
        report.append("改进建议:")
        for i, recommendation in enumerate(analysis["recommendations"], 1):
            report.append(f"  {i}. {recommendation}")
        report.append("")
        
        # 未测试文件列表
        if analysis["untested_files"]:
            report.append("未测试文件列表:")
            for file in analysis["untested_files"][:10]:  # 只显示前10个
                file_name = str(file.relative_to(self.src_dir))
                report.append(f"  - {file_name}")
            if len(analysis["untested_files"]) > 10:
                report.append(f"  ... 还有 {len(analysis['untested_files']) - 10} 个文件")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    analyzer = TestCoverageAnalyzer(project_root)
    
    report = analyzer.generate_report()
    print(report)
    
    # 保存报告到文件
    report_file = Path(project_root) / "docs" / "TEST_COVERAGE_ANALYSIS.md"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n详细报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
