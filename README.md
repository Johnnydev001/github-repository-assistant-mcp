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

At the moment, the server supports reading a text file, updating or creating a text file, and deleting a file in the private remote repository.

## Client

The client lives in `client/` and is a minimal command-line MCP client.

Its job is to:

- start the local MCP server
- initialize an MCP session
- list available tools
- invoke the `read_file` tool
- invoke the `update_file` tool
- invoke the `delete_file` tool

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

Update a file with inline content:

```bash
python client/cli.py update-file --path README.md --message "Update README" --content "# New README"
```

Update a file from a local replacement file inside `LOCAL_SOURCE_DIR`:

```bash
python client/cli.py update-file --path README.md --message "Replace README" --source-path README.md
```

Delete a file:

```bash
python client/cli.py delete-file --path old-page.md --message "Remove old page"
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

- three MCP tools are implemented: `read_file`, `update_file`, and `delete_file`
- the server reads from the remote GitHub repository only
- updates are limited to files through the GitHub Contents API
- deletes are limited to individual files through the GitHub Contents API

## Testing

Run the current test suite with:

```bash
.venv/bin/python -m unittest discover -s tests
```
