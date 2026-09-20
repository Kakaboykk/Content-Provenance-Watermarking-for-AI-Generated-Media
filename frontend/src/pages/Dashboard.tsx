import { Link } from 'react-router-dom';
import { ShieldCheck, ImagePlus, CheckCircle, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Dashboard() {
  const cards = [
    {
      title: 'Generate AI Media',
      description: 'Create stunning images using our integrated AI generation pipeline.',
      icon: ImagePlus,
      link: '/generate',
      color: 'text-blue-400',
      bg: 'bg-blue-400/10',
      border: 'hover:border-blue-500/50',
    },
    {
      title: 'Protect Asset',
      description: 'Inject invisible DWT-DCT watermarks and register cryptographic hashes.',
      icon: ShieldCheck,
      link: '/protect',
      color: 'text-primary-light',
      bg: 'bg-primary/10',
      border: 'hover:border-primary/50',
    },
    {
      title: 'Verify Provenance',
      description: 'Upload any image to blindly extract its watermark and verify authenticity.',
      icon: CheckCircle,
      link: '/verify',
      color: 'text-emerald-400',
      bg: 'bg-emerald-400/10',
      border: 'hover:border-emerald-500/50',
    },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-full flex flex-col"
    >
      <div className="mb-10">
        <h1 className="text-4xl font-bold mb-4 text-white">Content Provenance Dashboard</h1>
        <p className="text-zinc-400 text-lg max-w-3xl">
          A full-cycle platform that generates, protects, and verifies AI-generated media using 
          robust DWT-DCT watermarking and cryptographic hashing.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {cards.map((card, idx) => (
          <Link key={idx} to={card.link}>
            <motion.div 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`glass-card p-6 h-full flex flex-col transition-all cursor-pointer ${card.border}`}
            >
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${card.bg}`}>
                <card.icon className={`w-6 h-6 ${card.color}`} />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">{card.title}</h2>
              <p className="text-zinc-400 flex-1">{card.description}</p>
              
              <div className="mt-6 flex items-center text-sm font-medium text-zinc-300 group">
                Get started 
                <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
              </div>
            </motion.div>
          </Link>
        ))}
      </div>
      
      <div className="mt-12 glass-card p-6 border-zinc-800/50 bg-gradient-to-br from-zinc-900 to-zinc-950 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>
        <h3 className="text-lg font-semibold text-white mb-2">System Status</h3>
        <div className="flex items-center space-x-6 text-sm">
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></div>
            <span className="text-zinc-400">Backend API (FastAPI)</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></div>
            <span className="text-zinc-400">Database (PostgreSQL)</span>
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></div>
            <span className="text-zinc-400">Watermark Engine</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
