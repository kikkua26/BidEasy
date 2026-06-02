/**
 * 系统设置 API
 */
import client from './client'
import type { ApiResponse } from '@/types'

export interface AISettings {
  ai_api_key: string
  ai_base_url: string
  ai_model: string
  ai_temperature: string
  app_name: string
}

export const settingsApi = {
  /** 获取所有设置 */
  getAll() {
    return client.get<ApiResponse<AISettings>>('/v1/settings')
  },

  /** 更新设置 */
  update(data: Record<string, string>) {
    return client.put<ApiResponse<null>>('/v1/settings', data)
  },
}
