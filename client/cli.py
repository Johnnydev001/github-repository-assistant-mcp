from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVER_ARGS = [str(PROJECT_ROOT / "src" / "server.py")]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Minimal MCP client for the portfolio repository server."
    )
    parser.add_argument(
        "--server-command",
        default=sys.executable,
        help="Command used to start the MCP server. Defaults to the current Python interpreter.",
    )
    parser.add_argument(
        "--server-arg",
        action="append",
        dest="server_args",
        help="Extra argument for the server process. Can be passed multiple times.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-tools", help="List the tools exposed by the MCP server.")

    read_file_parser = subparsers.add_parser(
        "read-file", help="Read a file from the configured repository."
    )
    read_file_parser.add_argument(
        "--path",
        required=True,
        dest="relative_path",
        help="Repository-relative path of the file to read.",
    )

    update_file_parser = subparsers.add_parser(
        "update-file", help="Update a file in the configured repository."
    )
    update_file_parser.add_argument(
        "--path",
        required=True,
        dest="relative_path",
        help="Repository-relative path of the file to update.",
    )
    update_file_parser.add_argument(
        "--message",
        required=True,
        dest="commit_message",
        help="Commit message used for the remote file update.",
    )
    update_group = update_file_parser.add_mutually_exclusive_group(required=True)
    update_group.add_argument(
        "--content",
        dest="content",
        help="Inline UTF-8 content to write to the target file.",
    )
    update_group.add_argument(
        "--source-path",
        dest="source_relative_path",
        help="Path inside LOCAL_SOURCE_DIR to use as the replacement file content.",
    )

    delete_file_parser = subparsers.add_parser(
        "delete-file", help="Delete a file from the configured repository."
    )
    delete_file_parser.add_argument(
        "--path",
        required=True,
        dest="relative_path",
        help="Repository-relative path of the file to delete.",
    )
    delete_file_parser.add_argument(
        "--message",
        required=True,
        dest="commit_message",
        help="Commit message used for the remote file delete.",
    )

    return parser


def build_server_parameters(args: argparse.Namespace) -> StdioServerParameters:
    server_args = args.server_args if args.server_args else DEFAULT_SERVER_ARGS
    return StdioServerParameters(
        command=args.server_command,
        args=server_args,
        cwd=str(PROJECT_ROOT),
        env=os.environ.copy(),
    )


async def list_tools(server: StdioServerParameters) -> int:
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()

    for tool in result.tools:
        print(tool.name)
        if tool.description:
            print(f"  {tool.description}")

    return 0


def _render_tool_result(result: object) -> str:
    content = getattr(result, "content", None)
    if not content:
        return ""

    rendered_parts: list[str] = []
    for item in content:
        text = getattr(item, "text", None)
        if text is not None:
            rendered_parts.append(text)
            continue

        dumped = item.model_dump(mode="json") if hasattr(item, "model_dump") else str(item)
        rendered_parts.append(json.dumps(dumped, indent=2))

    return "\n".join(rendered_parts)


async def read_file(server: StdioServerParameters, relative_path: str) -> int:
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(
                "read_file",
                {"relative_path": relative_path},
            )

    if getattr(result, "isError", False):
        print(_render_tool_result(result), file=sys.stderr)
        return 1

    print(_render_tool_result(result))
    return 0


async def update_file(
    server: StdioServerParameters,
    relative_path: str,
    commit_message: str,
    content: str | None,
    source_relative_path: str | None,
) -> int:
    arguments: dict[str, str] = {
        "relative_path": relative_path,
        "commit_message": commit_message,
    }
    if content is not None:
        arguments["content"] = content
    if source_relative_path is not None:
        arguments["source_relative_path"] = source_relative_path

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("update_file", arguments)

    if getattr(result, "isError", False):
        print(_render_tool_result(result), file=sys.stderr)
        return 1

    print(_render_tool_result(result))
    return 0


async def delete_file(
    server: StdioServerParameters,
    relative_path: str,
    commit_message: str,
) -> int:
    arguments = {
        "relative_path": relative_path,
        "commit_message": commit_message,
    }

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("delete_file", arguments)

    if getattr(result, "isError", False):
        print(_render_tool_result(result), file=sys.stderr)
        return 1

    print(_render_tool_result(result))
    return 0


async def run_command(args: argparse.Namespace) -> int:
    server = build_server_parameters(args)

    if args.command == "list-tools":
        return await list_tools(server)
    if args.command == "read-file":
        return await read_file(server, args.relative_path)
    if args.command == "update-file":
        return await update_file(
            server,
            args.relative_path,
            args.commit_message,
            args.content,
            args.source_relative_path,
        )
    if args.command == "delete-file":
        return await delete_file(
            server,
            args.relative_path,
            args.commit_message,
        )

    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return anyio.run(run_command, args)


if __name__ == "__main__":
    raise SystemExit(main())
