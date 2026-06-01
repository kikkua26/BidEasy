/**
 * 内容生成状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { outlineApi } from '@/api/outline'
import type { SectionContent } from '@/types'

export const useGenerateStore = defineStore('generate', () => {
  const sectionContents = ref<Map<string, { content: string; status: string; wordCount: number }>>(new Map())
  const loading = ref(false)
  const generatingAll = ref(false)

  /** 已生成数量 */
  const completedCount = computed(() =>
    Array.from(sectionContents.value.values()).filter(v => v.status === 'done').length
  )

  /** 总数量 */
  const totalCount = computed(() => sectionContents.value.size)

  /** 进度百分比 */
  const progressPercent = computed(() =>
    totalCount.value > 0 ? Math.round(completedCount.value / totalCount.value * 100) : 0
  )

  /** 设置进度总数 */
  function setTotal(outlineIds: string[]) {
    outlineIds.forEach(id => {
      if (!sectionContents.value.has(id)) {
        sectionContents.value.set(id, { content: '', status: 'pending', wordCount: 0 })
      }
    })
  }

  /** 生成单个章节 */
  async function generateSection(projectId: string, outlineId: string, title: string) {
    sectionContents.value.set(outlineId, { content: '', status: 'generating', wordCount: 0 })

    try {
      const res = await outlineApi.generateSection(projectId, outlineId)
      const data = res.data.data
      sectionContents.value.set(outlineId, {
        content: data.content,
        status: 'done',
        wordCount: data.word_count,
      })
      return data
    } catch (e) {
      sectionContents.value.set(outlineId, { content: '', status: 'error', wordCount: 0 })
      throw e
    }
  }

  /** 流式生成章节 */
  function streamSection(projectId: string, outlineId: string, onChunk: (text: string) => void, onDone: () => void) {
    sectionContents.value.set(outlineId, { content: '', status: 'generating', wordCount: 0 })

    const es = outlineApi.streamSection(projectId, outlineId)
    let fullContent = ''

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        switch (data.type) {
          case 'start':
            break
          case 'chunk':
            fullContent += data.text
            sectionContents.value.set(outlineId, {
              content: fullContent,
              status: 'generating',
              wordCount: fullContent.length,
            })
            onChunk(data.text)
            break
          case 'done':
            sectionContents.value.set(outlineId, {
              content: fullContent,
              status: 'done',
              wordCount: data.word_count,
            })
            onDone()
            es.close()
            break
        }
      } catch { /* ignore parse errors */ }
    }

    es.onerror = () => {
      sectionContents.value.set(outlineId, { content: fullContent, status: 'error', wordCount: 0 })
      es.close()
    }

    return es
  }

  /** 加载已有内容 */
  function setContent(outlineId: string, content: string, wordCount = 0) {
    sectionContents.value.set(outlineId, {
      content,
      status: 'done',
      wordCount: wordCount || content.length,
    })
  }

  /** 获取已生成全部文本 */
  const allContent = computed(() => {
    let text = ''
    sectionContents.value.forEach((v, k) => {
      if (v.content) {
        text += v.content + '\n\n'
      }
    })
    return text
  })

  return {
    sectionContents,
    loading,
    generatingAll,
    completedCount,
    totalCount,
    progressPercent,
    allContent,
    setTotal,
    generateSection,
    streamSection,
    setContent,
  }
})
