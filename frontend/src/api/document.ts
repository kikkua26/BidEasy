/**
 * 文档管理 API
 */
import client from './client'
import type { DocumentItem, DocumentParseResult, ApiResponse } from '@/types'

export const documentApi = {
  /** 获取项目文档列表 */
  list(projectId: string) {
    return client.get<ApiResponse<DocumentItem[]>>(`/v1/projects/${projectId}/documents`)
  },

  /** 上传文档 */
  upload(projectId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return client.post<ApiResponse<DocumentParseResult>>(
      `/v1/projects/${projectId}/documents/upload`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },

  /** 手动输入文档文本 */
  inputText(projectId: string, text: string) {
    return client.post<ApiResponse<DocumentParseResult>>(
      `/v1/projects/${projectId}/documents/input`,
      { text }
    )
  },

  /** 删除文档 */
  delete(projectId: string, docId: string) {
    return client.delete<ApiResponse<null>>(`/v1/projects/${projectId}/documents/${docId}`)
  },
}
