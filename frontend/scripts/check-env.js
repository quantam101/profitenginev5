#!/usr/bin/env node
/* eslint-disable no-console */
/**
 * Deployment gate: validates required env vars and refuses to ship without them.
 * Run via `yarn env:check` or `npm run env:check`.
 */
const path = require("path");
const fs = require("fs");

const ENV_FILE = path.join(__dirname, "..", ".env");
const REQUIRED = ["REACT_APP_BACKEND_URL", "WDS_SOCKET_PORT"];
const FORBIDDEN_IN_BUNDLE = [
  "STRIPE_API_KEY", "EMERGENT_LLM_KEY", "MONGO_URL", "DB_NAME",
  "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
];

function readEnv() {
  const env = {};
  if (fs.existsSync(ENV_FILE)) {
    const raw = fs.readFileSync(ENV_FILE, "utf-8");
    raw.split("\n").forEach((line) => {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (m) env[m[1]] = m[2];
    });
  }
  return env;
}

function main() {
  const env = readEnv();
  const missing = REQUIRED.filter((k) => !env[k]);
  if (missing.length) {
    console.error("✗ missing required env vars:", missing.join(", "));
    process.exit(1);
  }
  const leaked = FORBIDDEN_IN_BUNDLE.filter((k) => env[k]);
  if (leaked.length) {
    console.error(
      "✗ server-only secrets present in frontend/.env (they would leak to the client bundle):",
      leaked.join(", "),
    );
    console.error("  → move them to backend/.env only.");
    process.exit(1);
  }
  // Backend URL sanity
  if (!/^https?:\/\//.test(env.REACT_APP_BACKEND_URL || "")) {
    console.error("✗ REACT_APP_BACKEND_URL must start with http:// or https://");
    process.exit(1);
  }
  console.log("✓ env check passed: all required vars present, no server secrets in client bundle.");
}

main();
