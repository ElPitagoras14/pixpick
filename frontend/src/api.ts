import axios from "axios";

import { config } from "@/config";

export const api = axios.create({
	baseURL: config.apiBaseUrl,
	withCredentials: true,
});

// The one shape every response body has (api-conventions spec): `data` on
// success, `error` on failure. `details` only ever appears on a state
// conflict (api-conventions spec, added by add-albums-and-upload) --
// the album-full case is the one place this project's own client reads it.
export interface ApiError {
	code: string;
	message: string;
	field?: string | null;
	requestId?: string | null;
	details?: Record<string, unknown> | null;
}

export interface ApiEnvelope<T> {
	data: T | null;
	error: ApiError | null;
}

// What every mutation in `features/albums` and `features/photos` throws
// on a non-2xx response, unwrapped from axios's own error shape so a
// component only ever reads `.error`, never `.response.data.error`.
export class ApiRequestError extends Error {
	constructor(
		public readonly error: ApiError,
		public readonly status: number,
	) {
		super(error.message);
	}
}

export function unwrapApiError(error: unknown): never {
	if (
		axios.isAxiosError<ApiEnvelope<unknown>>(error) &&
		error.response?.data?.error
	) {
		throw new ApiRequestError(error.response.data.error, error.response.status);
	}
	throw error;
}

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
