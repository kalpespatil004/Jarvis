export type ApiStatus = 'online' | 'offline' | 'starting';
export type VoiceState = 'idle' | 'listening' | 'recognizing' | 'thinking' | 'speaking' | 'offline' | 'muted';
export type AiModel = 'Gemini' | 'OpenRouter' | 'Ollama' | 'Offline' | 'Auto';

export interface ChatMessage { id: string; role: 'user' | 'assistant' | 'system'; content: string; timestamp: string; status?: 'streaming' | 'sent' | 'error'; }
export interface JarvisSettings { model: AiModel; theme: 'dark' | 'high-contrast'; voiceEnabled: boolean; ttsEnabled: boolean; backendUrl: string; }
export interface MemoryItem { id: string; title: string; content: string; pinned: boolean; updatedAt: string; }
export interface LogEntry { id: string; level: 'info' | 'warning' | 'error'; source: string; message: string; timestamp: string; }

const timeout = 30_000;

export class JarvisApi {
  constructor(private baseUrl = 'http://127.0.0.1:8000') {}
  setBaseUrl(url: string): void { this.baseUrl = url.replace(/\/$/, ''); }
  async healthCheck(): Promise<boolean> { try { await this.request('/'); return true; } catch { return false; } }
  async sendMessage(message: string): Promise<string> { const data = await this.request<{ response: string }>(`/ask?query=${encodeURIComponent(message)}`); return data.response; }
  async startListening(): Promise<void> { await this.optionalPost('/voice/start'); }
  async stopListening(): Promise<void> { await this.optionalPost('/voice/stop'); }
  async interruptSpeech(): Promise<void> { await this.optionalPost('/voice/interrupt'); }
  async getHistory(): Promise<ChatMessage[]> { return this.optionalGet('/history', []); }
  async clearHistory(): Promise<void> { await this.optionalPost('/history/clear'); }
  async getSettings(): Promise<Partial<JarvisSettings>> { return this.optionalGet('/settings', {}); }
  async saveSettings(settings: Partial<JarvisSettings>): Promise<void> { await this.optionalPost('/settings', settings); }
  async getMemory(): Promise<MemoryItem[]> { return this.optionalGet('/memory', []); }
  async syncFirebase(): Promise<void> { await this.optionalPost('/firebase/sync'); }
  async getLogs(): Promise<LogEntry[]> { return this.optionalGet('/logs', []); }

  private async optionalGet<T>(path: string, fallback: T): Promise<T> { try { return await this.request<T>(path); } catch { return fallback; } }
  private async optionalPost(path: string, body?: unknown): Promise<void> { try { await this.request(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }); } catch { /* optional backend capability */ } }
  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeout);
    try {
      const res = await fetch(`${this.baseUrl}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) }, signal: controller.signal });
      if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
      return await res.json() as T;
    } finally { window.clearTimeout(timer); }
  }
}
