export interface User {
  id: number;
  email: string;
  full_name: string;
  date_joined: string;
  preferences: UserPreference;
  workspaces: WorkspaceMembership[];
}

export interface UserPreference {
  niche: string;
  goals: string[];
  preferred_language: string;
  tone: string;
  content_style: string;
  target_audience: string;
  keywords: string[];
  updated_at?: string;
}

export interface Workspace {
  id: number;
  name: string;
  slug: string;
  niche: string;
  timezone: string;
  role?: string;
  members_count?: number;
  social_accounts_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface WorkspaceMembership {
  role: 'owner' | 'admin' | 'member';
  workspace: Workspace;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  token_type: string;
  expires_in: number;
  user: User;
  workspace?: Workspace | null;
}

export interface SocialAccount {
  id: number;
  platform: 'instagram' | 'tiktok' | 'youtube' | 'facebook' | 'linkedin';
  platform_display: string;
  handle: string;
  display_name: string;
  follower_count: number;
  posts_count: number;
  is_simulated: boolean;
  created_at: string;
}

export interface MetricOverview {
  date_range: {
    date_from: string;
    date_to: string;
    days: number;
  };
  totals: {
    impressions: number;
    reach: number;
    engagements: number;
    likes: number;
    comments: number;
    shares: number;
    saves: number;
    posts_count: number;
    engagement_rate: number;
  };
  prior_totals?: {
    impressions: number;
    reach: number;
    engagements: number;
    engagement_rate: number;
  };
  growth?: {
    impressions: number | null;
    reach: number | null;
    engagements: number | null;
    engagement_rate: number | null;
  };
  daily: Array<{
    date: string;
    impressions: number;
    reach: number;
    engagements: number;
  }>;
  top_posts: Array<{
    id: number;
    external_id: string;
    platform: string;
    caption: string;
    media_type: string;
    published_at: string;
    impressions: number;
    reach: number;
    engagement: number;
    engagement_rate: number;
  }>;
}

export interface PostingTimeRecommendation {
  day_of_week: string;
  hour: number;
  hour_display: string;
  average_engagement_rate: number;
  sample_posts: number;
  confidence: 'high' | 'medium' | 'low';
}

export interface AnalyticsReport {
  id: number;
  date_from: string;
  date_to: string;
  metrics_snapshot: Record<string, any>;
  summary: string;
  growth_explanation: string;
  key_findings: string[];
  recommendations: string[];
  model_used: string;
  created_at: string;
}

export interface ContentDraft {
  id: number;
  kind: 'idea' | 'caption' | 'script';
  title: string;
  body: string;
  content: Record<string, any>;
  status: 'draft' | 'approved' | 'archived';
  source: 'manual' | 'ai';
  model_used: string;
  prompt_context: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ReelPlanScene {
  scene_number: number;
  duration_seconds: number;
  visual_description: string;
  camera_angle: string;
  dialogue_or_voiceover: string;
  lighting: string;
  background: string;
  on_screen_text?: string;
}

export interface ReelPlan {
  id: number;
  title: string;
  topic: string;
  platform: string;
  target_duration_seconds: number;
  status: 'draft' | 'approved' | 'archived';
  notes: string;
  plan: {
    hook: {
      visual: string;
      spoken: string;
    };
    scenes: ReelPlanScene[];
    music_recommendation: string;
    caption: string;
    hashtags: string[];
    call_to_action: string;
  };
  model_used: string;
  created_at: string;
  updated_at: string;
}

export interface CommentItem {
  id: number;
  post: number;
  post_caption: string;
  author_username: string;
  text: string;
  commented_at: string;
  like_count: number;
  sentiment: 'positive' | 'neutral' | 'negative' | 'unknown';
  intent: 'question' | 'collaboration' | 'praise' | 'complaint' | 'feedback' | 'spam' | 'other' | 'unknown';
  is_question: boolean;
  is_collaboration_opportunity: boolean;
  confidence: number | null;
  analysis_summary: string;
  analyzed_at: string | null;
  is_simulated: boolean;
  created_at: string;
}

export interface ReplySuggestionResult {
  id: number;
  comment: number;
  suggestions: string[];
  tone: string;
  model_used: string;
  created_at: string;
}
