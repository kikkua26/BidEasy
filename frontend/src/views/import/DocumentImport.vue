<script setup lang="ts">
/**
 * 导入招文页面
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { documentApi } from '@/api/document'
import { useProjectStore } from '@/stores/project'
import type { DocumentItem, DocumentParseResult } from '@/types'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const projectStore = useProjectStore()

const documents = ref<DocumentItem[]>([])
const uploading = ref(false)
const manualText = ref('')
const inputMode = ref<'upload' | 'manual'>('upload')
const previewDoc = ref<DocumentParseResult | null>(null)

onMounted(() => {
  projectStore.fetchProject(projectId)
  loadDocuments()
})

async function loadDocuments() {
  try {
    const res = await documentApi.list(projectId)
    documents.value = res.data.data as DocumentItem[]
  } catch { /* ignore */ }
}

async function handleUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  uploading.value = true
  try {
    const res = await documentApi.upload(projectId, file)
    previewDoc.value = res.data.data as DocumentParseResult
    await loadDocuments()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '上传失败'
    alert(msg)
  } finally {
    uploading.value = false
  }
}

async function handleManualInput() {
  if (!manualText.value.trim()) return

  uploading.value = true
  try {
    const res = await documentApi.inputText(projectId, manualText.value)
    previewDoc.value = res.data.data as DocumentParseResult
    await loadDocuments()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '输入失败'
    alert(msg)
  } finally {
    uploading.value = false
  }
}

async function handleDelete(docId: string) {
  try {
    await documentApi.delete(projectId, docId)
    await loadDocuments()
    if (previewDoc.value && documents.value.length === 0) {
      previewDoc.value = null
    }
  } catch { /* ignore */ }
}

function goNext() {
  router.push({ name: 'Outline', params: { id: projectId } })
}
</script>

<template>
  <div class="import-page">
    <div class="page-top">
      <div>
        <h2>导入招标文件</h2>
        <p class="desc">上传PDF/Word文件或手动粘贴招标文本</p>
      </div>
      <button class="btn btn-primary" :disabled="!documents.length" @click="goNext">
        下一步：大纲工作台 →
      </button>
    </div>

    <!-- 输入方式切换 -->
    <div class="mode-tabs">
      <button
        :class="{ active: inputMode === 'upload' }"
        @click="inputMode = 'upload'"
      >📎 文件上传</button>
      <button
        :class="{ active: inputMode === 'manual' }"
        @click="inputMode = 'manual'"
      >📝 手动输入</button>
    </div>

    <!-- 文件上传统 -->
    <div v-if="inputMode === 'upload'" class="upload-section">
      <div class="upload-zone" :class="{ uploading }">
        <input
          type="file" accept=".pdf,.docx,.doc,.txt"
          class="file-input" @change="handleUpload" :disabled="uploading"
        />
        <p>{{ uploading ? '正在解析…' : '点击上传或拖拽文件到此处' }}</p>
        <span class="upload-hint">支持 PDF / Word / TXT，最大 50MB</span>
      </div>
    </div>

    <!-- 手动输入模式 -->
    <div v-if="inputMode === 'manual'" class="manual-section">
      <textarea
        v-model="manualText"
        placeholder="在此粘贴招标文件的文本内容…&#10;支持 Markdown 格式"
        class="manual-textarea"
        :disabled="uploading"
      />
      <div class="manual-bar">
        <span class="char-count">{{ manualText.length }} 字</span>
        <button
          class="btn btn-primary btn-sm"
          :disabled="!manualText.trim() || uploading"
          @click="handleManualInput"
        >
          {{ uploading ? '处理中…' : '提交处理' }}
        </button>
      </div>
    </div>

    <!-- 已导入文档列表 -->
    <div v-if="documents.length" class="doc-list">
      <h4>已导入文档（{{ documents.length }}）</h4>
      <div v-for="doc in documents" :key="doc.id" class="doc-item">
        <div class="doc-info">
          <span class="doc-name">{{ doc.file_name }}</span>
          <span class="doc-type">{{ doc.file_type }}</span>
          <span class="doc-meta">{{ doc.raw_text?.length || 0 }} 字</span>
        </div>
        <button class="btn-ghost btn-sm" @click="handleDelete(doc.id)">删除</button>
      </div>
    </div>

    <!-- 文本预览 -->
    <div v-if="previewDoc" class="preview-section">
      <h4>文本预览</h4>
      <pre class="preview-text">{{ previewDoc.raw_text }}</pre>
    </div>
  </div>
</template>

<style scoped>
.import-page {
  padding: 32px;
  max-width: 1000px;
}

.page-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-top h2 { font-size: 22px; }

.desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; font-family: var(--font-mono); }

/* Mode Tabs */
.mode-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px;
  width: fit-content;
}

.mode-tabs button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  font-family: var(--font-display);
  font-size: 13px;
  cursor: pointer;
  transition: all .2s;
}

.mode-tabs button.active {
  background: var(--surface-3);
  color: var(--text-primary);
}

/* Upload */
.upload-zone {
  background: var(--surface);
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 48px;
  text-align: center;
  position: relative;
  transition: border-color .2s;
}

.upload-zone:hover { border-color: rgba(212, 168, 83, 0.25); }

.upload-zone p {
  font-size: 14px;
  color: var(--text-secondary);
}

.upload-hint {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 8px;
  display: block;
}

.file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

/* Manual */
.manual-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.manual-textarea {
  width: 100%;
  min-height: 300px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.7;
  padding: 16px;
  resize: vertical;
  outline: none;
}

.manual-textarea:focus { border-color: rgba(212, 168, 83, 0.35); }

.manual-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.char-count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

/* Doc List */
.doc-list {
  margin-top: 24px;
}

.doc-list h4 {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 8px;
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.doc-name { font-size: 13px; color: var(--text-primary); }
.doc-type { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); background: var(--surface-3); padding: 2px 6px; border-radius: 3px; }
.doc-meta { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }

/* Preview */
.preview-section {
  margin-top: 24px;
}

.preview-section h4 {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.preview-text {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.8;
  color: var(--text-secondary);
  max-height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
