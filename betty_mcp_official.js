#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const { spawn } = require('child_process');

class LinearyMCPServer {
    constructor() {
        this.linearyBaseUrl = 'http://localhost:8620';
        this.userId = 'e8e3f2de-070d-4dbd-b899-e49745f1d29b';
        
        this.server = new Server(
            {
                name: 'lineary-server',
                version: '1.0.0',
            },
            {
                capabilities: {
                    tools: {},
                },
            }
        );

        this.setupHandlers();
    }

    setupHandlers() {
        // List available tools
        this.server.setRequestHandler(ListToolsRequestSchema, async () => {
            return {
                tools: [
                    {
                        name: 'lineary_search',
                        description: 'Search Lineary memory system for previous conversations and knowledge',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                query: {
                                    type: 'string',
                                    description: 'Search query to find relevant information in Lineary memory'
                                }
                            },
                            required: ['query']
                        }
                    }
                ]
            };
        });

        // Handle tool calls
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;

            if (name === 'lineary_search') {
                return await this.handleLinearySearch(args.query);
            }

            throw new Error(`Unknown tool: ${name}`);
        });
    }

    async handleLinearySearch(query) {
        try {
            const searchUrl = `${this.linearyBaseUrl}/api/knowledge/?search=${encodeURIComponent(query)}`;
            
            // Use curl for the HTTP request
            const response = await this.curlRequest(searchUrl);
            const data = JSON.parse(response);
            const items = data.data || [];

            // Filter out error messages and format results
            const relevantItems = items
                .filter(item => {
                    const content = item.content || '';
                    return !content.includes('Error calling Claude API') &&
                           !content.includes('HTTP Error') &&
                           content.trim().length > 20;
                })
                .slice(0, 5); // Top 5 results

            if (relevantItems.length > 0) {
                let resultText = `Found ${relevantItems.length} relevant memories for "${query}":\n\n`;
                
                relevantItems.forEach((item, index) => {
                    const title = item.title || 'No title';
                    const content = item.content || '';
                    const truncatedContent = content.length > 300 ? 
                        content.substring(0, 300) + '...' : content;
                    
                    resultText += `${index + 1}. **${title}**\n   ${truncatedContent}\n\n`;
                });

                return {
                    content: [
                        {
                            type: 'text',
                            text: resultText
                        }
                    ]
                };
            } else {
                return {
                    content: [
                        {
                            type: 'text',
                            text: `No relevant memories found for "${query}"`
                        }
                    ]
                };
            }

        } catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Lineary search error: ${error.message}`
                    }
                ],
                isError: true
            };
        }
    }

    curlRequest(url) {
        return new Promise((resolve, reject) => {
            const curl = spawn('curl', ['-s', url]);
            let data = '';
            let error = '';

            curl.stdout.on('data', (chunk) => {
                data += chunk;
            });

            curl.stderr.on('data', (chunk) => {
                error += chunk;
            });

            curl.on('close', (code) => {
                if (code === 0) {
                    resolve(data);
                } else {
                    reject(new Error(`curl failed: ${error}`));
                }
            });
        });
    }

    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        
        // Log to stderr (not stdout, which is used for MCP protocol)
        console.error('Lineary MCP Server started');
    }
}

// Start the server
async function main() {
    const server = new LinearyMCPServer();
    await server.run();
}

if (require.main === module) {
    main().catch((error) => {
        console.error('Server error:', error);
        process.exit(1);
    });
}