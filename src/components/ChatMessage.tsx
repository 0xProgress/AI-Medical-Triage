import { motion } from 'motion/react';
import { Message } from '../types';
import { Bot, User, ShieldAlert } from 'lucide-react';

interface ChatMessageProps {
  key?: string | number | null;
  message: Message;
  index: number;
}

const messageVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { duration: 0.3, ease: 'easeOut' } 
  }
};

export default function ChatMessage({ message, index }: ChatMessageProps) {
  const { role, content, timestamp } = message;

  if (role === 'system') {
    return (
      <motion.div
        id={`system-message-${index}`}
        className="flex justify-center p-2 my-4 select-none"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        variants={messageVariants}
      >
        <div className="flex items-center gap-1.5 rounded-full px-4 py-1.5 bg-error-container text-error border border-error/20 text-xs font-medium tracking-wide shadow-sm" id={`system-pill-${index}`}>
          <ShieldAlert className="w-3.5 h-3.5 animate-pulse text-error shrink-0" />
          <span className="italic uppercase font-sans text-[10px] sm:text-xs">{content}</span>
        </div>
      </motion.div>
    );
  }

  const isUser = role === 'user';

  return (
    <motion.div
      id={`message-container-${index}`}
      className={`flex items-start gap-3 w-full max-w-[85%] sm:max-w-[75%] ${
        isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
      }`}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      variants={messageVariants}
    >
      {/* Avatar Icon */}
      <div 
        className={`flex items-center justify-center select-none rounded-lg border w-8 h-8 font-mono text-xs font-semibold shrink-0 shadow-sm ${
          isUser 
            ? 'bg-primary-container border-primary-container text-white' 
            : 'bg-surface-container-high border-outline/30 text-primary'
        }`}
        id={`avatar-${index}`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4 text-primary" />}
      </div>

      {/* Message Bubble */}
      <div className="flex flex-col gap-1 w-full" id={`bubble-wrapper-${index}`}>
        <div 
          className={`px-4 py-3 rounded-2xl border shadow-sm ${
            isUser 
              ? 'rounded-tr-none bg-primary-container border-primary-container text-white' 
              : 'rounded-tl-none bg-[#1a1e2e] border-[#434654] text-on-surface'
          }`}
          id={`bubble-box-${index}`}
        >
          <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans break-words" id={`message-content-${index}`}>
            {content}
          </div>
        </div>
        
        {/* Timestamp */}
        {timestamp && (
          <span className={`text-[10px] text-on-surface-variant font-mono select-none px-1 ${
            isUser ? 'text-right mr-1' : 'text-left ml-1'
          }`} id={`timestamp-${index}`}>
            {timestamp}
          </span>
        )}
      </div>
    </motion.div>
  );
}
