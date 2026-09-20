import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertTriangle, XCircle, Search, UploadCloud, Loader2 } from 'lucide-react';
import { api, type VerificationResponse } from '../api/client';

export default function VerifyFlow() {
  const [fileBlob, setFileBlob] = useState<Blob | null>(null);
  const [imageObjectURL, setImageObjectURL] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<VerificationResponse | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (imageObjectURL) URL.revokeObjectURL(imageObjectURL);
    
    setFileBlob(file);
    setImageObjectURL(URL.createObjectURL(file));
    setResult(null);
    setError('');
  };

  const handleVerify = async () => {
    if (!fileBlob) return;
    setIsLoading(true);
    setError('');
    
    try {
      const resp = await api.verifyImage(fileBlob);
      setResult(resp);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const renderResultBadge = () => {
    if (!result) return null;
    
    switch (result.verdict) {
      case 'AUTHENTIC_UNMODIFIED':
        return (
          <div className="flex flex-col items-center p-6 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
            <CheckCircle className="w-16 h-16 text-emerald-400 mb-4" />
            <h2 className="text-2xl font-bold text-emerald-400 mb-2">Authentic & Unmodified</h2>
            <p className="text-zinc-400 text-center">
              A valid provenance watermark was found, and the image cryptographic hash perfectly matches the database record.
            </p>
          </div>
        );
      case 'TRACED_BUT_MODIFIED':
        return (
          <div className="flex flex-col items-center p-6 bg-amber-500/10 border border-amber-500/30 rounded-xl">
            <AlertTriangle className="w-16 h-16 text-amber-400 mb-4" />
            <h2 className="text-2xl font-bold text-amber-400 mb-2">Traced, But Modified</h2>
            <p className="text-zinc-400 text-center">
              The watermark survived and provenance was established, but the file hash differs from the registered original. This indicates the image has been edited, compressed, or resized.
            </p>
          </div>
        );
      case 'NO_WATERMARK_FOUND':
        return (
          <div className="flex flex-col items-center p-6 bg-zinc-800/30 border border-zinc-700/50 rounded-xl">
            <Search className="w-16 h-16 text-zinc-400 mb-4" />
            <h2 className="text-2xl font-bold text-zinc-300 mb-2">No Watermark Found</h2>
            <p className="text-zinc-400 text-center">
              The system could not extract any watermark from this image. It is either completely unrelated to this platform or has been severely modified beyond recovery.
            </p>
          </div>
        );
      case 'WATERMARK_UNRECOVERABLE':
        return (
          <div className="flex flex-col items-center p-6 bg-red-500/10 border border-red-500/30 rounded-xl">
            <XCircle className="w-16 h-16 text-red-400 mb-4" />
            <h2 className="text-2xl font-bold text-red-400 mb-2">Watermark Corrupted</h2>
            <p className="text-zinc-400 text-center">
              A watermark signal was detected but could not be cleanly decoded. The image has likely undergone heavy malicious manipulation.
            </p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center">
          <CheckCircle className="w-8 h-8 text-primary mr-3" />
          Verify Provenance
        </h1>
        <p className="text-zinc-400">
          Upload any image to blindly extract its hidden watermark. Our verification engine will cross-reference 
          the extracted UUID and check cryptographic hashes to prove authenticity.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload & Preview Side */}
        <div className="glass-card p-6 flex flex-col items-center min-h-[400px]">
          {imageObjectURL ? (
            <div className="w-full flex flex-col flex-1 items-center">
              <div className="flex-1 w-full bg-zinc-950 rounded-lg flex items-center justify-center p-2 mb-4">
                <img 
                  src={imageObjectURL} 
                  alt="To verify" 
                  className="max-w-full max-h-[400px] object-contain rounded"
                />
              </div>
              <div className="flex gap-4 w-full">
                <button 
                  onClick={() => {
                    setFileBlob(null);
                    setImageObjectURL(null);
                    setResult(null);
                  }}
                  className="btn-secondary flex-1"
                >
                  Clear Image
                </button>
                <button 
                  onClick={handleVerify}
                  disabled={isLoading}
                  className="btn-primary flex-1 flex justify-center shadow-[0_0_15px_rgba(16,185,129,0.3)] bg-emerald-600 hover:bg-emerald-500"
                >
                  {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Verify Authenticity"}
                </button>
              </div>
              {error && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm w-full">
                  {typeof error === 'object' ? JSON.stringify(error) : error}
                </div>
              )}
            </div>
          ) : (
            <label className="flex flex-col items-center justify-center w-full h-full border-2 border-dashed border-zinc-700 rounded-xl hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-all cursor-pointer">
              <UploadCloud className="w-16 h-16 text-zinc-500 mb-4" />
              <span className="text-zinc-300 text-lg mb-2">Drag & Drop or Click to Upload</span>
              <span className="text-sm text-zinc-500">Test modified, resized, or compressed JPEGs</span>
              <input type="file" className="hidden" accept="image/*" onChange={handleFileUpload} />
            </label>
          )}
        </div>

        {/* Results Side */}
        <div className="flex flex-col">
          <h3 className="text-xl font-semibold text-white mb-4">Verification Result</h3>
          
          <AnimatePresence mode="wait">
            {!result && !isLoading ? (
              <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="glass-card flex-1 flex items-center justify-center border-dashed border-zinc-700/50 p-8 text-center"
              >
                <p className="text-zinc-500">Upload an image and click Verify to see the provenance results.</p>
              </motion.div>
            ) : isLoading ? (
              <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="glass-card flex-1 flex flex-col items-center justify-center p-8"
              >
                <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                <p className="text-zinc-300">Extracting DWT-DCT coefficients...</p>
                <p className="text-zinc-500 text-sm mt-2">Checking database records</p>
              </motion.div>
            ) : (
              <motion.div 
                key="results"
                initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                className="flex flex-col gap-4 flex-1"
              >
                {renderResultBadge()}
                
                {result?.provenance_record && (
                  <div className="glass-card p-6 mt-4">
                    <h4 className="text-lg font-medium text-white mb-4 border-b border-border pb-2">Registered Provenance</h4>
                    <div className="space-y-4">
                      <div>
                        <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Internal UUID</p>
                        <p className="text-sm font-mono text-zinc-300 bg-zinc-950 p-2 rounded">{result.provenance_record.provenance_uuid}</p>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Source Type</p>
                          <p className="text-sm text-zinc-300">{result.provenance_record.source_type}</p>
                        </div>
                        <div>
                          <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Registration Date</p>
                          <p className="text-sm text-zinc-300">
                            {new Date(result.provenance_record.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      {result.provenance_record.source_type === 'ai_generated' && (
                        <>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Provider</p>
                              <p className="text-sm text-emerald-400">{result.provenance_record.generation_provider}</p>
                            </div>
                            <div>
                              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Model</p>
                              <p className="text-sm text-emerald-400">{result.provenance_record.model_name}</p>
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Original Prompt</p>
                            <p className="text-sm text-zinc-300 bg-zinc-950 p-3 rounded-lg italic">
                              "{result.provenance_record.prompt}"
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
