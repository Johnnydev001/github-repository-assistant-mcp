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
        payload = self._get_contents_payload(relative_path)
        if payload.get("type") != "file":
            raise IsADirectoryError(f"Path is not a file: {relative_path}")
        if payload.get("encoding") != "base64":
            raise RuntimeError("GitHub API returned an unsupported content encoding")

        raw_content = payload.get("content", "").replace("\n", "")
        return base64.b64decode(raw_content).decode("utf-8")

    def update_file_content(
        self,
        relative_path: str,
        content: bytes,
        commit_message: str,
    ) -> dict[str, str]:
        existing_sha: str | None = None
        try:
            existing_payload = self._get_contents_payload(relative_path)
        except FileNotFoundError:
            existing_payload = None
        else:
            if existing_payload.get("type") != "file":
                raise IsADirectoryError(f"Path is not a file: {relative_path}")
            existing_sha = str(existing_payload.get("sha") or "")

        request_url = self._build_contents_url(relative_path)
        request_body: dict[str, object] = {
            "message": commit_message,
            "content": base64.b64encode(content).decode("ascii"),
        }
        if existing_sha:
            request_body["sha"] = existing_sha
        if self.ref:
            request_body["branch"] = self.ref

        payload = self._perform_json_request(
            request_url,
            relative_path=relative_path,
            data=request_body,
            method="PUT",
        )

        commit = payload.get("commit") or {}
        content_info = payload.get("content") or {}
        return {
            "path": str(content_info.get("path") or relative_path),
            "commit_sha": str(commit.get("sha") or ""),
            "commit_message": str(commit.get("message") or commit_message),
        }

    def delete_file(
        self,
        relative_path: str,
        commit_message: str,
    ) -> dict[str, str]:
        existing_payload = self._get_contents_payload(relative_path)
        if existing_payload.get("type") != "file":
            raise IsADirectoryError(f"Path is not a file: {relative_path}")

        request_url = self._build_contents_url(relative_path)
        request_body: dict[str, object] = {
            "message": commit_message,
            "sha": existing_payload.get("sha"),
        }
        if self.ref:
            request_body["branch"] = self.ref

        payload = self._perform_json_request(
            request_url,
            relative_path=relative_path,
            data=request_body,
            method="DELETE",
        )

        commit = payload.get("commit") or {}
        return {
            "path": relative_path,
            "commit_sha": str(commit.get("sha") or ""),
            "commit_message": str(commit.get("message") or commit_message),
        }

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str | None = None,
    ) -> dict[str, object]:
        """Create a pull request on the repository.

        title: PR title
        head: the name of the branch where your changes are implemented
        base: the name of the branch you want the changes pulled into
        body: optional PR body text
        Returns the JSON payload from GitHub for the created PR.
        """
        request_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls"
        request_body: dict[str, object] = {"title": title, "head": head, "base": base}
        if body is not None:
            request_body["body"] = body

        payload = self._perform_json_request(
            request_url,
            relative_path="",
            data=request_body,
            method="POST",
        )

        return payload

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

    def _build_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "portfolio-repository-mcp-server",
        }

    def _get_contents_payload(self, relative_path: str) -> dict[str, object]:
        request_url = self._build_contents_url(relative_path)
        return self._perform_json_request(request_url, relative_path=relative_path)

    def _perform_json_request(
        self,
        request_url: str,
        *,
        relative_path: str,
        data: dict[str, object] | None = None,
        method: str = "GET",
    ) -> dict[str, object]:
        request_data = None
        if data is not None:
            request_data = json.dumps(data).encode("utf-8")

        request = Request(
            request_url,
            data=request_data,
            headers=self._build_headers(),
            method=method,
        )

        try:
            with urlopen(request, context=self.ssl_context) as response:
                payload = json.load(response)
        except HTTPError as error:
            self._raise_http_error(error, request_url, relative_path)

        if not isinstance(payload, dict):
            raise RuntimeError(f"GitHub API returned an unexpected payload for {request_url}")
        return payload

    def _raise_http_error(
        self,
        error: HTTPError,
        request_url: str,
        relative_path: str,
    ) -> None:
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
        if error.code in {409, 422}:
            raise RuntimeError(
                f"GitHub could not modify {self.owner}/{self.repo}:{relative_path}"
                f"{self._format_ref_suffix()}. GitHub message: {error_details}"
            ) from error
        raise RuntimeError(
            f"GitHub API request failed with status {error.code} for {request_url}. "
            f"GitHub message: {error_details}"
        ) from error

    @staticmethod
    def _read_error_details(error: HTTPError) -> str:
        try:
            payload = json.load(error)
        except Exception:
            return "no response body"

        if isinstance(payload, dict) and payload.get("message"):
            return str(payload["message"])
        return json.dumps(payload)
