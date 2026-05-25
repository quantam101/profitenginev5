import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Bundle config/registry YAML files into the /api/health serverless function
  // so buildHealthPayload() can read them from process.cwd() at runtime.
  experimental: {
    outputFileTracingIncludes: {
      '/api/health': [
        'eaos.config.yaml',
        'agents/registry.yaml',
        'connectors/registry.yaml',
        'observability/slo.yaml',
        'docker-compose.yml',
        'Dockerfile.web',
        '.github/workflows/ci.yml',
        'package.json',
        '.env.example',
        'vercel.json',
        'app/**/*',
        'runtime/**/*.py',
        'scripts/**/*.py',
        'scripts/**/*.sh',
        'lib/**/*',
      ],
    },
  },
};

export default nextConfig;
