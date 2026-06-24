import { motion } from 'motion/react';
import { OctagonAlert, ShieldAlert, PhoneCall } from 'lucide-react';

interface RedFlagAlertProps {
  redFlags: string[];
}

export default function RedFlagAlert({ redFlags }: RedFlagAlertProps) {
  if (!redFlags || redFlags.length === 0) return null;

  return (
    <motion.div
      id="red-flag-alert"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: 'spring', duration: 0.5 }}
      className="red-flag-glow rounded-xl bg-[#2a0a0a] text-on-surface p-4 relative overflow-hidden flex flex-col gap-3 shadow-md"
    >
      {/* Background Pulse Ring */}
      <div className="absolute top-2 right-2 flex h-3 w-3 select-none" id="red-flag-pulse-point">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-error opacity-75"></span>
        <span className="relative inline-flex h-3 w-3 rounded-full bg-error"></span>
      </div>

      <div className="flex items-start gap-3" id="red-flag-alert-header">
        <div className="p-2 rounded-lg bg-error/15 text-error shrink-0 border border-error/20" id="red-flag-alert-icon-box">
          <OctagonAlert className="w-5 h-5 animate-bounce" />
        </div>
        
        <div className="flex-1" id="red-flag-alert-text">
          <h3 className="text-sm font-black text-error uppercase tracking-wider flex items-center gap-1.5 font-sans">
            Critical Clinical Notice
          </h3>
          <p className="text-xs text-on-surface-variant leading-relaxed mt-1 font-sans">
            Our diagnostic parsing has identified high-severity physiological factors corresponding to potential medical emergencies:
          </p>
        </div>
      </div>

      {/* Flagged criteria list */}
      <ul className="list-disc pl-5 py-1 text-xs text-error font-medium space-y-1 bg-error-container/10 rounded-md border border-error/5" id="red-flag-symptoms-list">
        {redFlags.map((flag, idx) => (
          <li key={idx} id={`red-flag-item-${idx}`}>
            <span className="text-on-surface font-sans">{flag}</span>
          </li>
        ))}
      </ul>

      {/* Emergency dispatch CTA bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-error/10 border border-error/20 p-3 rounded-lg mt-1" id="emergency-cta-box">
        <div className="flex items-start gap-2" id="emergency-instruction">
          <ShieldAlert className="w-4 h-4 text-error shrink-0 mt-0.5" />
          <p className="text-xs text-on-surface font-bold leading-tight font-sans">
            Please seek immediate emergency care (e.g. Call 911 or visit the nearest ER) if you experience any of these markers.
          </p>
        </div>
        <a 
          href="tel:911"
          className="flex items-center justify-center gap-1.5 bg-error text-white font-bold py-1.5 px-3 rounded text-xs select-none hover:bg-error/95 transition-all shadow-sm shrink-0"
          id="call-911-btn"
        >
          <PhoneCall className="w-3.5 h-3.5" />
          <span>Call 911</span>
        </a>
      </div>
    </motion.div>
  );
}
