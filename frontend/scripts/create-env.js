// Script to create .env.production from Railway environment variables
// Railway passes env vars to the container, and this script makes them available to Next.js build

const fs = require('fs');
const path = require('path');

const envVars = {
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'AI SME Assistant',
  NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  NEXT_PUBLIC_ENABLE_FILE_UPLOAD: process.env.NEXT_PUBLIC_ENABLE_FILE_UPLOAD || 'true',
  NEXT_PUBLIC_ENABLE_FEEDBACK: process.env.NEXT_PUBLIC_ENABLE_FEEDBACK || 'true',
  NEXT_PUBLIC_ENABLE_DARK_MODE: process.env.NEXT_PUBLIC_ENABLE_DARK_MODE || 'true',
};

// Create .env.production file
const envContent = Object.entries(envVars)
  .map(([key, value]) => `${key}=${value}`)
  .join('\n');

const envPath = path.join(process.cwd(), '.env.production');
fs.writeFileSync(envPath, envContent);

console.log('📝 Created .env.production:');
console.log(envContent);
console.log(`\n✅ Environment file created at: ${envPath}`);
