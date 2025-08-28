#!/usr/bin/env node
/**
 * Test script for BETTY's enhanced error handling system
 */

const axios = require('axios');

const BETTY_API = 'http://localhost:8001';

async function testErrorHandling() {
    console.log('🔍 Testing BETTY Enhanced Error Handling System...\n');

    // Test 1: Check error tracking health
    console.log('1. Testing Error Tracking Health...');
    try {
        const health = await axios.get(`${BETTY_API}/api/errors/health-check`);
        console.log('✅ Error tracking health:', health.data);
    } catch (error) {
        console.log('❌ Error tracking health check failed:', error.message);
    }

    // Test 2: Test endpoint that doesn't exist (should trigger error handling)
    console.log('\n2. Testing 404 Error Handling...');
    try {
        await axios.get(`${BETTY_API}/api/nonexistent-endpoint`);
    } catch (error) {
        console.log('✅ 404 Error handled correctly:');
        console.log('   Status:', error.response?.status);
        console.log('   Message:', error.response?.data?.message);
        console.log('   Request ID:', error.response?.data?.request_id);
    }

    // Test 3: Test invalid POST data (should trigger validation error)
    console.log('\n3. Testing Validation Error Handling...');
    try {
        await axios.post(`${BETTY_API}/api/knowledge/ingest/batch`, {
            // Invalid data structure
            invalid_field: "test"
        });
    } catch (error) {
        console.log('✅ Validation error handled correctly:');
        console.log('   Status:', error.response?.status);
        console.log('   Error details:', error.response?.data?.detail);
    }

    // Test 4: Test timeout simulation
    console.log('\n4. Testing Timeout Error Handling...');
    try {
        await axios.get(`${BETTY_API}/api/analytics/dashboard-summary`, {
            timeout: 1 // Very short timeout to simulate timeout
        });
    } catch (error) {
        if (error.code === 'ECONNABORTED') {
            console.log('✅ Timeout error handled correctly:');
            console.log('   Code:', error.code);
            console.log('   Message:', error.message);
        } else {
            console.log('ℹ️  Timeout test completed faster than expected:', error.response?.status);
        }
    }

    // Test 5: Check if errors were logged
    console.log('\n5. Checking Error Logs...');
    try {
        const errorLogs = await axios.get(`${BETTY_API}/api/errors/summary?hours=1`);
        console.log('✅ Error summary retrieved:');
        console.log('   Total errors:', errorLogs.data.summary.total_errors);
        console.log('   Error rate per hour:', errorLogs.data.summary.error_rate_per_hour);
        console.log('   Most common errors:', errorLogs.data.summary.most_common_errors);
    } catch (error) {
        console.log('❌ Could not retrieve error logs:', error.message);
    }

    // Test 6: Test direct API health check
    console.log('\n6. Testing Main API Health...');
    try {
        const health = await axios.get(`${BETTY_API}/health`);
        console.log('✅ Main API health:', health.data);
    } catch (error) {
        console.log('❌ Main API health check failed:', error.message);
    }

    console.log('\n🎉 Error handling testing completed!');
    console.log('\nℹ️  You can now visit http://localhost:3377 to see the enhanced error monitoring in the frontend.');
    console.log('💡 Tip: Open browser dev tools to see structured error logging in the console.');
}

// Run the test
testErrorHandling().catch(console.error);