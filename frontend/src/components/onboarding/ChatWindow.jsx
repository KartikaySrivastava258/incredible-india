import React, { useEffect, useRef, useState } from 'react';
import ChatMessage from './ChatMessage';

export default function ChatWindow({ messages, onSend, disabled, placeholder = 'Type your message…' }) {
  const [draft, setDraft] = useState('');
  const listRef = useRef(null);
  const inputRef = useRef(null);
  const composingRef = useRef(false);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  // Re-focus textarea after the AI replies (disabled toggles false→true→false)
  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  function submit() {
    const trimmed = draft.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setDraft('');
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey && !composingRef.current) {
      e.preventDefault();
      submit();
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    submit();
  }

  return (
    <div className="chat-window">
      <div
        className="chat-window__messages"
        ref={listRef}
        role="log"
        aria-live="polite"
        aria-label="Conversation"
      >
        {messages.map((m) => (
          <ChatMessage key={m.id} from={m.from} text={m.text} pending={m.pending} />
        ))}
      </div>
      <form className="chat-window__composer" onSubmit={handleSubmit}>
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
        <button type="submit" className="btn btn-primary" disabled={disabled || !draft.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

