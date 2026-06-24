import { motion } from 'motion/react';

const dotVariants = {
  animate: (i: number) => ({
    y: [0, -6, 0],
    transition: {
      repeat: Infinity,
      duration: 0.6,
      delay: i * 0.15,
      ease: "easeInOut"
    }
  })
};

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 max-w-[85%] sm:max-w-[75%] mr-auto" id="typing-indicator-container">
      {/* Bot Icon */}
      <div className="flex select-none items-center justify-center rounded-lg border bg-surface-container-high border-outline/30 text-primary w-8 h-8 font-mono text-xs font-semibold shrink-0" id="bot-avatar-typing">
        AI
      </div>
      
      {/* Typing Bubble */}
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-none px-4 py-3 bg-surface-container-low text-on-surface-variant border border-outline-variant/50" id="typing-bubble">
        <span className="text-xs font-semibold uppercase tracking-wider text-primary/70 mr-1 font-sans">Analyzing</span>
        <div className="flex gap-1" id="bouncing-dots">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              custom={i}
              variants={dotVariants}
              animate="animate"
              className="w-2.5 h-2.5 rounded-full bg-primary/70"
            />
          ))}
        </div>
      </div>
    </div>
  );
}
