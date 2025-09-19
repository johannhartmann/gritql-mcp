#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs/promises";

const execAsync = promisify(exec);

class GritQLMCPServer {
  private server: Server;

  constructor() {
    this.server = new Server({
      name: "gritql-mcp",
      version: "1.0.0",
    });

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "grit_apply",
            description: "Apply a GritQL pattern to transform code files",
            inputSchema: {
              type: "object",
              properties: {
                pattern: {
                  type: "string",
                  description: "The GritQL pattern to apply (can be a pattern name or inline pattern)",
                },
                files: {
                  type: "array",
                  items: { type: "string" },
                  description: "Optional: Specific files to apply the pattern to",
                },
                directory: {
                  type: "string",
                  description: "Optional: Directory to apply the pattern to (defaults to current directory)",
                },
                dry_run: {
                  type: "boolean",
                  description: "Optional: Show what would be changed without making changes",
                  default: false,
                },
              },
              required: ["pattern"],
            },
          },
          {
            name: "grit_check",
            description: "Check code files against GritQL patterns for violations",
            inputSchema: {
              type: "object",
              properties: {
                directory: {
                  type: "string",
                  description: "Optional: Directory to check (defaults to current directory)",
                },
                patterns: {
                  type: "array",
                  items: { type: "string" },
                  description: "Optional: Specific patterns to check against",
                },
              },
              required: [],
            },
          },
          {
            name: "grit_list",
            description: "List available GritQL patterns and migrations",
            inputSchema: {
              type: "object",
              properties: {
                type: {
                  type: "string",
                  enum: ["patterns", "migrations", "all"],
                  description: "Type of items to list",
                  default: "all",
                },
              },
              required: [],
            },
          },
          {
            name: "grit_query",
            description: "Execute a custom GritQL query on code files",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "The GritQL query to execute",
                },
                files: {
                  type: "array",
                  items: { type: "string" },
                  description: "Optional: Specific files to query",
                },
                directory: {
                  type: "string",
                  description: "Optional: Directory to query (defaults to current directory)",
                },
              },
              required: ["query"],
            },
          },
        ] as Tool[],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case "grit_apply":
            return await this.handleGritApply(args);
          case "grit_check":
            return await this.handleGritCheck(args);
          case "grit_list":
            return await this.handleGritList(args);
          case "grit_query":
            return await this.handleGritQuery(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error executing ${name}: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  private async handleGritApply(args: any) {
    const { pattern, files, directory, dry_run } = args;
    
    let cmd = `npx @getgrit/cli apply "${pattern}"`;
    
    if (dry_run) {
      cmd += " --dry-run";
    }
    
    const cwd = directory || process.cwd();
    
    // Add files as arguments if specified
    if (files && files.length > 0) {
      cmd += ` ${files.join(" ")}`;
    }
    
    try {
      const { stdout, stderr } = await execAsync(cmd, { cwd });
      
      return {
        content: [
          {
            type: "text",
            text: `GritQL Apply Result:\n\nStdout:\n${stdout}\n\nStderr:\n${stderr}`,
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: "text",
            text: `GritQL Apply Error:\n${error.message}\nStdout: ${error.stdout}\nStderr: ${error.stderr}`,
          },
        ],
      };
    }
  }

  private async handleGritCheck(args: any) {
    const { directory, patterns } = args;
    
    let cmd = `npx @getgrit/cli check`;
    
    const cwd = directory || process.cwd();
    
    try {
      const { stdout, stderr } = await execAsync(cmd, { cwd });
      
      return {
        content: [
          {
            type: "text",
            text: `GritQL Check Result:\n\nStdout:\n${stdout}\n\nStderr:\n${stderr}`,
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: "text",
            text: `GritQL Check Result:\n${error.message}\nStdout: ${error.stdout}\nStderr: ${error.stderr}`,
          },
        ],
      };
    }
  }

  private async handleGritList(args: any) {
    const { type = "all" } = args;
    
    let cmd = `npx @getgrit/cli list`;
    
    try {
      const { stdout, stderr } = await execAsync(cmd);
      
      return {
        content: [
          {
            type: "text",
            text: `GritQL Available Patterns and Migrations:\n\n${stdout}`,
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: "text",
            text: `GritQL List Error:\n${error.message}\nStdout: ${error.stdout}\nStderr: ${error.stderr}`,
          },
        ],
      };
    }
  }

  private async handleGritQuery(args: any) {
    const { query, files, directory } = args;
    
    // For custom queries, we can use grit apply with a custom pattern
    let cmd = `npx @getgrit/cli apply "${query}" --dry-run`;
    
    const cwd = directory || process.cwd();
    
    // Add files as arguments if specified
    if (files && files.length > 0) {
      cmd += ` ${files.join(" ")}`;
    }
    
    try {
      const { stdout, stderr } = await execAsync(cmd, { cwd });
      
      return {
        content: [
          {
            type: "text",
            text: `GritQL Query Result:\n\nStdout:\n${stdout}\n\nStderr:\n${stderr}`,
          },
        ],
      };
    } catch (error: any) {
      return {
        content: [
          {
            type: "text",
            text: `GritQL Query Error:\n${error.message}\nStdout: ${error.stdout}\nStderr: ${error.stderr}`,
          },
        ],
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("GritQL MCP Server running on stdio");
  }
}

// Run the server
const server = new GritQLMCPServer();
server.run().catch((error) => {
  console.error("Failed to run server:", error);
  process.exit(1);
});