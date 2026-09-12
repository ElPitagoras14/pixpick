import tailwindcss from "@tailwindcss/vite";
import { devtools } from "@tanstack/devtools-vite";

import { tanstackRouter } from "@tanstack/router-plugin/vite";

import viteReact from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const config = defineConfig({
	resolve: { tsconfigPaths: true },
	plugins: [
		devtools(),
		tailwindcss(),
		tanstackRouter({ target: "react", autoCodeSplitting: true }),
		viteReact(),
	],
	server: {
		proxy: {
			// Keeps the native dev flow on a single origin (D10): the frontend
			// still requests the relative `/api` space, and the dev server
			// forwards it to the backend's native default port (`fastapi dev`).
			"/api": {
				target: "http://localhost:8000",
				changeOrigin: true,
			},
			// Unlike /api, this doesn't forward to a natively-run process: the
			// transformer only ever runs in a container and publishes no port
			// (D5 in add-media-ports-and-local-adapters), so native mode still
			// reaches it through nginx, keeping its cache in the loop either way.
			// Matches NGINX_PORT's default; update if that changes.
			"/images": {
				target: "http://localhost:8080",
				changeOrigin: true,
			},
		},
	},
});

export default config;
