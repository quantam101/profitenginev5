// Test-only resolver: next/server is a subpath export Node cannot resolve
// without bundler resolution; map it to the real file.
export async function resolve(specifier, context, next) {
  if (specifier === 'next/server') {
    return next(new URL('../node_modules/next/server.js', import.meta.url).href, context);
  }
  return next(specifier, context);
}
