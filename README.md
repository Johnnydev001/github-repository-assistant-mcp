# Portfolio Repository MCP

This repository contains a small local MCP setup for working with a private GitHub portfolio repository.

The code in this repository is public.
The target portfolio repository remains private.
Credentials are not committed here and must be provided locally through environment variables.

## What This Repository Contains

This project is split into two parts:

- `src/`: the MCP server
- `client/`: a simple local CLI client

They work together as follows:

1. The client starts the MCP server as a local subprocess over `stdio`.
2. The server exposes MCP tools.
3. The server authenticates against GitHub using a local token.
4. The server performes a set of pre-configured actions (read file for example) on the private remote repository through the GitHub API.

## Server

The MCP server lives in `src/` and is responsible for:

- loading configuration from `.env`
- validating the configured GitHub repository URL
- authenticating with GitHub using `GITHUB_TOKEN`
- exposing MCP tools

Current scope:

- `read_file`
- `update_file`
- `delete_file`
- `commit_file` (single-file commit with optional author metadata)
- `get_file_history` (returns commit history for a file)
- `create_pull_request` (open a PR from a head branch to a base branch)

At the moment, the server supports reading a text file, updating or creating a file, deleting a file, committing a single file on behalf of a user, fetching a file's commit history, and creating pull requests on the private remote repository.

## Client

The client lives in `client/` and is a minimal command-line MCP client.

Its job is to:

- start the local MCP server
- initialize an MCP session
- list available tools
- invoke the `read_file` tool
- invoke the `update_file` tool
- invoke the `delete_file` tool
- invoke the `commit_file` tool (single-file commit with optional author)
- invoke the `get_file_history` tool (list of commit entries)

This client exists so you can use the MCP server without needing a separate desktop MCP host.

## Project Structure

```text
.
├─ client/
│  └─ cli.py
├─ src/
│  ├─ config.py
│  ├─ github_client.py
│  ├─ security.py
│  └─ server.py
├─ tests/
├─ .env.example
├─ pyproject.toml
└─ README.md
```

## Configuration

Copy `.env.example` to `.env` and set:

```env
PORTFOLIO_REPO_URL=https://github.com/your-user/your-private-portfolio-repo.git
GITHUB_TOKEN=github_pat_your_token_here
PORTFOLIO_REPO_REF=main
LOCAL_SOURCE_DIR=/absolute/path/to/local/replacement-files
```

Variable meaning:

- `PORTFOLIO_REPO_URL`: the private GitHub repository to target
- `GITHUB_TOKEN`: a token with access to that private repository
- `PORTFOLIO_REPO_REF`: optional branch or tag to read from
- `LOCAL_SOURCE_DIR`: optional local directory used when `update_file` replaces content from a local file

For private repositories:

- classic personal access tokens typically need `repo`
- fine-grained tokens need repository access plus `Contents: Read` and `Contents: Write`

## Installation

Using a virtual environment is highly recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Usage

List tools:

```bash
python client/cli.py list-tools
```

Read a file from the private repository:

```bash
python client/cli.py read-file --path tsconfig.json
```

Docker (portable)

Build the image locally:

```bash
docker build -t portfolio-mcp .
```

Run client commands with the image. Provide required env vars (at minimum PORTFOLIO_REPO_URL and GITHUB_TOKEN).

Examples:

List tools:

```bash
docker run --rm -e PORTFOLIO_REPO_URL="https://github.com/your-user/your-private-repo.git" -e GITHUB_TOKEN="ghp_..." portfolio-mcp list-tools
```

Read a file:

```bash
docker run --rm -e PORTFOLIO_REPO_URL="https://github.com/your-user/your-private-repo.git" -e GITHUB_TOKEN="ghp_..." portfolio-mcp read-file --path README.md
```

Commit a file from a host directory (mount host dir into container and set LOCAL_SOURCE_DIR to the mount point):

```bash
docker run --rm \
  -e PORTFOLIO_REPO_URL="https://github.com/your-user/your-private-repo.git" \
  -e GITHUB_TOKEN="ghp_..." \
  -e LOCAL_SOURCE_DIR="/data" \
  -v /path/on/host/local_files:/data \
  portfolio-mcp commit-file --path README.md --message "Update via docker" --source-path README.md --author-name "Alice" --author-email "alice@example.com"
```

Notes:

- LOCAL_SOURCE_DIR must point to an absolute path inside the container. Bind-mount the host directory to that path with `-v`.
- Keep your tokens secret; prefer passing them via an environment file or Docker secrets in production.


Update a file with inline content:

```bash
python client/cli.py update-file --path README.md --message "Update README" --content "# New README"
```

Update a file from a local replacement file inside `LOCAL_SOURCE_DIR`:

```bash
python client/cli.py update-file --path README.md --message "Replace README" --source-path README.md
```

When `--source-path` is used, the replacement file can be binary, for example a `.pdf`.

Delete a file:

```bash
python client/cli.py delete-file --path old-page.md --message "Remove old page"
```

Create a pull request:

```bash
python client/cli.py create-pr --title "Add feature" --head feature-branch --base main --body "Please merge"
```

Get file history (returns a JSON array of commit entries):

```bash
python client/cli.py get-file-history --file-name .gitignore --branch main
```

Returned JSON shape (each entry):

```json
{
  "name": "Author name",
  "email": "author@example.com",
  "date": "2026-04-27T12:34:56Z",
  "message": "Commit message",
  "url": "https://github.com/owner/repo/commit/..."
}
```

You can also use the virtualenv Python directly:

```bash
.venv/bin/python client/cli.py read-file --path tsconfig.json
```

## Running the Server Directly

If you want to start the MCP server on its own:

```bash
python src/server.py
```

After installation, this also works:

```bash
portfolio-mcp-server
```

In normal usage, you do not need to start the server manually because the client starts it for you.

## Notes on Security

- this repository does not store credentials
- `.env` is local-only and ignored by git
- GitHub access happens at runtime through `GITHUB_TOKEN`
- TLS verification uses `certifi`
- local replacement files are restricted to `LOCAL_SOURCE_DIR`

## Current Limitations

- implemented MCP tools are focused on per-file operations and lightweight repo actions: `read_file`, `update_file`, `delete_file`, `commit_file`, `get_file_history`, and `create_pull_request`.
- the server reads from and modifies the remote GitHub repository using the GitHub REST APIs (Contents API for file ops, Pulls API for PRs).
- bulk or atomic multi-file tree operations are not supported (use Git Data API or local workflows for complex changes).
- authentication depends on GITHUB_TOKEN provided at runtime; ensure token has appropriate repo permissions.

## Testing

Run the current test suite with:

```bash
.venv/bin/python -m unittest discover -s tests
```
