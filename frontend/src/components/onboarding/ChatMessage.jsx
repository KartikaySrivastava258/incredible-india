import React from 'react';

export default function ChatMessage({ from, text, pending }) {
  const cls = ['chat-bubble', from === 'ai' ? 'from-ai' : 'from-seller', pending ? 'is-pending' : ''].filter(Boolean).join(' ');
  return <div className={cls}>{text}</div>;
}

