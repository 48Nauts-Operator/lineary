#!/usr/bin/env node

const { spawn } = require('child_process');
const readline = require('readline');

class BettyMCPServer {
    constructor() {
        this.bettyBaseUrl = 'http://localhost:8001';
        this.userId = 'e8e3f2de-070d-4dbd-b899-e49745f1d29b';
    }

    async handleRequest(request) {
        const { method, params } = request;

        switch (method) {
            case 'initialize':
                return {
                    protocolVersion: '2024-11-05',
                    capabilities: {
                        tools: {}
                    }
                };

            case 'tools/list':
                return {
                    tools: [
                        {
                            name: 'betty_search',
                            description: 'Search BETTY memory system for previous conversations and knowledge',
                            inputSchema: {
                                type: 'object',
                                properties: {
                                    query: {
                                        type: 'string',
                                        description: 'Search query to find relevant information in BETTY memory'
                                    }
                                },
                                required: ['query']
                            }
                        }
                    ]
                };

            case 'tools/call':
                const { name: toolName, arguments: args } = params;
                if (toolName === 'betty_search') {
                    return await this.bettySearch(args.query);
                }
                return {
                    content: [{ type: 'text', text: `Unknown tool: ${toolName}` }],
                    isError: true
                };

            default:
                return {
                    error: {
                        code: -32601,
                        message: `Method not found: ${method}`
                    }
                };
        }
    }

    async bettySearch(query) {
        try {
            const searchUrl = `${this.bettyBaseUrl}/api/knowledge/?search=${encodeURIComponent(query)}`;
            
            // Use curl for HTTP request (simple and reliable)
            const response = await this.curlRequest(searchUrl);
            const data = JSON.parse(response);
            const items = data.data || [];

            // Filter relevant items
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
                    content: [{ type: 'text', text: resultText }]
                };
            } else {
                return {
                    content: [{ type: 'text', text: `No relevant memories found for "${query}"` }]
                };
            }

        } catch (error) {
            return {
                content: [{ type: 'text', text: `BETTY search error: ${error.message}` }],
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
}

async function main() {
    const server = new BettyMCPServer();
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false
    });

    rl.on('line', async (line) => {
        try {
            const request = JSON.parse(line);
            const response = await server.handleRequest(request);

            // Add JSON-RPC fields
            response.jsonrpc = '2.0';
            if (request.id !== undefined) {
                response.id = request.id;
            }

            console.log(JSON.stringify(response));
        } catch (error) {
            const errorResponse = {
                jsonrpc: '2.0',
                error: {
                    code: -32603,
                    message: error.message
                }
            };
            
            if (request && request.id !== undefined) {
                errorResponse.id = request.id;
            }

            console.log(JSON.stringify(errorResponse));
        }
    });
}

if (require.main === module) {
    main().catch(console.error);
}