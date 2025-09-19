# GritQL MCP Server

A Model Context Protocol (MCP) server that provides a simple wrapper around GritQL, allowing AI models to search, analyze, and transform code using GritQL patterns.

## Overview

GritQL is a powerful query language for searching, linting, and modifying code. This MCP server exposes GritQL's capabilities through the Model Context Protocol, enabling AI assistants to:

- Apply code transformations using GritQL patterns
- Check code for pattern violations
- List available patterns and migrations
- Execute custom GritQL queries

## Installation

```bash
npm install
npm run build
```

## Usage

The server runs on stdio and can be used with any MCP-compatible client:

```bash
npm start
```

## Available Tools

### `grit_apply`
Apply a GritQL pattern to transform code files.

**Parameters:**
- `pattern` (required): The GritQL pattern to apply (can be a pattern name or inline pattern)
- `files` (optional): Specific files to apply the pattern to
- `directory` (optional): Directory to apply the pattern to (defaults to current directory)
- `dry_run` (optional): Show what would be changed without making changes

**Example:**
```json
{
  "name": "grit_apply",
  "arguments": {
    "pattern": "console.log($message) => console.debug($message)",
    "directory": "./src",
    "dry_run": true
  }
}
```

### `grit_check`
Check code files against GritQL patterns for violations.

**Parameters:**
- `directory` (optional): Directory to check (defaults to current directory)
- `patterns` (optional): Specific patterns to check against

**Example:**
```json
{
  "name": "grit_check",
  "arguments": {
    "directory": "./src"
  }
}
```

### `grit_list`
List available GritQL patterns and migrations.

**Parameters:**
- `type` (optional): Type of items to list ("patterns", "migrations", or "all")

**Example:**
```json
{
  "name": "grit_list",
  "arguments": {
    "type": "patterns"
  }
}
```

### `grit_query`
Execute a custom GritQL query on code files.

**Parameters:**
- `query` (required): The GritQL query to execute
- `files` (optional): Specific files to query
- `directory` (optional): Directory to query (defaults to current directory)

**Example:**
```json
{
  "name": "grit_query",
  "arguments": {
    "query": "console.log($message)",
    "directory": "./src"
  }
}
```

## GritQL Pattern Examples

Here are some common GritQL patterns you can use:

1. **Replace console.log with console.debug:**
   ```
   console.log($message) => console.debug($message)
   ```

2. **Find all function declarations:**
   ```
   function $name($params) { $body }
   ```

3. **Replace var with let:**
   ```
   var $name = $value => let $name = $value
   ```

4. **Find React components:**
   ```
   function $name($props) { return $jsx }
   ```

## Development

To run in development mode:

```bash
npm run dev
```

To build:

```bash
npm run build
```

## Dependencies

- [@modelcontextprotocol/sdk](https://www.npmjs.com/package/@modelcontextprotocol/sdk): MCP SDK for TypeScript
- [@getgrit/cli](https://www.npmjs.com/package/@getgrit/cli): GritQL command-line interface

## License

MIT