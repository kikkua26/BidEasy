<script setup lang="ts">
/**
 * 大纲树节点组件（递归）
 */
import { ref, watch, computed } from 'vue'
import type { OutlineNode } from '@/types'

const props = defineProps<{
  node: OutlineNode
  depth: number
  expandedIds: Set<string>
  editingNodeId: string | null
}>()

const emit = defineEmits<{
  'toggle': [nodeId: string]
  'select': [node: OutlineNode]
  'start-edit': [node: OutlineNode]
  'save-edit': [nodeId: string, title: string]
  'delete-node': [nodeId: string]
  'add-child': [parentId: string | null, level: number]
  'generate-content': [node: OutlineNode]
}>()

const localEditTitle = ref('')

// 进入编辑模式时初始化本地编辑值
watch(() => props.editingNodeId, (id) => {
  if (id === props.node.id) {
    localEditTitle.value = props.node.title
  }
})

const isExpanded = computed(() => props.expandedIds.has(props.node.id))
const isEditing = computed(() => props.editingNodeId === props.node.id)
const hasChildren = computed(() => props.node.children && props.node.children.length > 0)
const nextLevel = computed(() => Math.min(props.node.level + 1, 4))

const levelClass = computed(() => `level-${Math.min(props.node.level, 4)}`)
const statusClass = computed(() => props.node.status)

function handleSave() {
  if (localEditTitle.value.trim()) {
    emit('save-edit', props.node.id, localEditTitle.value)
  }
}
</script>

<template>
  <div class="outline-node" :class="[levelClass, statusClass]">
    <div class="node-header">
      <div class="node-bar" :style="{ marginLeft: depth * 24 + 'px' }" />

      <span v-if="hasChildren" class="node-toggle" :class="{ expanded: isExpanded }" @click="emit('toggle', node.id)">▶</span>
      <span v-else class="node-toggle-spacer" />

      <div class="node-info" @click="emit('select', node)">
        <span v-if="!isEditing" class="node-title">{{ node.title }}</span>
        <input
          v-else
          v-model="localEditTitle"
          class="node-edit-input"
          @blur="handleSave"
          @keydown.enter="handleSave"
          @click.stop
          autofocus
        />
        <span class="node-level-badge">H{{ node.level }}</span>
      </div>

      <div class="node-actions" @click.stop>
        <button class="node-btn node-btn-gen" @click="emit('generate-content', node)" title="AI生成此节内容">⚡</button>
        <button v-if="!isEditing" class="node-btn" @click="emit('start-edit', node)" title="编辑">✏️</button>
        <button v-if="node.level < 4" class="node-btn" @click="emit('add-child', node.id, nextLevel)" title="添加子章节">➕</button>
        <button class="node-btn node-btn-delete" @click="emit('delete-node', node.id)" title="删除">🗑️</button>
      </div>
    </div>

    <div v-if="hasChildren && isExpanded" class="node-children">
      <OutlineTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :expanded-ids="expandedIds"
        :editing-node-id="editingNodeId"
        @toggle="emit('toggle', $event)"
        @select="emit('select', $event)"
        @start-edit="emit('start-edit', $event)"
        @save-edit="(nodeId: string, title: string) => emit('save-edit', nodeId, title)"
        @delete-node="emit('delete-node', $event)"
        @add-child="emit('add-child', $event[0], $event[1])"
        @generate-content="emit('generate-content', $event)"
      />
    </div>
  </div>
</template>

<style scoped>
.outline-node { user-select: none; }

.node-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; cursor: pointer; border-radius: 6px;
  transition: background .15s;
}
.node-header:hover { background: var(--surface-2); }

.node-bar {
  width: 3px; min-height: 24px; border-radius: 2px;
  flex-shrink: 0; align-self: stretch;
}
.level-1 .node-bar { background: var(--accent); }
.level-2 .node-bar { background: var(--accent-dim); }
.level-3 .node-bar { background: var(--text-muted); }
.level-4 .node-bar { background: var(--border-light); }

.node-toggle {
  font-size: 10px; color: var(--text-muted);
  transition: transform .2s; flex-shrink: 0;
}
.node-toggle.expanded { transform: rotate(90deg); }
.node-toggle-spacer { width: 14px; flex-shrink: 0; }

.node-info {
  flex: 1; display: flex; align-items: center;
  gap: 8px; min-width: 0;
}

.node-title {
  font-size: 14px; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.level-1 .node-title { font-size: 15px; font-weight: 700; }
.level-3 .node-title { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.level-4 .node-title { font-size: 12.5px; font-weight: 400; color: var(--text-muted); }
.status-confirmed .node-title { color: var(--green); }

.node-edit-input {
  background: var(--bg); border: 1px solid var(--accent);
  border-radius: 4px; color: var(--text-primary);
  font-family: var(--font-display); font-size: 14px;
  padding: 4px 8px; width: 100%; outline: none;
}

.node-level-badge {
  font-family: var(--font-mono); font-size: 9px;
  padding: 1px 5px; border-radius: 3px;
  background: var(--surface-3); color: var(--text-muted); flex-shrink: 0;
}

.node-actions {
  display: flex; gap: 4px; opacity: 0; transition: opacity .15s;
}
.node-header:hover .node-actions { opacity: 1; }

.node-btn {
  padding: 2px 6px; border: none; border-radius: 4px;
  background: transparent; font-size: 12px; cursor: pointer;
  transition: background .15s;
}
.node-btn:hover { background: var(--surface-3); }
.node-btn-gen { color: var(--accent); font-size: 11px; }
.node-btn-gen:hover { background: var(--accent-glow) !important; }
.node-btn-delete:hover { background: rgba(212, 83, 83, 0.15); }
</style>
