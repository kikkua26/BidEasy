/**
 * 项目管理 API
 */
import client from './client'
import type { Project, ApiResponse, PaginatedData } from '@/types'

export const projectApi = {
  /** 获取项目列表 */
  list(params?: { status?: string; page?: number; page_size?: number }) {
    return client.get<ApiResponse<PaginatedData<Project>>>('/v1/projects', { params })
  },

  /** 获取项目详情 */
  get(id: string) {
    return client.get<ApiResponse<Project>>(`/v1/projects/${id}`)
  },

  /** 创建项目 */
  create(data: { name: string; project_type?: string; project_scale?: string; project_info?: string }) {
    return client.post<ApiResponse<Project>>('/v1/projects', data)
  },

  /** 更新项目 */
  update(id: string, data: Record<string, unknown>) {
    return client.put<ApiResponse<Project>>(`/v1/projects/${id}`, data)
  },

  /** 删除项目 */
  delete(id: string) {
    return client.delete<ApiResponse<null>>(`/v1/projects/${id}`)
  },
}
