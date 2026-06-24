import { motion } from 'motion/react';
import { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, HelpCircle, Heart, Star, Activity, Pill } from 'lucide-react';

interface ConditionCardProps {
  key?: string | number | null;
  name: string;
  description: string;
  matchPercentage: number;
  urgency: 'urgent' | 'moderate' | 'low';
  precautions?: string[];
  medications?: string[];
  diet?: string;
  workouts?: string;
}

const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { type: 'spring', stiffness: 300, damping: 24 } 
  }
};

export default function ConditionCard({
  name,
  description,
  matchPercentage,
  urgency,
  precautions = [],
  medications = [],
  diet = '',
  workouts = ''
}: ConditionCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Get color configurations based on urgency
  const getStyles = () => {
    switch (urgency) {
      case 'urgent':
        return {
          border: 'border-l-4 border-l-error bg-error-container/10 border-outline-variant hover:border-l-error hover:border-error/30',
          badge: 'bg-error/20 text-error border border-error/30',
          progress: 'bg-error',
          bgOpacity: 'bg-error/10',
          text: 'text-error'
        };
      case 'moderate':
        return {
          border: 'border-l-4 border-l-primary bg-primary-container/5 border-outline-variant hover:border-l-primary hover:border-primary/30',
          badge: 'bg-primary/20 text-primary border border-primary/30',
          progress: 'bg-primary-container',
          bgOpacity: 'bg-primary-container/10',
          text: 'text-primary'
        };
      case 'low':
      default:
        return {
          border: 'border-l-4 border-l-on-surface-variant bg-surface-container/5 border-outline-variant hover:border-on-surface hover:border-outline',
          badge: 'bg-surface-container-high text-on-surface-variant border border-outline-variant',
          progress: 'bg-on-surface-variant',
          bgOpacity: 'bg-surface-container-high',
          text: 'text-on-surface-variant'
        };
    }
  };

  const style = getStyles();

  return (
    <motion.div
      variants={itemVariants}
      className={`rounded-lg border p-4 transition-all duration-200 select-none shadow-sm cursor-pointer ${style.border}`}
      whileHover={{ y: -3, transition: { duration: 0.15 } }}
      onClick={() => setIsOpen(!isOpen)}
      id={`condition-card-${name.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-start justify-between gap-2" id="card-header">
        <div id="card-info">
          <div className="flex items-center gap-2 flex-wrap" id="badge-row">
            <span className={`text-[10px] font-bold uppercase py-0.5 px-2 rounded-full tracking-wider select-none ${style.badge}`} id="urgency-badge">
              {urgency}
            </span>
            <span className="text-xs font-mono text-on-surface-variant" id="match-label">
              Match: {matchPercentage}%
            </span>
          </div>
          <h3 className="text-base font-bold text-on-surface mt-1.5 font-sans" id="condition-name">
            {name}
          </h3>
        </div>
        
        {/* Toggle details */}
        <button 
          className="text-on-surface-variant hover:text-on-surface p-1 rounded-md"
          id="toggle-btn"
          aria-label="Toggle details"
        >
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      <p className="text-xs text-on-surface-variant leading-relaxed mt-2 font-sans line-clamp-2" id="condition-desc">
        {description}
      </p>

      {/* Matching percentage progress bar */}
      <div className="w-full bg-surface-container-low h-1.5 rounded-full mt-3 overflow-hidden border border-outline-variant/30" id="progress-wrapper">
        <motion.div 
          className={`h-full rounded-full ${style.progress}`}
          initial={{ width: 0 }}
          animate={{ width: `${matchPercentage}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          id="progress-bar"
        />
      </div>

      {/* Expanded Actions/Notes Details */}
      {isOpen && (
        <motion.div 
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ duration: 0.25 }}
          className="mt-4 pt-3 border-t border-outline-variant/40 space-y-3.5"
          id="expanded-details"
        >
          {/* Precautions guidelines checklist */}
          {precautions.length > 0 && (
            <div id="precautions-section">
              <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5 text-error" /> General Care & Precautions
              </h4>
              <ul className="list-disc pl-4 text-xs text-on-surface-variant space-y-1" id="precautions-list">
                {precautions.map((item, idx) => (
                  <li key={idx} id={`precaution-item-${idx}`}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommended Medications */}
          {medications.length > 0 && (
            <div id="medications-section">
              <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider mb-1.5 flex items-center gap-1">
                <Pill className="w-3.5 h-3.5 text-primary" /> Potential Actions / Over the Counter
              </h4>
              <div className="flex flex-wrap gap-1.5" id="medications-tags">
                {medications.map((med, idx) => (
                  <span 
                    key={idx} 
                    className="text-[10px] sm:text-xs px-2 py-0.5 rounded bg-surface-container text-on-surface border border-outline/35"
                    id={`medication-${idx}`}
                  >
                    {med}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Supportive diet & exercise details if available */}
          {(diet || workouts) && (
            <div className="grid grid-cols-2 gap-2 text-[11px] bg-surface-container-low border border-outline-variant/30 p-2 rounded-md" id="clinical-support">
              {diet && (
                <div id="diet-support">
                  <span className="font-bold text-on-surface block" id="diet-label">Dietary Advice:</span>
                  <span className="text-on-surface-variant leading-tight" id="diet-text">{diet}</span>
                </div>
              )}
              {workouts && (
                <div id="workouts-support">
                  <span className="font-bold text-on-surface block" id="workout-label">Activity Status:</span>
                  <span className="text-on-surface-variant leading-tight" id="workout-text">{workouts}</span>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
