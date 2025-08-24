#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const { spawn } = require('child_process');
const crypto = require('crypto');
const fs = require('fs').promises;

class BettyMCPServer {
    constructor() {
        this.bettyBaseUrl = 'http://localhost:3034';
        this.userId = 'e8e3f2de-070d-4dbd-b899-e49745f1d29b';
        this.projectId = 'betty-project';
        
        // Conversation capture state
        this.currentSessionId = null;
        this.messageBuffer = [];
        this.sessionStartTime = null;
        this.sessionMetadata = {};
        
        this.server = new Server(
            {
                name: 'betty-server',
                version: '2.0.0',
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
                    },
                    {
                        name: 'betty_start_session',
                        description: 'Start a new Claude conversation session for automatic memory capture',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                project_context: {
                                    type: 'string',
                                    description: 'Context about what project or task this session relates to'
                                },
                                user_goal: {
                                    type: 'string',
                                    description: 'What the user hopes to accomplish in this session'
                                },
                                expected_duration: {
                                    type: 'string',
                                    description: 'Expected session duration (short/medium/long)',
                                    enum: ['short', 'medium', 'long']
                                }
                            },
                            required: ['project_context', 'user_goal']
                        }
                    },
                    {
                        name: 'betty_capture_message',
                        description: 'Capture a message from the current Claude conversation',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                role: {
                                    type: 'string',
                                    description: 'Message role (user, assistant, system)',
                                    enum: ['user', 'assistant', 'system']
                                },
                                content: {
                                    type: 'string',
                                    description: 'Full message content'
                                },
                                context: {
                                    type: 'object',
                                    properties: {
                                        user_intent: { type: 'string' },
                                        problem_category: { type: 'string' },
                                        files_mentioned: { type: 'array', items: { type: 'string' } },
                                        technologies_mentioned: { type: 'array', items: { type: 'string' } }
                                    }
                                },
                                tool_calls: {
                                    type: 'array',
                                    items: { type: 'object' }
                                }
                            },
                            required: ['role', 'content']
                        }
                    },
                    {
                        name: 'betty_end_session',
                        description: 'End the current conversation session and trigger final processing',
                        inputSchema: {
                            type: 'object',
                            properties: {
                                outcome: {
                                    type: 'string',
                                    description: 'Session outcome (successful/partial/failed/interrupted)',
                                    enum: ['successful', 'partial', 'failed', 'interrupted']
                                },
                                summary: {
                                    type: 'string',
                                    description: 'Brief summary of what was accomplished'
                                },
                                key_decisions: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Key decisions made during the session'
                                },
                                lessons_learned: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Important lessons or insights gained'
                                },
                                technologies_used: {
                                    type: 'array',
                                    items: { type: 'string' },
                                    description: 'Technologies discussed or implemented'
                                }
                            },
                            required: ['outcome', 'summary']
                        }
                    }
                ]
            };
        });

        // Handle tool calls
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;

            switch (name) {
                case 'betty_search':
                    return await this.handleBettySearch(args.query);
                case 'betty_start_session':
                    return await this.handleStartSession(args);
                case 'betty_capture_message':
                    return await this.handleCaptureMessage(args);
                case 'betty_end_session':
                    return await this.handleEndSession(args);
                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        });
    }

    async handleBettySearch(query) {
        try {
            const searchUrl = `${this.bettyBaseUrl}/api/knowledge/?search=${encodeURIComponent(query)}`;
            
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
                        text: `BETTY search error: ${error.message}`
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

    // Generate UUID v4
    generateUUID() {
        return crypto.randomUUID();
    }

    // Format timestamp for BETTY API
    formatTimestamp(date = new Date()) {
        return date.toISOString();
    }

    // HTTP POST request using curl
    async curlPost(url, data, headers = {}) {
        const tempFile = `/tmp/betty-payload-${Date.now()}.json`;
        
        try {
            await fs.writeFile(tempFile, JSON.stringify(data));
            
            const curlArgs = [
                '-s',
                '-X', 'POST',
                '-H', 'Content-Type: application/json',
                '-d', `@${tempFile}`,
                ...Object.entries(headers).flatMap(([key, value]) => ['-H', `${key}: ${value}`]),
                url
            ];
            
            const response = await this.curlRequest(url, curlArgs);
            return JSON.parse(response);
            
        } finally {
            // Clean up temp file
            try {
                await fs.unlink(tempFile);
            } catch (e) {
                // Ignore cleanup errors
            }
        }
    }

    // Enhanced curl request with custom args
    curlRequest(url, customArgs = null) {
        return new Promise((resolve, reject) => {
            const args = customArgs || ['-s', url];
            const curl = spawn('curl', args);
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
                    reject(new Error(`curl failed (${code}): ${error}`));
                }
            });
        });
    }

    // Start a new conversation session
    async handleStartSession(args) {
        try {
            this.currentSessionId = this.generateUUID();
            this.messageBuffer = [];
            this.sessionStartTime = new Date();
            this.sessionMetadata = {
                project_context: args.project_context,
                user_goal: args.user_goal,
                expected_duration: args.expected_duration || 'medium'
            };
            
            console.error(`BETTY: Started session ${this.currentSessionId}`);
            
            return {
                content: [
                    {
                        type: 'text',
                        text: `Started BETTY memory capture session: ${this.currentSessionId}\n\nProject Context: ${args.project_context}\nUser Goal: ${args.user_goal}\nExpected Duration: ${args.expected_duration || 'medium'}\n\nAll messages in this conversation will now be automatically captured for memory.`
                    }
                ]
            };
            
        } catch (error) {
            console.error('BETTY: Error starting session:', error);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Failed to start BETTY session: ${error.message}`
                    }
                ],
                isError: true
            };
        }
    }

    // Capture a message from the conversation
    async handleCaptureMessage(args) {
        try {
            if (!this.currentSessionId) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: 'No active BETTY session. Please start a session first with betty_start_session.'
                        }
                    ],
                    isError: true
                };
            }
            
            const message = {
                role: args.role,
                content: args.content,
                timestamp: this.formatTimestamp(),
                context: args.context || {},
                tool_calls: args.tool_calls || []
            };
            
            this.messageBuffer.push(message);
            
            console.error(`BETTY: Captured ${args.role} message (${message.content.substring(0, 100)}...)`);
            
            return {
                content: [
                    {
                        type: 'text',
                        text: `Message captured for BETTY memory (${this.messageBuffer.length} messages in session)`
                    }
                ]
            };
            
        } catch (error) {
            console.error('BETTY: Error capturing message:', error);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Failed to capture message: ${error.message}`
                    }
                ],
                isError: true
            };
        }
    }

    // End session and send to BETTY API
    async handleEndSession(args) {
        try {
            if (!this.currentSessionId) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: 'No active BETTY session to end.'
                        }
                    ],
                    isError: true
                };
            }
            
            const sessionDuration = Math.floor((new Date() - this.sessionStartTime) / 1000 / 60); // minutes
            
            // Prepare conversation data for BETTY API
            const conversationData = {
                messages: this.messageBuffer,
                outcome: args.outcome,
                summary: args.summary,
                key_decisions: args.key_decisions || [],
                lessons_learned: args.lessons_learned || [],
                technologies_used: args.technologies_used || [],
                patterns_applied: [] // Could be enhanced to extract patterns
            };
            
            const ingestionRequest = {
                user_id: this.userId,
                project_id: this.projectId,
                session_id: this.currentSessionId,
                conversation_data: conversationData,
                claude_version: 'claude-3-sonnet',
                environment: 'development',
                duration_minutes: sessionDuration
            };
            
            // Send to BETTY ingestion API
            const ingestionUrl = `${this.bettyBaseUrl}/api/knowledge/ingest/conversation`;
            const response = await this.curlPost(ingestionUrl, ingestionRequest);
            
            // Clear session state
            const completedSessionId = this.currentSessionId;
            const messageCount = this.messageBuffer.length;
            this.currentSessionId = null;
            this.messageBuffer = [];
            this.sessionStartTime = null;
            this.sessionMetadata = {};
            
            console.error(`BETTY: Completed session ${completedSessionId} - ${messageCount} messages ingested`);
            
            return {
                content: [
                    {
                        type: 'text',
                        text: `BETTY session completed successfully!\n\nSession ID: ${completedSessionId}\nMessages Captured: ${messageCount}\nDuration: ${sessionDuration} minutes\nOutcome: ${args.outcome}\n\nConversation has been ingested into BETTY memory system for future reference.`
                    }
                ]
            };
            
        } catch (error) {
            console.error('BETTY: Error ending session:', error);
            return {
                content: [
                    {
                        type: 'text',
                        text: `Failed to end BETTY session: ${error.message}\n\nSession data has been preserved in buffer for retry.`
                    }
                ],
                isError: true
            };
        }
    }

    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        
        // Log to stderr (not stdout, which is used for MCP protocol)
        console.error('BETTY MCP Server v2.0 started with conversation capture');
        console.error('Available tools: betty_search, betty_start_session, betty_capture_message, betty_end_session');
    }
}

// Start the server
async function main() {
    const server = new BettyMCPServer();
    await server.run();
}

if (require.main === module) {
    main().catch((error) => {
        console.error('Server error:', error);
        process.exit(1);
    });
}