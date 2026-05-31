import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, ShieldCheck, Fingerprint, Activity, ArrowRight } from 'lucide-react';

const Login = ({ onLogin }) => {
  const [passcode, setPasscode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (passcode === '1234') { // Mock secure passcode
      setIsVerifying(true);
      await new Promise(r => setTimeout(r, 1500)); // Simulate biometric sync
      onLogin(true);
    } else {
      setError(true);
      setTimeout(() => setError(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center p-6 z-50 overflow-hidden bg-[#020617]">
      {/* Animated Background Elements */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-apollo-teal/20 rounded-full blur-[120px] animate-pulse"></div>
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }}></div>

      <motion.div 
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        className="glass-panel w-full max-w-md p-10 relative"
      >
        <div className="scanline rounded-[2.5rem]"></div>
        
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mb-6 border border-white/10 neo-glow">
            <ShieldCheck className="w-10 h-10 text-cyan-400" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-glow mb-2 font-outfit">SurgeGuard<span className="text-cyan-400">AI</span></h1>
          <p className="text-slate-400 text-sm">Secure Biomedical Authorization Required</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="relative group">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-500 group-focus-within:text-cyan-400 transition-colors">
              <Lock size={18} />
            </div>
            <input
              type="password"
              placeholder="Enter Operation Key"
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:border-cyan-500/50 focus:ring-4 focus:ring-cyan-500/10 transition-all text-center tracking-[0.5em] text-lg font-mono placeholder:text-slate-600 placeholder:tracking-normal placeholder:text-sm"
            />
          </div>

          <button
            disabled={isVerifying}
            className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 text-white rounded-2xl py-4 font-semibold transition-all flex items-center justify-center gap-2 group relative overflow-hidden"
          >
            <AnimatePresence mode="wait">
              {isVerifying ? (
                <motion.div
                  key="verifying"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-3"
                >
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                  >
                    <Activity size={20} className="text-cyan-200" />
                  </motion.div>
                  <span>Syncing Neural Link...</span>
                </motion.div>
              ) : (
                <motion.div
                  key="idle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2"
                >
                  <span>Initiate Operation</span>
                  <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </motion.div>
              )}
            </AnimatePresence>
          </button>
          
          {error && (
            <motion.p 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-red-400 text-xs text-center font-medium"
            >
              Invalid Authorization Key. Access Denied.
            </motion.p>
          )}
        </form>

        <div className="mt-10 flex items-center justify-between border-t border-white/5 pt-6 text-[10px] text-slate-500 uppercase tracking-widest">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
            Mainframe Online
          </div>
          <div>v4.2.0-STABLE</div>
        </div>
      </motion.div>

      {/* Footer Info */}
      <div className="fixed bottom-8 text-slate-600 text-[10px] uppercase tracking-[0.3em] pointer-events-none">
        Classified Medical Technology // Level 5 Clearance Required
      </div>
    </div>
  );
};

export default Login;
