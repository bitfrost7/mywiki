#!/usr/bin/env python3
"""
Go AST 提取器 - 基于 Tree-sitter

提取 Go 代码的确定性事实：
- 函数定义（含 receiver、参数、返回值）
- 类型定义（struct、interface）
- 常量/变量
- 包信息和导入
"""

import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

# 处理导入路径
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from interfaces import IASTExtractor, CodeFact, CodeLocation, FactSource

# Tree-sitter 导入（延迟加载，确保模块可用性检查）
try:
    from tree_sitter import Language, Parser, Tree, Node
    from tree_sitter_go import language as _GO_LANGUAGE_FUNC
    TREE_SITTER_AVAILABLE = True

    # tree-sitter-go 的 language 是一个函数，需要调用后得到 capsule
    # 然后用 Language(capsule) 包装，再传给 Parser
    try:
        _LANG = Language(_GO_LANGUAGE_FUNC())
        _PARSER = Parser(_LANG)
    except Exception:
        TREE_SITTER_AVAILABLE = False
        _LANG = None
        _PARSER = None
except ImportError:
    TREE_SITTER_AVAILABLE = False
    _GO_LANGUAGE_FUNC = None
    _LANG = None
    _PARSER = None


@dataclass
class GoFunction:
    """Go 函数的内部表示"""
    name: str
    receiver: Optional[str]  # 如 "*API"
    params: List[Tuple[str, str]]  # [(name, type), ...]
    returns: List[str]  # 返回类型列表
    is_method: bool
    doc_comment: str
    location: CodeLocation


class GoASTExtractor(IASTExtractor):
    """
    Go 代码 AST 提取器

    使用 Tree-sitter 从 Go 源码提取结构化事实。
    100% 确定性，无 LLM 参与。
    """

    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "Tree-sitter 未安装。请运行:\n"
                "  pip install tree-sitter tree-sitter-go\n"
                "或使用你的 mise 环境安装。"
            )
        # 使用预初始化的 parser
        global _PARSER, _LANG
        if _PARSER is None:
            raise ImportError("Tree-sitter 初始化失败")
        self.parser = _PARSER
        self.language = _LANG
        self._node_handlers = {
            'function_declaration': self._extract_function,
            'method_declaration': self._extract_method,
            'type_declaration': self._extract_type,
            'const_declaration': self._extract_const,
            'var_declaration': self._extract_var,
            'import_declaration': self._extract_import,
        }

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix == '.go'

    def get_supported_languages(self) -> List[str]:
        return ['go']

    def extract(self, file_path: Path, repo_root: Path) -> List[CodeFact]:
        """
        从 Go 文件提取代码事实
        """
        if not file_path.exists():
            return []

        # 读取原始字节，tree-sitter 的 start_byte/end_byte 是字节偏移
        # 必须用 bytes 切片，而非 str（否则中文字符会导致偏移错位）
        raw = file_path.read_bytes()
        if not raw.strip():
            return []

        tree = self.parser.parse(raw)
        root = tree.root_node

        facts = []
        rel_path = str(file_path.relative_to(repo_root))

        # 遍历 AST，传入 raw bytes
        cursor = root.walk()
        self._walk_tree(cursor, file_path, raw, rel_path, facts)

        return facts

    @staticmethod
    def _text(content: bytes, node: 'Node') -> str:
        """从字节内容中按字节偏移提取文本，正确处理中文等多字节字符"""
        return content[node.start_byte:node.end_byte].decode('utf-8', errors='replace')

    def _walk_tree(self, cursor, file_path: Path, content: bytes, rel_path: str, facts: List[CodeFact]):
        """递归遍历 AST"""
        node = cursor.node

        handler = self._node_handlers.get(node.type)
        if handler:
            fact = handler(node, content, rel_path)
            if fact:
                facts.append(fact)

        if cursor.goto_first_child():
            self._walk_tree(cursor, file_path, content, rel_path, facts)
            while cursor.goto_next_sibling():
                self._walk_tree(cursor, file_path, content, rel_path, facts)
            cursor.goto_parent()

    def _extract_function(self, node: 'Node', content: bytes, file_path: str) -> Optional[CodeFact]:
        """提取函数定义"""
        func_node = self._find_child(node, 'identifier')
        if not func_node:
            return None

        name = self._text(content, func_node)
        location = self._make_location(node, file_path, content)

        # 提取参数
        params = self._extract_params(node, content)
        returns = self._extract_returns(node, content)

        # 获取文档注释
        doc = self._extract_doc_comment(node, content)

        source_code = self._text(content, node)

        return CodeFact(
            id=self._make_id(file_path, name, location.start_line),
            fact_type='function',
            name=name,
            location=location,
            source_code=source_code,
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            metadata={
                'params': params,
                'returns': returns,
                'is_method': False,
                'doc_comment': doc,
            }
        )

    def _extract_method(self, node: 'Node', content: bytes, file_path: str) -> Optional[CodeFact]:
        """提取方法定义（带 receiver）"""
        # method_declaration 的方法名节点类型是 field_identifier，不是 identifier
        func_node = self._find_child(node, 'field_identifier')
        if not func_node:
            return None

        name = self._text(content, func_node)
        location = self._make_location(node, file_path, content)

        # 提取 receiver
        receiver = self._extract_receiver(node, content)

        # 提取参数（跳过 receiver）
        params = self._extract_params(node, content, skip_receiver=True)
        returns = self._extract_returns(node, content)

        doc = self._extract_doc_comment(node, content)
        source_code = self._text(content, node)

        return CodeFact(
            id=self._make_id(file_path, name, location.start_line),
            fact_type='method',
            name=name,
            location=location,
            source_code=source_code,
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            metadata={
                'receiver': receiver,
                'params': params,
                'returns': returns,
                'is_method': True,
                'doc_comment': doc,
            }
        )

    def _extract_type(self, node: 'Node', content: bytes, file_path: str) -> Optional[CodeFact]:
        """提取类型定义（struct/interface）"""
        # 可能包含多个类型声明
        spec = self._find_child(node, 'type_spec')
        if not spec:
            return None

        name_node = self._find_child(spec, 'type_identifier') or self._find_child(spec, 'identifier')
        if not name_node:
            return None

        name = self._text(content, name_node)
        location = self._make_location(node, file_path, content)

        # 判断是 struct 还是 interface
        type_kind = 'unknown'
        struct_node = self._find_child(spec, 'struct_type')
        interface_node = self._find_child(spec, 'interface_type')

        if struct_node:
            type_kind = 'struct'
            fields = self._extract_struct_fields(struct_node, content)
        elif interface_node:
            type_kind = 'interface'
            fields = self._extract_interface_methods(interface_node, content)
        else:
            fields = []

        doc = self._extract_doc_comment(node, content)
        source_code = self._text(content, node)

        return CodeFact(
            id=self._make_id(file_path, name, location.start_line),
            fact_type=f'type_{type_kind}',
            name=name,
            location=location,
            source_code=source_code,
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            metadata={
                'kind': type_kind,
                'fields': fields,
                'doc_comment': doc,
            }
        )

    def _extract_const(self, node: 'Node', content: bytes, file_path: str) -> Optional[CodeFact]:
        """提取常量定义"""
        # 简化处理，提取第一个常量名
        spec = self._find_child(node, 'const_spec')
        if not spec:
            # 可能是 const ( ... ) 块
            return None  # 复杂块暂不处理

        name_node = self._find_child(spec, 'identifier')
        if not name_node:
            return None

        name = self._text(content, name_node)
        location = self._make_location(node, file_path, content)

        # 尝试获取值
        value_node = self._find_child(spec, 'expression')
        value = self._text(content, value_node) if value_node else ""

        # 检查是否是 Action 常量（特殊标记）
        is_action = name.startswith('Action')

        return CodeFact(
            id=self._make_id(file_path, name, location.start_line),
            fact_type='const',
            name=name,
            location=location,
            source_code=self._text(content, node),
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            metadata={
                'value': value,
                'is_action': is_action,
            }
        )

    def _extract_var(self, node: 'Node', content: str, file_path: str) -> Optional[CodeFact]:
        """提取变量定义"""
        # 类似 const，简化处理
        return None  # 暂不处理复杂 var 块

    def _extract_import(self, node: 'Node', content: str, file_path: str) -> Optional[CodeFact]:
        """提取导入"""
        # 收集包导入信息
        return None  # 暂不作为事实存储

    # ═══════════════════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════════════════

    def _find_child(self, node: 'Node', type_name: str) -> Optional['Node']:
        """查找指定类型的子节点"""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _make_location(self, node: 'Node', file_path: str, content: bytes) -> CodeLocation:
        """创建代码位置（content 为字节，字节偏移计数 \\n 是正确的）"""
        start_line = content[:node.start_byte].count(b'\n') + 1
        end_line = content[:node.end_byte].count(b'\n') + 1

        return CodeLocation(
            file=file_path,
            start_line=start_line,
            end_line=end_line,
            start_col=node.start_point[1],
            end_col=node.end_point[1]
        )

    def _make_id(self, file_path: str, name: str, line: int) -> str:
        """创建唯一 ID"""
        hash_input = f"{file_path}:{name}:{line}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def _extract_receiver(self, node: 'Node', content: bytes) -> Optional[str]:
        """提取方法 receiver"""
        recv_node = self._find_child(node, 'receiver')
        if not recv_node:
            return None
        return self._text(content, recv_node).strip()

    def _extract_params(self, node: 'Node', content: bytes, skip_receiver: bool = False) -> List[Tuple[str, str]]:
        """提取参数列表"""
        params_node = self._find_child(node, 'parameter_list')
        if not params_node:
            return []

        params = []
        for child in params_node.children:
            if child.type == 'parameter_declaration':
                name_node = self._find_child(child, 'identifier')
                type_node = self._find_child(child, 'type_identifier') or \
                           self._find_child(child, 'pointer_type') or \
                           self._find_child(child, 'qualified_type') or \
                           self._find_child(child, 'slice_type')

                if name_node and type_node:
                    params.append((
                        self._text(content, name_node),
                        self._text(content, type_node),
                    ))

        return params

    def _extract_returns(self, node: 'Node', content: bytes) -> List[str]:
        """提取返回类型"""
        result_node = self._find_child(node, 'result')
        if not result_node:
            return []

        types = []
        for child in result_node.children:
            if child.type in ['type_identifier', 'pointer_type', 'qualified_type']:
                types.append(self._text(content, child))

        return types

    def _extract_struct_fields(self, node: 'Node', content: bytes) -> List[Dict[str, str]]:
        """提取 struct 字段"""
        fields = []
        field_list = self._find_child(node, 'field_declaration_list')
        if field_list:
            for field in field_list.children:
                if field.type == 'field_declaration':
                    name_node = self._find_child(field, 'identifier')
                    type_node = self._find_child(field, 'type_identifier')
                    if name_node and type_node:
                        fields.append({
                            'name': self._text(content, name_node),
                            'type': self._text(content, type_node),
                        })
        return fields

    def _extract_interface_methods(self, node: 'Node', content: bytes) -> List[Dict[str, str]]:
        """提取 interface 方法签名"""
        methods = []
        method_list = self._find_child(node, 'method_spec_list')
        if method_list:
            for method in method_list.children:
                if method.type == 'method_spec':
                    name_node = self._find_child(method, 'identifier')
                    if name_node:
                        methods.append({
                            'name': self._text(content, name_node),
                            'signature': '...',
                        })
        return methods

    def _extract_doc_comment(self, node: 'Node', content: bytes) -> str:
        """提取文档注释（函数上方的 // 或 /* */）"""
        start_line = content[:node.start_byte].count(b'\n')
        lines = content.split(b'\n')

        comments = []
        for i in range(max(0, start_line - 5), start_line):
            line = lines[i].strip()
            if line.startswith(b'//'):
                comments.append(line[2:].strip().decode('utf-8', errors='replace'))
            elif line == b'*/':
                break
            elif line.startswith(b'/*'):
                comments.append(line[2:].strip().decode('utf-8', errors='replace'))

        return ' '.join(reversed(comments)) if comments else ""


# ═══════════════════════════════════════════════════════════════════════════
# 提取 Action 常量的专用方法（用于路由分析）
# ═══════════════════════════════════════════════════════════════════════════

def extract_action_constants(repo_path: Path) -> Dict[str, str]:
    """
    从仓库提取所有 Action 常量

    使用正则表达式提取，因为 Action 常量通常在 const() 块中定义，
    AST 提取器单次只能处理一个节点，不适合批量提取。

    Returns:
        {ActionCreateVPCEndpoint: "CreateVPCEndpoint", ...}
    """
    actions = {}

    for go_file in repo_path.rglob("*.go"):
        try:
            content = go_file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        # 匹配两种形式：
        # 1. const ActionXxx = "..."  (单行)
        # 2. 在 const() 块内: ActionXxx = "..."
        for m in re.finditer(r'\b(Action\w+)\s*=\s*"([^"]*)"', content):
            action_name = m.group(1)
            action_value = m.group(2)
            # handler 名通常等于 Action 值或去掉 "Action" 前缀
            handler_name = action_value if action_value else action_name[6:]
            actions[action_name] = handler_name

    return actions


if __name__ == "__main__":
    # 测试
    if not TREE_SITTER_AVAILABLE:
        print("Tree-sitter 未安装，无法测试")
    else:
        import tempfile
        test_code = '''
package api

// CreateVPCEndpoint 创建 VPC 终端节点
func (a *API) CreateVPCEndpoint(c *gin.Context) CommonResponse {
    return nil
}

type EndpointService struct {
    ServiceID string
    Name      string
}
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
            f.write(test_code)
            f.flush()
            test_path = Path(f.name)

        extractor = GoASTExtractor()
        facts = extractor.extract(test_path, test_path.parent)

        for fact in facts:
            print(f"  {fact.fact_type}: {fact.name} @ {fact.location}")
            if fact.metadata.get('doc_comment'):
                print(f"    doc: {fact.metadata['doc_comment']}")
