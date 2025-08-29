#!/usr/bin/env node

/**
 * API Testing Script
 * 
 * Tests the Python FastAPI application with generated Clerk JWT tokens.
 */

require('dotenv').config({ path: '../.env' });
const axios = require('axios');
const fs = require('fs');
const { createMockJWTToken, extractInstanceId } = require('./generate-token');

// Configuration
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

// ANSI color codes
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
    console.log(`${color}${message}${colors.reset}`);
}

function logSuccess(message) {
    log(`✅ ${message}`, colors.green);
}

function logError(message) {
    log(`❌ ${message}`, colors.red);
}

function logInfo(message) {
    log(`ℹ️  ${message}`, colors.blue);
}

function logTitle(message) {
    log(`\n${colors.bright}${colors.cyan}🧪 ${message}${colors.reset}`);
    log('='.repeat(50));
}

/**
 * Get or generate JWT token
 */
function getJWTToken() {
    // Try to read from saved file first
    try {
        if (fs.existsSync('.token')) {
            const token = fs.readFileSync('.token', 'utf8').trim();
            if (token && token.split('.').length === 3) {
                logInfo('Using saved token from .token file');
                return token;
            }
        }
    } catch (error) {
        // Ignore file read errors
    }
    
    // Generate new token
    const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || process.env.CLERK_PUBLISHABLE_KEY;
    if (!publishableKey) {
        throw new Error('No Clerk publishable key found in environment');
    }
    
    const instanceId = extractInstanceId(publishableKey);
    if (!instanceId) {
        throw new Error('Invalid publishable key format');
    }
    
    logInfo('Generating new JWT token...');
    const token = createMockJWTToken(instanceId);
    
    // Save for future use
    fs.writeFileSync('.token', token);
    return token;
}

/**
 * Make HTTP request with error handling
 */
async function makeRequest(method, endpoint, data = null, headers = {}) {
    try {
        const config = {
            method,
            url: `${API_BASE_URL}${endpoint}`,
            headers: {
                'Content-Type': 'application/json',
                ...headers
            },
            validateStatus: () => true, // Don't throw on HTTP errors
        };
        
        if (data) {
            config.data = data;
        }
        
        const response = await axios(config);
        return {
            success: response.status >= 200 && response.status < 300,
            status: response.status,
            data: response.data,
            headers: response.headers
        };
    } catch (error) {
        return {
            success: false,
            error: error.message,
            status: 0
        };
    }
}

/**
 * Test API endpoints
 */
async function runTests() {
    logTitle('API Test Suite');
    
    let token;
    try {
        token = getJWTToken();
    } catch (error) {
        logError(`Failed to get JWT token: ${error.message}`);
        return false;
    }
    
    const tests = [
        {
            name: 'Health Check (Public)',
            method: 'GET',
            endpoint: '/health',
            expectedStatus: 200,
            requiresAuth: false
        },
        {
            name: 'Root Endpoint (Public)',
            method: 'GET',
            endpoint: '/',
            expectedStatus: 200,
            requiresAuth: false
        },
        {
            name: 'Fiscal Code Validation (No Auth)',
            method: 'POST',
            endpoint: '/fiscal-code/validate',
            data: { code: 'CCCFBA85D03L219P' },
            expectedStatus: 401,
            requiresAuth: false,
            expectError: true
        },
        {
            name: 'Fiscal Code Validation (With Auth)',
            method: 'POST',
            endpoint: '/fiscal-code/validate',
            data: { code: 'CCCFBA85D03L219P' },
            expectedStatus: 200,
            requiresAuth: true
        },
        {
            name: 'Fiscal Code Validation (Invalid Code)',
            method: 'POST',
            endpoint: '/fiscal-code/validate',
            data: { code: 'INVALID123' },
            expectedStatus: 200,
            requiresAuth: true
        },
        {
            name: 'VAT Number Validation (With Auth)',
            method: 'POST',
            endpoint: '/vat/validate',
            data: { partita_iva: '01234567897' },
            expectedStatus: 200,
            requiresAuth: true
        },
        {
            name: 'Fiscal Code Encoding (With Auth)',
            method: 'POST',
            endpoint: '/fiscal-code/encode',
            data: {
                lastname: 'Rossi',
                firstname: 'Mario',
                gender: 'M',
                birthdate: '01/01/1990',
                birthplace: 'Milano'
            },
            expectedStatus: 200,
            requiresAuth: true
        }
    ];
    
    let passed = 0;
    let failed = 0;
    
    for (const test of tests) {
        console.log(`\nRunning: ${test.name}`);
        console.log('-'.repeat(40));
        
        const headers = test.requiresAuth ? { Authorization: `Bearer ${token}` } : {};
        
        const result = await makeRequest(test.method, test.endpoint, test.data, headers);
        
        if (result.error) {
            logError(`Request failed: ${result.error}`);
            failed++;
            continue;
        }
        
        const statusMatch = result.status === test.expectedStatus;
        
        if (statusMatch) {
            logSuccess(`Status: ${result.status} (expected)`);
            
            if (result.success && result.data) {
                if (typeof result.data === 'object') {
                    console.log('Response:', JSON.stringify(result.data, null, 2));
                } else {
                    console.log('Response:', result.data.toString().substring(0, 200) + '...');
                }
            }
            
            passed++;
        } else {
            logError(`Status: ${result.status} (expected ${test.expectedStatus})`);
            if (result.data) {
                console.log('Response:', JSON.stringify(result.data, null, 2));
            }
            failed++;
        }
    }
    
    // Summary
    logTitle('Test Results');
    logSuccess(`Passed: ${passed}`);
    if (failed > 0) {
        logError(`Failed: ${failed}`);
    }
    log(`Total: ${passed + failed}`);
    
    return failed === 0;
}

/**
 * Interactive mode for testing specific endpoints
 */
async function interactiveMode() {
    logTitle('Interactive API Testing');
    
    const readline = require('readline');
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    
    function question(prompt) {
        return new Promise(resolve => rl.question(prompt, resolve));
    }
    
    try {
        const token = getJWTToken();
        console.log('\nAvailable endpoints:');
        console.log('1. /health (GET)');
        console.log('2. /fiscal-code/validate (POST)');
        console.log('3. /fiscal-code/encode (POST)');
        console.log('4. /vat/validate (POST)');
        console.log('5. Custom endpoint');
        console.log('6. Exit');
        
        while (true) {
            const choice = await question('\nSelect option (1-6): ');
            
            if (choice === '6') break;
            
            let endpoint, method, data;
            
            switch (choice) {
                case '1':
                    endpoint = '/health';
                    method = 'GET';
                    break;
                case '2':
                    endpoint = '/fiscal-code/validate';
                    method = 'POST';
                    const code = await question('Enter fiscal code: ');
                    data = { code };
                    break;
                case '3':
                    endpoint = '/fiscal-code/encode';
                    method = 'POST';
                    const lastname = await question('Last name: ');
                    const firstname = await question('First name: ');
                    const gender = await question('Gender (M/F): ');
                    const birthdate = await question('Birth date (DD/MM/YYYY): ');
                    const birthplace = await question('Birth place: ');
                    data = { lastname, firstname, gender, birthdate, birthplace };
                    break;
                case '4':
                    endpoint = '/vat/validate';
                    method = 'POST';
                    const partita_iva = await question('Enter VAT number: ');
                    data = { partita_iva };
                    break;
                case '5':
                    endpoint = await question('Enter endpoint (e.g., /health): ');
                    method = await question('Enter method (GET/POST): ');
                    const rawData = await question('Enter JSON data (empty for none): ');
                    data = rawData ? JSON.parse(rawData) : null;
                    break;
                default:
                    console.log('Invalid choice');
                    continue;
            }
            
            const headers = endpoint !== '/health' ? { Authorization: `Bearer ${token}` } : {};
            const result = await makeRequest(method, endpoint, data, headers);
            
            console.log(`\nResponse (${result.status}):`);
            if (result.data) {
                console.log(JSON.stringify(result.data, null, 2));
            }
        }
        
    } catch (error) {
        logError(`Interactive mode failed: ${error.message}`);
    } finally {
        rl.close();
    }
}

/**
 * Main function
 */
async function main() {
    const args = process.argv.slice(2);
    
    if (args.includes('--interactive') || args.includes('-i')) {
        await interactiveMode();
    } else {
        const success = await runTests();
        process.exit(success ? 0 : 1);
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(error => {
        logError(`Unexpected error: ${error.message}`);
        process.exit(1);
    });
}