<script setup lang="ts">
/**
 * 章节生成卡片组件
 */
import { computed } from 'vue'
import type { OutlineNode } from '@/types'

const props = defineProps<{
  node: OutlineNode
  generatingId: string | null
  streamingContent: string
  sectionContents: Map<string, { content: string; status: string; wordCount: number }>
}>()

const emit = defineEmits<{
  'generate': [node: OutlineNode]
  'view-content': [node: OutlineNode]
}>()

const contentData = computed(() => props.sectionContents.get(props.node.id))
const status = computed(() => contentData.value?.status || 'pending')
const isGenerating = computed(() => props.generatingId === props.node.id)
const isDone = computed(() => status.value === 'done')
const content = computed(() => contentData.value?.content || '')
const wordCount = computed(() => contentData.value?.wordCount || 0)

const statusText = computed(() => {
  switch (status.value) {
    case 'generating': return '生成中…'
    case 'done': return '已完成'
    case 'error': return '失败'
    default: return '待生成'
  }
})

const statusClass = computed(() => `status-${status.value}`)

function handleClick() {
  if (isDone.value && content.value) {
    emit('view-content', props.node)
  }
}
</script>

<template>
  <div class="section-card" :class="[`level-${Math.min(node.level, 4)}`, statusClass]">
    <div class="card-main" @click="handleClick">
      <div class="card-bar" />
      <div class="card-info">
        <span class="card-title">{{ node.title }}</span>
        <span class="card-level">H{{ node.level }}</span>
      </div>
      <div class="card-status">
        <span v-if="isGenerating" class="status-generating">
          <span class="spinner-sm"></span> 生成中…
        </span>
        <span v-else class="status-badge" :class="statusClass">{{ statusText }}</span>
        <span v-if="isDone" class="word-count">{{ wordCount }}字</span>
      </div>
      <div class="card-actions">
        <button
          class="gen-btn"
          :class="{ generating: isGenerating }"
          :disabled="isGenerating"
          @click.stop="emit('generate', node)"
        >
          <span v-if="isGenerating" class="spinner-xs"></span>
          {{ isGenerating ? '生成中…' : isDone ? '重新生成' : 'AI生成' }}
        </button>
      </div>
    </div>
    <!-- 流式预览 -->
    <div v-if="isGenerating && streamingContent" class="card-stream-preview">
      <pre>{{ streamingContent.slice(-300) }}</pre>
    </div>
  </div>
</template>

<style scoped>
.section-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color .2s;
}

.section-card:hover { border-color: var(--border-light); }

.card-main {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
}

.card-bar {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
  align-self: stretch;
  min-height: 20px;
}

.level-1 .card-bar { background: var(--accent); }
.level-2 .card-bar { background: var(--accent-dim); }
.level-3 .card-bar { background: var(--text-muted); }
.level-4 .card-bar { background: var(--border-light); }

.card-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.card-title {
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.level-1 .card-title { font-size: 15px; font-weight: 700; }

.card-level {
  font-family: var(--font-mono);
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--surface-3);
  color: var(--text-muted);
  flex-shrink: 0;
}

.card-status {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.status-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-pending { color: var(--text-muted); background: var(--surface-3); }
.status-generating { color: var(--accent); background: var(--accent-glow); }
.status-done { color: var(--green); background: var(--green-glow); }
.status-error { color: var(--red); background: rgba(212, 83, 83, 0.1); }

.word-count {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}

.status-generating {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ── 转圈动画 ── */
.spinner-xs,
.spinner-sm {
  display: inline-block;
  border-radius: 50%;
  animation: spin .6s linear infinite;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
}

.spinner-xs { width: 10px; height: 10px; border-width: 1.5px; }
.spinner-sm { width: 14px; height: 14px; border-width: 2px; }

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: .3; }
  40% { transform: translateY(-4px); opacity: 1; }
}

.card-actions { flex-shrink: 0; }

.gen-btn {
  padding: 5px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--surface-3);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
  transition: all .2s;
}

.gen-btn:hover { color: var(--accent); border-color: rgba(212, 168, 83, 0.3); background: var(--accent-glow); }
.gen-btn:disabled { opacity: .4; cursor: not-allowed; }
.gen-btn.generating { color: var(--accent); }

.card-stream-preview {
  padding: 8px 14px 12px;
  border-top: 1px solid var(--border);
  background: var(--surface-2);
}

.card-stream-preview pre {
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.6;
  color: var(--text-muted);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 100px;
  overflow-y: auto;
}
</style>
