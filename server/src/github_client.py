from __future__ import annotations

import base64
import json
import ssl
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import certifi
from models import RequestUrlSuffix, CommitAuthor
from utils.parsing import parse_file_history_entry
   
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
        request_url = self.build_pull_request_url()
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

    def get_file_history(self, file_name: str, branch: str = "main") -> list[CommitAuthor]:
        request_url = self.build_commits_url(file_name, branch)
        payload: list[dict[str,object]] = self._perform_json_request(
            request_url,
            relative_path="",
            data=None,
            method="GET",
        )
        commit_authors: list[CommitAuthor] = []
        for entry in payload:
            parsed_entry = parse_file_history_entry(entry)
            commit_authors.append(parsed_entry)

        return commit_authors

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
    ) -> dict[str, object] | list[dict[str, object]]:
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

        # Accept both object and array payloads; some GitHub endpoints (e.g. commits)
        # return a JSON array rather than an object.
        if not isinstance(payload, (dict, list)):
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

        if not isinstance(payload, dict):
            return json.dumps(payload)

        message = str(payload.get("message", ""))
        errors = payload.get("errors")
        if errors:
            details = "; ".join(
                e.get("message") or f"{e.get('field', '?')} {e.get('code', '?')}"
                if isinstance(e, dict) else str(e)
                for e in errors
            )
            return f"{message}: {details}"
        return message or json.dumps(payload)


    # The following methods are used to build request URLs
    def build_base_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/"

    def build_pull_request_url(self) -> str:
        return f"{self.build_base_url()}{RequestUrlSuffix.PULL_REQUEST.value}"

    def list_branches(self, per_page: int = 100) -> list[str]:
        url = f"{self.build_base_url()}{RequestUrlSuffix.BRANCHES.value}?per_page={per_page}"
        payload = self._perform_json_request(url, relative_path="", data=None, method="GET")
        if isinstance(payload, list):
            return [b["name"] for b in payload if isinstance(b, dict) and "name" in b]
        return []

    def build_commits_url(self, file_name: str, branch: str = "main") -> str:
        base = f"{self.build_base_url()}{RequestUrlSuffix.COMMITS.value}"
        return f"{base}?path={quote(file_name, safe='')}&sha={quote(branch, safe='')}"

    def _build_contents_url(self, relative_path: str) -> str:
        base_url = (
           f"{self.build_base_url()}{RequestUrlSuffix.CONTENTS.value}/"
           f"{quote(relative_path, safe='/')}"
        )
        if not self.ref:
            return base_url
        return f"{base_url}?ref={quote(self.ref, safe='')}"
