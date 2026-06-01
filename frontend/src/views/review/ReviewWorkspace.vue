<script setup lang="ts">
/**
 * 审查导出工作台
 * 功能：初稿预览、审查、导出
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useOutlineStore } from '@/stores/outline'
import { useGenerateStore } from '@/stores/generate'
import { outlineApi } from '@/api/outline'
import type { OutlineNode } from '@/types'

const route = useRoute()
const projectId = route.params.id as string
const projectStore = useProjectStore()
const outlineStore = useOutlineStore()
const generateStore = useGenerateStore()

const draft = ref('')
const draftLoaded = ref(false)
const composing = ref(false)

onMounted(async () => {
  await projectStore.fetchProject(projectId)
  await outlineStore.fetchOutline(projectId)
  await loadDraft()
})

async function loadDraft() {
  composing.value = true
  try {
    // 本地组装（从已有内容）
    draft.value = composeLocal()
    draftLoaded.value = true
  } catch {
    draft.value = '加载失败'
  } finally {
    composing.value = false
  }
}

function composeLocal() {
  const nodes = flattenNodes(outlineStore.outlineTree)
  let text = `# ${projectStore.currentProject?.name || '技术标'}\n\n`
  text += `## 项目概况\n${projectStore.currentProject?.project_info || ''}\n\n`

  for (const node of nodes) {
    const marker = '#'.repeat(Math.min(node.level + 1, 6))
    text += `\n${marker} ${node.title}\n\n`

    const data = generateStore.sectionContents.get(node.id)
    if (data?.content) {
      text += data.content + '\n'
    } else {
      text += '（内容待生成）\n'
    }
  }
  return text
}

function flattenNodes(nodes: OutlineNode[]): OutlineNode[] {
  return nodes.flatMap(n => [n, ...flattenNodes(n.children || [])])
}

function copyDraft() {
  navigator.clipboard.writeText(draft.value)
}

function downloadDraft() {
  const blob = new Blob([draft.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${projectStore.currentProject?.name || '技术标'}.md`
  a.click()
  URL.revokeObjectURL(url)
}

const wordCount = computed(() => draft.value.replace(/\s/g, '').length)
</script>

<template>
  <div class="review-workspace">
    <div class="page-top">
      <div>
        <h2>审查导出</h2>
        <p class="desc">预览初稿，检查内容完整性，导出文档</p>
      </div>
      <div class="top-actions">
        <button class="btn btn-primary" @click="copyDraft">📋 复制全文</button>
        <button class="btn btn-success" @click="downloadDraft">⬇️ 下载 Markdown</button>
      </div>
    </div>

    <!-- 统计 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总字数</span>
        <span class="stat-value">{{ wordCount.toLocaleString() }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">章节数</span>
        <span class="stat-value">{{ flattenNodes(outlineStore.outlineTree).length }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已生成</span>
        <span class="stat-value">{{ generateStore.completedCount }}</span>
      </div>
    </div>

    <!-- 初稿预览 -->
    <div class="draft-section">
      <div class="draft-header">
        <h3>📄 初稿预览</h3>
      </div>
      <div class="draft-body" v-if="draftLoaded">
        <pre class="draft-text">{{ draft }}</pre>
      </div>
      <div v-else class="draft-loading">加载中…</div>
    </div>
  </div>
</template>

<style scoped>
.review-workspace {
  padding: 28px 32px;
  max-width: 1000px;
}

.page-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-top h2 { font-size: 22px; }

.desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; font-family: var(--font-mono); }

.top-actions { display: flex; gap: 8px; }

/* Stats */
.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
}

/* Draft */
.draft-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.draft-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
}

.draft-header h3 { font-size: 14px; }

.draft-body {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.draft-text {
  font-family: var(--font-display);
  font-size: 14px;
  line-height: 1.9;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.draft-loading {
  padding: 60px;
  text-align: center;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
</style>
