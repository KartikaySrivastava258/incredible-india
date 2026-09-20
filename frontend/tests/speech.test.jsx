import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatWindow from '../src/components/onboarding/ChatWindow';
import { toSpeechLanguage } from '../src/utils/speech';

describe('onboarding voice controls', () => {
  let recognitionInstances;
  let speech;

  beforeEach(() => {
    recognitionInstances = [];
    class MockRecognition {
      constructor() { this.start = vi.fn(() => this.onstart?.()); this.stop = vi.fn(() => this.onend?.()); recognitionInstances.push(this); }
    }
    window.SpeechRecognition = MockRecognition;
    window.webkitSpeechRecognition = MockRecognition;
    speech = {
      cancel: vi.fn(), speak: vi.fn(), getVoices: vi.fn(() => [{ lang: 'hi-IN' }]),
      addEventListener: vi.fn(), removeEventListener: vi.fn()
    };
    window.speechSynthesis = speech;
    window.SpeechSynthesisUtterance = vi.fn(function (text) { this.text = text; this.lang = ''; });
  });

  afterEach(() => {
    delete window.SpeechRecognition;
    delete window.webkitSpeechRecognition;
    delete window.speechSynthesis;
    delete window.SpeechSynthesisUtterance;
  });

  it('maps all supported languages and unknown to Hindi', () => {
    expect(['hi','en','ta','te','bn','mr','gu','kn','pa'].map(toSpeechLanguage)).toEqual([
      'hi-IN','en-IN','ta-IN','te-IN','bn-IN','mr-IN','gu-IN','kn-IN','pa-IN'
    ]);
    expect(toSpeechLanguage('xx')).toBe('hi-IN');
    expect(toSpeechLanguage('en-IN')).toBe('en-IN');
  });

  it('starts Hindi recognition and fills textarea without sending', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatWindow language="hi" messages={[]} onSend={onSend} disabled={false} />);
    await user.click(screen.getByRole('button', { name: /voice typing/i }));
    expect(recognitionInstances[0].lang).toBe('hi-IN');
    act(() => recognitionInstances[0].onresult({ results: [[{ transcript: 'मैं अचार बनाती हूँ' }]] }));
    expect(screen.getByLabelText(/message/i)).toHaveValue('मैं अचार बनाती हूँ');
    expect(onSend).not.toHaveBeenCalled();
  });

  it('shows recognition errors', async () => {
    const user = userEvent.setup();
    render(<ChatWindow language="hi" messages={[]} onSend={vi.fn()} disabled={false} />);
    await user.click(screen.getByRole('button', { name: /voice typing/i }));
    act(() => recognitionInstances[0].onerror({ error: 'not-allowed' }));
    expect(screen.getByText(/microphone permission was denied/i)).toBeInTheDocument();
  });

  it('speaks a new assistant message with the right language, but not pending/history', async () => {
    const { rerender } = render(<ChatWindow language="hi" messages={[{ id: 'old', from: 'ai', text: 'History' }]} onSend={vi.fn()} disabled={false} />);
    expect(speech.speak).not.toHaveBeenCalled();
    await act(async () => {});
    // Turn speaker on; the existing history must not be treated as a new message.
    await userEvent.setup().click(screen.getByRole('button', { name: /read replies aloud/i }));
    rerender(<ChatWindow language="hi" messages={[
      { id: 'old', from: 'ai', text: 'History' },
      { id: 'pending', from: 'ai', text: 'Waiting', pending: true },
      { id: 'new', from: 'ai', text: 'नमस्ते' }
    ]} onSend={vi.fn()} disabled={false} />);
    expect(speech.speak).toHaveBeenCalledTimes(1);
    expect(window.SpeechSynthesisUtterance).toHaveBeenCalledWith('नमस्ते');
    expect(window.SpeechSynthesisUtterance.mock.instances[0].lang).toBe('hi-IN');
  });

  it('toggling speaker off cancels speech', async () => {
    const user = userEvent.setup();
    render(<ChatWindow language="hi" messages={[]} onSend={vi.fn()} disabled={false} />);
    await user.click(screen.getByRole('button', { name: /read replies aloud/i }));
    await user.click(screen.getByRole('button', { name: /read replies aloud/i }));
    expect(speech.cancel).toHaveBeenCalled();
  });
});
