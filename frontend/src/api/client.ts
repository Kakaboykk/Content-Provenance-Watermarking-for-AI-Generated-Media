import axios from 'axios';

// The proxy in vite.config.ts routes /api to http://localhost:8000
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 60000, // 60s for intensive operations like generation or watermarking
});

export interface GenerateRequest {
  prompt: string;
}

export interface GenerateResponse {
  blob: Blob;
  provider: string;
  model: string;
}

export interface WatermarkEmbedResponse {
  blob: Blob;
  provenanceUuid: string;
  assetSha256: string;
}

export interface VerificationResponse {
  verdict: 'AUTHENTIC_UNMODIFIED' | 'TRACED_BUT_MODIFIED' | 'WATERMARK_UNRECOVERABLE' | 'NO_WATERMARK_FOUND';
  match_found: boolean;
  provenance_record: {
    id: string;
    provenance_uuid: string;
    source_type: string;
    generation_provider: string | null;
    model_name: string | null;
    prompt: string | null;
    metadata: any;
    created_at: string;
  } | null;
}

export const api = {
  // Generate Image
  generateImage: async (prompt: string): Promise<GenerateResponse> => {
    const response = await apiClient.post(
      '/generate',
      { prompt },
      { responseType: 'blob' } // CRITICAL: Endpoint returns raw binary bytes
    );
    
    return {
      blob: response.data,
      provider: response.headers['x-ai-provider'] || 'unknown',
      model: response.headers['x-ai-model'] || 'unknown',
    };
  },

  // Embed Watermark & Register Provenance
  embedWatermark: async (
    fileBlob: Blob,
    sourceType: string,
    provider?: string,
    model?: string,
    prompt?: string
  ): Promise<WatermarkEmbedResponse> => {
    const formData = new FormData();
    formData.append('file', fileBlob, 'upload.png');
    formData.append('source_type', sourceType);
    if (provider) formData.append('generation_provider', provider);
    if (model) formData.append('model_name', model);
    if (prompt) formData.append('prompt', prompt);

    const response = await apiClient.post('/watermark/embed', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob', // Returns the watermarked PNG binary
    });

    return {
      blob: response.data,
      provenanceUuid: response.headers['x-provenance-uuid'] || 'unknown',
      assetSha256: response.headers['x-asset-sha256'] || 'unknown',
    };
  },

  // Verify Image
  verifyImage: async (fileBlob: Blob): Promise<VerificationResponse> => {
    const formData = new FormData();
    formData.append('file', fileBlob, 'verify.png');

    const response = await apiClient.post<VerificationResponse>('/verify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    return response.data;
  },
};
