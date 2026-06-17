#!/usr/bin/env python3
"""
Knowledge Generator V2 - 确定性代码知识库生成

核心改进：
1. AST 提取事实（100% 确定）
2. 路由类型自动检测（Gin REST vs Action 分发）
3. 置信度量化（每个事实带分数）
4. 输出验证（检测幻觉并修正）
5. 谨慎 Prompt（禁止编造）

架构：
  Repo → ASTExtractor → CodeFacts → ConfidenceEngine → (Fact, Score)
                                                 ↓
  Routes ← RouterExtractor ← Repo
    ↓
  PromptBuilder(Facts + Routes + Rules) → LLM → GeneratedDoc
                                                 ↓
  OutputVerifier(Facts) → VerificationResult → FinalDoc
"""

import os
import json
import hashlib
import sys
import urllib.request
import urllib.error
from datetime import datetime

# 检查是否被直接运行（应该通过 run_pipeline_v2.py 入口）
if __name__ == "__main__" and __package__ is None:
    print("⚠️  提示：请使用入口脚本运行:")
    print("   python3 _tools/run_pipeline_v2.py --system privatelink --repo apisvr")
    print("")
    print("不要直接运行 core/generator/pipeline_v2.py")
    sys.exit(1)
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

# 添加 core 到路径
_core_path = Path(__file__).parent.parent
if str(_core_path) not in sys.path:
    sys.path.insert(0, str(_core_path))

from interfaces import (
    CodeFact, RouteFact, FactSource, ConfidenceLevel,
    DocumentSection, CodeLocation
)
from extractors import (
    GoASTExtractor,
    GinRouterExtractor, ActionRouterExtractor,
    detect_route_type, get_router_extractor
)
# C 提取器待实现
# from extractors import CASTExtractor
from confidence import (
    ConfidenceEngine, ConfidenceScorer,
    OutputVerifier, VerificationResult,
    calculate_batch_confidence
)

# 导入生成器
from .prompt_builder import CautiousPromptBuilder
from .doc_assembler import MarkdownAssembler  # 稍后创建


# ═══════════════════════════════════════════════════════════════════════════
# 配置和常量
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "llm": {
        "base_url": "https://api.modelverse.cn",
        "default_model": "deepseek-ai/DeepSeek-V3.2",
        "max_tokens": 8000,
        "temperature": 0.1,  # 更低温度，更确定性
    },
    "confidence": {
        "min_for_generation": 0.3,  # 低于此分数不生成
        "flag_uncertain": 0.7,      # 低于此分数标注需确认
    },
    "output": {
        "vault_path": "~/Documents/Code/work/mywiki",
        "include_source_refs": True,
        "include_confidence": True,
    }
}


@dataclass
class GenerationConfig:
    """生成配置"""
    system: str
    repo: str
    repo_path: Path
    skip_extract: bool = False
    skip_generate: bool = False
    verify_output: bool = True
    min_confidence: float = 0.3


class KnowledgeGenerator:
    """
    知识库生成器 V2

    端到端生成流程：代码 → 事实 → 置信度 → 文档 → 验证
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}

        # 初始化组件
        self.confidence_engine = ConfidenceEngine()
        self.prompt_builder = CautiousPromptBuilder()

        # 状态
        self._current_repo: Optional[Path] = None
        self._facts: List[CodeFact] = []
        self._routes: List[RouteFact] = []
        self._confidence_stats: Optional[Dict] = None

    def generate(self, gen_config: GenerationConfig) -> Dict[str, Path]:
        """
        生成知识库文档

        Returns:
            {文档类型: 文件路径}
        """
        print(f"\n{'='*60}")
        print(f"Knowledge Generator V2 - {gen_config.system}/{gen_config.repo}")
        print(f"{'='*60}")

        self._current_repo = gen_config.repo_path

        # 阶段 1: AST 提取
        if not gen_config.skip_extract:
            print("\n[1/5] AST 提取代码事实...")
            self._facts = self._extract_facts(gen_config.repo_path)
            print(f"      提取 {len(self._facts)} 个代码事实")

            # 提取路由
            print("\n[1.5/5] 检测并提取路由...")
            self._routes = self._extract_routes(gen_config.repo_path)
            print(f"      发现 {len(self._routes)} 个路由映射")

            # 计算置信度
            print("\n[2/5] 计算置信度...")
            self._confidence_stats = calculate_batch_confidence(self._facts)
            print(f"      平均置信度: {self._confidence_stats['mean']:.2f}")
            print(f"      需审查: {self._confidence_stats['needs_review']} 个")
        else:
            print("\n[1-2/5] 跳过提取（使用缓存）")

        # 阶段 3: 生成文档
        if gen_config.skip_generate:
            print("\n[3-5/5] 跳过生成")
            return {}

        results = {}

        # 3.1 项目概览
        print("\n[3.1/5] 生成项目概览...")
        overview_doc = self._generate_overview(gen_config)
        if overview_doc:
            results['overview'] = overview_doc

        # 3.2 架构设计
        print("\n[3.2/5] 生成架构文档...")
        arch_doc = self._generate_architecture(gen_config)
        if arch_doc:
            results['architecture'] = arch_doc

        # 3.3 API 文档（关键：使用正确的路由类型）
        print("\n[3.3/5] 生成 API 文档...")
        api_doc = self._generate_api(gen_config)
        if api_doc:
            results['api'] = api_doc

        # 3.4 模块详情
        print("\n[3.4/5] 生成模块详情...")
        module_docs = self._generate_modules(gen_config)
        results.update(module_docs)

        # 3.5 数据库文档
        print("\n[3.5/5] 生成数据库文档...")
        db_doc = self._generate_db(gen_config)
        if db_doc:
            results['db'] = db_doc

        # 阶段 4: 组装最终文档
        print("\n[4/5] 组装最终文档...")
        final_paths = self._assemble_docs(results, gen_config)

        # 阶段 5: 验证（可选）
        if gen_config.verify_output:
            print("\n[5/5] 验证生成内容...")
            self._verify_outputs(final_paths, gen_config)

        print(f"\n{'='*60}")
        print(f"生成完成: {len(final_paths)} 个文档")
        for doc_type, path in final_paths.items():
            print(f"  - {doc_type}: {path}")

        return final_paths

    # ═══════════════════════════════════════════════════════════════════════
    # 内部方法：提取
    # ═══════════════════════════════════════════════════════════════════════

    def _extract_facts(self, repo_path: Path) -> List[CodeFact]:
        """提取所有代码事实"""
        all_facts = []

        # Go 文件
        try:
            go_extractor = GoASTExtractor()
            for go_file in sorted(repo_path.rglob("*.go")):
                if self._should_skip_file(go_file):
                    continue
                facts = go_extractor.extract(go_file, repo_path)
                all_facts.extend(facts)
        except ImportError as e:
            print(f"      ⚠️ Go 提取器不可用: {e}")

        # C 文件（未来扩展）
        # c_extractor = CASTExtractor()

        # 为所有事实计算置信度
        self.confidence_engine.index_facts(all_facts)
        for fact in all_facts:
            fact.confidence = self.confidence_engine.score_fact(fact, {})

        # 标记不确定性
        all_facts = self.confidence_engine.flag_uncertainties(all_facts)

        return all_facts

    def _extract_routes(self, repo_path: Path) -> List[RouteFact]:
        """提取路由映射"""
        extractor = get_router_extractor(repo_path)

        if not extractor:
            print("      ⚠️ 未能识别路由类型")
            return []

        route_type = detect_route_type(repo_path)
        print(f"      检测到路由类型: {route_type}")

        routes = extractor.extract_routes(repo_path)

        # 为路由计算置信度
        for route in routes:
            route.confidence = self.confidence_engine.score_fact(route, {})

        return routes

    def _should_skip_file(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        skip_patterns = [
            '_test.go', 'vendor/', '.pb.go', '.mock.go', '_gen.go',
            'node_modules/', 'third_party/'
        ]
        return any(p in str(file_path) for p in skip_patterns)

    # ═══════════════════════════════════════════════════════════════════════
    # 内部方法：生成各类文档
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_overview(self, config: GenerationConfig) -> Optional[str]:
        """生成项目概览"""
        # 筛选高置信度事实
        high_conf_facts = [f for f in self._facts if f.confidence >= 0.7]

        # 构建 Prompt
        prompt = self.prompt_builder.build_overview_prompt(high_conf_facts[:30])

        # 调用 LLM
        doc = self._call_llm(prompt, max_tokens=2000)

        # 验证
        if config.verify_output:
            verifier = OutputVerifier(config.repo_path)
            result = verifier.verify(doc, high_conf_facts[:20])
            if result.hallucinations:
                print(f"      ⚠️ 检测到 {len(result.hallucinations)} 处问题")
                doc = self._add_verification_notes(doc, result)

        return doc

    def _generate_architecture(self, config: GenerationConfig) -> Optional[str]:
        """生成架构文档"""
        # 筛选类型定义和函数
        arch_facts = [f for f in self._facts
                      if f.fact_type in ['type_struct', 'type_interface', 'method']
                      and f.confidence >= 0.6]

        prompt = self.prompt_builder.build_architecture_prompt(arch_facts, self._routes)

        doc = self._call_llm(prompt, max_tokens=4000)

        # 验证（关键：检查 REST 路径编造）
        if config.verify_output:
            verifier = OutputVerifier(config.repo_path)
            result = verifier.verify(doc, arch_facts)

            # 特别检查路由类型错误
            if self._routes and self._routes[0].route_type == 'action':
                if '/api/' in doc and 'REST' in doc:
                    print("      ❌ 严重：检测到 REST 描述，但实际是 Action 路由！")
                    doc = self._correct_route_description(doc, 'action')

            if result.hallucinations:
                doc = self._add_verification_notes(doc, result)

        return doc

    def _generate_api(self, config: GenerationConfig) -> Optional[str]:
        """生成 API 文档（最关键）"""
        # 筛选 handler 函数
        handlers = [f for f in self._facts
                   if f.fact_type in ['function', 'method']
                   and f.confidence >= 0.5]

        # 使用专用 Prompt（根据路由类型）
        prompt = self.prompt_builder.build_api_prompt(self._routes, handlers[:20])

        doc = self._call_llm(prompt, max_tokens=4000)

        # 严格验证 API 文档
        if config.verify_output:
            verifier = OutputVerifier(config.repo_path)
            result = verifier.verify(doc, handlers)

            # 检查编造的路由路径
            path_issues = [h for h in result.hallucinations if 'REST' in h or '路径' in h]
            if path_issues:
                print(f"      ❌ 检测到编造路由路径: {len(path_issues)} 处")
                for issue in path_issues[:3]:
                    print(f"         - {issue}")

            if result.hallucinations:
                doc = self._add_verification_notes(doc, result)

        return doc

    def _generate_modules(self, config: GenerationConfig) -> Dict[str, str]:
        """生成模块详情（每个文件一个文档）"""
        # 按文件分组事实
        file_facts: Dict[str, List[CodeFact]] = {}
        for fact in self._facts:
            file_key = fact.location.file
            if file_key not in file_facts:
                file_facts[file_key] = []
            file_facts[file_key].append(fact)

        # 为每个核心文件生成文档
        results = {}
        core_files = [f for f in file_facts.keys()
                     if any(x in f for x in ['api/', 'db/', 'service/', 'handler/'])]

        for file_key in core_files[:10]:  # 限制数量
            facts = file_facts[file_key]
            prompt = f"""为代码文件生成详细文档。

【代码事实】
{self._format_facts_for_prompt(facts[:15])}

【要求】
1. 模块职责（基于函数名推断，标注【推测】）
2. 主要函数/类型清单（表格，带代码位置）
3. 关键实现逻辑（描述代码结构，不粘贴代码）
4. **所有不确定的内容标注【推测】或【需确认】**
"""
            doc = self._call_llm(prompt, max_tokens=1500)
            results[f"module_{Path(file_key).stem}"] = doc

        return results

    def _generate_db(self, config: GenerationConfig) -> Optional[str]:
        """生成数据库文档"""
        db_facts = [f for f in self._facts
                   if f.fact_type in ['type_struct'] and
                   any(x in f.name.lower() for x in ['model', 'entity', 'table', 'dao'])]

        if not db_facts:
            return None

        prompt = f"""生成数据库模型文档。

【模型事实】
{self._format_facts_for_prompt(db_facts[:20])}

【要求】
1. 表/模型清单（名称、文件位置）
2. 每个模型的字段说明（如果源码中有字段信息）
3. DAO 方法清单（如果有）
4. **不确定的字段标注【未确认】**
"""
        return self._call_llm(prompt, max_tokens=3000)

    # ═══════════════════════════════════════════════════════════════════════
    # 内部方法：组装和验证
    # ═══════════════════════════════════════════════════════════════════════

    def _assemble_docs(self, docs: Dict[str, str], config: GenerationConfig) -> Dict[str, Path]:
        """组装最终文档"""
        vault_path = Path(self.config['output']['vault_path']).expanduser()
        output_dir = vault_path / "CodeNotes" / config.system / config.repo
        output_dir.mkdir(parents=True, exist_ok=True)

        final_paths = {}

        # 写入各类型文档
        for doc_type, content in docs.items():
            if doc_type == 'overview':
                path = output_dir / "README.md"
            elif doc_type.startswith('module_'):
                module_name = doc_type.replace('module_', '')
                modules_dir = output_dir / "modules"
                modules_dir.mkdir(exist_ok=True)
                path = modules_dir / f"{module_name}.md"
            else:
                path = output_dir / f"{doc_type}.md"

            # 添加头部信息
            header = self._build_doc_header(doc_type, config)
            full_content = header + "\n\n" + content

            # 添加置信度统计
            if self.config['output']['include_confidence'] and self._confidence_stats:
                full_content += self._build_confidence_footer()

            path.write_text(full_content, encoding='utf-8')
            final_paths[doc_type] = path

        return final_paths

    def _build_doc_header(self, doc_type: str, config: GenerationConfig) -> str:
        """构建文档头部"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        route_info = ""
        if self._routes:
            route_types = set(r.route_type for r in self._routes)
            route_info = f"\n路由类型: {', '.join(route_types)}"

        return f"""# {config.repo} - {doc_type}

> 自动生成文档 | 系统: [[{config.system}]] | 时间: {timestamp}{route_info}
> **置信度**: 见文档末尾统计 | **验证状态**: {'✓' if self.config['output']['include_confidence'] else '未验证'}

---
"""

    def _build_confidence_footer(self) -> str:
        """构建置信度统计脚注"""
        if not self._confidence_stats:
            return ""

        dist = self._confidence_stats['distribution']
        return f"""

---

## 置信度统计

| 等级 | 数量 |
|------|------|
| 高置信度 (≥0.9) | {dist.get('HIGH', 0)} |
| 中置信度 (0.6-0.9) | {dist.get('MEDIUM', 0)} |
| 低置信度 (0.3-0.6) | {dist.get('LOW', 0)} |
| 不确定 (<0.3) | {dist.get('UNCERTAIN', 0)} |

- **平均置信度**: {self._confidence_stats['mean']:.2f}
- **需人工审查**: {self._confidence_stats['needs_review']} 个事实

*置信度基于来源可信度、完整性、一致性和可验证性计算*
"""

    def _verify_outputs(self, paths: Dict[str, Path], config: GenerationConfig):
        """批量验证输出"""
        print("\n  验证结果汇总:")

        for doc_type, path in paths.items():
            content = path.read_text(encoding='utf-8')
            verifier = OutputVerifier(config.repo_path)

            # 根据文档类型选择源事实
            if doc_type == 'api':
                source = [f for f in self._facts if f.fact_type in ['function', 'method']][:30]
            elif doc_type == 'architecture':
                source = [f for f in self._facts if f.confidence >= 0.6][:30]
            else:
                source = self._facts[:20]

            result = verifier.verify(content, source)

            status = "✓" if result.is_valid else f"⚠️ ({len(result.hallucinations)}问题)"
            print(f"    {doc_type}: {status}")

            # 如果有问题，写入日志
            if result.hallucinations:
                log_path = path.parent / f"{path.stem}_verification.log"
                log_content = f"""验证时间: {datetime.now()}
问题数: {len(result.hallucinations)}

问题列表:
"""
                for issue in result.hallucinations:
                    log_content += f"- {issue}\n"

                log_content += f"\n建议修正:\n"
                for fix in result.suggested_fixes:
                    log_content += f"- {fix}\n"

                log_path.write_text(log_content, encoding='utf-8')

    # ═══════════════════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════════════════

    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """调用 LLM 生成内容"""
        try:
            # 获取配置
            base_url = os.getenv('ANTHROPIC_BASE_URL', self.config['llm']['base_url'])
            model = self.config['llm']['default_model']
            # 按优先级读取 key：ANTHROPIC_AUTH_TOKEN → LLM_API_KEY
            api_key = os.getenv('ANTHROPIC_AUTH_TOKEN') or os.getenv('LLM_API_KEY', '')

            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.1,  # 更低温度，更确定性
            }).encode()

            req = urllib.request.Request(
                f"{base_url}/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            error_msg = f"[LLM 生成失败: {e}]\n\n请检查:\n1. API_KEY 是否设置: export LLM_API_KEY=your_key\n2. 网络连接是否正常\n3. 模型服务是否可用"
            print(f"      ⚠️ LLM 调用失败: {e}")
            return error_msg

    def _format_facts_for_prompt(self, facts: List[CodeFact]) -> str:
        """格式化事实用于 Prompt"""
        lines = []
        for f in facts:
            marker = "✓" if f.confidence > 0.8 else "~"
            line = f"  {marker} [{f.fact_type}] {f.name} @ {f.location}"
            lines.append(line)
        return "\n".join(lines)

    def _add_verification_notes(self, doc: str, result: VerificationResult) -> str:
        """在文档中添加验证批注"""
        notes = """

---

## ⚠️ 验证批注

以下内容经自动验证发现需要关注：

"""
        for issue in result.hallucinations[:5]:  # 最多显示5个
            notes += f"- {issue}\n"

        if len(result.hallucinations) > 5:
            notes += f"- ... 还有 {len(result.hallucinations) - 5} 个问题\n"

        notes += "\n**建议**: 请人工复核上述内容，特别是标注【需确认】的部分。\n"

        return doc + notes

    def _correct_route_description(self, doc: str, correct_type: str) -> str:
        """修正路由描述错误"""
        # 添加强制修正标记
        warning = """

> ❌ **自动检测到路由描述错误**
> 原文可能错误地描述为 REST 路由，实际代码使用 Action 字段分发。
> 请以代码中的 `switch req.Action` 语句为准。

"""
        return warning + doc


# ═══════════════════════════════════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Generator V2")
    parser.add_argument('--system', required=True, help='系统名')
    parser.add_argument('--repo', required=True, help='仓库名')
    parser.add_argument('--repo-path', help='仓库路径（默认从缓存查找）')
    parser.add_argument('--skip-extract', action='store_true', help='跳过提取阶段')
    parser.add_argument('--skip-generate', action='store_true', help='跳过生成阶段')
    parser.add_argument('--no-verify', action='store_true', help='跳过验证')
    parser.add_argument('--min-confidence', type=float, default=0.3, help='最低置信度')

    args = parser.parse_args()

    # 确定仓库路径
    if args.repo_path:
        repo_path = Path(args.repo_path)
    else:
        # 从缓存查找
        cache_dir = Path.home() / '.cache' / 'mywiki-repos' / args.repo
        if cache_dir.exists():
            repo_path = cache_dir
        else:
            # 尝试本地开发路径
            local_path = Path.home() / 'Documents' / 'Code' / 'work' / args.system / args.repo
            repo_path = local_path if local_path.exists() else Path.cwd()

    if not repo_path.exists():
        print(f"错误: 找不到仓库路径 {repo_path}")
        return 1

    # 创建配置
    config = GenerationConfig(
        system=args.system,
        repo=args.repo,
        repo_path=repo_path,
        skip_extract=args.skip_extract,
        skip_generate=args.skip_generate,
        verify_output=not args.no_verify,
        min_confidence=args.min_confidence,
    )

    # 运行生成器
    generator = KnowledgeGenerator()
    results = generator.generate(config)

    print(f"\n✓ 完成，生成 {len(results)} 个文档")
    return 0


if __name__ == "__main__":
    exit(main())
