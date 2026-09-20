import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, Loader2, UploadCloud, ShieldCheck, Download, Fingerprint } from 'lucide-react';
import { api, type WatermarkEmbedResponse } from '../api/client';

export default function ProtectFlow() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [fileBlob, setFileBlob] = useState<Blob | null>(null);
  const [imageObjectURL, setImageObjectURL] = useState<string | null>(null);
  const [metadata, setMetadata] = useState({
    sourceType: 'user_upload',
    provider: '',
    model: '',
    prompt: ''
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<WatermarkEmbedResponse | null>(null);
  const [resultObjectURL, setResultObjectURL] = useState<string | null>(null);

  // Initialize from Generate Flow state if present
  useEffect(() => {
    if (location.state?.generatedBlob) {
      setFileBlob(location.state.generatedBlob);
      setImageObjectURL(URL.createObjectURL(location.state.generatedBlob));
      setMetadata({
        sourceType: 'ai_generated',
        provider: location.state.provider || '',
        model: location.state.model || '',
        prompt: location.state.prompt || ''
      });
    }
    
    return () => {
      if (imageObjectURL) URL.revokeObjectURL(imageObjectURL);
      if (resultObjectURL) URL.revokeObjectURL(resultObjectURL);
    };
  }, [location.state]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (imageObjectURL) URL.revokeObjectURL(imageObjectURL);
    
    setFileBlob(file);
    setImageObjectURL(URL.createObjectURL(file));
    setResult(null); // Clear previous result
    setMetadata({
      sourceType: 'user_upload',
      provider: '',
      model: '',
      prompt: ''
    });
  };

  const handleProtect = async () => {
    if (!fileBlob) return;

    setIsLoading(true);
    setError('');

    try {
      const resp = await api.embedWatermark(
        fileBlob,
        metadata.sourceType,
        metadata.provider,
        metadata.model,
        metadata.prompt
      );
      setResult(resp);
      setResultObjectURL(URL.createObjectURL(resp.blob));
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to embed watermark');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
          <Lock className="w-8 h-8 text-primary mr-3" />
          Protect & Register Asset
        </h1>
        <p className="text-zinc-400">
          Embed an invisible cryptographic DWT-DCT watermark into your image and register its SHA-256 hash 
          to establish permanent provenance.
        </p>
      </div>

      {!result ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Image Input Side */}
          <div className="glass-card p-6 flex flex-col items-center justify-center min-h-[400px]">
            {imageObjectURL ? (
              <div className="relative w-full h-full flex flex-col items-center">
                <img 
                  src={imageObjectURL} 
                  alt="To protect" 
                  className="max-w-full max-h-[300px] rounded-lg shadow-lg mb-4"
                />
                <button 
                  onClick={() => {
                    setFileBlob(null);
                    setImageObjectURL(null);
                  }}
                  className="text-sm text-zinc-400 hover:text-white underline"
                >
                  Clear and upload different image
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center w-full h-full border-2 border-dashed border-zinc-700 rounded-xl hover:border-primary hover:bg-primary/5 transition-all cursor-pointer">
                <UploadCloud className="w-12 h-12 text-zinc-500 mb-4" />
                <span className="text-zinc-400 mb-2">Click to upload image</span>
                <span className="text-xs text-zinc-600">PNG, JPEG, WEBP (Max 20MB)</span>
                <input type="file" className="hidden" accept="image/*" onChange={handleFileUpload} />
              </label>
            )}
          </div>

          {/* Configuration & Action Side */}
          <div className="flex flex-col">
            <h3 className="text-xl font-semibold text-white mb-4">Provenance Metadata</h3>
            
            <div className="glass-card p-4 space-y-4 mb-6 flex-1">
              <div>
                <label className="block text-sm text-zinc-500 mb-1">Source Type</label>
                <select 
                  className="input-field"
                  value={metadata.sourceType}
                  onChange={e => setMetadata({...metadata, sourceType: e.target.value})}
                  disabled={!!location.state?.generatedBlob} // Lock if from AI flow
                >
                  <option value="user_upload">User Upload</option>
                  <option value="ai_generated">AI Generated</option>
                </select>
              </div>

              {metadata.sourceType === 'ai_generated' && (
                <>
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <label className="block text-sm text-zinc-500 mb-1">Provider</label>
                      <input 
                        type="text" 
                        className="input-field"
                        value={metadata.provider}
                        onChange={e => setMetadata({...metadata, provider: e.target.value})}
                        disabled={!!location.state?.generatedBlob}
                      />
                    </div>
                    <div className="flex-1">
                      <label className="block text-sm text-zinc-500 mb-1">Model</label>
                      <input 
                        type="text" 
                        className="input-field"
                        value={metadata.model}
                        onChange={e => setMetadata({...metadata, model: e.target.value})}
                        disabled={!!location.state?.generatedBlob}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-500 mb-1">Prompt</label>
                    <textarea 
                      className="input-field min-h-[80px]"
                      value={metadata.prompt}
                      onChange={e => setMetadata({...metadata, prompt: e.target.value})}
                      disabled={!!location.state?.generatedBlob}
                    />
                  </div>
                </>
              )}
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                {typeof error === 'object' ? JSON.stringify(error) : error}
              </div>
            )}

            <button 
              onClick={handleProtect}
              disabled={!fileBlob || isLoading}
              className="btn-primary w-full py-4 text-lg shadow-[0_0_20px_rgba(99,102,241,0.4)]"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <Loader2 className="w-6 h-6 animate-spin mr-2" />
                  Embedding Watermark...
                </span>
              ) : (
                <span className="flex items-center justify-center">
                  <ShieldCheck className="w-6 h-6 mr-2" />
                  Protect & Register
                </span>
              )}
            </button>
          </div>
        </div>
      ) : (
        /* Result State */
        <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass-card overflow-hidden">
          <div className="bg-emerald-500/20 border-b border-emerald-500/20 p-6 flex items-center justify-center">
            <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center mb-2 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
              <ShieldCheck className="w-8 h-8 text-emerald-400" />
            </div>
          </div>
          <div className="p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-2">Asset Successfully Protected</h2>
            <p className="text-zinc-400 mb-8 max-w-lg mx-auto">
              Your image has been permanently watermarked and its cryptographic hash has been registered in the database.
            </p>

            <div className="flex flex-col md:flex-row gap-8 text-left mb-8">
              <div className="flex-1 bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                <div className="flex items-center mb-2">
                  <Fingerprint className="w-5 h-5 text-primary mr-2" />
                  <span className="text-sm text-zinc-400 uppercase tracking-wider">Provenance UUID</span>
                </div>
                <code className="text-emerald-400 font-mono text-sm break-all">
                  {result.provenanceUuid}
                </code>
              </div>
              
              <div className="flex-1 bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                <div className="flex items-center mb-2">
                  <Lock className="w-5 h-5 text-primary mr-2" />
                  <span className="text-sm text-zinc-400 uppercase tracking-wider">Asset SHA-256</span>
                </div>
                <code className="text-emerald-400 font-mono text-sm break-all">
                  {result.assetSha256}
                </code>
              </div>
            </div>

            <div className="flex justify-center gap-4">
              <a 
                href={resultObjectURL!} 
                download="protected_watermarked.png"
                className="btn-primary flex items-center"
              >
                <Download className="w-5 h-5 mr-2" />
                Download Protected Image
              </a>
              <button 
                onClick={() => navigate('/verify')}
                className="btn-secondary"
              >
                Test Verification
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
