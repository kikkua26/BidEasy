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
import type { OutlineNode } from '@/types'

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

  if (projectStore.currentProject?.status !== 'draft') {
    await outlineStore.fetchOutline(projectId)
  }
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
const editTitle = ref('')

function startEdit(node: OutlineNode) {
  editingNodeId.value = node.id
  editTitle.value = node.title
}

async function saveEdit(nodeId: string) {
  if (!editTitle.value.trim()) return
  await outlineStore.updateNode(projectId, nodeId, { title: editTitle.value })
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
    <!-- ── 共享概况 ── -->
    <section class="project-info-section">
      <div class="section-label">
        📋 项目概况
        <span class="label-hint">所有AI生成内容均会参考此信息</span>
      </div>
      <div class="info-row">
        <textarea
          v-model="projectInfo"
          class="info-textarea"
          placeholder="输入项目背景、工程概况、招标要求等关键信息…&#10;&#10;例如：&#10;• 项目名称：XX市XX路市政工程&#10;• 工程规模：全长3.2km，双向六车道&#10;• 主要施工内容：路基、路面、排水、照明、绿化&#10;• 工期要求：540日历天&#10;• 质量目标：确保优良工程"
          @blur="saveProjectInfo"
        />
        <span class="save-indicator" v-if="savingInfo">保存中…</span>
      </div>
    </section>

    <!-- ── 操作栏 ── -->
    <div class="toolbar">
      <div class="toolbar-left">
        <button
          class="btn btn-primary"
          :disabled="generating"
          @click="handleGenerate"
        >
          {{ generating ? '⚡ 生成中…' : '🤖 AI生成大纲' }}
        </button>
        <input
          v-model="additionalReqs"
          class="reqs-input"
          placeholder="额外要求（可选）：如「重点突出安全管理章节」"
          :disabled="generating"
          @keydown.enter="handleGenerate"
        />
      </div>
      <div class="toolbar-right">
        <button
          v-if="hasOutline"
          class="btn btn-success btn-sm"
          @click="lockOutline"
        >
          ✅ 确认大纲，开始生成
        </button>
      </div>
    </div>

    <!-- ── 大纲树 ── -->
    <div v-if="hasOutline" class="outline-section">
      <h3 class="section-title">📑 大纲结构（共 {{ flattenNodes(outlineStore.outlineTree).length }} 节）</h3>

      <div class="outline-tree">
        <template v-for="node in outlineStore.outlineTree" :key="node.id">
          <OutlineTreeNode
            :node="node"
            :depth="0"
            :expanded-ids="expandedIds"
            :editing-node-id="editingNodeId"
            :edit-title="editTitle"
            @toggle="toggleExpand"
            @start-edit="startEdit"
            @save-edit="saveEdit"
            @delete-node="deleteNode"
            @add-child="addChildNode"
          />
        </template>
      </div>
    </div>

    <!-- ── 空状态 ── -->
    <div v-else class="empty-state">
      <p>点击 "AI生成大纲" 开始</p>
      <span class="empty-hint">基于招标文档和项目概况自动生成技术标大纲</span>
    </div>

    <!-- ── 对话调整 ── -->
    <div v-if="hasOutline" class="chat-section">
      <h3 class="section-title">💬 大纲对话调整</h3>
      <div class="chat-messages">
        <div
          v-for="(msg, i) in chatMessages" :key="i"
          class="chat-msg"
          :class="msg.role"
        >
          <span class="msg-role">{{ msg.role === 'user' ? '👤' : '🤖' }}</span>
          <span class="msg-content">{{ msg.content }}</span>
        </div>
        <div v-if="chatting" class="chat-msg assistant">
          <span class="msg-role">🤖</span>
          <span class="msg-content typing">思考中…</span>
        </div>
      </div>
      <div class="chat-input-row">
        <input
          v-model="chatInput"
          class="chat-input"
          placeholder="输入修改意见，如：增加一个绿色施工章节，合并安全管理和文明施工"
          :disabled="chatting"
          @keydown.enter="sendChat"
        />
        <button class="btn btn-primary btn-sm" :disabled="chatting || !chatInput.trim()" @click="sendChat">
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.outline-workbench {
  padding: 28px 32px;
  max-width: 960px;
}

/* ── 项目概况 ── */
.project-info-section {
  background: linear-gradient(135deg, var(--accent-glow), rgba(90, 70, 160, 0.04));
  border: 1px solid rgba(212, 168, 83, 0.15);
  border-radius: var(--radius);
  padding: 18px 20px;
  margin-bottom: 20px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  font-family: var(--font-mono);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.label-hint {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 400;
}

.info-textarea {
  width: 100%;
  min-height: 80px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(212, 168, 83, 0.12);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-display);
  font-size: 13px;
  line-height: 1.7;
  padding: 12px 14px;
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
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.reqs-input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  padding: 8px 12px;
  font-family: var(--font-display);
  font-size: 12px;
  outline: none;
}

.reqs-input:focus { border-color: rgba(212, 168, 83, 0.3); }
.reqs-input::placeholder { color: var(--text-muted); font-size: 11px; }

/* ── 大纲 ── */
.outline-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  margin-bottom: 12px;
}

.outline-tree {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px;
}

/* ── 空状态 ── */
.empty-state {
  text-align: center;
  padding: 60px;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
}

.empty-state p {
  font-size: 15px;
  color: var(--text-secondary);
}

.empty-hint {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
  display: block;
}

/* ── 对话 ── */
.chat-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.chat-messages {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.chat-msg {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  line-height: 1.6;
}

.chat-msg.user .msg-content {
  color: var(--blue);
}

.chat-msg.assistant .msg-content {
  color: var(--text-primary);
}

.msg-role { flex-shrink: 0; }

.typing { opacity: .6; animation: pulse 1.5s ease infinite; }

.chat-input-row {
  display: flex;
  gap: 8px;
}

.chat-input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  padding: 8px 12px;
  font-family: var(--font-display);
  font-size: 13px;
  outline: none;
}

.chat-input:focus { border-color: rgba(212, 168, 83, 0.3); }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }
</style>
</template>
