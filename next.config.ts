import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  outputFileTracingIncludes: {
    '/api/distillation/status': ['config/distillation.yaml'],
    '/api/agents/parallel': ['agents/registry.yaml'],
    '/api/health': [
      'eaos.config.yaml',
      'agents/registry.yaml',
      'connectors/registry.yaml',
      'observability/slo.yaml',
      'docker-compose.yml',
      'Dockerfile.web',
      '.github/workflows/ci.yml',
      'package.json',
      'package-lock.json',
      '.env.example',
      'vercel.json',
      'app/**/*',
      'runtime/**/*.py',
      'scripts/**/*.py',
      'scripts/**/*.sh',
      'lib/**/*',
    ],
  },
};

export default nextConfig;
