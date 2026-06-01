<script setup lang="ts">
/**
 * 内容生成工作台
 * 功能：逐节生成、一键全部生成、实时进度、流式预览
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useOutlineStore } from '@/stores/outline'
import { useGenerateStore } from '@/stores/generate'
import { useProjectStore } from '@/stores/project'
import type { OutlineNode } from '@/types'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const outlineStore = useOutlineStore()
const generateStore = useGenerateStore()
const projectStore = useProjectStore()

onMounted(async () => {
  await outlineStore.fetchOutline(projectId)
  projectStore.fetchProject(projectId)

  // 初始化进度
  const ids = flattenIds(outlineStore.outlineTree)
  generateStore.setTotal(ids)
})

function flattenIds(nodes: OutlineNode[]): string[] {
  return nodes.flatMap(n => [n.id, ...flattenIds(n.children || [])])
}

function flattenNodes(nodes: OutlineNode[]): OutlineNode[] {
  return nodes.flatMap(n => [n, ...flattenNodes(n.children || [])])
}

// ── 单节生成 ──
const generatingId = ref<string | null>(null)
const streamingContent = ref('')

async function generateSingle(node: OutlineNode) {
  generatingId.value = node.id
  streamingContent.value = ''

  try {
    // 使用流式生成
    const es = generateStore.streamSection(
      projectId,
      node.id,
      (chunk) => { streamingContent.value += chunk },
      () => { generatingId.value = null }
    )
  } catch {
    generatingId.value = null
  }
}

// ── 批量生成 ──
const generatingAll = ref(false)

async function generateAll() {
  generatingAll.value = true
  const allNodes = flattenNodes(outlineStore.outlineTree)

  for (const node of allNodes) {
    if (generateStore.sectionContents.get(node.id)?.status === 'done') continue
    try {
      await generateStore.generateSection(projectId, node.id, node.title)
    } catch {
      // 继续下一个
    }
  }

  generatingAll.value = false
}

// ── 组装 ──
async function composeAndReview() {
  router.push({ name: 'Review', params: { id: projectId } })
}

const progressPercent = computed(() => generateStore.progressPercent)
const completedCount = computed(() => generateStore.completedCount)
const totalCount = computed(() => generateStore.totalCount || flattenNodes(outlineStore.outlineTree).length)

// ── 预览 ──
const viewingContent = ref<{ title: string; content: string } | null>(null)

function viewContent(node: OutlineNode) {
  const data = generateStore.sectionContents.get(node.id)
  if (data?.content) {
    viewingContent.value = { title: node.title, content: data.content }
  }
}
</script>

<template>
  <div class="generate-workspace">
    <div class="page-top">
      <div>
        <h2>内容生成</h2>
        <p class="desc">逐节生成或一键批量生成技术标内容</p>
      </div>
      <div class="top-actions">
        <button
          class="btn btn-primary"
          :disabled="generatingAll"
          @click="generateAll"
        >
          {{ generatingAll ? '⚡ 批量生成中…' : '🚀 一键全部生成' }}
        </button>
        <button
          class="btn btn-success"
          :disabled="completedCount < totalCount"
          @click="composeAndReview"
        >
          组装初稿 →
        </button>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-section">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }" />
      </div>
      <span class="progress-text">{{ completedCount }} / {{ totalCount }} 已生成 ({{ progressPercent }}%)</span>
    </div>

    <!-- 章节列表 -->
    <div class="sections-grid">
      <template v-for="node in outlineStore.outlineTree" :key="node.id">
        <SectionCard
          :node="node"
          :generating-id="generatingId"
          :streaming-content="streamingContent"
          :section-contents="generateStore.sectionContents"
          @generate="generateSingle"
          @view-content="viewContent"
        />
      </template>
    </div>

    <!-- 内容预览弹窗 -->
    <div v-if="viewingContent" class="preview-overlay" @click.self="viewingContent = null">
      <div class="preview-panel">
        <div class="preview-header">
          <h3>{{ viewingContent.title }}</h3>
          <button class="btn-ghost btn-sm" @click="viewingContent = null">关闭</button>
        </div>
        <div class="preview-body">
          <div class="preview-markdown">{{ viewingContent.content }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.generate-workspace {
  padding: 28px 32px;
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

/* Progress */
.progress-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #e0b560);
  border-radius: 2px;
  transition: width .3s ease;
  min-width: 2px;
}

.progress-text {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

/* Sections */
.sections-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Preview overlay */
.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.preview-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 800px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.preview-header h3 { font-size: 16px; }

.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.preview-markdown {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
}
</style>
</template>
