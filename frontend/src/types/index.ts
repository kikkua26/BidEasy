/** 项目相关类型 */

export type ProjectStatus = 'draft' | 'in_progress' | 'completed'

export interface Project {
  id: string
  name: string
  project_type: string | null
  project_scale: string | null
  bid_amount: number | null
  project_info: string | null
  status: ProjectStatus
  created_at: string
  updated_at: string
}

/** 大纲相关类型 */
export type OutlineStatus = 'draft' | 'confirmed' | 'locked'

export interface OutlineNode {
  id: string
  project_id: string
  parent_id: string | null
  level: 1 | 2 | 3 | 4
  title: string
  sort_order: number
  status: OutlineStatus
  ai_suggested: boolean
  children?: OutlineNode[]
}

/** 文档相关 */
export interface DocumentItem {
  id: string
  project_id: string
  file_name: string | null
  file_type: string | null
  content_type: string | null
  raw_text: string | null
  created_at: string
}

export interface DocumentParseResult {
  file_name: string
  file_type: string
  raw_text: string
  word_count: number
  page_count: number | null
}

/** 评分点 */
export interface ScoringCriteria {
  id: string
  project_id: string
  category: string | null
  item_name: string | null
  max_score: number | null
  description: string | null
  requirements: string | null
  sort_order: number
}

/** 章节内容 */
export type SectionContentStatus = 'generated' | 'reviewed' | 'approved'

export interface SectionContent {
  id: string
  project_id: string
  outline_id: string
  content: string | null
  word_count: number
  version: number
  status: SectionContentStatus
  created_at: string
}

/** 审查 */
export interface ReviewItem {
  id: string
  project_id: string
  outline_id: string | null
  review_type: string | null
  score: number | null
  feedback: string | null
  suggestions: Record<string, unknown> | null
  status: string | null
}

/** 通用API响应 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface PaginatedData<T = unknown> {
  list: T[]
  total: number
  page: number
  page_size: number
}

/** 大纲对话 */
export interface OutlineChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface OutlineChatResponse {
  message: string
  outline: OutlineNode[]
  changes: string[]
}

/** 流式生成事件 */
export interface SSEContentEvent {
  type: 'start' | 'chunk' | 'done'
  outline_id?: string
  title?: string
  text?: string
  word_count?: number
}
