/**
 * 大纲状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { outlineApi } from '@/api/outline'
import type { OutlineNode } from '@/types'

export const useOutlineStore = defineStore('outline', () => {
  const outlineTree = ref<OutlineNode[]>([])
  const loading = ref(false)
  const generating = ref(false)

  /** 获取大纲树 */
  async function fetchOutline(projectId: string) {
    loading.value = true
    try {
      const res = await outlineApi.getTree(projectId)
      outlineTree.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  /** AI生成大纲 */
  async function generateOutline(projectId: string, requirements?: string) {
    generating.value = true
    try {
      const res = await outlineApi.generate(projectId, requirements)
      outlineTree.value = res.data.data as OutlineNode[]
      return res.data.data as OutlineNode[]
    } finally {
      generating.value = false
    }
  }

  /** 对话调整大纲 */
  async function chatRefine(projectId: string, message: string) {
    const res = await outlineApi.chat(projectId, message)
    const data = res.data.data
    if (data?.outline) {
      outlineTree.value = data.outline
    }
    return data
  }

  /** 添加节点 */
  async function addNode(projectId: string, data: {
    parent_id?: string | null
    level: number
    title: string
    sort_order?: number
  }) {
    const res = await outlineApi.createNode(projectId, data)
    await fetchOutline(projectId) // 重新获取以保持一致性
    return res.data.data as OutlineNode
  }

  /** 更新节点 */
  async function updateNode(projectId: string, nodeId: string, data: Record<string, unknown>) {
    await outlineApi.updateNode(projectId, nodeId, data)
    await fetchOutline(projectId)
  }

  /** 删除节点 */
  async function deleteNode(projectId: string, nodeId: string) {
    await outlineApi.deleteNode(projectId, nodeId)
    await fetchOutline(projectId)
  }

  return {
    outlineTree,
    loading,
    generating,
    fetchOutline,
    generateOutline,
    chatRefine,
    addNode,
    updateNode,
    deleteNode,
  }
})
