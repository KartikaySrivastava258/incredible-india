// Central configuration for the Kalaa Setu frontend.
//
// Per BRAIN.md Section H / I: the frontend has exactly one environment
// variable that matters, API_BASE_URL. It never reads AI_SERVICE_URL,
// MATCHING_SERVICE_URL, OPENSEARCH_URL, DYNAMODB_ENDPOINT, S3_ENDPOINT, or
// any other backend/infra variable — those are behind the backend and are
// none of the frontend's business.
//
// VITE_USE_MOCK_API is an additional, frontend-only convenience flag (not
// part of BRAIN.md's canonical .env.example) that lets a developer force
// the in-memory mock client during isolated frontend work. It defaults to
// false: the app talks to the real backend by default.

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

export const USE_MOCK_API = String(import.meta.env.VITE_USE_MOCK_API).toLowerCase() === 'true';

