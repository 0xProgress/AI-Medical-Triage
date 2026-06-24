import React, { useRef, useEffect, useState } from 'react';
import { Send, FileText, Lock, RefreshCw } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  onGenerateReport: () => void;
  isComplete: boolean;
  isLoading: boolean;
  hasMessages: boolean;
}

export default function ChatInput({
  onSend,
  onGenerateReport,
  isComplete,
  isLoading,
  hasMessages
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea logic
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || isComplete) return;
    onSend(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col gap-2.5 w-full bg-surface-container p-4 rounded-xl border border-outline-variant/60 shadow-lg" id="chat-input-wrapper">
      <form onSubmit={handleSubmit} className="flex gap-2.5 items-end relative" id="chat-input-form">
        <div className="relative flex-1" id="textarea-box">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading || isComplete}
            placeholder={
              isComplete 
                ? "Triage session complete. Please export your report."
                : "Type your symptoms, duration, and pain levels..."
            }
            className="w-full resize-none rounded-lg border border-outline bg-surface-container-low px-4 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/60 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50 font-sans pr-10 min-h-[44px]"
            id="chat-textarea"
          />
          {input.trim() && (
            <span className="absolute bottom-2.5 right-3 text-[10px] font-mono text-on-surface-variant/75 hidden sm:inline" id="key-hint">
              ↵ to send
            </span>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 shrink-0 select-none" id="input-actions">
          {hasMessages && (
            <button
              type="button"
              onClick={onGenerateReport}
              disabled={isLoading}
              title="Generate triage session report"
              className="flex items-center justify-center rounded-lg border border-outline-variant bg-surface-container-high text-on-surface hover:bg-surface-container-low transition-all p-3 h-[44px]"
              id="generate-report-btn"
            >
              <FileText className="w-5 h-5 text-primary" />
              <span className="max-w-0 overflow-hidden group-hover:max-w-24 transition-all duration-300 text-xs font-bold pl-0 whitespace-nowrap hidden md:inline ml-1 text-primary">Report</span>
            </button>
          )}

          <button
            type="submit"
            disabled={!input.trim() || isLoading || isComplete}
            className="flex items-center justify-center rounded-lg bg-primary-container text-white hover:bg-primary-container/90 active:scale-95 transition-all p-3 h-[44px] px-4 disabled:opacity-40"
            id="chat-send-btn"
          >
            {isLoading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>

      {/* Footer disclaimer and privacy lock indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[10px] text-on-surface-variant/80 border-t border-outline-variant/30 pt-2" id="input-privacy-note">
        <div className="flex items-center gap-1 font-mono" id="lock-label">
          <Lock className="w-3 h-3 text-primary" />
          <span>HIPAA Compliant Session Encryption</span>
        </div>
        <p className="font-sans" id="disclaimer-label">
          All data processed locally and strictly encrypted in transit.
        </p>
      </div>
    </div>
  );
}
