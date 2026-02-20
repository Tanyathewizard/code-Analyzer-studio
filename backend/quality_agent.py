import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum

class QualityGrade(Enum):
    A = "Excellent"
    B = "Good"
    C = "Average"
    D = "Below Average"
    F = "Poor"

@dataclass
class QualityMetrics:
    readability_score: float = 0.0
    avg_line_length: float = 0.0
    naming_convention_score: float = 0.0
    comment_ratio: float = 0.0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    nesting_depth: int = 0
    maintainability_index: float = 0.0
    code_duplication_ratio: float = 0.0
    function_length_avg: float = 0.0
    algorithmic_efficiency: str = "Unknown"
    memory_patterns: List[str] = field(default_factory=list)
    performance_issues: List[str] = field(default_factory=list)
    security_vulnerabilities: List[str] = field(default_factory=list)
    unsafe_patterns: List[str] = field(default_factory=list)
    overall_grade: str = "C"
    overall_score: float = 0.0

class CodeQualityEvaluator:
    def __init__(self):
        self.metrics = QualityMetrics()
        self.issues = []
        self.recommendations = []

    def evaluate(self, code: str, language: str = "python",
                 analyzer_results: Optional[Dict] = None,
                 semantic_results: Optional[Dict] = None) -> Dict[str, Any]:
        self.metrics = QualityMetrics()
        self.issues = []
        self.recommendations = []
        self._evaluate_readability(code)
        self._evaluate_complexity(code)
        self._evaluate_maintainability(code)
        self._evaluate_efficiency(code, semantic_results)
        self._evaluate_security(code)
        if analyzer_results:
            self._integrate_analyzer_results(analyzer_results)
        if semantic_results:
            self._integrate_semantic_results(semantic_results)
        self._calculate_overall_score()
        self._generate_recommendations()
        return self._generate_report()

    def _evaluate_readability(self, code: str):
        lines = [l for l in code.split("\n") if l.strip()]
        self.metrics.avg_line_length = sum(map(len, lines)) / len(lines) if lines else 0
        long_lines = sum(1 for l in lines if len(l) > 100)
        if long_lines > len(lines) * 0.2:
            self.issues.append({"category": "Readability", "severity": "Medium",
                                "message": f"{long_lines} lines exceed 100 characters"})
        self.metrics.naming_convention_score = self._analyze_naming_conventions(code)
        comments = len([l for l in lines if l.strip().startswith("#")])
        self.metrics.comment_ratio = comments / len(lines) if lines else 0
        self.metrics.readability_score = (
            max(0, 100 - (self.metrics.avg_line_length - 60)) * 0.3 +
            self.metrics.naming_convention_score * 0.4 +
            min(100, self.metrics.comment_ratio * 300) * 0.3
        )
        if self.metrics.readability_score < 60:
            self.issues.append({"category": "Readability", "severity": "High",
                                "message": f"Low readability score: {self.metrics.readability_score:.1f}/100"})

    def _analyze_naming_conventions(self, code: str) -> float:
        identifiers = [
            i for i in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", code)
            if i not in {"def", "class", "if", "else", "for", "while", "try", "except",
                         "import", "from", "return", "True", "False", "None"} and len(i) > 1
        ]
        if not identifiers:
            return 100
        valid = sum(
            1 for i in identifiers
            if re.match(r"^([a-z_][a-z0-9_]*|[A-Z][a-zA-Z0-9]*)$", i)
        )
        return valid / len(identifiers) * 100

    def _evaluate_complexity(self, code: str):
        self.metrics.cyclomatic_complexity = (
            len(re.findall(r"\b(if|elif|for|while|and|or|except)\b", code)) + 1
        )
        self.metrics.nesting_depth = max(
            ((len(l) - len(l.lstrip())) // 4)
            for l in code.split("\n")
            if l.strip() and not l.strip().startswith("#")
        ) if code.strip() else 0
        self.metrics.cognitive_complexity = sum(
            1 + sum(1 for _ in re.finditer(r"if|elif|for|while|except|with", l.strip()))
            for l in code.split("\n")
        )
        if self.metrics.cyclomatic_complexity > 10:
            self.issues.append({"category": "Complexity", "severity": "High",
                                "message": f"High cyclomatic complexity: {self.metrics.cyclomatic_complexity}"})
        if self.metrics.nesting_depth > 4:
            self.issues.append({"category": "Complexity", "severity": "High",
                                "message": f"Deep nesting: {self.metrics.nesting_depth} levels"})

    def _evaluate_maintainability(self, code: str):
        lines = [l for l in code.split("\n") if l.strip() and not l.strip().startswith("#")]
        functions = re.findall(r"def\s+\w+\([^)]*\):", code)
        self.metrics.function_length_avg = len(lines) / len(functions) if functions else 0
        if self.metrics.function_length_avg > 50:
            self.issues.append({"category": "Maintainability", "severity": "Medium",
                                "message": f"Large average function size: {self.metrics.function_length_avg:.0f} lines"})
        self.metrics.code_duplication_ratio = self._detect_duplication(lines)
        if self.metrics.code_duplication_ratio > 0.1:
            self.issues.append({"category": "Maintainability", "severity": "Medium",
                                "message": f"Code duplication detected: {self.metrics.code_duplication_ratio * 100:.1f}%"})
        volume = len(lines) * 2.4
        complexity = self.metrics.cyclomatic_complexity
        mi = 171 - 5.2 * (volume ** 0.23) - 0.23 * complexity - 16.2 * (volume / max(1, complexity)) ** 0.5
        self.metrics.maintainability_index = max(0, min(100, mi))
        if self.metrics.maintainability_index < 50:
            self.issues.append({"category": "Maintainability", "severity": "High",
                                "message": f"Low maintainability index: {self.metrics.maintainability_index:.1f}/100"})

    def _detect_duplication(self, lines: List[str]) -> float:
        seen = set()
        duplicates = 0
        for i in range(len(lines) - 2):
            block = tuple(lines[i:i + 3])
            if block in seen:
                duplicates += 1
            else:
                seen.add(block)
        return duplicates / max(1, len(lines))

    def _evaluate_efficiency(self, code: str, semantic_results: Optional[Dict] = None):
        self.metrics.algorithmic_efficiency = "Linear or better"
        if len(re.findall(r"for\s+\w+.*:\s*\n\s+for\s+\w+", code)):
            self.metrics.algorithmic_efficiency = "O(n²) or worse"
            self.metrics.performance_issues.append("Nested loop detected - potential O(n²)")
        if "list(filter(" in code or "list(map(" in code:
            self.metrics.performance_issues.append("Consider using list comprehensions")
        if code.count(".append(") > 10:
            self.metrics.performance_issues.append("Multiple append() in loops")
        if "global " in code:
            self.metrics.memory_patterns.append("Uses global variables")
        if re.search(r"\[\s*\].*\*", code):
            self.metrics.memory_patterns.append("Uses list multiplication")
        if semantic_results and "complexity_analysis" in semantic_results:
            self.metrics.algorithmic_efficiency = semantic_results["complexity_analysis"].get(
                "time_complexity", self.metrics.algorithmic_efficiency
            )

    def _evaluate_security(self, code: str):
        if re.search(r'execute\(["\'].*%s.*["\']', code):
            self.metrics.security_vulnerabilities.append("Potential SQL injection")
        if "os.system(" in code or "subprocess.call(" in code:
            self.metrics.unsafe_patterns.append("Direct command execution")
        if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', code, re.I):
            self.metrics.security_vulnerabilities.append("Hardcoded credentials")
        if "eval(" in code or "exec(" in code:
            self.metrics.unsafe_patterns.append("Use of eval/exec")
        if "pickle.load" in code:
            self.metrics.unsafe_patterns.append("Pickle deserialization risk")
        for vuln in self.metrics.security_vulnerabilities:
            self.issues.append({"category": "Security", "severity": "Critical", "message": vuln})

    def _integrate_analyzer_results(self, results: Dict):
        self.metrics.cyclomatic_complexity = max(
            self.metrics.cyclomatic_complexity,
            results.get("complexity", 0)
        )
        for issue in results.get("issues", []):
            self.issues.append({
                "category": "Analyzer",
                "severity": issue.get("severity", "Medium"),
                "message": issue.get("message", str(issue))
            })

    def _integrate_semantic_results(self, results: Dict):
        for smell in results.get("code_smells", []):
            self.issues.append({"category": "Code Smell", "severity": "Low", "message": smell})
        if results.get("design_patterns"):
            self.recommendations.append(
                f"Good: Uses {len(results['design_patterns'])} design pattern(s)"
            )

    def _calculate_overall_score(self):
        scores = {
            "readability": (self.metrics.readability_score, 0.25),
            "complexity": (self._complexity_score(), 0.2),
            "maintainability": (self.metrics.maintainability_index, 0.25),
            "efficiency": (self._efficiency_score(), 0.15),
            "security": (self._security_score(), 0.15),
        }
        self.metrics.overall_score = sum(s * w for s, w in scores.values())
        grade_boundaries = [
            (90, QualityGrade.A),
            (80, QualityGrade.B),
            (70, QualityGrade.C),
            (60, QualityGrade.D),
        ]
        self.metrics.overall_grade = next(
            (g.value for b, g in grade_boundaries if self.metrics.overall_score >= b),
            QualityGrade.F.value
        )

    def _complexity_score(self) -> float:
        c = self.metrics.cyclomatic_complexity
        n = self.metrics.nesting_depth
        cog = self.metrics.cognitive_complexity
        return (
            max(0, 100 - (c - 1) * 5) +
            max(0, 100 - n * 15) +
            max(0, 100 - cog * 3)
        ) / 3

    def _efficiency_score(self) -> float:
        base = 80 if self.metrics.algorithmic_efficiency != "O(n²) or worse" else 40
        penalty = min(40, len(self.metrics.performance_issues) * 10)
        return max(0, base - penalty)

    def _security_score(self) -> float:
        score = 100 - (
            len(self.metrics.security_vulnerabilities) * 30 +
            len(self.metrics.unsafe_patterns) * 15
        )
        return max(0, score)

    def _generate_recommendations(self):
        if self.metrics.readability_score < 70:
            self.recommendations.append("Improve readability")
        if self.metrics.comment_ratio < 0.1:
            self.recommendations.append("Add more comments")
        if self.metrics.cyclomatic_complexity > 10:
            self.recommendations.append("Reduce cyclomatic complexity")
        if self.metrics.nesting_depth > 3:
            self.recommendations.append("Reduce nesting depth")
        if self.metrics.maintainability_index < 65:
            self.recommendations.append("Improve maintainability")
        if self.metrics.code_duplication_ratio > 0.05:
            self.recommendations.append("Eliminate code duplication")
        if self.metrics.performance_issues:
            self.recommendations.append("Optimize performance")
        if self.metrics.security_vulnerabilities or self.metrics.unsafe_patterns:
            self.recommendations.append("CRITICAL: Address security vulnerabilities immediately")

    def _generate_report(self) -> Dict[str, Any]:
        report = {
            "summary": {
                "overall_grade": self.metrics.overall_grade,
                "overall_score": round(self.metrics.overall_score, 2),
                "total_issues": len(self.issues),
                "critical_issues": len([i for i in self.issues if i["severity"] == "Critical"]),
            },
            "metrics": {k: v for k, v in asdict(self.metrics).items()},
            "issues": sorted(
                self.issues,
                key=lambda x: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}[x["severity"]],
            ),
            "recommendations": self.recommendations,
        }
        return report

    def save_report(self, filepath: str = "quality_result.txt"):
        report = self._generate_report()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\nCODE QUALITY EVALUATION REPORT\n" + "=" * 80 + "\n\n")
            f.write("SUMMARY\n" + "-" * 80 + "\n")
            for k, v in report["summary"].items():
                f.write(f"{k.replace('_', ' ').title()}: {v}\n")
            f.write("\nDETAILED METRICS\n" + "-" * 80 + "\n")
            f.write(json.dumps(report["metrics"], indent=2) + "\n\n")
            issues = report["issues"]
            if issues:
                f.write("ISSUES FOUND\n" + "-" * 80 + "\n")
                for i, issue in enumerate(issues, 1):
                    f.write(f"{i}. [{issue['severity']}] {issue['category']}: {issue['message']}\n")
            recs = report["recommendations"]
            if recs:
                f.write("\nRECOMMENDATIONS\n" + "-" * 80 + "\n")
                for i, r in enumerate(recs, 1):
                    f.write(f"{i}. {r}\n")
            f.write("\n" + "=" * 80 + "\n")

def pretty_print_evaluation(result: dict):
    print("\n" + "="*60)
    print("                 CODE QUALITY REPORT")
    print("="*60)
    print("\nSUMMARY:")
    print(result.get("summary", {}))
    print("\nMETRICS:")
    for k, v in result.get("metrics", {}).items():
        print(f"  - {k}: {v}")
    print("\nISSUES:")
    for i in result.get("issues", []):
        print(f"  - [{i['severity']}] {i['category']}: {i['message']}")
    print("\nRECOMMENDATIONS:")
    for r in result.get("recommendations", []):
        print(f"  - {r}")
    print("\nRAW JSON OUTPUT:")
    print(json.dumps(result, indent=4))
    print("\n" + "="*60 + "\n")
