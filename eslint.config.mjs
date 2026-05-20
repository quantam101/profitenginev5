import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({ resolvePluginsRelativeTo: __dirname });

const config = [
  { ignores: ["runtime/**", "scripts/**", "tests/**", "deploy/**", ".next/**", "pytest-tmp-local/**", "node_modules/**"] },
  ...compat.extends("next/core-web-vitals"),
];

export default config;
