# GitHub Extended MCP

An MCP server that extends Claude's GitHub capabilities beyond the standard Docker-based server. Covers gists, starring, profile management, notifications, and other API operations.

## Why

The standard GitHub MCP server (`ghcr.io/github/github-mcp-server`) exposes 26 tools focused on repos, PRs, issues, and code search. This server fills the gaps: **gists**, **starring**, **profile updates**, and **notifications**.

Use both together for complete GitHub coverage from Claude.

## Tools (10)

| Tool | Description |
|------|-------------|
| `create_gist` | Create a public or secret gist |
| `list_gists` | List your gists with pagination |
| `get_gist` | Get a gist with full file contents |
| `delete_gist` | Delete a gist by ID |
| `star_repo` | Star a repository |
| `unstar_repo` | Unstar a repository |
| `list_starred` | List your starred repos |
| `get_profile` | Get your GitHub profile info |
| `update_profile` | Update name, bio, company, location, blog |
| `list_notifications` | List unread notifications |

## Quick Start

```bash
git clone https://github.com/ZZtopBR/github-extended-mcp.git
cd github-extended-mcp
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Token

Create a Personal Access Token at [github.com/settings/tokens](https://github.com/settings/tokens) with scopes: `gist`, `user`, `notifications`, `read:user`.

## Connect to Claude Desktop

```json
{
  "mcpServers": {
    "github-extended": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/github-extended-mcp/src/server.py"],
      "env": { "GITHUB_TOKEN": "ghp_your_token_here" }
    }
  }
}
```

## Using alongside the standard GitHub MCP

Run both for full coverage:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_token" }
    },
    "github-extended": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/github-extended-mcp/src/server.py"],
      "env": { "GITHUB_TOKEN": "ghp_token" }
    }
  }
}
```

## Usage

```
"Create a gist with my Python snippet"
"List my recent gists"
"Star the repo anthropics/courses"
"Update my GitHub bio"
"Show my unread notifications"
```

## License

MIT

---

*Built with [FastMCP](https://github.com/jlowin/fastmcp) and the [GitHub REST API](https://docs.github.com/en/rest).*
