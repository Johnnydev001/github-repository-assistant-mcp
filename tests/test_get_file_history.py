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

from github_client import GitHubRepositoryClient


class GitHubCreatePullRequestTests(unittest.TestCase):
    @patch("github_client.urlopen")
    def test_get_file_history_success(self, mock_urlopen) -> None:
        mock_urlopen.return_value.__enter__.return_value = StringIO(
            '{"number":123,"html_url":"https://github.com/octocat/portfolio/commits/main/file.txt"}'
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
        self.assertEqual(result.get("number"), 123)


if __name__ == "__main__":
    unittest.main()
