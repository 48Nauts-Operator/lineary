#!/usr/bin/env node
// Simple test to verify MCP server can start

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('🧪 Testing Lineary MCP Server...\n');

// Test 1: Check if server starts
console.log('Test 1: Starting server...');
const server = spawn('node', [join(__dirname, 'index.js')], {
  env: { ...process.env, LINEARY_API_URL: 'http://localhost:3134/api' }
});

let output = '';
server.stderr.on('data', (data) => {
  output += data.toString();
});

setTimeout(() => {
  if (output.includes('Lineary MCP Server')) {
    console.log('✅ Server started successfully');
    console.log(output);
  } else {
    console.log('❌ Server failed to start');
    console.log(output);
  }
  
  server.kill();
  process.exit(0);
}, 2000);