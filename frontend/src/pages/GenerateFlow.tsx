import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Wand2, Loader2, ArrowRight, ShieldCheck, Download } from 'lucide-react';
import { api, type GenerateResponse } from '../api/client';

export default function GenerateFlow() {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [imageObjectURL, setImageObjectURL] = useState<string | null>(null);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError('');
    
    // Clean up previous blob URL
    if (imageObjectURL) URL.revokeObjectURL(imageObjectURL);

    try {
      const resp = await api.generateImage(prompt);
      setResult(resp);
      setImageObjectURL(URL.createObjectURL(resp.blob));
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to generate image');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProtect = () => {
    if (!result || !imageObjectURL) return;
    // Pass the generated image to the Protect flow via route state
    navigate('/protect', { 
      state: { 
        generatedBlob: result.blob, 
        prompt, 
        provider: result.provider, 
        model: result.model 
      } 
    });
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
          <Wand2 className="w-8 h-8 text-primary mr-3" />
          Generate AI Media
        </h1>
        <p className="text-zinc-400">
          Enter a prompt to generate a new AI image. The generated image will be pristine and unwatermarked.
        </p>
      </div>

      <div className="glass-card p-6 mb-8">
        <form onSubmit={handleGenerate} className="flex gap-4">
          <input
            type="text"
            className="input-field flex-1"
            placeholder="A futuristic cyber city at sunset..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="btn-primary min-w-[140px] flex items-center justify-center"
            disabled={!prompt.trim() || isLoading}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                Generate <Wand2 className="w-4 h-4 ml-2" />
              </>
            )}
          </button>
        </form>
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}
      </div>

      {result && imageObjectURL && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }} 
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-8"
        >
          <div className="glass-card overflow-hidden">
            <div className="bg-zinc-950 aspect-square flex items-center justify-center p-4 relative group">
              <img 
                src={imageObjectURL} 
                alt="Generated" 
                className="max-w-full max-h-full rounded-lg shadow-lg"
              />
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <a 
                  href={imageObjectURL} 
                  download="generated_unprotected.png"
                  className="btn-secondary flex items-center"
                >
                  <Download className="w-4 h-4 mr-2" /> Download Original
                </a>
              </div>
            </div>
          </div>

          <div className="flex flex-col">
            <h3 className="text-xl font-semibold text-white mb-4">Generation Metadata</h3>
            
            <div className="space-y-4 mb-8 flex-1">
              <div className="glass-card p-4 bg-zinc-900/50">
                <p className="text-sm text-zinc-500 mb-1">Prompt</p>
                <p className="text-zinc-200">{prompt}</p>
              </div>
              <div className="flex gap-4">
                <div className="glass-card p-4 bg-zinc-900/50 flex-1">
                  <p className="text-sm text-zinc-500 mb-1">Provider</p>
                  <p className="text-zinc-200">{result.provider}</p>
                </div>
                <div className="glass-card p-4 bg-zinc-900/50 flex-1">
                  <p className="text-sm text-zinc-500 mb-1">Model</p>
                  <p className="text-zinc-200">{result.model}</p>
                </div>
              </div>
            </div>

            <div className="glass-card p-6 bg-primary/5 border-primary/20">
              <h4 className="text-lg font-medium text-white mb-2 flex items-center">
                <ShieldCheck className="w-5 h-5 text-primary mr-2" />
                Ready for Protection
              </h4>
              <p className="text-sm text-zinc-400 mb-6">
                This image is currently untracked. Embed a cryptographic provenance watermark 
                before distribution.
              </p>
              <button 
                onClick={handleProtect}
                className="btn-primary w-full flex items-center justify-center"
              >
                Protect & Register Asset <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
