from __future__ import annotations

from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

from server.src.github_client import GitHubRepositoryClient
from server.src.security import normalize_repo_path, resolve_local_source_path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "server" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))



class NormalizeRepoPathTests(unittest.TestCase):
    def test_normalize_repo_path_allows_valid_relative_path(self) -> None:
        self.assertEqual(normalize_repo_path("content/index.md"), "content/index.md")

    def test_normalize_repo_path_rejects_escape_attempt(self) -> None:
        with self.assertRaises(ValueError):
            normalize_repo_path("../secrets.txt")


class ResolveLocalSourcePathTests(unittest.TestCase):
    def test_resolve_local_source_path_allows_files_inside_source_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir).resolve()
            source_file = source_root / "replacement.txt"
            source_file.write_text("hello", encoding="utf-8")

            resolved = resolve_local_source_path(source_root, "replacement.txt")

            self.assertEqual(resolved, source_file)

    def test_resolve_local_source_path_rejects_escape_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_root = Path(temp_dir).resolve()

            with self.assertRaises(ValueError):
                resolve_local_source_path(source_root, "../outside.txt")


class GitHubRepositoryClientTests(unittest.TestCase):
    @patch("github_client.urlopen")
    def test_read_text_file_decodes_base64_content(self, mock_urlopen) -> None:
        mock_urlopen.return_value.__enter__.return_value = StringIO(
            '{"type":"file","encoding":"base64","content":"SGVsbG8gZnJvbSBHaXRIdWIh"}'
        )
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        content = client.read_text_file("README.md")

        self.assertEqual(content, "Hello from GitHub!")
        self.assertIsNotNone(client.ssl_context)

    @patch("github_client.urlopen")
    def test_read_text_file_surfaces_404_details(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = HTTPError(
            url="https://api.github.com/repos/octocat/portfolio/contents/tsconfig.json?ref=main",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=StringIO('{"message":"Not Found"}'),
        )
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        with self.assertRaises(FileNotFoundError) as context:
            client.read_text_file("tsconfig.json")

        self.assertIn("octocat/portfolio:tsconfig.json @ main", str(context.exception))
        self.assertIn("GitHub message: Not Found", str(context.exception))

    @patch("github_client.urlopen")
    def test_update_file_content_writes_with_existing_sha(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = [
            _json_response(
                '{"type":"file","encoding":"base64","content":"T2xk","sha":"blobsha123"}'
            ),
            _json_response(
                '{"content":{"path":"README.md"},"commit":{"sha":"commitsha456","message":"Update file"}}'
            ),
        ]
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        result = client.update_file_content("README.md", b"New content", "Update file")

        self.assertEqual(result["path"], "README.md")
        self.assertEqual(result["commit_sha"], "commitsha456")
        put_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(put_request.method, "PUT")
        self.assertIn(b'"sha": "blobsha123"', put_request.data)
        self.assertIn(b'"branch": "main"', put_request.data)

    @patch("github_client.urlopen")
    def test_update_file_content_creates_when_file_is_missing(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = [
            HTTPError(
                url="https://api.github.com/repos/octocat/portfolio/contents/new-file.md?ref=main",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=StringIO('{"message":"Not Found"}'),
            ),
            _json_response(
                '{"content":{"path":"new-file.md"},"commit":{"sha":"commitsha789","message":"Create file"}}'
            ),
        ]
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        result = client.update_file_content("new-file.md", b"Hello", "Create file")

        self.assertEqual(result["path"], "new-file.md")
        self.assertEqual(result["commit_sha"], "commitsha789")
        put_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(put_request.method, "PUT")
        self.assertNotIn(b'"sha"', put_request.data)
        self.assertIn(b'"branch": "main"', put_request.data)

    @patch("github_client.urlopen")
    def test_update_file_content_supports_binary_payloads(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = [
            HTTPError(
                url="https://api.github.com/repos/octocat/portfolio/contents/file.pdf?ref=main",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=StringIO('{"message":"Not Found"}'),
            ),
            _json_response(
                '{"content":{"path":"file.pdf"},"commit":{"sha":"commitsha999","message":"Upload pdf"}}'
            ),
        ]
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        binary_content = b"%PDF-1.7\n\xe2\xe3\xcf\xd3\n"
        result = client.update_file_content("file.pdf", binary_content, "Upload pdf")

        self.assertEqual(result["path"], "file.pdf")
        put_request = mock_urlopen.call_args_list[1].args[0]
        self.assertIn(b'"content": "JVBERi0xLjcK4uPP0wo="', put_request.data)

    @patch("github_client.urlopen")
    def test_delete_file_uses_delete_request_with_sha(self, mock_urlopen) -> None:
        mock_urlopen.side_effect = [
            _json_response(
                '{"type":"file","encoding":"base64","content":"SGVsbG8=","sha":"blobsha999"}'
            ),
            _json_response(
                '{"commit":{"sha":"commitsha321","message":"Delete file"}}'
            ),
        ]
        client = GitHubRepositoryClient(
            owner="octocat",
            repo="portfolio",
            token="secret-token",
            ref="main",
        )

        result = client.delete_file("README.md", "Delete file")

        self.assertEqual(result["path"], "README.md")
        self.assertEqual(result["commit_sha"], "commitsha321")
        delete_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(delete_request.method, "DELETE")
        self.assertIn(b'"sha": "blobsha999"', delete_request.data)
        self.assertIn(b'"branch": "main"', delete_request.data)


def _json_response(payload: str) -> StringIO:
    return StringIO(payload)


if __name__ == "__main__":
    unittest.main()
