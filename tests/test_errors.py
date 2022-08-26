"""Contains special test cases that fall outside the scope of remaining test files."""
import textwrap

import pytest

from flake8_type_checking.constants import TC001, TC002
from tests.conftest import _get_error, mod


class TestFoundBugs:
    def test_mixed_errors(self):
        example = textwrap.dedent(
            f"""
        import {mod}
        import pytest
        from x import y

        x: {mod} | pytest | y
        """
        )
        assert _get_error(example) == {
            f"2:0 {TC001.format(module=f'{mod}')}",
            '3:0 ' + TC002.format(module='pytest'),
            '4:0 ' + TC002.format(module='x.y'),
        }

    def test_type_checking_block_imports_dont_generate_errors(self):
        example = textwrap.dedent(
            """
        import x
        from y import z

        if TYPE_CHECKING:
            import a

            # arbitrary whitespace

            from b import c

        def test(foo: z, bar: x):
            pass
        """
        )
        assert _get_error(example) == {
            '2:0 ' + TC002.format(module='x'),
            '3:0 ' + TC002.format(module='y.z'),
        }

    def test_model_declarations_dont_trigger_error(self):
        """
        Initially found false positives in Django project, because name
        visitor did not capture the SomeModel usage in the example below.
        """
        example = textwrap.dedent(
            """
        from django.db import models
        from app.models import SomeModel

        class LoanProvider(models.Model):
            fk: SomeModel = models.ForeignKey(
                SomeModel,
                on_delete=models.CASCADE,
            )
        """
        )
        assert _get_error(example) == set()

    def test_all_list_declaration(self):
        """__all__ declarations originally generated false positives."""
        example = textwrap.dedent(
            """
        from app.models import SomeModel
        from another_app.models import AnotherModel

        __all__ = [
            'SomeModel',
            'AnotherModel'
        ]
        """
        )
        assert _get_error(example) == set()

    def test_all_tuple_declaration(self):
        """__all__ declarations originally generated false positives."""
        example = textwrap.dedent(
            """
        from app.models import SomeModel
        from another_app.models import AnotherModel

        __all__ = (
            'SomeModel',
            'AnotherModel'
        )
        """
        )
        assert _get_error(example) == set()

    def test_callable_import(self):
        """__all__ declarations originally generated false positives."""
        example = textwrap.dedent(
            """
        from x import y

        class X:
            def __init__(self):
                self.all_sellable_models: list[CostModel] = y(
                    country=self.country
                )
        """
        )
        assert _get_error(example) == set()

    def test_ellipsis(self):
        example = textwrap.dedent(
            """
        x: Tuple[str, ...]
        """
        )
        assert _get_error(example) == set()

    def test_literal(self):
        example = textwrap.dedent(
            """
        from __future__ import annotations

        x: Literal['string']
        """
        )
        assert _get_error(example) == set()

    def test_conditional_import(self):
        example = textwrap.dedent(
            """
        version = 2

        if version == 2:
            import x
        else:
            import y as x

        var: x
        """
        )
        assert _get_error(example) == {"7:4 TC002 Move third-party import 'x' into a type-checking block"}

    def test_type_checking_block_formats_detected(self):
        """
        We should detect type-checking blocks, no matter* the format.

        https://github.com/snok/flake8-type-checking/issues/68
        """
        type_checking = """
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from pathlib import Path

            p: Path
            """
        typing_type_checking = """
            import typing

            if typing.TYPE_CHECKING:
                from pathlib import Path

            p: Path
            """
        alias = """
            from typing import TYPE_CHECKING as test

            if test:
                from pathlib import Path

            p: Path
            """
        aliased_typing = """
            import typing as T

            if T.TYPE_CHECKING:
                from pathlib import Path

            p: Path
            """
        for example in [type_checking, typing_type_checking, alias, aliased_typing]:
            assert _get_error(textwrap.dedent(example)) == set()

    def test_import_not_flagged_when_existing_import_present(self):
        """
        When an import is made to a module, we treat it as already used.

        Guarding additional imports to the same module shouldn't present
        a performance gain of note, so it's probably not worth the effort.
        """
        example = """
            from os import x  # <-- would otherwise be flagged
            from os import y  # <-- but this should prevent that

            z = y
            """
        assert _get_error(textwrap.dedent(example)) == set()

    @pytest.mark.parametrize(
        'example',
        [
            """
            import urllib.parse

            urllib.parse.urlencode('')
            """,
            """
            import botocore.exceptions

            try:
                ...
            except botocore.exceptions.ClientError:
                ...
           """,
            """
            import boto3.s3.transfer

            print(f"hello there: {boto3.s3.transfer.TransferConfig()}")
           """,
            """
            import boto3.s3.transfer

            print(f"hello there: {boto3.s3.transfer()}")
           """,
        ],
    )
    def test_double_namespace_import(self, example):
        """
        Ensure double namespaced imports are handled correctly.

        Re https://github.com/snok/flake8-type-checking/issues/101.
        """
        assert _get_error(textwrap.dedent(example)) == set()

    @pytest.mark.parametrize(
        'example',
        [
            '''
            if TYPE_CHECKING:
               from datetime import date

            def bar(self, *, baz: date | None):
                ...
            ''',
            '''
            if TYPE_CHECKING:
               from datetime import date

            def bar(self) -> date | None:
                ...
            ''',
            '''
            if TYPE_CHECKING:
               from typing import Literal

            def bar(self, baz: Literal['installer'] | None):
                ...
            ''',
        ],
    )
    def test_tc004_false_positive(self, example):
        """Re https://github.com/snok/flake8-type-checking/issues/106."""
        assert _get_error(textwrap.dedent(example)) == set()

    def test_tc002_false_positive(self):
        """Re https://github.com/snok/flake8-type-checking/issues/120."""
        example = textwrap.dedent(
            """
            from logging import INFO

            from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

            class C:
                level: int = INFO
                status: int = HTTP_500_INTERNAL_SERVER_ERROR
        """
        )
        assert _get_error(example) == set()

    def test_tc001_false_positive(self):
        """Re https://github.com/snok/flake8-type-checking/issues/116."""
        assert _get_error('from x import y') == set()

    def test_tc00123_false_cast_positive(self):
        """Re https://github.com/snok/flake8-type-checking/issues/127."""
        example = textwrap.dedent("""
        from __future__ import annotations
        
        from collections.abc import Callable
        
        a = cast('Callable[..., Any]', {})
        """)
        assert _get_error(example) == {'1:0 ' + TC001.format(module='x')}