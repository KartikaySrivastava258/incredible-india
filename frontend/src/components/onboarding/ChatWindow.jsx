import React, { useEffect, useRef, useState } from 'react';
import ChatMessage from './ChatMessage';
import { getSpeechRecognition, toSpeechLanguage } from '../../utils/speech';

export default function ChatWindow({ messages, onSend, disabled, placeholder = 'Type your message…', language }) {
  const [draft, setDraft] = useState('');
  const [listening, setListening] = useState(false);
  const [speakerOn, setSpeakerOn] = useState(false);
  const [speechHint, setSpeechHint] = useState('');
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const composingRef = useRef(false);
  const recognitionRef = useRef(null);
  const lastSpokenIdRef = useRef(null);
  const speechSupported = typeof window !== 'undefined' && !!getSpeechRecognition();
  const outputSupported = typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
  const speechLang = toSpeechLanguage(language);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  useEffect(() => {
    if (disabled && recognitionRef.current) recognitionRef.current.stop();
  }, [disabled]);

  useEffect(() => {
    const synthesis = outputSupported ? window.speechSynthesis : null;
    return () => {
      recognitionRef.current?.stop();
      recognitionRef.current = null;
      synthesis?.cancel();
    };
  }, [outputSupported]);

  useEffect(() => {
    const latest = [...messages].reverse().find((m) => m.from === 'ai' && !m.pending && m.text);
    if (!speakerOn || !outputSupported) {
      if (latest) lastSpokenIdRef.current = latest.id;
      return;
    }
    const synthesis = window.speechSynthesis;
    const speakLatest = () => {
      const current = [...messages].reverse().find((m) => m.from === 'ai' && !m.pending && m.text);
      if (!current || current.id === lastSpokenIdRef.current) return;
      const latest = current;
      const voices = window.speechSynthesis.getVoices();
      const base = speechLang.split('-')[0].toLowerCase();
      const hasVoice = voices.some((v) => String(v.lang || '').toLowerCase().split('-')[0] === base);
      if (!hasVoice) {
        setSpeechHint(`No ${speechLang} voice on this device`);
        lastSpokenIdRef.current = latest.id;
        return;
      }
      setSpeechHint('');
      lastSpokenIdRef.current = latest.id;
      synthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(latest.text);
      utterance.lang = speechLang;
      synthesis.speak(utterance);
    };
    speakLatest();
    synthesis.addEventListener?.('voiceschanged', speakLatest);
    return () => synthesis.removeEventListener?.('voiceschanged', speakLatest);
  }, [messages, speakerOn, outputSupported, speechLang]);

  function submit() {
    const trimmed = draft.trim();
    if (!trimmed || disabled) return;
    recognitionRef.current?.stop();
    onSend(trimmed);
    setDraft('');
  }

  function startListening() {
    const Recognition = getSpeechRecognition();
    if (!Recognition || disabled) return;
    recognitionRef.current?.stop();
    const recognition = new Recognition();
    recognition.lang = speechLang;
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onstart = () => { setListening(true); setSpeechHint(''); };
    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = 0; i < event.results.length; i += 1) transcript += event.results[i][0].transcript;
      setDraft(transcript);
    };
    recognition.onerror = (event) => {
      const messagesByError = {
        'not-allowed': 'Microphone permission was denied.',
        'no-speech': 'No speech was detected. Try again.',
        network: 'Voice typing is unavailable due to a network error.',
        'language-not-supported': `Voice typing does not support ${speechLang} on this device.`
      };
      setSpeechHint(messagesByError[event.error] || 'Voice typing failed. Try again.');
      setListening(false);
    };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    try { recognition.start(); } catch { setListening(false); }
  }

  function toggleListening() {
    if (listening) recognitionRef.current?.stop();
    else startListening();
  }

  function toggleSpeaker() {
    if (!outputSupported) return;
    setSpeakerOn((current) => {
      if (current) window.speechSynthesis.cancel();
      return !current;
    });
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey && !composingRef.current) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-window__messages" ref={listRef} role="log" aria-live="polite" aria-label="Conversation">
        {messages.map((m) => <ChatMessage key={m.id} from={m.from} text={m.text} pending={m.pending} />)}
      </div>
      <form className="chat-window__composer" onSubmit={(e) => { e.preventDefault(); submit(); }}>
        <textarea
          ref={inputRef}
          aria-label="Message"
          value={draft}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onCompositionStart={() => { composingRef.current = true; }}
          onCompositionEnd={() => { composingRef.current = false; }}
        />
        {speechSupported && (
          <button type="button" className="btn btn-ghost chat-window__voice-btn" aria-label="Voice typing"
            aria-pressed={listening} disabled={disabled} title={listening ? 'Stop listening' : 'Start voice typing'} onClick={toggleListening}>
            {listening ? '● Listening' : '🎙 Mic'}
          </button>
        )}
        {outputSupported && (
          <button type="button" className="btn btn-ghost chat-window__voice-btn" aria-label="Read replies aloud"
            aria-pressed={speakerOn} disabled={disabled} title={speakerOn ? 'Turn speaker off' : 'Turn speaker on'} onClick={toggleSpeaker}>
            {speakerOn ? '🔊 On' : '🔈 Off'}
          </button>
        )}
        <button type="submit" className="btn btn-primary" disabled={disabled || !draft.trim()}>Send</button>
      </form>
      <div className="chat-window__speech-hint" aria-live="polite">
        {speechSupported && 'Voice typing uses your browser’s speech service.'}
        {listening && ' Listening…'}
        {speechHint && ` ${speechHint}`}
        {!speechSupported && ' Voice typing is not supported in this browser.'}
        {!outputSupported && ' Speaker output is not supported in this browser.'}
      </div>
    </div>
  );
}
