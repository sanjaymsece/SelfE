import type {
  AnalyticsReport,
  AuthResponse,
  CommentItem,
  ContentDraft,
  MetricOverview,
  PostingTimeRecommendation,
  ReelPlan,
  ReplySuggestionResult,
  SocialAccount,
  User,
  UserPreference,
  Workspace,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

class ApiClient {
  private extractErrorMessage(data: any, defaultStatus?: number): string {
    if (!data) return defaultStatus ? `Request failed with status ${defaultStatus}` : 'An unexpected error occurred.';
    const rawError = data.error || data.detail || data.message || data.errors;
    if (typeof rawError === 'string') return rawError;
    if (typeof rawError === 'object' && rawError !== null) {
      if (rawError.message && typeof rawError.message === 'string') {
        return rawError.message;
      }
      try {
        return JSON.stringify(rawError);
      } catch {
        return 'Request encountered an error.';
      }
    }
    return defaultStatus ? `Request failed with status ${defaultStatus}` : 'An unexpected error occurred.';
  }

  async chatWithCoPilot(prompt: string): Promise<{
    status: string;
    reply: string;
    hook: string;
    why_it_works: string;
    model: string;
    error?: string;
  }> {
    const url = `${API_BASE_URL}/content/chat/`;
    const customKey = localStorage.getItem('gemini_api_key') || undefined;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({ prompt, api_key: customKey }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(this.extractErrorMessage(data, response.status));
    }
    return data;
  }

  async synthesizeVoice(text: string, voiceId?: string): Promise<Blob> {
    const url = `${API_BASE_URL}/content/voice/synthesize/`;
    const elevenlabsKey = localStorage.getItem('elevenlabs_api_key') || undefined;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'audio/mpeg',
      },
      body: JSON.stringify({
        text,
        voice_id: voiceId || '21m00Tcm4TlvDq8ikWAM',
        elevenlabs_api_key: elevenlabsKey,
      }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(this.extractErrorMessage(data, response.status));
    }
    return await response.blob();
  }

  async testGeminiKey(payload: {
    api_key?: string;
    prompt?: string;
    save_to_env?: boolean;
  }): Promise<{
    status: string;
    reply: string;
    strategy: string;
    model: string;
    latency_seconds: number;
    api_key_valid: boolean;
    error?: string;
  }> {
    const url = `${API_BASE_URL}/content/gemini-test/`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(this.extractErrorMessage(data, response.status));
    }
    return data;
  }

  private getAuthToken(): string | null {
    return localStorage.getItem('selfe_token');
  }

  private getWorkspaceId(): string | null {
    return localStorage.getItem('selfe_workspace_id');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const token = this.getAuthToken();
    const workspaceId = this.getWorkspaceId();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (workspaceId) {
      headers['X-Workspace-ID'] = workspaceId;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('selfe_token');
        localStorage.removeItem('selfe_workspace_id');
      }
      const rawError = data.error || data.detail || data.message || data.errors;
      let errorMsg: string;
      if (typeof rawError === 'object' && rawError !== null) {
        errorMsg = rawError.message || JSON.stringify(rawError);
      } else if (rawError) {
        errorMsg = String(rawError);
      } else {
        errorMsg = `Request failed with status ${response.status}`;
      }
      throw new Error(errorMsg);
    }

    return data as T;
  }

  // --- Auth & Profile ---
  async login(payload: { email: string; password: string }): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    localStorage.setItem('selfe_token', res.access);
    localStorage.setItem('selfe_refresh', res.refresh);
    if (res.workspace?.id) {
      localStorage.setItem('selfe_workspace_id', String(res.workspace.id));
    }
    return res;
  }

  async register(payload: {
    email: string;
    password: string;
    full_name?: string;
    workspace_name?: string;
    niche?: string;
  }): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    localStorage.setItem('selfe_token', res.access);
    localStorage.setItem('selfe_refresh', res.refresh);
    if (res.workspace?.id) {
      localStorage.setItem('selfe_workspace_id', String(res.workspace.id));
    }
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me/');
  }

  async updatePreferences(payload: Partial<UserPreference>): Promise<UserPreference> {
    return this.request<UserPreference>('/auth/preferences/', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  logout() {
    localStorage.removeItem('selfe_token');
    localStorage.removeItem('selfe_refresh');
    localStorage.removeItem('selfe_workspace_id');
  }

  // --- Workspaces ---
  async listWorkspaces(): Promise<{ count: number; results: Workspace[] }> {
    return this.request<{ count: number; results: Workspace[] }>('/workspaces/');
  }

  async createWorkspace(payload: {
    name: string;
    niche?: string;
    timezone?: string;
  }): Promise<Workspace> {
    return this.request<Workspace>('/workspaces/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateWorkspace(id: number, payload: Partial<Workspace>): Promise<Workspace> {
    return this.request<Workspace>(`/workspaces/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  // --- Social Accounts ---
  async listSocialAccounts(platform?: string): Promise<{ count: number; results: SocialAccount[] }> {
    const q = platform ? `?platform=${encodeURIComponent(platform)}` : '';
    return this.request<{ count: number; results: SocialAccount[] }>(`/social-accounts/${q}`);
  }

  async connectSocialAccount(payload: {
    platform: string;
    handle: string;
    display_name?: string;
    follower_count?: number;
  }): Promise<SocialAccount> {
    return this.request<SocialAccount>('/social-accounts/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async disconnectSocialAccount(id: number): Promise<void> {
    return this.request<void>(`/social-accounts/${id}/`, {
      method: 'DELETE',
    });
  }

  // --- Analytics ---
  async getOverview(params?: { date_from?: string; date_to?: string }): Promise<MetricOverview> {
    const searchParams = new URLSearchParams();
    if (params?.date_from) searchParams.set('date_from', params.date_from);
    if (params?.date_to) searchParams.set('date_to', params.date_to);
    const q = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<MetricOverview>(`/analytics/overview/${q}`);
  }

  async getPosts(params?: {
    date_from?: string;
    date_to?: string;
    platform?: string;
    media_type?: string;
  }): Promise<{ count: number; results: any[] }> {
    const searchParams = new URLSearchParams();
    if (params?.date_from) searchParams.set('date_from', params.date_from);
    if (params?.date_to) searchParams.set('date_to', params.date_to);
    if (params?.platform) searchParams.set('platform', params.platform);
    if (params?.media_type) searchParams.set('media_type', params.media_type);
    const q = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<{ count: number; results: any[] }>(`/analytics/posts/${q}`);
  }

  async getPostingTimes(params?: {
    limit?: number;
    platform?: string;
  }): Promise<{ recommendations: PostingTimeRecommendation[] }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.platform) searchParams.set('platform', params.platform);
    const q = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<{ recommendations: PostingTimeRecommendation[] }>(`/analytics/posting-times/${q}`);
  }

  async generateReport(date_from: string, date_to: string): Promise<AnalyticsReport> {
    return this.request<AnalyticsReport>('/analytics/reports/generate/', {
      method: 'POST',
      body: JSON.stringify({
        date_range: { date_from, date_to },
      }),
    });
  }

  async listReports(): Promise<{ count: number; results: AnalyticsReport[] }> {
    return this.request<{ count: number; results: AnalyticsReport[] }>('/analytics/reports/');
  }

  // --- Content Studio ---
  async generateIdeas(payload: {
    topic: string;
    goal?: string;
    platform?: string;
    tone?: string;
    count?: number;
  }): Promise<{ draft: ContentDraft; ideas: any[] }> {
    return this.request<{ draft: ContentDraft; ideas: any[] }>('/content/ideas/generate/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async generateCaptions(payload: {
    topic: string;
    tone?: string;
    platform?: string;
    count?: number;
  }): Promise<{ draft: ContentDraft; captions: any[] }> {
    return this.request<{ draft: ContentDraft; captions: any[] }>('/content/captions/generate/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async generateScripts(payload: {
    topic: string;
    target_duration_seconds?: number;
    platform?: string;
    tone?: string;
  }): Promise<{ draft: ContentDraft; scripts: any[] }> {
    return this.request<{ draft: ContentDraft; scripts: any[] }>('/content/scripts/generate/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listDrafts(params?: {
    kind?: string;
    status?: string;
    search?: string;
  }): Promise<{ count: number; results: ContentDraft[] }> {
    const searchParams = new URLSearchParams();
    if (params?.kind) searchParams.set('kind', params.kind);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.search) searchParams.set('search', params.search);
    const q = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<{ count: number; results: ContentDraft[] }>(`/content/drafts/${q}`);
  }

  async createDraft(payload: {
    kind: string;
    title: string;
    body: string;
    status?: string;
  }): Promise<ContentDraft> {
    return this.request<ContentDraft>('/content/drafts/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateDraft(id: number, payload: Partial<ContentDraft>): Promise<ContentDraft> {
    return this.request<ContentDraft>(`/content/drafts/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteDraft(id: number): Promise<void> {
    return this.request<void>(`/content/drafts/${id}/`, {
      method: 'DELETE',
    });
  }

  // --- Reel Studio ---
  async generateReel(payload: {
    topic: string;
    target_audience?: string;
    vibe?: string;
    target_duration_seconds?: number;
    platform?: string;
  }): Promise<ReelPlan> {
    return this.request<ReelPlan>('/reels/generate/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listReels(params?: {
    status?: string;
    platform?: string;
    search?: string;
  }): Promise<{ count: number; results: ReelPlan[] }> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.platform) searchParams.set('platform', params.platform);
    if (params?.search) searchParams.set('search', params.search);
    const q = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<{ count: number; results: ReelPlan[] }>(`/reels/${q}`);
  }

  async updateReel(id: number, payload: Partial<ReelPlan>): Promise<ReelPlan> {
    return this.request<ReelPlan>(`/reels/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteReel(id: number): Promise<void> {
    return this.request<void>(`/reels/${id}/`, {
      method: 'DELETE',
    });
  }

  // --- Comment Intelligence ---
  async listComments(params?: {
    sentiment?: string;
    intent?: string;
    is_question?: boolean;
    analyzed?: boolean;
    search?: string;
  }): Promise<{ count: number; results: CommentItem[] }> {
    const searchParams = new URLSearchParams();
    if (params?.sentiment) searchParams.set('sentiment', params.sentiment);
    if (params?.intent) searchParams.set('intent', params.intent);
    if (params?.is_question !== undefined) searchParams.set('is_question', String(params.is_question));
    if (params?.analyzed !== undefined) searchParams.set('analyzed', String(params.analyzed));
    if (params?.search) searchParams.set('search', params.search);
    const q = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.request<{ count: number; results: CommentItem[] }>(`/comments/${q}`);
  }

  async updateComment(id: number, payload: Partial<CommentItem>): Promise<CommentItem> {
    return this.request<CommentItem>(`/comments/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteComment(id: number): Promise<void> {
    return this.request<void>(`/comments/${id}/`, {
      method: 'DELETE',
    });
  }

  async analyzeComments(comment_ids?: number[]): Promise<{ count: number; analyzed: CommentItem[] }> {
    const payload = comment_ids && comment_ids.length > 0 ? { comment_ids } : {};
    return this.request<{ count: number; analyzed: CommentItem[] }>('/comments/analyze/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async suggestReply(
    commentId: number,
    payload?: { tone?: string; language?: string; extra_instructions?: string }
  ): Promise<ReplySuggestionResult> {
    return this.request<ReplySuggestionResult>(`/comments/${commentId}/suggest-reply/`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  }
}

export const api = new ApiClient();
