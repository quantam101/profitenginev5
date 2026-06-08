module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.js'],
  collectCoverageFrom: [
    'agents/**/*.js','publishers/**/*.js',
    'core/**/*.js','pipeline/**/*.js','ultraflow/**/*.js',
    '!**/node_modules/**',
  ],
  coverageThreshold: { global: { branches:60, functions:70, lines:70, statements:70 } },
  testTimeout: 15000,
};
