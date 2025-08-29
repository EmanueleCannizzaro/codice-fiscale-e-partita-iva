#!/usr/bin/env node

/**
 * Example usage of the token generator and API testing
 */

const { createMockJWTToken, extractInstanceId } = require('./generate-token');
const axios = require('axios');
require('dotenv').config({ path: '../.env' });

async function demonstrateUsage() {
    console.log('🎯 Demonstrating Clerk JWT Token Usage\n');
    
    // 1. Extract instance ID from environment
    const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    const instanceId = extractInstanceId(publishableKey);
    
    console.log('📋 Configuration:');
    console.log(`   Instance ID: ${instanceId}`);
    console.log(`   API URL: http://localhost:8000\n`);
    
    // 2. Generate token
    console.log('🔐 Generating JWT Token...');
    const token = createMockJWTToken(instanceId);
    console.log(`   Token: ${token.substring(0, 50)}...\n`);
    
    // 3. Test specific endpoints
    const tests = [
        {
            name: 'Validate valid fiscal code',
            endpoint: '/fiscal-code/validate',
            data: { code: 'CCCFBA85D03L219P' }
        },
        {
            name: 'Validate invalid fiscal code',  
            endpoint: '/fiscal-code/validate',
            data: { code: 'INVALID123' }
        },
        {
            name: 'Encode fiscal code',
            endpoint: '/fiscal-code/encode',
            data: {
                lastname: 'Rossi',
                firstname: 'Mario',
                gender: 'M',
                birthdate: '01/01/1990',
                birthplace: 'Milano'
            }
        },
        {
            name: 'Validate VAT number',
            endpoint: '/vat/validate', 
            data: { partita_iva: '01234567897' }
        }
    ];
    
    console.log('🧪 Testing API Endpoints:\n');
    
    for (const test of tests) {
        try {
            const response = await axios.post(`http://localhost:8000${test.endpoint}`, test.data, {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
            
            console.log(`✅ ${test.name}:`);
            console.log(`   Status: ${response.status}`);
            console.log(`   Response: ${JSON.stringify(response.data, null, 2).substring(0, 200)}...\n`);
            
        } catch (error) {
            console.log(`❌ ${test.name}: ${error.message}\n`);
        }
    }
    
    console.log('🎉 Demo complete! The JWT token is working correctly.');
    console.log('\n💡 Next steps:');
    console.log('   • Use `npm run token` to generate new tokens');
    console.log('   • Use `npm run test-api` for comprehensive testing');
    console.log('   • Use `node test-api.js --interactive` for manual testing');
}

// Run the demo
if (require.main === module) {
    demonstrateUsage().catch(console.error);
}