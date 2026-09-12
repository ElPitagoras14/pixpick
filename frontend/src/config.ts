interface AppConfig {
	apiBaseUrl: string;
	environment: "development" | "production";
}

declare global {
	interface Window {
		__PIXPICK_CONFIG__: AppConfig;
	}
}

// Read from the global object populated by `config.js`, loaded synchronously
// in index.html before this module ever runs (D4). No fallback branch: a
// missing value is a broken deployment, not a state this code tolerates.
export const config: AppConfig = window.__PIXPICK_CONFIG__;
