import { queryOptions } from "@tanstack/react-query";
import axios from "axios";

import { api } from "@/api";

export interface CurrentUser {
	id: string;
	email: string | null;
	name: string | null;
	avatarUrl: string | null;
}

interface ApiEnvelope<T> {
	data: T | null;
	error: { code: string; message: string } | null;
}

async function fetchCurrentUser(): Promise<CurrentUser | null> {
	try {
		const response = await api.get<ApiEnvelope<CurrentUser>>("/auth/me");
		return response.data.data;
	} catch (error) {
		// Not authenticated is a normal, valid answer to "who is the
		// current user", not a failure this query should reject with.
		if (axios.isAxiosError(error) && error.response?.status === 401) {
			return null;
		}
		throw error;
	}
}

// The one place this query is defined (D9): the root loader and the
// authenticated layout's guard both consume this same query, so neither
// keeps a second copy of the session's state.
export function sessionQueryOptions() {
	return queryOptions({
		queryKey: ["auth", "session"] as const,
		queryFn: fetchCurrentUser,
	});
}
