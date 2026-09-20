/**
 * ApiError normalizes every failure mode the app needs to branch on:
 *  - a well-formed backend error body: { error: { code, message } }
 *  - an HTTP status with no parseable body
 *  - a network-level failure (backend unreachable at all)
 *
 * BRAIN.md Section G: every error follows { "error": { "code", "message" } }.
 * Every endpoint can return 400 (invalid/missing fields), 403 (Cedar
 * denied), 404 (unknown id), or 502 (AI/matching/LLM/OpenSearch upstream
 * unavailable). The UI must never show a blank screen or raw error JSON
 * for any of these — see SALONI_BATRA_TASK.md Section 5.1 / 5.2 / 12.
 */
export class ApiError extends Error {
  constructor({ status, code, message, details = null, isNetworkError = false }) {
    super(message || 'Request failed');
    this.name = 'ApiError';
    this.status = status ?? null;
    this.code = code || (isNetworkError ? 'NETWORK_ERROR' : 'UNKNOWN_ERROR');
    this.isNetworkError = isNetworkError;
    this.details = details || null;
  }

  get isUpstreamUnavailable() {
    return this.status === 502;
  }

  get isForbidden() {
    return this.status === 403;
  }

  get isNotFound() {
    return this.status === 404;
  }

  get isBadRequest() {
    return this.status === 400;
  }

  /** A short, user-facing message. Never a raw stack trace or JSON dump. */
  friendlyMessage() {
    if (this.isNetworkError) {
      return "We couldn't reach the Kalaa Setu server. Check your connection and try again.";
    }
    switch (this.status) {
      case 502:
        return 'AI is temporarily unavailable, please retry.';
      case 403:
        return this.message?.startsWith('Cedar denied:')
          ? this.message
          : "You don't have permission to do that.";
      case 404:
        return "We couldn't find what you were looking for.";
      case 400:
        return this.message || 'Something about that request was invalid.';
      default:
        return this.message || 'Something went wrong. Please try again.';
    }
  }
}

