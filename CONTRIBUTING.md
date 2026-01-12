# Contributing to RTFD

Thank you for your interest in contributing to RTFD! This document outlines how to contribute code and how the release process works.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/aserper/RTFD.git
   cd RTFD
   ```

2. Install in development mode:
   ```bash
   uv sync --extra dev
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

## Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit with clear messages:
   ```bash
   git commit -m "feat: add new feature"
   # or
   git commit -m "fix: resolve issue with X"
   ```

3. **Update the CHANGELOG.md**:
   - Add your changes under the `[Unreleased]` section
   - **Note**: Do not create a new version header. The release process will automatically move your `[Unreleased]` changes to a new version section.
   - Follow the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
   - Use categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
   - Write clear, user-focused descriptions
   - Example:
     ```markdown
     ## [Unreleased]

     ### Added
     - New feature X that allows users to do Y

     ### Fixed
     - Issue with Z that caused incorrect behavior
     ```

4. Push and create a pull request on GitHub

## Code Quality

- Follow PEP 8 style guidelines
- Write clear commit messages
- Include docstrings for public functions
- Add tests for new features
- Ensure all tests pass before submitting PR

## Writing Tool Descriptions

RTFD follows a token-efficient format for MCP tool descriptions. This section explains how to write descriptions that are clear for LLMs while minimizing token consumption.

### Format Template

Use this 3-4 line structure:

```python
async def tool_name(param1: str, param2: int = 5) -> CallToolResult:
    """
    {One-line summary}. For {related context}, use {other_tool}.

    When: {Brief description of when to use this tool}
    Args: param1="example", param2=5
    Ex: tool_name("value") → {brief result description}
    """
```

### Component Guidelines

**Summary Line**
- **DO**: Be concise and specific: "Fetch PyPI package README docs"
- **DON'T**: Be verbose: "Fetch actual Python package documentation from PyPI README/description"
- Keep it under 60 characters
- Mention the main resource/action

**When** (Optional)
- One short phrase describing the use case
- Examples: "Need installation instructions", "Finding Docker images"
- Omit if the summary is self-explanatory

**Args**
- Inline format with example values: `package="requests", max_bytes=20480`
- Use realistic example values (not "foo", "bar")
- Show all parameters with their defaults

**Ex** (Example)
- Show a concrete function call and brief result
- Format: `tool_name("example") → result description`
- Keep result description under 30 characters

**See also** (Optional)
- List related tools: `See also: other_tool, another_tool`
- Use when there's a clear workflow or alternative

**Not for** (Optional)
- Briefly mention what the tool is NOT for
- Example: "Not for: External doc sites (use WebFetch)"

### Before/After Example

**Before** (810 chars, ~202 tokens):
```python
"""
Get content of a specific file from a GitHub repository.

USE THIS WHEN: You need to read the actual source code or contents of a specific file.

BEST FOR: Examining implementation details, understanding how code works, or reading configuration files.
Returns the full file content (UTF-8 text only, binary files are rejected).

Automatically handles:
- Base64 decoding from GitHub API
- UTF-8 conversion with safe truncation
- Binary file detection

Args:
    repo: Repository in format "owner/repo" (e.g., "psf/requests")
    path: Path to file (e.g., "requests/api.py")
    max_bytes: Maximum content size (default 100KB, increase for large files)

Returns:
    JSON with file content, size, truncation status, and metadata

Example: get_file_content("psf/requests", "requests/api.py") → Returns source code of api.py
"""
```

**After** (189 chars, ~47 tokens, **77% reduction**):
```python
"""
Read file from GitHub repo. UTF-8 only, rejects binary.

When: Need source code or config file content
Args: repo="owner/repo", path="src/file.py", max_bytes=102400
Ex: get_file_content("psf/requests", "requests/api.py") → file content
"""
```

### Why This Works for LLMs

1. **LLMs don't need verbose prose** - They excel at pattern matching and semantic understanding
2. **Structured format is easier to parse** - Key/value pairs are clearer than narrative text
3. **Examples provide concrete patterns** - Real parameter values beat abstract descriptions
4. **Token efficiency compounds** - 29 tools × 600 chars saved = ~15,000 chars (~4,000 tokens)
5. **Response schema is self-documenting** - LLMs see the actual JSON response, no need to describe it

### Target Metrics

- **Character count:** ~150-250 chars per tool description
- **Line count:** 3-5 lines (excluding the opening `"""` and closing `"""`)
- **Token count:** ~40-60 tokens per description

### Common Mistakes to Avoid

❌ **Don't repeat what the function signature says**
```python
async def fetch_pypi_docs(package: str, max_bytes: int = 20480) -> CallToolResult:
    """
    Args:
        package: PyPI package name
        max_bytes: Maximum content size
    """
```

✅ **Do show example values**
```python
    """
    Args: package="requests", max_bytes=20480
    """
```

❌ **Don't describe the return value in detail**
```python
"""
Returns:
    JSON with actual documentation content, size, truncation status, version
"""
```

✅ **LLMs see the actual response - omit redundant descriptions**

❌ **Don't use boilerplate phrases**
```python
"""
USE THIS WHEN: You need to...
BEST FOR: Getting...
"""
```

✅ **Use structured format**
```python
"""
When: Need installation instructions
"""
```

## Questions?

Feel free to open an issue or discussion if you have questions about the contribution process!
