from __future__ import annotations

from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from portfolio_mcp_server.github_client import GitHubRepositoryClient


class GitHubCreatePullRequestTests(unittest.TestCase):
    @patch("portfolio_mcp_server.github_client.urlopen")
    def test_get_file_history_success(self, mock_urlopen) -> None:
        # Return a JSON array like the real commits endpoint
        mock_urlopen.return_value.__enter__.return_value = StringIO(
            '[{"commit":{"author":{"name":"Alice","email":"alice@example.com","date":"2026-04-27T12:34:56Z"},"message":"Initial commit"},"html_url":"https://github.com/octocat/portfolio/commit/abc"}]'
        )
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        result = client.get_file_history(
            file_name="file.txt",
            branch="main",
        )

        get_request = mock_urlopen.call_args_list[0].args[0]
        self.assertEqual(get_request.method, "GET")
        # result is a list of CommitAuthor dataclasses
        self.assertEqual(len(result), 1)
        first = result[0]
        self.assertEqual(first.name, "Alice")
        self.assertEqual(first.email, "alice@example.com")
        self.assertEqual(first.message, "Initial commit")


if __name__ == "__main__":
    unittest.main()
