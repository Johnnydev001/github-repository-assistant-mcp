Purpose

Short reference for Copilot sessions working on this repository. Focused on build/test/run commands, architecture overview, and repository-specific conventions.

Build, test, and run commands

- Create and activate venv:
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -e .

- Run the MCP server (standalone):
  python src/server.py
  # or after install
  portfolio-mcp-server

- Client (starts server for you):
  python client/cli.py list-tools
  python client/cli.py read-file --path tsconfig.json
  python client/cli.py update-file --path README.md --message "msg" --content "..."
  python client/cli.py update-file --path README.md --message "Replace" --source-path README.md
  python client/cli.py delete-file --path old.md --message "Remove"
  python client/cli.py commit-file --path README.md --message "Fix" --content "..." --author-name "Alice" --author-email "alice@example.com"
  python client/cli.py get-file-history --file-name .gitignore --branch main
  python client/cli.py create-pr --title "Add feature" --head feature-branch --base main --body "Please merge"

- Tests:
  Run full suite:
    .venv/bin/python -m unittest discover -s tests
  Run a single test file:
    .venv/bin/python -m unittest tests.test_read_file
  Run a single test case:
    .venv/bin/python -m unittest tests.test_read_file.TestClass.test_method

High-level architecture

- Two components:
  - src/: the MCP server (MCP tool registry, GitHub integration, auth/security).
  - client/: minimal CLI client that starts the server over stdio and invokes tools.

- Interaction flow:
  1. Client spawns server subprocess communicating over stdio.
  2. Server registers MCP tools and authenticates using GITHUB_TOKEN (from .env).
  3. Server uses src/github_client.py to call GitHub Contents API to read/update/delete files in the private portfolio repo.

- Core modules to inspect when adding features:
  - src/server.py        (tool registration, server lifecycle)
  - src/github_client.py (GitHub API wrappers; follow existing patterns)
  - src/security.py      (validation and path/source restrictions)
  - src/config.py        (env-based configuration)
  - client/cli.py        (CLI -> MCP tool invocation)

Key conventions and patterns

- Environment variables (set from .env):
  - PORTFOLIO_REPO_URL
  - GITHUB_TOKEN (needs `repo` or fine-grained Contents read/write)
  - PORTFOLIO_REPO_REF (branch/tag; optional)
  - LOCAL_SOURCE_DIR (only allowed directory for replacement files)

- Update semantics:
  - update_file supports inline `--content` or `--source-path` that must be inside LOCAL_SOURCE_DIR. Binary files are allowed when using source-path.
  - All remote changes require a `--message` (commit message) from the client and are executed via the GitHub Contents API.
  - get_file_history returns a list of commit entries. Each entry is serialized as a dict with fields: `name`, `email`, `date`, `message`, and `url` (derived from the GitHub commit payload). The server converts internal dataclasses to plain dicts for transport.

- Tools naming and placement:
  - Tools are snake_case (read_file, update_file, delete_file). Add new tools in src/server.py and wire them into the same registration pattern.
  - Client CLI flags map 1:1 to tool parameters — update client/cli.py when adding a new action.

- Testing and structure:
  - Tests use unittest in tests/ and mock GitHub interactions where appropriate. Add a test file per new tool (e.g., tests/test_commit.py).
  - Package uses src/ layout and a console script `portfolio-mcp-server` (pyproject.toml -> server:main).

Notes for adding a "commit on behalf of the user" action

Follow existing patterns used by update_file/delete_file:
1. Add a new MCP tool handler in src/server.py (e.g., `commit_on_behalf` or `commit`) that accepts parameters such as `changes` (path->content or list), `message`, and optional author metadata.
2. Reuse src/github_client.py helpers or add a new helper to create commits via the Git Data or Contents API. Prefer reusing existing `update` flows if the change is per-file.
3. Validate inputs in src/security.py (ensure paths stay in repo, source files remain inside LOCAL_SOURCE_DIR if used).
4. Add a client subcommand in client/cli.py and map CLI args to the MCP call.
5. Add unit tests in tests/ that mock GitHub responses and cover success/failure cases and required token scopes.
6. Ensure README and this copilot-instructions.md are updated with any new CLI examples and required scopes.

Files to check when implementing:
- src/server.py
- src/github_client.py
- client/cli.py
- src/security.py
- tests/

Other AI assistant configs

- No CLAUDE.md, AGENTS.md, .cursorrules, .windsurfrules or AIDER/CLINE convention files detected. Update this doc if you add one.

Summary

Created a concise Copilot-focused reference covering run/test commands, repository architecture, and conventions. It also outlines the steps to add a new "commit on behalf of the user" action following existing patterns.