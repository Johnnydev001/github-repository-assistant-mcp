from __future__ import annotations

import base64
import json
import ssl
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import certifi


class GitHubRepositoryClient:
    def __init__(
        self,
        owner: str,
        repo: str,
        token: str,
        ref: str | None = None,
    ) -> None:
        self.owner = owner
        self.repo = repo
        self.token = token
        self.ref = ref
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    def read_text_file(self, relative_path: str) -> str:
        request_url = self._build_contents_url(relative_path)
        request = Request(
            request_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "portfolio-repository-mcp-server",
            },
        )

        try:
            with urlopen(request, context=self.ssl_context) as response:
                payload = json.load(response)
        except HTTPError as error:
            error_details = self._read_error_details(error)
            if error.code == 404:
                raise FileNotFoundError(
                    "GitHub returned 404 for "
                    f"{self.owner}/{self.repo}:{relative_path}"
                    f"{self._format_ref_suffix()}. "
                    "This can mean the file path is wrong, the ref does not contain the file, "
                    "or the token does not have access to this private repository. "
                    f"GitHub message: {error_details}"
                ) from error
            if error.code in {401, 403}:
                raise PermissionError(
                    "GitHub rejected the request for "
                    f"{self.owner}/{self.repo}{self._format_ref_suffix()}. "
                    f"Check GITHUB_TOKEN permissions. GitHub message: {error_details}"
                ) from error
            raise RuntimeError(
                f"GitHub API request failed with status {error.code} for {request_url}. "
                f"GitHub message: {error_details}"
            ) from error

        if payload.get("type") != "file":
            raise IsADirectoryError(f"Path is not a file: {relative_path}")
        if payload.get("encoding") != "base64":
            raise RuntimeError("GitHub API returned an unsupported content encoding")

        raw_content = payload.get("content", "").replace("\n", "")
        return base64.b64decode(raw_content).decode("utf-8")

    def _build_contents_url(self, relative_path: str) -> str:
        base_url = (
            f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/"
            f"{quote(relative_path, safe='/')}"
        )
        if not self.ref:
            return base_url
        return f"{base_url}?ref={quote(self.ref, safe='')}"

    def _format_ref_suffix(self) -> str:
        if not self.ref:
            return ""
        return f" @ {self.ref}"

    @staticmethod
    def _read_error_details(error: HTTPError) -> str:
        try:
            payload = json.load(error)
        except Exception:
            return "no response body"

        if isinstance(payload, dict) and payload.get("message"):
            return str(payload["message"])
        return json.dumps(payload)
