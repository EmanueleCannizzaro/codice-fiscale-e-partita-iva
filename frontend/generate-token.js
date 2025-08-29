#!/usr/bin/env node

/**
 * Clerk JWT Token Generator
 * 
 * This script generates valid JWT tokens for testing the Python FastAPI
 * application with Clerk authentication.
 */

require('dotenv').config({ path: '../.env' });
const jwt = require('jsonwebtoken');

// ANSI color codes for better output
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

function logWarning(message) {
    log(`⚠️  ${message}`, colors.yellow);
}

function logTitle(message) {
    log(`\n${colors.bright}${colors.cyan}🔐 ${message}${colors.reset}`);
    log('='.repeat(50));
}

/**
 * Extract instance ID from Clerk publishable key
 */
function extractInstanceId(publishableKey) {
    if (!publishableKey) return null;
    
    const parts = publishableKey.split('_');
    if (parts.length < 3) return null;
    
    return parts[2];
}

/**
 * Create a mock JWT token for testing
 */
function createMockJWTToken(instanceId) {
    const now = Math.floor(Date.now() / 1000);
    const expiry = now + (60 * 60 * 24); // 24 hours from now
    
    const header = {
        alg: 'RS256',
        typ: 'JWT',
        kid: 'test-key-id'
    };
    
    const payload = {
        // Standard JWT claims
        sub: 'user_2abcdef1234567890abcdef12', // User ID
        iss: `https://${instanceId}.clerk.accounts.dev`,
        aud: 'test-audience',
        exp: expiry,
        iat: now,
        nbf: now,
        
        // Clerk-specific claims
        sid: 'sess_2abcdef1234567890abcdef12', // Session ID
        email: 'test@example.com',
        email_verified: true,
        name: 'Test User',
        given_name: 'Test',
        family_name: 'User',
        picture: 'https://images.clerk.dev/test-avatar.jpg',
        
        // Additional metadata
        created_at: now - (60 * 60 * 24 * 30), // 30 days ago
        updated_at: now - (60 * 60), // 1 hour ago
        
        // Custom metadata (if needed)
        public_metadata: {},
        private_metadata: {},
        unsafe_metadata: {}
    };
    
    // Create token without signature (our API has signature verification disabled)
    const headerB64 = Buffer.from(JSON.stringify(header)).toString('base64url');
    const payloadB64 = Buffer.from(JSON.stringify(payload)).toString('base64url');
    const signature = 'mock-signature-for-testing';
    
    return `${headerB64}.${payloadB64}.${signature}`;
}

/**
 * Validate the generated token format
 */
function validateTokenFormat(token) {
    const parts = token.split('.');
    if (parts.length !== 3) {
        throw new Error(`Invalid JWT format: expected 3 parts, got ${parts.length}`);
    }
    
    try {
        // Decode without verification to check structure
        const decoded = jwt.decode(token, { complete: true });
        if (!decoded) {
            throw new Error('Failed to decode JWT token');
        }
        
        const { header, payload } = decoded;
        
        // Validate required claims
        const requiredClaims = ['sub', 'iss', 'exp', 'iat'];
        for (const claim of requiredClaims) {
            if (!payload[claim]) {
                throw new Error(`Missing required claim: ${claim}`);
            }
        }
        
        return { valid: true, header, payload };
    } catch (error) {
        return { valid: false, error: error.message };
    }
}

/**
 * Display token information
 */
function displayTokenInfo(token) {
    const validation = validateTokenFormat(token);
    
    if (!validation.valid) {
        logError(`Token validation failed: ${validation.error}`);
        return false;
    }
    
    const { payload } = validation;
    
    logTitle('Generated JWT Token');
    
    logInfo('Token Details:');
    console.log(`   User ID: ${payload.sub}`);
    console.log(`   Email: ${payload.email || 'N/A'}`);
    console.log(`   Name: ${payload.name || 'N/A'}`);
    console.log(`   Issuer: ${payload.iss}`);
    console.log(`   Expires: ${new Date(payload.exp * 1000).toLocaleString()}`);
    console.log('');
    
    log('🎫 JWT Token:', colors.bright);
    log(token, colors.cyan);
    console.log('');
    
    logInfo('Usage Examples:');
    console.log('');
    console.log('  Test fiscal code validation:');
    console.log(`  ${colors.yellow}curl -X POST http://localhost:8000/fiscal-code/validate \\${colors.reset}`);
    console.log(`  ${colors.yellow}    -H "Content-Type: application/json" \\${colors.reset}`);
    console.log(`  ${colors.yellow}    -H "Authorization: Bearer ${token}" \\${colors.reset}`);
    console.log(`  ${colors.yellow}    -d '{"code": "CCCFBA85D03L219P"}'${colors.reset}`);
    console.log('');
    
    console.log('  Test VAT number validation:');
    console.log(`  ${colors.yellow}curl -X POST http://localhost:8000/vat/validate \\${colors.reset}`);
    console.log(`  ${colors.yellow}    -H "Content-Type: application/json" \\${colors.reset}`);
    console.log(`  ${colors.yellow}    -H "Authorization: Bearer ${token}" \\${colors.reset}`);
    console.log(`  ${colors.yellow}    -d '{"partita_iva": "01234567897"}'${colors.reset}`);
    console.log('');
    
    return true;
}

/**
 * Check environment configuration
 */
function checkEnvironment() {
    logTitle('Environment Check');
    
    const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || process.env.CLERK_PUBLISHABLE_KEY;
    const secretKey = process.env.CLERK_SECRET_KEY;
    
    if (!publishableKey) {
        logError('No Clerk publishable key found!');
        logInfo('Set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY or CLERK_PUBLISHABLE_KEY in your .env file');
        return null;
    }
    
    if (!secretKey) {
        logWarning('No Clerk secret key found (optional for this testing tool)');
    } else {
        logSuccess('Clerk secret key found');
    }
    
    const instanceId = extractInstanceId(publishableKey);
    if (!instanceId) {
        logError('Invalid publishable key format');
        return null;
    }
    
    logSuccess(`Clerk instance ID extracted: ${instanceId}`);
    logSuccess(`JWKS URL: https://${instanceId}.clerk.accounts.dev/.well-known/jwks.json`);
    
    return instanceId;
}

/**
 * Main function
 */
function main() {
    logTitle('Clerk JWT Token Generator');
    console.log('This tool generates JWT tokens for testing your Python FastAPI application.');
    console.log('');
    
    // Check environment
    const instanceId = checkEnvironment();
    if (!instanceId) {
        process.exit(1);
    }
    
    try {
        // Generate token
        logInfo('Generating JWT token...');
        const token = createMockJWTToken(instanceId);
        
        // Display token information
        if (displayTokenInfo(token)) {
            logSuccess('Token generated successfully!');
            
            logWarning('Important Notes:');
            console.log('  • This token is for TESTING ONLY');
            console.log('  • Signature verification is disabled in the Python API');
            console.log('  • For production, use proper Clerk authentication flow');
            console.log('  • Token expires in 24 hours');
            console.log('');
            
            // Save to file for easy access
            const fs = require('fs');
            fs.writeFileSync('.token', token);
            logInfo('Token saved to .token file for easy access');
        }
        
    } catch (error) {
        logError(`Failed to generate token: ${error.message}`);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = {
    createMockJWTToken,
    validateTokenFormat,
    extractInstanceId
};