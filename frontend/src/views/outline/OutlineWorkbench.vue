<script setup lang="ts">
/**
 * 大纲工作台 - 核心页面
 * 功能：项目概况编辑、大纲树展示、AI对话调整、内容预览
 */
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useOutlineStore } from '@/stores/outline'
import { projectApi } from '@/api/project'
import { outlineApi } from '@/api/outline'
import type { OutlineNode } from '@/types'
import OutlineTreeNode from '@/components/outline/OutlineTreeNode.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id as string
const projectStore = useProjectStore()
const outlineStore = useOutlineStore()

// ── 项目概况 ──
const projectInfo = ref('')
const savingInfo = ref(false)

onMounted(async () => {
  await projectStore.fetchProject(projectId)
  projectInfo.value = projectStore.currentProject?.project_info || ''
  // 始终加载已有大纲
  await outlineStore.fetchOutline(projectId)
})

async function saveProjectInfo() {
  savingInfo.value = true
  try {
    await projectApi.update(projectId, { project_info: projectInfo.value })
  } finally {
    savingInfo.value = false
  }
}

// ── 大纲生成 ──
const generating = ref(false)
const additionalReqs = ref('')

async function handleGenerate() {
  generating.value = true
  try {
    await outlineStore.generateOutline(projectId,
      additionalReqs.value || undefined
    )
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
    alert(msg)
  } finally {
    generating.value = false
    nextTick(() => { /* scroll to outline */ })
  }
}

// ── 大纲对话 ──
const chatMessages = ref<{ role: string; content: string }[]>([])
const chatInput = ref('')
const chatting = ref(false)

async function sendChat() {
  if (!chatInput.value.trim()) return
  const msg = chatInput.value
  chatMessages.value.push({ role: 'user', content: msg })
  chatInput.value = ''
  chatting.value = true

  try {
    const result = await outlineStore.chatRefine(projectId, msg)
    const reply = result?.message || '大纲已更新'
    chatMessages.value.push({ role: 'assistant', content: reply })
  } catch (e: unknown) {
    const errMsg = (e as Error).message || '对话失败'
    chatMessages.value.push({ role: 'assistant', content: `抱歉，出错了：${errMsg}` })
  } finally {
    chatting.value = false
  }
}

// ── 节点编辑 ──
const editingNodeId = ref<string | null>(null)

function startEdit(node: OutlineNode) {
  editingNodeId.value = node.id
}

async function saveEdit(nodeId: string, title: string) {
  if (!title.trim()) return
  await outlineStore.updateNode(projectId, nodeId, { title })
  editingNodeId.value = null
}

async function deleteNode(nodeId: string) {
  if (!confirm('确认删除此节点及其子节点？')) return
  await outlineStore.deleteNode(projectId, nodeId)
}

function addChildNode(parentId: string | null, level: number) {
  outlineStore.addNode(projectId, {
    parent_id: parentId,
    level: Math.min(level, 4),
    title: '新章节',
    sort_order: 999,
  })
}

// ── 单节生成 ──
const genNodeId = ref<string | null>(null)
const toastMsg = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(msg: string) {
  toastMsg.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 2500)
}

async function handleGenerateContent(node: OutlineNode) {
  genNodeId.value = node.id
  try {
    const res = await outlineApi.generateSection(projectId, node.id)
    const content = res.data.data.content
    showToast('内容已生成（' + res.data.data.word_count + ' 字）')
    // 更新右侧预览
    if (selectedNode.value?.id === node.id) {
      nodeContent.value = content
      nodeContentLoaded.value = true
    }
  } catch (e: unknown) {
    const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
    showToast('生成失败: ' + msg)
  } finally {
    genNodeId.value = null
  }
}

// ── 右侧预览编辑 ──
const selectedNode = ref<OutlineNode | null>(null)
const nodeContent = ref('')
const nodeContentLoaded = ref(false)
const loadingContent = ref(false)
const editingContent = ref(false)
const savingContent = ref(false)

async function handleSelectNode(node: OutlineNode) {
  selectedNode.value = node
  editingContent.value = false
  loadingContent.value = true
  nodeContent.value = ''

  try {
    // 通过 compose 获取初稿，从中提取该章节内容
    const res = await outlineApi.compose(projectId)
    const draft = res.data.data.draft || ''
    if (draft && node) {
      const title = node.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const marker = '#'.repeat(Math.min(node.level + 1, 6))
      const pattern = new RegExp(`${marker} ${title}\\n([\\s\\S]*?)(?=\\n#{1,6} |$)`)
      const match = draft.match(pattern)
      nodeContent.value = match ? match[1].trim() : ''
    }
  } catch {
    nodeContent.value = ''
  } finally {
    loadingContent.value = false
    nodeContentLoaded.value = true
  }
}

async function loadNodeContent(nodeId: string) {
  loadingContent.value = true
  try {
    const res = await outlineApi.compose(projectId)
    const draft = res.data.data.draft || ''
    if (selectedNode.value && draft) {
      const title = selectedNode.value.title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const marker = '#'.repeat(Math.min(selectedNode.value.level + 1, 6))
      const pattern = new RegExp(`${marker} ${title}\\n([\\s\\S]*?)(?=\\n#{1,6} |$)`)
      const match = draft.match(pattern)
      nodeContent.value = match ? match[1].trim() : ''
    }
    nodeContentLoaded.value = true
  } catch {
    nodeContent.value = ''
    nodeContentLoaded.value = true
  } finally {
    loadingContent.value = false
  }
}

async function saveContent() {
  if (!selectedNode.value) return
  savingContent.value = true
  try {
    // 调用生成接口覆盖内容
    await outlineApi.generateSection(projectId, selectedNode.value.id)
    editingContent.value = false
  } finally {
    savingContent.value = false
  }
}

// ── 展开/折叠 ──
const expandedIds = ref<Set<string>>(new Set())

function toggleExpand(nodeId: string) {
  if (expandedIds.value.has(nodeId)) {
    expandedIds.value.delete(nodeId)
  } else {
    expandedIds.value.add(nodeId)
  }
}

// ── 锁定大纲 ──
async function lockOutline() {
  // 将所有节点状态设为 confirmed
  for (const node of flattenNodes(outlineStore.outlineTree)) {
    await outlineStore.updateNode(projectId, node.id, { status: 'confirmed' })
  }
  router.push({ name: 'Generate', params: { id: projectId } })
}

function flattenNodes(nodes: OutlineNode[]): OutlineNode[] {
  return nodes.flatMap(n => [n, ...flattenNodes(n.children || [])])
}

const hasOutline = computed(() => outlineStore.outlineTree.length > 0)
</script>

<template>
  <div class="outline-workbench">
    <!-- ── 顶部：项目概况 + 操作栏 ── -->
    <section class="project-info-section">
      <div class="section-label">
        📋 项目概况
        <span class="label-hint">所有AI生成内容均会参考此信息</span>
      </div>
      <textarea
        v-model="projectInfo" class="info-textarea"
        placeholder="输入项目背景、工程概况、招标要求等…"
        @blur="saveProjectInfo"
      />
      <span class="save-indicator" v-if="savingInfo">保存中…</span>
    </section>

    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-primary" :disabled="generating" @click="handleGenerate">
          <span v-if="generating" class="spinner"></span>
          {{ generating ? 'AI 生成中…' : '🤖 AI生成大纲' }}
        </button>
        <input v-model="additionalReqs" class="reqs-input"
          placeholder="额外要求（可选）" :disabled="generating" @keydown.enter="handleGenerate" />
      </div>
      <button v-if="hasOutline" class="btn btn-success btn-sm" @click="lockOutline">
        ✅ 确认大纲，下一阶段 →
      </button>
    </div>

    <!-- ── 主区域：左大纲树 + 右预览编辑 ── -->
    <div class="main-area">
      <!-- 左：大纲树 + 对话 -->
      <div class="left-panel">
        <!-- 加载中 -->
        <div v-if="generating && !hasOutline" class="loading-section">
          <span class="spinner-lg"></span>
          <p>AI 正在分析招标文件并生成大纲…</p>
          <span class="loading-sub">请稍候，这可能需要 10-30 秒</span>
        </div>

        <!-- 大纲树 -->
        <div v-else-if="hasOutline" class="outline-section">
          <h3 class="section-title">📑 大纲结构（共 {{ flattenNodes(outlineStore.outlineTree).length }} 节）</h3>
          <div class="outline-tree">
            <template v-for="node in outlineStore.outlineTree" :key="node.id">
              <OutlineTreeNode
                :node="node" :depth="0" :expanded-ids="expandedIds"
                :editing-node-id="editingNodeId"
                :generating-node-id="genNodeId"
                @toggle="toggleExpand" @select="handleSelectNode"
                @start-edit="startEdit" @save-edit="saveEdit"
                @delete-node="deleteNode" @add-child="addChildNode"
                @generate-content="handleGenerateContent"
              />
            </template>
          </div>

          <!-- 对话调整 -->
          <div class="chat-section">
            <h4>💬 对话调整大纲</h4>
            <div class="chat-messages">
              <div v-for="(msg, i) in chatMessages" :key="i" class="chat-msg" :class="msg.role">
                <span class="msg-role">{{ msg.role === 'user' ? '👤' : '🤖' }}</span>
                <span class="msg-content">{{ msg.content }}</span>
              </div>
              <div v-if="chatting" class="chat-msg assistant">
                <span class="msg-role">🤖</span>
                <span class="msg-content typing"><span class="spinner-sm"></span> 思考中…</span>
              </div>
            </div>
            <div class="chat-input-row">
              <input v-model="chatInput" class="chat-input"
                placeholder="如：增加绿色施工章节，合并安全和文明施工"
                :disabled="chatting" @keydown.enter="sendChat" />
              <button class="btn btn-primary btn-sm" :disabled="chatting || !chatInput.trim()" @click="sendChat">发送</button>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <p>点击 "AI生成大纲" 开始</p>
          <span class="empty-hint">基于招标文档和项目概况自动生成技术标大纲</span>
        </div>
      </div>

      <!-- 右：内容预览编辑 -->
      <div class="right-panel">
        <template v-if="selectedNode">
          <div class="preview-header">
            <h3>{{ selectedNode.title }}</h3>
            <span class="preview-level">H{{ selectedNode.level }}</span>
            <button class="btn-ghost btn-sm" @click="selectedNode = null">✕</button>
          </div>

          <div class="preview-body">
            <!-- 加载中 -->
            <div v-if="loadingContent" class="preview-loading">
              <span class="spinner"></span> 加载中…
            </div>

            <!-- 无内容 -->
            <div v-else-if="!nodeContent" class="preview-empty">
              <p>该章节暂无内容</p>
              <button class="btn btn-primary btn-sm" @click="handleGenerateContent(selectedNode)">
                ⚡ AI 生成此节内容
              </button>
            </div>

            <!-- 有内容 -->
            <template v-else>
              <div v-if="!editingContent" class="preview-text">
                {{ nodeContent }}
              </div>
              <textarea
                v-else
                v-model="nodeContent"
                class="preview-editor"
                rows="15"
              />
            </template>
          </div>

          <div v-if="nodeContent" class="preview-footer">
            <span class="preview-wc">{{ nodeContent.replace(/\s/g, '').length }} 字</span>
            <div class="preview-actions">
              <button v-if="!editingContent" class="btn btn-ghost btn-sm" @click="editingContent = true">✏️ 编辑</button>
              <button v-else class="btn btn-primary btn-sm" :disabled="savingContent" @click="saveContent">
                <span v-if="savingContent" class="spinner"></span> 保存
              </button>
              <button class="btn btn-primary btn-sm" @click="handleGenerateContent(selectedNode)">
                ⚡ {{ nodeContent ? '重新生成' : 'AI生成' }}
              </button>
            </div>
          </div>
        </template>

        <div v-else class="preview-placeholder">
          <p>👈 点击左侧大纲节点<br>查看和编辑内容</p>
        </div>
      </div>
    </div>

    <!-- Toast 提示 -->
    <div v-if="toastMsg" class="toast">{{ toastMsg }}</div>
  </div>
</template>

<style scoped>
.outline-workbench {
  padding: 20px 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── 项目概况 ── */
.project-info-section {
  background: linear-gradient(135deg, var(--accent-glow), rgba(90, 70, 160, 0.04));
  border: 1px solid rgba(212, 168, 83, 0.15);
  border-radius: var(--radius);
  padding: 12px 16px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  font-family: var(--font-mono);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.label-hint { font-size: 10px; color: var(--text-muted); font-weight: 400; }

.info-textarea {
  width: 100%;
  min-height: 50px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 168, 83, 0.12);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: 12px;
  line-height: 1.6;
  padding: 8px 10px;
  resize: vertical;
  outline: none;
}

.info-textarea:focus { border-color: rgba(212, 168, 83, 0.35); }

.save-indicator {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent);
}

/* ── 工具栏 ── */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.reqs-input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  padding: 7px 10px;
  font-family: var(--font-display);
  font-size: 12px;
  outline: none;
}

.reqs-input:focus { border-color: rgba(212, 168, 83, 0.3); }
.reqs-input::placeholder { color: var(--text-muted); font-size: 11px; }

/* ── 主区域：两栏 ── */
.main-area {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

.left-panel {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.right-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 300px;
}

/* ── 大纲 ── */
.outline-section { flex: 1; }

.section-title {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  margin-bottom: 8px;
}

.outline-tree {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px;
  max-height: 400px;
  overflow-y: auto;
}

/* ── 对话 ── */
.chat-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
}

.chat-section h4 { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }

.chat-messages {
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 8px;
}

.chat-msg {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 12px;
  line-height: 1.5;
}

.chat-msg.user .msg-content { color: var(--blue); }
.chat-msg.assistant .msg-content { color: var(--text-primary); }
.msg-role { flex-shrink: 0; }
.typing { opacity: .6; }

.chat-input-row { display: flex; gap: 6px; }

.chat-input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 5px;
  color: var(--text-primary);
  padding: 6px 10px;
  font-family: var(--font-display);
  font-size: 12px;
  outline: none;
}

.chat-input:focus { border-color: rgba(212, 168, 83, 0.3); }

/* ── 右侧预览 ── */
.preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
}

.preview-header h3 {
  flex: 1;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preview-level {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--surface-3);
  color: var(--text-muted);
}

.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.preview-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 13px;
  justify-content: center;
  padding: 40px;
}

.preview-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.preview-empty p { margin-bottom: 12px; font-size: 13px; }

.preview-text {
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.preview-editor {
  width: 100%;
  min-height: 200px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: 13px;
  line-height: 1.7;
  padding: 12px;
  resize: vertical;
  outline: none;
}

.preview-editor:focus { border-color: rgba(212, 168, 83, 0.3); }

.preview-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-top: 1px solid var(--border);
  background: var(--surface-2);
}

.preview-wc {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}

.preview-actions { display: flex; gap: 6px; }

.preview-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.8;
}

/* ── 空状态 ── */
.empty-state {
  text-align: center;
  padding: 40px;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
}

.empty-state p { font-size: 14px; color: var(--text-secondary); }

.empty-hint {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  display: block;
}

/* ── 加载动画 ── */
.spinner, .spinner-sm, .spinner-lg {
  display: inline-block;
  border-radius: 50%;
  animation: spin .6s linear infinite;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
}
.spinner { width: 16px; height: 16px; }

.spinner-sm { width: 12px; height: 12px; border-width: 1.5px; }

.spinner-lg { width: 32px; height: 32px; border-width: 3px; margin-bottom: 12px; }

@keyframes spin { to { transform: rotate(360deg); } }

.toast {
  position: fixed; bottom: 24px; left: 50%;
  transform: translateX(-50%);
  background: var(--surface-3); color: var(--text-primary);
  padding: 10px 22px; border-radius: 8px;
  font-size: 12px; font-family: var(--font-mono);
  border: 1px solid var(--border); z-index: 999;
  box-shadow: 0 4px 20px rgba(0,0,0,.4);
  animation: fadeUp .3s ease;
}
@keyframes fadeUp { from { opacity:0; transform: translateX(-50%) translateY(10px); } }

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  text-align: center;
}

.loading-section p { font-size: 14px; color: var(--text-secondary); }

.loading-sub {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>
