/**
 * 大纲管理 API
 */
import client from './client'
import type {
  OutlineNode, SectionContent, ScoringCriteria,
  OutlineChatResponse, ApiResponse, SSEContentEvent,
} from '@/types'

export const outlineApi = {
  /** 获取大纲树 */
  getTree(projectId: string) {
    return client.get<ApiResponse<OutlineNode[]>>(`/v1/projects/${projectId}/outline`)
  },

  /** 创建节点 */
  createNode(projectId: string, data: {
    parent_id?: string | null
    level: number
    title: string
    sort_order?: number
  }) {
    return client.post<ApiResponse<OutlineNode>>(`/v1/projects/${projectId}/outline/nodes`, data)
  },

  /** 更新节点 */
  updateNode(projectId: string, nodeId: string, data: Record<string, unknown>) {
    return client.put<ApiResponse<OutlineNode>>(`/v1/projects/${projectId}/outline/nodes/${nodeId}`, data)
  },

  /** 删除节点 */
  deleteNode(projectId: string, nodeId: string) {
    return client.delete<ApiResponse<null>>(`/v1/projects/${projectId}/outline/nodes/${nodeId}`)
  },

  /** AI生成大纲 */
  generate(projectId: string, additionalRequirements?: string) {
    return client.post<ApiResponse<OutlineNode[]>>(`/v1/projects/${projectId}/outline/generate`, {
      additional_requirements: additionalRequirements,
    })
  },

  /** 对话调整大纲 */
  chat(projectId: string, message: string) {
    return client.post<ApiResponse<OutlineChatResponse>>(`/v1/projects/${projectId}/outline/chat`, {
      message,
    })
  },

  /** 生成章节内容 */
  generateSection(projectId: string, outlineId: string) {
    return client.post<ApiResponse<{ outline_id: string; content: string; word_count: number }>>(
      `/v1/projects/${projectId}/sections/${outlineId}/generate`
    )
  },

  /** 流式生成章节内容 */
  streamSection(projectId: string, outlineId: string): EventSource {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
    return new EventSource(
      `${baseUrl}/v1/projects/${projectId}/sections/${outlineId}/stream`
    )
  },

  /** 组装初稿 */
  compose(projectId: string) {
    return client.get<ApiResponse<{ draft: string; word_count: number; section_count: number }>>(
      `/v1/projects/${projectId}/compose`
    )
  },
}
