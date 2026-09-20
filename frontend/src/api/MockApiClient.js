import { ApiError } from './errors';
import {
  touchpoints as seedTouchpoints,
  sellers as seedSellers,
  products as seedProducts,
  listings as seedListings,
  contributions as seedContributions,
  ledgerEntries as seedLedgerEntries,
  onboardingScript
} from '../data/seedData';

const uuid = () =>
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });

const nowIso = () => new Date().toISOString();

/** Category is guessed from the seller's own free-text words, the same
 * kind of lightweight heuristic the real AI service does with a proper
 * LLM — this is a stand-in so the mock "feels" consistent, not a claim
 * that this is how ai/ actually classifies things. */
function guessCategory(text = '') {
  const t = text.toLowerCase();
  if (/(shawl|oon|wool|kambal|scarf|saree|dupatta|kapda|cloth|textile|bunai|weav)/.test(t)) return 'textile';
  if (/(khilaune|toy|gudiya|doll|khilona)/.test(t)) return 'toy';
  if (/(achaar|pickle|namkeen|mithai|sweet|food|masala|honey|shahad)/.test(t)) return 'food';
  return 'handicraft';
}

/**
 * MockApiClient — implements exactly the same methods as ApiClient
 * (./ApiClient.js), returning responses shaped exactly like BRAIN.md
 * Section G's documented bodies, backed by the canned data in
 * ../data/seedData.js. Swappable with the real client via a config flag
 * (see ./index.js) — nothing in the rest of the app knows or cares which
 * one it's talking to.
 *
 * Dev-only error injection: any onboarding message_text, contribution
 * percentage call, or sale amount containing the literal substrings
 * "simulate502" / "simulate403" / "simulate404" makes the corresponding
 * mock call throw that ApiError, so the error-handling UI (and its tests)
 * can be exercised without a real backend.
 */
export class MockApiClient {
  constructor() {
    this.touchpoints = [...seedTouchpoints];
    this.sellers = [...seedSellers];
    this.products = [...seedProducts];
    this.listings = [...seedListings];
    this.contributions = [...seedContributions];
    this.ledgerEntries = [...seedLedgerEntries];
    this.conversations = new Map(); // conversation_id -> { stage, draft_state, seller_id }
    this._latency = 250;
  }

  async _delay() {
    await new Promise((resolve) => setTimeout(resolve, this._latency));
  }

  _maybeInjectedError(text) {
    if (typeof text !== 'string') return;
    if (text.includes('simulate502')) {
      throw new ApiError({ status: 502, code: 'UPSTREAM_UNAVAILABLE', message: 'AI service is unavailable.' });
    }
    if (text.includes('simulate403')) {
      throw new ApiError({ status: 403, code: 'CEDAR_DENIED', message: 'Policy denied this action.' });
    }
    if (text.includes('simulate404')) {
      throw new ApiError({ status: 404, code: 'NOT_FOUND', message: 'Resource not found.' });
    }
  }

  // ---- Sellers / touchpoints / products -----------------------------

  async createSeller(seller) {
    await this._delay();
    this._maybeInjectedError(seller?.name);
    if (!seller?.name || !seller?.village || !seller?.state || !seller?.seller_language || !seller?.touchpoint_id) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'Missing required seller fields.' });
    }
    const record = { seller_id: uuid(), phone: null, ...seller, created_at: nowIso() };
    this.sellers.push(record);
    return record;
  }

  async createTouchpoint(touchpoint) {
    await this._delay();
    const record = { touchpoint_id: uuid(), admin_user_id: null, ...touchpoint };
    this.touchpoints.push(record);
    return record;
  }

  async createProduct(product) {
    await this._delay();
    if (!product?.seller_id || !product?.category || !product?.raw_description || !product?.seller_language) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'Missing required product fields.' });
    }
    const record = { product_id: uuid(), created_at: nowIso(), ...product };
    this.products.push(record);
    return record;
  }

  // ---- Onboarding conversation ----------------------------------------

  async sendOnboardingMessage({ seller_id, conversation_id, message_text }) {
    await this._delay();
    this._maybeInjectedError(message_text);

    if (!seller_id || !message_text) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'seller_id and message_text are required.' });
    }

    let conversation_id_out = conversation_id;
    let convo = conversation_id ? this.conversations.get(conversation_id) : null;

    if (!convo) {
      conversation_id_out = uuid();
      convo = { stage: 'idea', draft_state: { messages: [] }, seller_id };
      this.conversations.set(conversation_id_out, convo);
    }

    convo.draft_state.messages.push({ from: 'seller', text: message_text });

    const currentScript = onboardingScript[convo.stage];
    if (!currentScript) {
      // Already done — no further turns expected, but respond gracefully.
      return {
        conversation_id: conversation_id_out,
        ai_reply_text: 'This onboarding conversation is already complete. Generate the listing when ready.',
        stage: 'done',
        draft_state: convo.draft_state
      };
    }

    if (convo.stage === 'idea') {
      convo.draft_state.category = guessCategory(message_text);
      convo.draft_state.idea_text = message_text;
    } else if (convo.stage === 'procedure') {
      convo.draft_state.procedure_ack = true;
    } else if (convo.stage === 'business_model') {
      convo.draft_state.business_model_ack = true;
    } else if (convo.stage === 'capture') {
      convo.draft_state.capture_text = message_text;
    }

    convo.stage = currentScript.nextStage;
    convo.draft_state.messages.push({ from: 'ai', text: currentScript.reply });

    return {
      conversation_id: conversation_id_out,
      ai_reply_text: currentScript.reply,
      stage: convo.stage,
      draft_state: convo.draft_state
    };
  }

  async generateListing({ seller_id, conversation_id }) {
    await this._delay();
    if (!seller_id || !conversation_id) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'seller_id and conversation_id are required.' });
    }
    const convo = this.conversations.get(conversation_id);
    if (!convo) {
      throw new ApiError({ status: 404, code: 'CONVERSATION_NOT_FOUND', message: 'Unknown conversation_id.' });
    }

    const category = convo.draft_state.category || 'handicraft';
    const seller = this.sellers.find((s) => s.seller_id === seller_id);
    const rawText = convo.draft_state.capture_text || convo.draft_state.idea_text || '';

    const product = {
      product_id: uuid(),
      seller_id,
      category,
      raw_description: rawText,
      seller_language: seller?.seller_language || 'hi',
      created_at: nowIso()
    };
    this.products.push(product);

    const listing = {
      listing_id: uuid(),
      product_id: product.product_id,
      category,
      listing_title: `${category[0].toUpperCase()}${category.slice(1)} from ${seller?.village || 'a rural village'}`,
      description_en: `A hand-made ${category} product, described by the seller as: "${rawText.slice(0, 160)}". Produced in ${seller?.village || 'a rural village'}, ${seller?.state || 'India'}.`,
      description_local: rawText,
      price_suggestion: category === 'textile' ? 2500 : category === 'toy' ? 700 : category === 'food' ? 350 : 900,
      photo_guidance: [
        'Shoot in daylight, near a window',
        'Show the full product against a plain background',
        'Include a size reference like a coin or ruler'
      ],
      story: null,
      compliance_flags: [],
      review_status: 'pending',
      created_at: nowIso()
    };
    this.listings.push(listing);
    convo.stage = 'done';
    convo.draft_state.listing_id = listing.listing_id;
    return listing;
  }

  async getListing(listingId) {
    await this._delay();
    const listing = this.listings.find((l) => l.listing_id === listingId);
    if (!listing) {
      throw new ApiError({ status: 404, code: 'LISTING_NOT_FOUND', message: 'No listing with that id.' });
    }
    return listing;
  }

  // ---- Contributions ---------------------------------------------------

  async setContribution({ seller_id, opted_in, percentage, touchpoint_id }) {
    await this._delay();
    if (typeof percentage === 'string') this._maybeInjectedError(percentage);
    if (!seller_id || typeof opted_in !== 'boolean' || !touchpoint_id) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'seller_id, opted_in and touchpoint_id are required.' });
    }
    const pct = opted_in ? Number(percentage) || 0 : 0;
    if (opted_in && (pct < 0 || pct > 100)) {
      throw new ApiError({ status: 400, code: 'INVALID_PERCENTAGE', message: 'percentage must be between 0 and 100.' });
    }

    const existingIdx = this.contributions.findIndex((c) => c.seller_id === seller_id);
    const record = {
      contribution_id: existingIdx >= 0 ? this.contributions[existingIdx].contribution_id : uuid(),
      seller_id,
      opted_in,
      percentage: pct,
      touchpoint_id,
      updated_at: nowIso()
    };
    if (existingIdx >= 0) {
      this.contributions[existingIdx] = record;
    } else {
      this.contributions.push(record);
    }

    // Mirror the seller's disclosure choice onto the buyer-visible `story`
    // field the way the real AI/backend would once review approves it.
    const listing = [...this.listings].reverse().find((l) => {
      const product = this.products.find((p) => p.product_id === l.product_id);
      return product?.seller_id === seller_id;
    });
    if (listing && !opted_in) {
      listing.story = null;
    }

    return record;
  }

  // ---- Buyer search ------------------------------------------------------

  async searchMatch({ query_text, buyer_id = null }) {
    await this._delay();
    this._maybeInjectedError(query_text);
    if (!query_text || !query_text.trim()) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'query_text is required.' });
    }
    const q = query_text.toLowerCase();
    const approved = this.listings.filter((l) => l.review_status === 'approved');

    const scored = approved
      .map((l) => {
        const haystack = `${l.listing_title} ${l.description_en} ${l.category}`.toLowerCase();
        const terms = q.split(/\s+/).filter(Boolean);
        const hits = terms.filter((term) => haystack.includes(term)).length;
        const score = terms.length ? hits / terms.length : 0;
        return { l, score };
      })
      .filter(({ score }) => score > 0)
      .sort((a, b) => b.score - a.score);

    const matches = scored.map(({ l, score }) => {
      const contribution = this.contributions.find((c) => {
        const product = this.products.find((p) => p.product_id === l.product_id);
        return product && c.seller_id === product.seller_id;
      });
      return {
        listing_id: l.listing_id,
        score: Number(score.toFixed(2)),
        listing_title: l.listing_title,
        noble_cause_note: contribution?.opted_in ? l.story || null : null
      };
    });

    return { matches };
  }

  // ---- Sales / ledger / impact --------------------------------------------

  async simulateSale({ listing_id, buyer_id = null, sale_amount }) {
    await this._delay();
    if (typeof sale_amount === 'string') this._maybeInjectedError(sale_amount);
    if (!listing_id || typeof sale_amount !== 'number' || sale_amount <= 0) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'listing_id and a positive sale_amount are required.' });
    }
    const listing = this.listings.find((l) => l.listing_id === listing_id);
    if (!listing) {
      throw new ApiError({ status: 404, code: 'LISTING_NOT_FOUND', message: 'No listing with that id.' });
    }
    const product = this.products.find((p) => p.product_id === listing.product_id);
    const seller_id = product?.seller_id;
    const contribution = this.contributions.find((c) => c.seller_id === seller_id);

    const platform_fee = Math.round(sale_amount * 0.08 * 100) / 100;
    const netBeforeContribution = sale_amount - platform_fee;
    // Cedar-enforced invariant (BRAIN.md Section F, LedgerEntry note):
    // contribution_amount MUST be 0 if Contribution.opted_in is false.
    const contribution_amount =
      contribution?.opted_in
        ? Math.round(netBeforeContribution * (contribution.percentage / 100) * 100) / 100
        : 0;
    const seller_net = Math.round((netBeforeContribution - contribution_amount) * 100) / 100;

    const entry = {
      ledger_entry_id: uuid(),
      sale_id: uuid(),
      seller_id,
      listing_id,
      sale_amount,
      platform_fee,
      seller_net,
      contribution_amount,
      touchpoint_id: contribution?.touchpoint_id || product?.seller_id,
      buyer_visible: Boolean(contribution?.opted_in),
      created_at: nowIso()
    };
    this.ledgerEntries.push(entry);
    return entry;
  }

  async getLedger(sellerId) {
    await this._delay();
    if (!sellerId) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'seller_id is required.' });
    }
    return this.ledgerEntries.filter((e) => e.seller_id === sellerId);
  }

  async getLedgerAsAdmin(sellerId, touchpointId) {
    await this._delay();
    if (!sellerId || !touchpointId) {
      throw new ApiError({ status: 400, code: 'INVALID_FIELDS', message: 'seller_id and touchpoint_id are required.' });
    }
    const seller = this.sellers.find((s) => s.seller_id === sellerId);
    if (!seller) throw new ApiError({ status: 404, code: 'NOT_FOUND', message: 'Seller not found.' });
    if (seller.touchpoint_id !== touchpointId) {
      throw new ApiError({
        status: 403,
        code: 'FORBIDDEN',
        message: 'Cedar denied: you cannot view this seller\'s ledger',
        details: {
          policy: 'touchpoint_admin_scope.cedar',
          action: 'viewLedgerData',
          principal_touchpoint_id: touchpointId,
          resource_touchpoint_id: seller.touchpoint_id
        }
      });
    }
    return this.ledgerEntries.filter((e) => e.seller_id === sellerId);
  }

  async getImpact(options = {}) {
    await this._delay();
    const { principalTouchpointId } = options;

    const scopedSellerIds = principalTouchpointId
      ? new Set(this.sellers.filter((s) => s.touchpoint_id === principalTouchpointId).map((s) => s.seller_id))
      : null;
    const scopedTouchpoints = principalTouchpointId
      ? this.touchpoints.filter((t) => t.touchpoint_id === principalTouchpointId)
      : this.touchpoints;
    const scopedLedger = principalTouchpointId
      ? this.ledgerEntries.filter((e) => scopedSellerIds.has(e.seller_id))
      : this.ledgerEntries;
    const scopedContributions = principalTouchpointId
      ? this.contributions.filter((c) => c.touchpoint_id === principalTouchpointId)
      : this.contributions;
    const scopedListings = principalTouchpointId
      ? this.listings.filter((l) => {
          const product = this.products.find((p) => p.product_id === l.product_id);
          return product && scopedSellerIds.has(product.seller_id);
        })
      : this.listings;

    const villages = new Set(scopedTouchpoints.map((t) => t.village));
    const sellersEarning = new Set(scopedLedger.map((e) => e.seller_id));
    const optedInCount = scopedContributions.filter((c) => c.opted_in).length;
    const opt_in_rate = scopedContributions.length ? optedInCount / scopedContributions.length : 0;
    const total_community_funds = scopedLedger.reduce((sum, e) => sum + (e.contribution_amount || 0), 0);

    return {
      villages_onboarded: villages.size,
      sellers_earning: sellersEarning.size,
      opt_in_rate: Number(opt_in_rate.toFixed(2)),
      total_community_funds: Number(total_community_funds.toFixed(2)),
      total_sellers: principalTouchpointId
        ? this.sellers.filter((s) => s.touchpoint_id === principalTouchpointId).length
        : this.sellers.length,
      total_listings_live: scopedListings.filter((l) => l.review_status === 'approved').length
    };
  }
}

