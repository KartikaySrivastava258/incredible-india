import { ApiError } from './errors';
import { session } from '../session';

/**
 * ApiClient — the single, fetch-based implementation of the backend
 * contract documented in BRAIN.md Section G. This is the "interface":
 * every method here has a fixed name and signature. MockApiClient
 * (./MockApiClient.js) implements the exact same methods so the rest of
 * the app can depend on the shape below without caring which one is
 * actually wired up (see ./index.js).
 *
 * Rules this class follows (BRAIN.md Section I / SALONI_BATRA_TASK.md):
 *  - Never hardcodes localhost:PORT — baseUrl is passed in from config,
 *    which itself reads only VITE_API_BASE_URL.
 *  - Never calls the AI or matching services directly — everything goes
 *    through the backend's API_BASE_URL.
 *  - Never renames a field client-side — request/response bodies are
 *    passed through with the exact snake_case keys BRAIN.md Section F/G
 *    defines, so a contract mismatch during integration surfaces instead
 *    of being silently masked.
 *  - Every method throws an ApiError (never a bare fetch/TypeError) so
 *    callers can branch on .status / .code without inspecting raw JSON.
 */
export class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async _request(method, path, body, extraHeaders) {
    let response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers: { 'Content-Type': 'application/json', ...extraHeaders },
        body: body !== undefined ? JSON.stringify(body) : undefined
      });
    } catch (networkErr) {
      // fetch() only throws for network-level failures (DNS, connection
      // refused, CORS, offline) — never for HTTP error status codes.
      throw new ApiError({ isNetworkError: true, message: networkErr.message });
    }

    let parsed = null;
    const text = await response.text();
    if (text) {
      try {
        parsed = JSON.parse(text);
      } catch {
        // Non-JSON body (e.g. a raw 502 from an upstream proxy). Leave
        // parsed as null; we still branch on response.status below.
        parsed = null;
      }
    }

    if (!response.ok) {
      const errBody = parsed && parsed.error ? parsed.error : null;
      throw new ApiError({
        status: response.status,
        code: errBody?.code,
        message: errBody?.message,
        details: errBody?.details
      });
    }

    return parsed;
  }

  _get(path, extraHeaders) {
    return this._request('GET', path, undefined, extraHeaders);
  }

  _post(path, body) {
    return this._request('POST', path, body);
  }

  // ---- Sellers / touchpoints / products -----------------------------

  /** POST /sellers → Seller */
  createSeller(seller) {
    return this._post('/sellers', seller);
  }

  /** POST /touchpoints → CommunityTouchpoint */
  createTouchpoint(touchpoint) {
    return this._post('/touchpoints', touchpoint);
  }

  /** POST /products → Product */
  createProduct(product) {
    return this._post('/products', product);
  }

  // ---- Onboarding conversation ----------------------------------------

  /**
   * POST /onboarding/message
   * request:  { seller_id, conversation_id, message_text }
   * response: { conversation_id, ai_reply_text, stage, draft_state }
   */
  sendOnboardingMessage({ seller_id, conversation_id, message_text }) {
    return this._post('/onboarding/message', { seller_id, conversation_id, message_text });
  }

  /**
   * POST /listings/generate
   * request:  { seller_id, conversation_id }
   * response: Listing (review_status = "pending")
   */
  generateListing({ seller_id, conversation_id }) {
    return this._post('/listings/generate', { seller_id, conversation_id });
  }

  /** GET /listings/:id → Listing */
  getListing(listingId) {
    return this._get(`/listings/${listingId}`);
  }

  // ---- Contributions ---------------------------------------------------

  /**
   * POST /contributions
   * request: { seller_id, opted_in, percentage, touchpoint_id, principal_seller_id }
   * response: Contribution
   * principal_seller_id is required by Cedar for authorization — sourced from the active session.
   */
  setContribution({ seller_id, opted_in, percentage, touchpoint_id }) {
    const principal_seller_id = session.get().seller?.seller_id ?? seller_id;
    return this._post('/contributions', { seller_id, opted_in, percentage, touchpoint_id, principal_seller_id });
  }

  // ---- Buyer search ------------------------------------------------------

  /**
   * POST /search/match
   * request:  { query_text, buyer_id }
   * response: { matches: [{ listing_id, score, listing_title, noble_cause_note }] }
   */
  searchMatch({ query_text, buyer_id = null }) {
    return this._post('/search/match', { query_text, buyer_id });
  }

  // ---- Sales / ledger / impact --------------------------------------------

  /**
   * POST /sales
   * request:  { listing_id, buyer_id, sale_amount, principal_seller_id }
   * response: LedgerEntry
   * principal_seller_id is required by Cedar — sourced from the active session.
   */
  simulateSale({ listing_id, buyer_id = null, sale_amount }) {
    const principal_seller_id = session.get().seller?.seller_id ?? null;
    return this._post('/sales', { listing_id, buyer_id, sale_amount, principal_seller_id });
  }

  /**
   * GET /ledger/:seller_id → { entries: LedgerEntry[] }
   * Requires X-Principal-Type and X-Principal-Seller-Id headers for Cedar authorization.
   */
  getLedger(sellerId) {
    return this._get(`/ledger/${sellerId}`, {
      'X-Principal-Type': 'Seller',
      'X-Principal-Seller-Id': sellerId,
    });
  }

  /** GET /ledger/:seller_id as a touchpoint administrator. */
  getLedgerAsAdmin(sellerId, touchpointId) {
    return this._get(`/ledger/${sellerId}`, {
      'X-Principal-Type': 'TouchpointAdmin',
      'X-Principal-Touchpoint-Id': touchpointId,
    });
  }

  /**
   * GET /impact → impact dashboard aggregate.
   * options.principalTouchpointId (optional, STRETCH admin view only):
   * sent as an X-Principal-Touchpoint-Id header for compatibility with the
   * admin UI. The current /impact handler does not enforce Cedar scoping.
   */
  getImpact(options = {}) {
    const headers = options.principalTouchpointId
      ? { 'X-Principal-Touchpoint-Id': options.principalTouchpointId }
      : undefined;
    return this._get('/impact', headers);
  }
}

