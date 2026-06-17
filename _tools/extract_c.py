#!/usr/bin/env python3
"""
mywiki extract_c — C 代码符号提取模块

基于 ctags 提取 C/C++ 源码的符号（函数、struct、typedef、宏定义）。
输出格式与 extract.py 统一，供 agent 精确搜索 + LLM 摘要。

依赖: ctags (macOS: brew install universal-ctags, Linux: apt install universal-ctags)
"""

import json
import re
import subprocess
from pathlib import Path
from typing import List


def _get_ctags_path() -> str | None:
    """检查 ctags 是否可用。"""
    try:
        result = subprocess.run(
            ["ctags", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and "Universal Ctags" in result.stdout:
            return "ctags"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _extract_comment_before(filepath: Path, line_num: int) -> str:
    """提取指定行前的块注释（/* */ 或 //）。"""
    try:
        lines = filepath.read_text(errors="replace").splitlines()
    except Exception:
        return ""

    if line_num < 2 or line_num > len(lines):
        return ""

    # 从目标行的前一行开始向上扫描
    comments = []
    i = line_num - 2  # 转换为 0-indexed，从目标行前一行的索引开始

    # 收集 // 风格的注释（连续向上）
    while i >= 0:
        line = lines[i].strip()
        if line.startswith("//"):
            comments.insert(0, line[2:].strip())
            i -= 1
        elif line == "" or line.startswith("/*"):
            # 空行或块注释开始，停止
            break
        else:
            break

    if comments:
        return "\n".join(comments)

    # 尝试找 /* */ 块注释（单行或多行）
    # 简化处理：扫描前 10 行找最近的 /* */
    block_comment = []
    in_block = False
    for j in range(max(0, line_num - 12), line_num - 1):
        line = lines[j]
        if "*/" in line and not in_block:
            # 可能是块注释的结尾
            if "/*" not in line or line.find("*/") > line.find("/*"):
                # 提取 /* 到 */ 之间的内容
                start = line.rfind("/*")
                if start >= 0:
                    end = line.find("*/", start)
                    if end > start:
                        return line[start+2:end].strip()
        elif "/*" in line:
            in_block = True
            start = line.find("/*")
            block_comment.append(line[start+2:])
        elif in_block:
            if "*/" in line:
                block_comment.append(line[:line.find("*/")])
                return " ".join(block_comment).strip()
            else:
                block_comment.append(line.strip())

    return ""


def extract_c_symbols(filepath: Path, repo_root: Path) -> List[dict]:
    """
    从单个 C/C++ 文件提取符号。

    使用 Universal Ctags 获取基础信息，再读取文件提取注释。
    输出格式与 Go 符号统一: {"kind", "name", "signature", "file", "line", "comment"}
    """
    rel = str(filepath.relative_to(repo_root))
    symbols = []

    # 检查 ctags
    ctags = _get_ctags_path()
    if not ctags:
        # 回退到简单正则提取
        return _fallback_extract(filepath, repo_root)

    # ctags 命令
    cmd = [
        ctags,
        "--fields=+nKSt",
        "--extras=+r",
        "--output-format=json",
        "--language-force=C",
        "-o", "-",
        str(filepath)
    ]

    try:
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=10)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return _fallback_extract(filepath, repo_root)

    for line in output.strip().split("\n"):
        if not line:
            continue
        try:
            tag = json.loads(line)
        except json.JSONDecodeError:
            continue

        kind = tag.get("kind", "")
        name = tag.get("name", "")
        line_num = int(tag.get("line", 0))

        # 只处理我们关心的 kind
        kind_map = {
            "function": "func",
            "struct": "struct",
            "typedef": "type",
            "macro": "macro",
            "enum": "enum",
            "enumerator": "const",
            "variable": "var",
        }

        if kind not in kind_map:
            continue

        # 构建 signature
        signature = tag.get("signature", "")
        typeref = tag.get("typeref", "")

        if kind == "function":
            # signature 通常是 (int arg1, char* arg2) 格式
            sig = f"{name}{signature}" if signature else name
        elif kind == "struct":
            sig = f"struct {name}"
        elif kind == "typedef":
            sig = f"typedef {typeref} {name}" if typeref else f"typedef {name}"
        elif kind == "macro":
            sig = f"#define {name}{signature}" if signature else f"#define {name}"
        else:
            sig = name

        # 提取注释
        comment = _extract_comment_before(filepath, line_num)

        symbols.append({
            "kind": kind_map[kind],
            "name": name,
            "signature": sig,
            "file": rel,
            "line": line_num,
            "comment": comment,
            "lang": "c",
        })

    return symbols


def _fallback_extract(filepath: Path, repo_root: Path) -> List[dict]:
    """
    ctags 不可用时使用简单正则回退。
    准确性较低，但零依赖。
    """
    rel = str(filepath.relative_to(repo_root))
    symbols = []

    try:
        content = filepath.read_text(errors="replace")
        lines = content.splitlines()
    except Exception:
        return symbols

    # 函数定义: return_type func_name(args) { 或 return_type func_name(args);
    # 关键：必须以大括号或分号结尾，返回类型必须是有效的 C 类型
    func_pattern = re.compile(
        r'^\s*(?:static\s+|inline\s+|extern\s+)*'  # 可选修饰符
        r'((?:struct\s+|enum\s+|union\s+)?[\w\s\*]+?)\s+'  # 返回类型 (如 int, void, char*, struct Foo)
        r'(\w+)\s*'  # 函数名
        r'\(([^)]*)\)\s*'  # 参数列表
        r'(?:\{|\s*;)'  # 必须后跟 { 或 ;（排除函数调用）
    )

    # struct 定义
    struct_pattern = re.compile(r'^\s*struct\s+(\w+)\s*\{')

    # typedef
    typedef_pattern = re.compile(r'^\s*typedef\s+(.+?)\s+(\w+)\s*;')

    # 宏定义
    macro_pattern = re.compile(r'^\s*#define\s+(\w+)(?:\s+(.*))?')

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        # 函数
        m = func_pattern.match(line)
        if m:
            ret_type, name, params = m.groups()
            ret_type = ret_type.strip()
            # 验证返回类型看起来像 C 类型（不能是空白，不能是纯数字/字符串）
            valid_type_keywords = ['int', 'void', 'char', 'float', 'double', 'long', 'short',
                                 'signed', 'unsigned', 'bool', 'size_t', 'ssize_t',
                                 'struct', 'enum', 'union', 'static', 'const']
            if not ret_type or ret_type.replace('*', '').replace(' ', '') == '':
                continue
            # 检查返回类型是否包含有效的类型关键词或自定义类型名
            ret_clean = ret_type.replace('*', '').replace('const', '').strip()
            has_type = any(kw in ret_clean for kw in valid_type_keywords)
            if not has_type and not re.match(r'^[A-Za-z_]\w+$', ret_clean):
                continue  # 不是有效的类型模式
            symbols.append({
                "kind": "func",
                "name": name,
                "signature": f"{ret_type} {name}({params.strip()})",
                "file": rel,
                "line": i,
                "comment": "",
                "lang": "c",
            })
            continue

        # struct
        m = struct_pattern.match(line)
        if m:
            symbols.append({
                "kind": "struct",
                "name": m.group(1),
                "signature": f"struct {m.group(1)}",
                "file": rel,
                "line": i,
                "comment": "",
                "lang": "c",
            })
            continue

        # typedef
        m = typedef_pattern.match(line)
        if m:
            type_def, name = m.groups()
            symbols.append({
                "kind": "type",
                "name": name,
                "signature": f"typedef {type_def.strip()} {name}",
                "file": rel,
                "line": i,
                "comment": "",
                "lang": "c",
            })
            continue

        # 宏
        m = macro_pattern.match(line)
        if m:
            name, value = m.groups()
            symbols.append({
                "kind": "macro",
                "name": name,
                "signature": f"#define {name} {value or ''}".strip(),
                "file": rel,
                "line": i,
                "comment": "",
                "lang": "c",
            })

    return symbols


if __name__ == "__main__":
    # 简单测试
    import sys
    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])
        if test_file.exists():
            syms = extract_c_symbols(test_file, test_file.parent)
            print(json.dumps(syms, indent=2, ensure_ascii=False))
        else:
            print(f"File not found: {test_file}")
