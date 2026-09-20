import { motion } from 'framer-motion';
import { Clock, Lock } from 'lucide-react';

export default function HistoryView() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full flex flex-col items-center justify-center max-w-2xl mx-auto text-center">
      <div className="w-20 h-20 bg-zinc-900 rounded-full flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(39,39,42,0.8)] border border-zinc-800">
        <Clock className="w-10 h-10 text-zinc-500" />
      </div>
      
      <h2 className="text-3xl font-bold text-white mb-4">Provenance History</h2>
      
      <p className="text-zinc-400 text-lg mb-8 leading-relaxed">
        The complete activity ledger of generated, protected, and verified assets will be available here. 
        Currently, this view is scheduled for the Phase 5 (Authentication & Auditing) release.
      </p>

      <div className="glass-card p-6 flex items-center bg-primary/5 border-primary/20">
        <Lock className="w-6 h-6 text-primary mr-4" />
        <div className="text-left">
          <h3 className="font-semibold text-white">Database Persisted</h3>
          <p className="text-sm text-zinc-400">All of your actions are actively being recorded securely in the PostgreSQL database.</p>
        </div>
      </div>
    </motion.div>
  );
}
