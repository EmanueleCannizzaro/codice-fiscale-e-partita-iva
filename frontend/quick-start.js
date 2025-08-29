#!/usr/bin/env node

/**
 * Quick Start Script for New Users
 * 
 * This script helps new users get started with JWT token generation
 * by guiding them through the setup process.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// ANSI color codes
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
};

function log(message, color = colors.reset) {
    console.log(`${color}${message}${colors.reset}`);
}

function logTitle(message) {
    log(`\n${colors.bright}${colors.cyan}🚀 ${message}${colors.reset}`);
    log('='.repeat(50));
}

function logSuccess(message) {
    log(`✅ ${message}`, colors.green);
}

function logError(message) {
    log(`❌ ${message}`, colors.red);
}

function logWarning(message) {
    log(`⚠️  ${message}`, colors.yellow);
}

function logInfo(message) {
    log(`ℹ️  ${message}`, colors.blue);
}

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(prompt) {
    return new Promise(resolve => rl.question(prompt, resolve));
}

async function checkEnvironment() {
    logTitle('Environment Check');
    
    const envPath = path.join(__dirname, '..', '.env');
    const envExamplePath = path.join(__dirname, '..', '.env.example');
    
    // Check if .env exists
    if (!fs.existsSync(envPath)) {
        logWarning('.env file not found');
        
        if (fs.existsSync(envExamplePath)) {
            logInfo('Found .env.example, would you like to copy it?');
            const answer = await question('Copy .env.example to .env? (y/n): ');
            
            if (answer.toLowerCase() === 'y') {
                fs.copyFileSync(envExamplePath, envPath);
                logSuccess('Created .env file from example');
            }
        } else {
            logInfo('Creating basic .env file...');
            const basicEnv = `# Clerk Configuration
# Get these keys from https://clerk.com dashboard
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=

# Optional: Uncomment to use demo credentials
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_YW1hemVkLWNvd2JpcmQtMjkuY2xlcmsuYWNjb3VudHMuZGV2JA
# CLERK_SECRET_KEY=sk_test_kUCqZqmoyztygDHbdpyax1QEXTJZ5MECpdSLncXG7I
`;
            fs.writeFileSync(envPath, basicEnv);
            logSuccess('Created basic .env file');
        }
    } else {
        logSuccess('.env file found');
    }
    
    return envPath;
}

async function setupClerkCredentials(envPath) {
    logTitle('Clerk Setup Options');
    
    console.log('Choose your setup option:');
    console.log('1. 🔑 Use your own Clerk account (recommended for real development)');
    console.log('2. 🧪 Use demo credentials (quick testing)');
    console.log('3. 🚫 Disable authentication (simplest - all endpoints public)');
    console.log('4. ⚙️  I already have credentials configured');
    
    const choice = await question('\nEnter your choice (1-4): ');
    
    switch (choice) {
        case '1':
            await setupOwnClerkAccount(envPath);
            break;
        case '2':
            await setupDemoCredentials(envPath);
            break;
        case '3':
            await disableAuthentication(envPath);
            break;
        case '4':
            logInfo('Using existing credentials');
            break;
        default:
            logError('Invalid choice, using existing configuration');
    }
}

async function setupOwnClerkAccount(envPath) {
    logTitle('Setting Up Your Clerk Account');
    
    console.log('Follow these steps:');
    console.log('1. Go to https://clerk.com and create an account');
    console.log('2. Create a new application');
    console.log('3. Copy your publishable key (starts with pk_test_)');
    console.log('4. Copy your secret key (starts with sk_test_)');
    console.log('');
    
    const publishableKey = await question('Enter your publishable key: ');
    const secretKey = await question('Enter your secret key (optional): ');
    
    if (publishableKey) {
        let envContent = fs.readFileSync(envPath, 'utf8');
        
        // Update or add the keys
        envContent = envContent.replace(/^NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=.*$/m, 
            `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=${publishableKey}`);
        
        if (secretKey) {
            envContent = envContent.replace(/^CLERK_SECRET_KEY=.*$/m, 
                `CLERK_SECRET_KEY=${secretKey}`);
        }
        
        fs.writeFileSync(envPath, envContent);
        logSuccess('Saved your Clerk credentials');
    }
}

async function setupDemoCredentials(envPath) {
    logTitle('Setting Up Demo Credentials');
    
    const demoConfig = `# Demo Clerk Configuration (for testing only)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_YW1hemVkLWNvd2JpcmQtMjkuY2xlcmsuYWNjb3VudHMuZGV2JA
CLERK_SECRET_KEY=sk_test_kUCqZqmoyztygDHbdpyax1QEXTJZ5MECpdSLncXG7I
CLERK_JWKS_URL=https://amazed-cowbird-29.clerk.accounts.dev/.well-known/jwks.json
`;
    
    fs.writeFileSync(envPath, demoConfig);
    logSuccess('Configured demo credentials');
    logWarning('These are demo credentials - only use for testing!');
}

async function disableAuthentication(envPath) {
    logTitle('Disabling Authentication');
    
    const noAuthConfig = `# Authentication disabled - all endpoints are public
# NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
# CLERK_SECRET_KEY=
`;
    
    fs.writeFileSync(envPath, noAuthConfig);
    logSuccess('Authentication disabled - all API endpoints are now public');
}

async function testSetup() {
    logTitle('Testing Your Setup');
    
    try {
        // Try to load environment
        require('dotenv').config({ path: '../.env' });
        
        const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
        
        if (!publishableKey || publishableKey.trim() === '') {
            logInfo('No authentication configured - API will be public');
            console.log('✅ You can test the API without authentication headers');
            return true;
        }
        
        // Try to generate a token
        const { createMockJWTToken, extractInstanceId } = require('./generate-token');
        const instanceId = extractInstanceId(publishableKey);
        
        if (!instanceId) {
            logError('Invalid publishable key format');
            return false;
        }
        
        const token = createMockJWTToken(instanceId);
        
        // Save token
        fs.writeFileSync('.token', token);
        
        logSuccess('JWT token generated successfully!');
        logInfo('Token saved to .token file');
        
        return true;
        
    } catch (error) {
        logError(`Setup test failed: ${error.message}`);
        return false;
    }
}

async function showNextSteps() {
    logTitle('Next Steps');
    
    console.log('Your setup is complete! Here\'s what to do next:\n');
    
    console.log('1. 🚀 Start the Python API server:');
    console.log('   cd .. && uv run python -m codicefiscale.__main_api__\n');
    
    console.log('2. 🔐 Generate a JWT token (if using auth):');
    console.log('   npm run token\n');
    
    console.log('3. 🧪 Test the API:');
    console.log('   npm run test-api\n');
    
    console.log('4. 📖 Interactive testing:');
    console.log('   node test-api.js --interactive\n');
    
    console.log('5. 💻 Manual testing example:');
    console.log('   curl -X POST http://localhost:8000/fiscal-code/validate \\');
    console.log('     -H "Content-Type: application/json" \\');
    console.log('     -H "Authorization: Bearer $(cat .token)" \\');
    console.log('     -d \'{"code": "CCCFBA85D03L219P"}\'\n');
    
    console.log('📚 Documentation:');
    console.log('   • API docs: http://localhost:8000/docs');
    console.log('   • Setup guide: ../NEW_USER_SETUP.md');
    console.log('   • Frontend README: ./README.md');
}

async function main() {
    logTitle('Python Codicefiscale - Quick Start Setup');
    
    console.log('This script will help you set up JWT token generation for testing the API.\n');
    
    try {
        // Check and setup environment
        const envPath = await checkEnvironment();
        
        // Setup Clerk credentials
        await setupClerkCredentials(envPath);
        
        // Test the setup
        const setupSuccessful = await testSetup();
        
        if (setupSuccessful) {
            // Show next steps
            await showNextSteps();
        }
        
        logSuccess('Setup complete!');
        
    } catch (error) {
        logError(`Setup failed: ${error.message}`);
        console.log('\n💡 For help, see the NEW_USER_SETUP.md guide or check the README.md');
    } finally {
        rl.close();
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}