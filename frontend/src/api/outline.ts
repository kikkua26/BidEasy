/**
 * 大纲管理 API（支持 AbortController 取消）
 */
import client from './client'
import type {
  OutlineNode, OutlineChatResponse, ApiResponse,
} from '@/types'

export const outlineApi = {
  /** 获取大纲树 */
  getTree(projectId: string) {
    return client.get<ApiResponse<OutlineNode[]>>(`/v1/projects/${projectId}/outline`)
  },

  /** 创建节点 */
  createNode(projectId: string, data: {
    parent_id?: string | null; level: number; title: string; sort_order?: number
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

  /** AI生成大纲（可取消） */
  generate(projectId: string, additionalRequirements?: string, signal?: AbortSignal) {
    return client.post<ApiResponse<OutlineNode[]>>(
      `/v1/projects/${projectId}/outline/generate`,
      { additional_requirements: additionalRequirements },
      { signal }
    )
  },

  /** 对话调整大纲 */
  chat(projectId: string, message: string, signal?: AbortSignal) {
    return client.post<ApiResponse<OutlineChatResponse>>(
      `/v1/projects/${projectId}/outline/chat`,
      { message },
      { signal }
    )
  },

  /** 生成章节内容（可取消，recursive=true 则递归生成子节） */
  generateSection(projectId: string, outlineId: string, signal?: AbortSignal) {
    return client.post<ApiResponse<{ outline_id: string; content: string; word_count: number; children_contents?: Record<string, { content: string; word_count: number }> }>>(
      `/v1/projects/${projectId}/sections/${outlineId}/generate`,
      { recursive: true },
      { signal }
    )
  },

  /** 组装初稿 */
  compose(projectId: string) {
    return client.get<ApiResponse<{ draft: string; word_count: number; section_count: number }>>(
      `/v1/projects/${projectId}/compose`
    )
  },
}
