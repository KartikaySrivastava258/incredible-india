export const SPEECH_LANGUAGE_MAP = {
  hi: 'hi-IN', en: 'en-IN', ta: 'ta-IN', te: 'te-IN', bn: 'bn-IN',
  mr: 'mr-IN', gu: 'gu-IN', kn: 'kn-IN', pa: 'pa-IN'
};

export function toSpeechLanguage(language) {
  const base = String(language || '').toLowerCase().split('-')[0];
  return SPEECH_LANGUAGE_MAP[base] || 'hi-IN';
}

export function getSpeechRecognition() {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}
