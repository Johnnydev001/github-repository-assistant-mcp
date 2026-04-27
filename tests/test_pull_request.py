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
    def test_create_pull_request_sends_post(self, mock_urlopen) -> None:
        mock_urlopen.return_value.__enter__.return_value = StringIO(
            '{"number":123,"html_url":"https://github.com/octocat/portfolio/pull/123"}'
        )
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        result = client.create_pull_request(
            title="Add feature",
            head="feature-branch",
            base="main",
            body="Please merge",
        )

        post_request = mock_urlopen.call_args_list[0].args[0]
        self.assertEqual(post_request.method, "POST")
        self.assertIn(b'"title": "Add feature"', post_request.data)
        self.assertIn(b'"head": "feature-branch"', post_request.data)
        self.assertIn(b'"base": "main"', post_request.data)
        self.assertIn(b'"body": "Please merge"', post_request.data)
        self.assertEqual(result.get("number"), 123)


if __name__ == "__main__":
    unittest.main()
