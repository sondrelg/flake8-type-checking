from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import ast
    from collections.abc import Generator
    from typing import Any, Protocol, Union

    Function = Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda]
    Comprehension = Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]
    Import = Union[ast.Import, ast.ImportFrom]
    Flake8Generator = Generator[tuple[int, int, str, Any], None, None]

    class HasPosition(Protocol):
        @property
        def lineno(self) -> int:
            pass

        @property
        def col_offset(self) -> int:
            pass

    class SupportsIsTyping(Protocol):
        def is_typing(self, node: ast.AST, symbol: str) -> bool:
            pass


ImportTypeValue = Literal['APPLICATION', 'THIRD_PARTY', 'BUILTIN', 'FUTURE']
