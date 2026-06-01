/**
 * Axios 封装
 */
import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截
client.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || '请求失败'
    console.error('[API Error]', message)
    return Promise.reject(error)
  }
)

export default client
