import axios from "axios";

import { config } from "@/config";

export const api = axios.create({
	baseURL: config.apiBaseUrl,
	withCredentials: true,
});

type UnauthorizedHandler = () => void;

let handleUnauthorized: UnauthorizedHandler | null = null;

// Set once, from the router's own setup (D9): this client only reports
// that a request came back unauthorized. Whether that means "the
// session died mid-use" -- as opposed to the normal, un-alarming shape
// of an anonymous visit -- is a decision that belongs to whoever holds
// the cached session state, not to this module.
export function onUnauthorized(handler: UnauthorizedHandler): void {
	handleUnauthorized = handler;
}

api.interceptors.response.use(
	(response) => response,
	(error: unknown) => {
		if (axios.isAxiosError(error) && error.response?.status === 401) {
			handleUnauthorized?.();
		}
		return Promise.reject(error);
	},
);
