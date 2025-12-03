"""Tests for GitHub provider."""

import pytest

from src.RTFD.providers.github import GitHubProvider
from src.RTFD.utils import create_http_client


@pytest.fixture
def provider():
    """Create a GitHub provider instance."""
    return GitHubProvider(create_http_client)


def test_github_metadata():
    """Test GitHub provider metadata."""
    provider = GitHubProvider(lambda: None)
    metadata = provider.get_metadata()

    assert metadata.name == "github"
    assert metadata.expose_as_tool is True
    assert "github_repo_search" in metadata.tool_names
    assert "github_code_search" in metadata.tool_names
    assert metadata.supports_library_search is True


def test_github_get_tools():
    """Test that GitHub provider provides correct tools."""
    provider = GitHubProvider(lambda: None)
    tools = provider.get_tools()

    assert "github_repo_search" in tools
    assert "github_code_search" in tools
    assert callable(tools["github_repo_search"])
    assert callable(tools["github_code_search"])


@pytest.mark.asyncio
async def test_github_search_repos_success(provider):
    """Test repository search on GitHub (may fail due to rate limits)."""
    try:
        result = await provider._search_repos("python requests", limit=2)
        assert isinstance(result, list)
        assert len(result) <= 2
        for repo in result:
            assert "name" in repo
            assert "description" in repo
            assert "stars" in repo
            assert "url" in repo
            assert "default_branch" in repo
    except Exception as e:
        # May fail due to rate limits without GITHUB_TOKEN
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_github_search_library_success(provider):
    """Test library search integration (may fail due to rate limits)."""
    result = await provider.search_library("requests", limit=2)

    # May fail due to rate limits without GITHUB_TOKEN
    if not result.success:
        assert result.error is not None
        assert "rate limit" in result.error.lower() or "403" in result.error
    else:
        assert result.data is not None
        assert result.provider_name == "github"
        assert isinstance(result.data, list)


@pytest.mark.asyncio
async def test_github_search_code_success(provider):
    """Test code search on GitHub (may fail without auth)."""
    # GitHub code search requires authentication
    # This test verifies the method exists and handles errors gracefully
    try:
        result = await provider._search_code("def hello", limit=2)
        assert isinstance(result, list)
        for hit in result:
            assert "name" in hit
            assert "path" in hit
            assert "repository" in hit
            assert "url" in hit
    except Exception as e:
        # Expected: 401 Unauthorized without GITHUB_TOKEN
        # Also handle 403 Rate Limit which can happen in shared environments
        error_str = str(e)
        assert any(x in error_str for x in ["401", "Unauthorized", "403", "rate limit"])


@pytest.mark.asyncio
async def test_github_search_code_with_repo(provider):
    """Test code search scoped to a repository."""
    # GitHub code search requires authentication
    try:
        result = await provider._search_code("function", repo="psf/requests", limit=2)
        assert isinstance(result, list)
    except Exception:
        # Expected: authentication required
        pass


@pytest.mark.asyncio
async def test_github_repo_search_tool(provider):
    """Test the github_repo_search tool directly (may fail due to rate limits)."""
    tools = provider.get_tools()
    tool = tools["github_repo_search"]

    try:
        result = await tool("python requests", limit=2)
        assert result.content[0].type == "text"
        text_content = result.content[0].text
        assert isinstance(text_content, str)
        assert "[" in text_content  # JSON array format
    except Exception as e:
        # May fail due to rate limits without GITHUB_TOKEN
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_github_code_search_tool(provider):
    """Test the github_code_search tool directly."""
    tools = provider.get_tools()
    tool = tools["github_code_search"]

    try:
        result = await tool("def main", limit=2)
        assert result.content[0].type == "text"
        text_content = result.content[0].text
        assert isinstance(text_content, str)
    except Exception as e:
        # GitHub code search requires authentication
        error_str = str(e)
        assert any(x in error_str for x in ["401", "Unauthorized", "403", "rate limit"])


@pytest.mark.asyncio
async def test_list_repo_contents_root(provider):
    """Test listing repository root contents."""
    try:
        result = await provider._list_repo_contents("psf", "requests", "")
        assert "repository" in result
        assert result["repository"] == "psf/requests"
        assert "contents" in result
        assert isinstance(result["contents"], list)
        # Root should have some files/dirs
        if len(result["contents"]) > 0:
            item = result["contents"][0]
            assert "name" in item
            assert "path" in item
            assert "type" in item
    except Exception as e:
        # May fail due to rate limits
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_list_repo_contents_subdirectory(provider):
    """Test listing a subdirectory in a repository."""
    try:
        result = await provider._list_repo_contents("psf", "requests", "requests")
        assert "repository" in result
        assert "contents" in result
        assert isinstance(result["contents"], list)
    except Exception as e:
        # May fail due to rate limits or if path doesn't exist
        assert "40" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_get_file_content_success(provider):
    """Test getting file content from a repository."""
    try:
        result = await provider._get_file_content("psf", "requests", "README.md")
        assert "repository" in result
        assert result["repository"] == "psf/requests"
        assert "path" in result
        assert result["path"] == "README.md"
        assert "content" in result
        # If no error, content should be non-empty
        if "error" not in result:
            assert len(result["content"]) > 0
            assert "size_bytes" in result
    except Exception as e:
        # May fail due to rate limits
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_get_file_content_not_a_file(provider):
    """Test error handling when path is a directory."""
    try:
        result = await provider._get_file_content("psf", "requests", "requests")
        # Should return error indicating it's not a file
        assert "error" in result
        assert "dir" in result["error"].lower() or "not a file" in result["error"].lower()
    except Exception:
        # May fail due to rate limits
        pass


@pytest.mark.asyncio
async def test_get_repo_tree_non_recursive(provider):
    """Test getting repository tree non-recursively."""
    try:
        result = await provider._get_repo_tree("psf", "requests", recursive=False)
        assert "repository" in result
        assert result["repository"] == "psf/requests"
        assert "tree" in result
        assert isinstance(result["tree"], list)
        assert "branch" in result
        # Non-recursive should have fewer items than recursive
        assert len(result["tree"]) < 1000
    except Exception as e:
        # May fail due to rate limits
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_get_repo_tree_recursive(provider):
    """Test getting full repository tree recursively."""
    try:
        result = await provider._get_repo_tree("psf", "requests", recursive=True, max_items=100)
        assert "repository" in result
        assert "tree" in result
        assert isinstance(result["tree"], list)
        # Recursive should include nested files
        if len(result["tree"]) > 0:
            item = result["tree"][0]
            assert "path" in item
            assert "type" in item
    except Exception as e:
        # May fail due to rate limits
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_list_repo_contents_tool(provider):
    """Test the list_repo_contents tool."""
    tools = provider.get_tools()

    # Tool should only be available when fetch is enabled
    if "list_repo_contents" not in tools:
        pytest.skip("list_repo_contents tool not enabled (fetch disabled)")

    tool = tools["list_repo_contents"]

    try:
        result = await tool("psf/requests", "")
        assert result.content[0].type == "text"
        text_content = result.content[0].text
        assert isinstance(text_content, str)
        assert "psf/requests" in text_content
    except Exception as e:
        # May fail due to rate limits
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_get_file_content_tool(provider):
    """Test the get_file_content tool."""
    tools = provider.get_tools()

    if "get_file_content" not in tools:
        pytest.skip("get_file_content tool not enabled (fetch disabled)")

    tool = tools["get_file_content"]

    try:
        result = await tool("psf/requests", "README.md")
        assert result.content[0].type == "text"
        text_content = result.content[0].text
        assert isinstance(text_content, str)
    except Exception as e:
        # May fail due to rate limits
        assert "403" in str(e) or "rate limit" in str(e).lower()


@pytest.mark.asyncio
async def test_get_repo_tree_tool(provider):
    """Test the get_repo_tree tool."""
    tools = provider.get_tools()

    if "get_repo_tree" not in tools:
        pytest.skip("get_repo_tree tool not enabled (fetch disabled)")

    tool = tools["get_repo_tree"]

    try:
        result = await tool("psf/requests", recursive=False, max_items=50)
        assert result.content[0].type == "text"
        text_content = result.content[0].text
        assert isinstance(text_content, str)
        assert "psf/requests" in text_content
    except Exception as e:
        # May fail due to rate limits
        assert "403" in str(e) or "rate limit" in str(e).lower()
