<script setup lang="ts">
/**
 * 项目列表页
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const store = useProjectStore()

const showCreate = ref(false)
const newProject = ref({
  name: '',
  project_type: '',
  project_scale: '',
  project_info: '',
})

onMounted(() => {
  store.fetchProjects()
})

async function handleCreate() {
  if (!newProject.value.name.trim()) return
  const project = await store.createProject(newProject.value)
  showCreate.value = false
  router.push({ name: 'Import', params: { id: project.id } })
}

function handleDelete(id: string) {
  if (confirm('确认删除此项目？')) {
    store.deleteProject(id)
  }
}
</script>

<template>
  <div class="project-list-page">
    <header class="page-header">
      <div>
        <h1>奇易AI编标</h1>
        <p class="subtitle">施工行业技术标智能编制系统</p>
      </div>
      <button class="btn btn-primary" @click="showCreate = true">
        + 新建项目
      </button>
    </header>

    <!-- 创建项目对话框 -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-panel">
        <h3>新建项目</h3>
        <div class="form-group">
          <label>项目名称 <span class="required">*</span></label>
          <input v-model="newProject.name" placeholder="请输入项目名称" class="form-input" />
        </div>
        <div class="form-group">
          <label>工程类型</label>
          <input v-model="newProject.project_type" placeholder="如：建筑工程、市政工程" class="form-input" />
        </div>
        <div class="form-group">
          <label>建设规模</label>
          <input v-model="newProject.project_scale" placeholder="如：建筑面积50000㎡" class="form-input" />
        </div>
        <div class="form-group">
          <label>项目概况</label>
          <textarea v-model="newProject.project_info" placeholder="简要描述项目概况…" class="form-textarea" rows="3" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="handleCreate" :disabled="!newProject.name.trim()">创建</button>
        </div>
      </div>
    </div>

    <!-- 项目列表 -->
    <div v-if="store.loading" class="loading-state">加载中…</div>

    <div v-else-if="!store.projects.length" class="empty-state">
      <p>暂无项目，点击上方按钮创建第一个项目</p>
    </div>

    <div v-else class="project-grid">
      <div
        v-for="project in store.projects" :key="project.id"
        class="project-card"
        @click="router.push({ name: 'Import', params: { id: project.id } })"
      >
        <div class="card-header">
          <h3>{{ project.name }}</h3>
          <span class="status-badge" :class="project.status">{{ project.status }}</span>
        </div>
        <div class="card-meta">
          <span v-if="project.project_type">{{ project.project_type }}</span>
          <span v-if="project.project_scale">{{ project.project_scale }}</span>
        </div>
        <div class="card-footer">
          <span class="card-time">{{ new Date(project.updated_at).toLocaleDateString('zh-CN') }}</span>
          <button class="btn-ghost btn-sm" @click.stop="handleDelete(project.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.project-list-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 28px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-top: 4px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px;
  width: 480px;
  max-width: 90vw;
}

.modal-panel h3 {
  font-size: 18px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-family: var(--font-mono);
}

.required { color: var(--red); }

.form-input,
.form-textarea {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  padding: 10px 12px;
  font-family: var(--font-display);
  font-size: 13px;
  outline: none;
  transition: border-color .2s;
}

.form-input:focus,
.form-textarea:focus {
  border-color: rgba(212, 168, 83, 0.35);
}

.form-textarea { resize: vertical; }

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* Grid */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.project-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  cursor: pointer;
  transition: all .2s;
}

.project-card:hover {
  border-color: rgba(212, 168, 83, 0.25);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.status-badge {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--surface-3);
  color: var(--text-muted);
}

.card-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 16px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-time {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 14px;
}
</style>
