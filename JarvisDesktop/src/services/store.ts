import type { AiModel, ApiStatus, ChatMessage, JarvisSettings, LogEntry, MemoryItem, VoiceState } from '../api/jarvisApi';
export interface AppState { messages: ChatMessage[]; backend: ApiStatus; internet: boolean; voiceState: VoiceState; model: AiModel; settings: JarvisSettings; memory: MemoryItem[]; logs: LogEntry[]; notifications: NotificationItem[]; sidebarCollapsed: boolean; activePage: string; cpu: number; ram: number; }
export interface NotificationItem { id: string; type: 'success' | 'warning' | 'error' | 'info' | 'progress'; title: string; message: string; }
type Listener = (state: AppState) => void;
const defaults: JarvisSettings = { model: 'Auto', theme: 'dark', voiceEnabled: true, ttsEnabled: true, backendUrl: 'http://127.0.0.1:8000' };
export class Store { private listeners = new Set<Listener>(); state: AppState = { messages: [], backend: 'starting', internet: navigator.onLine, voiceState: 'idle', model: 'Auto', settings: defaults, memory: [], logs: [], notifications: [], sidebarCollapsed: false, activePage: 'chat', cpu: 0, ram: 0 };
 subscribe(listener: Listener): () => void { this.listeners.add(listener); listener(this.state); return () => this.listeners.delete(listener); }
 set(patch: Partial<AppState>): void { this.state = { ...this.state, ...patch }; this.emit(); }
 notify(item: Omit<NotificationItem, 'id'>): void { const notification = { ...item, id: crypto.randomUUID() }; this.set({ notifications: [...this.state.notifications, notification] }); window.setTimeout(() => this.set({ notifications: this.state.notifications.filter(n => n.id !== notification.id) }), item.type === 'progress' ? 6000 : 4200); }
 private emit(): void { this.listeners.forEach(l => l(this.state)); }}
export const store = new Store();
