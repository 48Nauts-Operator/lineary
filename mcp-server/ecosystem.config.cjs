module.exports = {
  apps: [
    {
      name: 'lineary-mcp-server',
      script: './index.js',
      cwd: '/home/jarvis/projects/Lineary/mcp-server',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        NODE_ENV: 'production',
        LINEARY_API_URL: 'https://ai-linear.blockonauts.io/api'
      },
      error_file: '/home/jarvis/projects/Lineary/logs/mcp-error.log',
      out_file: '/home/jarvis/projects/Lineary/logs/mcp-out.log',
      log_file: '/home/jarvis/projects/Lineary/logs/mcp-combined.log',
      time: true,
      // Restart if it crashes
      min_uptime: '10s',
      max_restarts: 10,
      // Restart if memory usage is too high
      max_memory_restart: '500M',
      // Exponential backoff restart delay
      exp_backoff_restart_delay: 100
    }
  ]
};