#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2016-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import textwrap

from edb.lang.edgeql import parser as eql_parser
from edb.lang.edgeql import utils as eql_utils

from edb.lang import _testbase as tb


class TestEdgeQLUtils(tb.BaseEdgeQLCompilerTest):
    SCHEMA = r"""
        abstract type NamedObject:
            required property name -> str

        type UserGroup extending NamedObject:
            multi link settings -> Setting

        type Setting extending NamedObject:
            required property value -> str

        type Profile extending NamedObject:
            required property value -> str

        type User extending NamedObject:
            required property active -> bool
            multi link groups -> UserGroup
            required property age -> int64
            required property score -> float64
            link profile -> Profile
    """

    def _assert_normalize_expr(self, text, expected,
                               expected_const_type=None, *,
                               anchors=None, inline_anchors=False):
        edgeql_tree = eql_parser.parse(text)
        ir, _, normalized = eql_utils.normalize_tree(
            edgeql_tree, self.__class__.schema,
            anchors=anchors, inline_anchors=inline_anchors)

        self.assertEqual(
            textwrap.dedent(normalized).strip(),
            textwrap.dedent(expected).strip()
        )

        if expected_const_type is not None:
            self.assertEqual(
                ir.expr.stype.get_displayname(self.__class__.schema),
                expected_const_type)

    def test_edgeql_utils_normalize_01(self):
        self._assert_normalize_expr(
            """SELECT 40 + 2""",
            """SELECT 42""",
            'std::int64',
        )

    def test_edgeql_utils_normalize_02(self):
        self._assert_normalize_expr(
            """SELECT -10""",
            """SELECT -10""",
            'std::int64',
        )

    def test_edgeql_utils_normalize_03(self):
        self._assert_normalize_expr(
            """SELECT len('a')""",
            """SELECT std::len('a')""",
        )

    def test_edgeql_utils_normalize_04(self):
        self._assert_normalize_expr(
            """WITH MODULE test SELECT User{name}""",
            """SELECT test::User { name }"""
        )

    def test_edgeql_utils_normalize_05(self):
        self._assert_normalize_expr(
            """SELECT <int64>'1'""",
            """SELECT <std::int64>'1'""",
            'std::int64',
        )

    def test_edgeql_utils_normalize_06(self):
        self._assert_normalize_expr(
            """SELECT ('aaa')[2:-1]""",
            """SELECT ('aaa')[2:-1]"""
        )

    def test_edgeql_utils_normalize_07(self):
        self._assert_normalize_expr(
            """SELECT ('aaa')[2]""",
            """SELECT ('aaa')[2]"""
        )

    def test_edgeql_utils_normalize_08(self):
        self._assert_normalize_expr(
            """SELECT 40 + 2 - 20 * +2 + (-10 // 2)""",
            """SELECT -3""",
            'std::int64',
        )

    def test_edgeql_utils_normalize_09(self):
        self._assert_normalize_expr(
            """SELECT 2 + (len('a')+1)""",
            """SELECT (3 + std::len('a'))""",
        )

        self._assert_normalize_expr(
            """SELECT (1 + len('a')) + 2""",
            """SELECT (3 + std::len('a'))""",
        )

        self._assert_normalize_expr(
            """SELECT 2 * (len('a')*1)""",
            """SELECT (2 * std::len('a'))""",
        )

        self._assert_normalize_expr(
            """SELECT (1 * len('a')) * 2""",
            """SELECT (2 * std::len('a'))""",
        )

    def test_edgeql_utils_normalize_10(self):
        self._assert_normalize_expr(
            """SELECT 1 > 2""",
            """SELECT false""",
            'std::bool',
        )

        self._assert_normalize_expr(
            """SELECT 1 = 1""",
            """SELECT true""",
            'std::bool',
        )

        self._assert_normalize_expr(
            """SELECT 1 < (1 + 1)""",
            """SELECT true""",
            'std::bool',
        )

    def test_edgeql_utils_normalize_11(self):
        self._assert_normalize_expr(
            """SELECT 5 // 2""",
            """SELECT 2""",
        )
