#!/usr/bin/env node

/**
 * Claude Code Session Keeper
 * Maintains a persistent browser session to keep Claude Code running
 * even when the main client disconnects
 */

const puppeteer = require('puppeteer');

class ClaudeSessionKeeper {
    constructor(options = {}) {
        this.browser = null;
        this.page = null;
        this.projectName = 'betty';
        this.options = {
            headless: true,
            keepAliveInterval: 30000, // 30 seconds
            retryInterval: 5000, // 5 seconds
            maxRetries: 10,
            projectName: this.projectName,
            ...options
        };
    }

    async initialize() {
        console.log(`🚀 Initializing Claude Session Keeper for ${this.projectName}...`);
        
        try {
            this.browser = await puppeteer.launch({
                headless: this.options.headless,
                userDataDir: `/tmp/puppeteer-${this.projectName}`,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            });

            this.page = await this.browser.newPage();
            
            // Set user agent to look like a real browser
            await this.page.setUserAgent(`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Betty/${this.projectName}`);
            
            console.log(`✅ Browser initialized successfully for ${this.projectName}`);
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize browser:', error);
            return false;
        }
    }

    async navigateToClaudeCode() {
        console.log('🌐 Navigating to Claude Code...');
        
        try {
            // You would replace this with the actual Claude Code URL
            // This is a placeholder for demonstration
            await this.page.goto('https://claude.ai/code', {
                waitUntil: 'networkidle2',
                timeout: 60000
            });
            
            console.log('✅ Successfully navigated to Claude Code');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to navigate to Claude Code:', error);
            return false;
        }
    }

    async maintainSession() {
        console.log('🔄 Starting session maintenance...');
        
        const keepAlive = setInterval(async () => {
            try {
                // Keep the session alive by interacting with the page
                await this.page.evaluate(() => {
                    // Send a heartbeat or small interaction
                    window.focus();
                    return 'alive';
                });
                
                console.log('💓 Session heartbeat sent');
                
            } catch (error) {
                console.error('❌ Heartbeat failed:', error);
                // Attempt to recover
                await this.recover();
            }
        }, this.options.keepAliveInterval);

        // Handle cleanup on exit
        process.on('SIGINT', () => {
            console.log('🛑 Shutting down session keeper...');
            clearInterval(keepAlive);
            this.cleanup();
            process.exit(0);
        });

        console.log(`✅ Session maintenance started (${this.options.keepAliveInterval}ms intervals)`);
    }

    async recover() {
        console.log('🔧 Attempting session recovery...');
        
        try {
            // Check if page is still responsive
            await this.page.evaluate(() => window.location.href);
            console.log('✅ Page is responsive, recovery not needed');
            
        } catch (error) {
            console.log('🔄 Page unresponsive, attempting full recovery...');
            
            try {
                // Close current page and create new one
                await this.page.close();
                this.page = await this.browser.newPage();
                await this.navigateToClaudeCode();
                
                console.log('✅ Session recovered successfully');
                
            } catch (recoveryError) {
                console.error('❌ Recovery failed:', recoveryError);
                // Could implement more aggressive recovery here
            }
        }
    }

    async cleanup() {
        console.log('🧹 Cleaning up browser resources...');
        
        try {
            if (this.page) {
                await this.page.close();
            }
            if (this.browser) {
                await this.browser.close();
            }
            console.log('✅ Cleanup completed');
            
        } catch (error) {
            console.error('❌ Cleanup error:', error);
        }
    }

    async start() {
        console.log('🎯 Starting Claude Session Keeper');
        
        const initialized = await this.initialize();
        if (!initialized) {
            process.exit(1);
        }

        const navigated = await this.navigateToClaudeCode();
        if (!navigated) {
            await this.cleanup();
            process.exit(1);
        }

        await this.maintainSession();
        
        console.log('🎉 Claude Session Keeper is now running');
        console.log('Press Ctrl+C to stop');
    }
}

// Run if called directly
if (require.main === module) {
    const keeper = new ClaudeSessionKeeper({
        headless: true, // Run headless on server
        keepAliveInterval: 30000 // 30 second heartbeat
    });
    
    keeper.start().catch(error => {
        console.error('❌ Fatal error:', error);
        process.exit(1);
    });
}

module.exports = ClaudeSessionKeeper;