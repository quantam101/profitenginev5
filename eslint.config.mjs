const config = [
  {
    ignores: [
      "*.js",
      "*.mjs",
      "runtime/**",
      "scripts/**",
      "tests/**",
      "deploy/**",
      ".next/**",
      ".pytest*/**",
      "pytest-tmp-local/**",
      "node_modules/**",
      "ci/**",
      "frontend/**",
      ".claude/**",
      ".github/**"
    ]
  },
  {
    files: ["app/**/*.{ts,tsx}", "components/**/*.{ts,tsx}", "lib/**/*.mjs"],
    rules: {}
  }
];

export default config;
