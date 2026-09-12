// Local/native dev fallback: `pnpm dev` and `pnpm preview` serve this file
// as-is, since there is no entrypoint to run envsubst outside a container.
// The containerized image never ships this file's values: its build copies
// this same path from `dist/`, but the entrypoint overwrites it with the
// values substituted from `config.template.js` before nginx starts (D4).
window.__PIXPICK_CONFIG__ = {
  apiBaseUrl: "/api",
  environment: "development",
};
