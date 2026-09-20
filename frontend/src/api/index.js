import { ApiClient } from './ApiClient';
import { MockApiClient } from './MockApiClient';
import { API_BASE_URL, USE_MOCK_API } from '../config';

// The single place that decides which ApiClient implementation the rest
// of the app talks to. Everything else imports `api` from here and never
// imports ApiClient/MockApiClient directly, so switching from mock to
// real backend (or back) during development is a one-line/one-env-var
// change, never a rewrite of call sites.
export const api = USE_MOCK_API ? new MockApiClient() : new ApiClient(API_BASE_URL);

export { ApiError } from './errors';

