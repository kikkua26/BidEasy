/**
 * Axios 封装（支持 AbortController 取消请求）
 */
import axios from 'axios'
import type { AxiosInstance } from 'axios'

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isCancel(error)) {
      console.log('[API] 请求已取消')
      return Promise.reject(error)
    }
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('[API Error]', message)
    return Promise.reject(error)
  }
)

/** 创建一个可取消的请求信号 */
export function createCancelSignal() {
  const controller = new AbortController()
  return {
    signal: controller.signal,
    cancel: () => controller.abort(),
    canceled: false,
  }
}

/** 生成可取消的请求配置 */
export function cancelableConfig(signal: AbortSignal) {
  return { signal }
}

export default client
