const fs = require('fs');
const path = require('path');

// Read .env file
const envPath = path.join(__dirname, '.env');
const envContent = fs.readFileSync(envPath, 'utf-8');
const lines = envContent.split('\n').filter(line => line && !line.startsWith('#'));

const secrets = {};
lines.forEach(line => {
  const [key, ...valueParts] = line.split('=');
  if (key && valueParts.length) {
    secrets[key.trim()] = valueParts.join('=').trim();
  }
});

console.log(`Found ${Object.keys(secrets).length} secrets in .env`);
console.log('Secrets ready for Vercel:');
Object.keys(secrets).forEach(key => {
  const val = secrets[key];
  const display = val.substring(0, 20) + (val.length > 20 ? '...' : '');
  console.log(`  ${key}: ${display}`);
});

// Instructions for user
console.log('\n✅ Ready to push to Vercel Production');
