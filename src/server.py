"""
GitHub Extended MCP Server
Covers GitHub API operations not available in the standard Docker-based MCP server:
gists, starring, profile management, notifications, and more.

Usage: python server.py (stdio transport for Claude Desktop/Code)

Environment variables:
  GITHUB_TOKEN  - Personal access token with scopes: gist, user, notifications, read:user
"""

import os, json, logging, sys
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', stream=sys.stderr)

API = "https://api.github.com"
mcp = FastMCP("github-extended")

def _headers():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set. Create at https://github.com/settings/tokens")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}

def _api(method, path, **kwargs):
    r = getattr(requests, method)(f"{API}{path}", headers=_headers(), **kwargs)
    if r.status_code >= 400:
        return {"status": "error", "code": r.status_code, "message": r.text[:500]}
    if r.status_code == 204:
        return {"status": "ok"}
    try: return r.json()
    except: return {"status": "ok", "body": r.text[:500]}


# === GISTS ===

class CreateGistIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    description: str = Field(default="", description="Gist description")
    filename: str = Field(..., description="Filename (e.g. snippet.py)")
    content: str = Field(..., description="File content")
    public: bool = Field(default=True, description="Public or secret gist")

@mcp.tool(name="create_gist")
def create_gist(params: CreateGistIn) -> str:
    """Create a GitHub gist with a single file."""
    data = {"description": params.description, "public": params.public,
            "files": {params.filename: {"content": params.content}}}
    r = _api("post", "/gists", json=data)
    if isinstance(r, dict) and "html_url" in r:
        return json.dumps({"status": "ok", "url": r["html_url"], "id": r["id"]}, indent=2)
    return json.dumps(r, indent=2)


class ListGistsIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    per_page: int = Field(default=10, description="Results per page (max 100)")
    page: int = Field(default=1)

@mcp.tool(name="list_gists")
def list_gists(params: ListGistsIn) -> str:
    """List authenticated user's gists."""
    r = _api("get", f"/gists?per_page={params.per_page}&page={params.page}")
    if isinstance(r, list):
        gists = [{"id": g["id"], "description": g.get("description",""), "url": g["html_url"],
                  "files": list(g["files"].keys()), "public": g["public"]} for g in r]
        return json.dumps({"status": "ok", "total": len(gists), "gists": gists}, indent=2)
    return json.dumps(r, indent=2)


class GistIdIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    gist_id: str = Field(..., description="Gist ID")

@mcp.tool(name="get_gist")
def get_gist(params: GistIdIn) -> str:
    """Get a gist by ID with full file contents."""
    r = _api("get", f"/gists/{params.gist_id}")
    if isinstance(r, dict) and "files" in r:
        files = {n: {"content": f.get("content",""), "language": f.get("language",""),
                      "size": f.get("size",0)} for n, f in r["files"].items()}
        return json.dumps({"status": "ok", "id": r["id"], "url": r["html_url"], "files": files}, indent=2)
    return json.dumps(r, indent=2)

@mcp.tool(name="delete_gist")
def delete_gist(params: GistIdIn) -> str:
    """Delete a gist by ID."""
    return json.dumps(_api("delete", f"/gists/{params.gist_id}"), indent=2)


# === STARRING ===

class StarRepoIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    owner: str = Field(..., description="Repo owner")
    repo: str = Field(..., description="Repo name")

@mcp.tool(name="star_repo")
def star_repo(params: StarRepoIn) -> str:
    """Star a GitHub repository."""
    return json.dumps(_api("put", f"/user/starred/{params.owner}/{params.repo}"), indent=2)

@mcp.tool(name="unstar_repo")
def unstar_repo(params: StarRepoIn) -> str:
    """Unstar a GitHub repository."""
    return json.dumps(_api("delete", f"/user/starred/{params.owner}/{params.repo}"), indent=2)

@mcp.tool(name="list_starred")
def list_starred(params: ListGistsIn) -> str:
    """List repositories starred by the authenticated user."""
    r = _api("get", f"/user/starred?per_page={params.per_page}&page={params.page}")
    if isinstance(r, list):
        repos = [{"full_name": x["full_name"], "url": x["html_url"],
                  "description": x.get("description",""), "stars": x.get("stargazers_count",0)} for x in r]
        return json.dumps({"status": "ok", "total": len(repos), "repos": repos}, indent=2)
    return json.dumps(r, indent=2)


# === PROFILE ===

@mcp.tool(name="get_profile")
def get_profile() -> str:
    """Get authenticated user's GitHub profile."""
    r = _api("get", "/user")
    if isinstance(r, dict) and "login" in r:
        return json.dumps({"status": "ok", "login": r["login"], "name": r.get("name"),
                           "bio": r.get("bio"), "company": r.get("company"),
                           "location": r.get("location"), "blog": r.get("blog"),
                           "public_repos": r.get("public_repos"),
                           "followers": r.get("followers"), "url": r["html_url"]}, indent=2)
    return json.dumps(r, indent=2)

class UpdateProfileIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    name: Optional[str] = Field(default=None, description="Display name")
    bio: Optional[str] = Field(default=None, description="Profile bio")
    company: Optional[str] = Field(default=None, description="Company")
    location: Optional[str] = Field(default=None, description="Location")
    blog: Optional[str] = Field(default=None, description="Website URL")

@mcp.tool(name="update_profile")
def update_profile(params: UpdateProfileIn) -> str:
    """Update authenticated user's GitHub profile."""
    data = {k: v for k, v in params.model_dump().items() if v is not None}
    if not data: return json.dumps({"status": "error", "message": "No fields to update"})
    r = _api("patch", "/user", json=data)
    if isinstance(r, dict) and "login" in r:
        return json.dumps({"status": "ok", "login": r["login"], "name": r.get("name"),
                           "bio": r.get("bio"), "url": r["html_url"]}, indent=2)
    return json.dumps(r, indent=2)


# === NOTIFICATIONS ===

@mcp.tool(name="list_notifications")
def list_notifications() -> str:
    """List unread GitHub notifications."""
    r = _api("get", "/notifications?per_page=20")
    if isinstance(r, list):
        notifs = [{"id": n["id"], "reason": n["reason"], "title": n["subject"]["title"],
                   "type": n["subject"]["type"], "repo": n["repository"]["full_name"]} for n in r]
        return json.dumps({"status": "ok", "total": len(notifs), "notifications": notifs}, indent=2)
    return json.dumps(r, indent=2)


if __name__ == "__main__":
    mcp.run()
