from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unittest

from server.cli import DEFAULT_SERVER_ARGS, _render_tool_result, build_server_parameters

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "server" / "src"
CLIENT_ROOT = PROJECT_ROOT / "server"
for path in (SRC_ROOT, CLIENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))



class FakeContentItem:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeToolResult:
    def __init__(self, content: list[FakeContentItem], is_error: bool = False) -> None:
        self.content = content
        self.isError = is_error


class ClientCliTests(unittest.TestCase):
    def test_build_server_parameters_defaults_to_local_server_script(self) -> None:
        args = argparse.Namespace(server_command=sys.executable, server_args=None)

        params = build_server_parameters(args)

        self.assertEqual(params.command, sys.executable)
        self.assertEqual(params.args, DEFAULT_SERVER_ARGS)

    def test_render_tool_result_joins_text_items(self) -> None:
        result = FakeToolResult([FakeContentItem("line 1"), FakeContentItem("line 2")])

        rendered = _render_tool_result(result)

        self.assertEqual(rendered, "line 1\nline 2")


if __name__ == "__main__":
    unittest.main()
