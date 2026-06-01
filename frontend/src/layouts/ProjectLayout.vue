<script setup lang="ts">
/**
 * 项目编辑主布局
 * 左右两栏：左侧导航 + 右侧内容区
 */
import { computed } from 'vue'
import { useRoute, RouterView, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => route.params.id as string)

// 初始化加载项目
projectStore.fetchProject(projectId.value)

const steps = [
  { step: 1, label: '导入招文', route: 'Import' },
  { step: 2, label: '大纲工作台', route: 'Outline' },
  { step: 3, label: '内容生成', route: 'Generate' },
  { step: 4, label: '审查导出', route: 'Review' },
]

const currentStep = computed(() => {
  const matched = steps.find(s => s.route === route.name)
  return matched?.step || 1
})

const projectName = computed(() => projectStore.currentProject?.name || '加载中...')

function goTo(name: string) {
  router.push({ name, params: { id: projectId.value } })
}
</script>

<template>
  <div class="project-layout">
    <!-- 侧边导航 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2 class="project-name" :title="projectName">{{ projectName }}</h2>
        <span class="project-id">ID: {{ projectId.slice(0, 8) }}</span>
      </div>

      <nav class="sidebar-nav">
        <button
          v-for="item in steps" :key="item.step"
          class="nav-item"
          :class="{ active: currentStep === item.step, completed: currentStep > item.step }"
          @click="goTo(item.route)"
        >
          <span class="nav-step">{{ currentStep > item.step ? '✓' : item.step }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <button class="btn btn-ghost btn-sm" @click="router.push('/projects')">
          ← 返回项目列表
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.project-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  background: var(--bg);
}

.sidebar {
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 20px 0;
  position: sticky;
  top: 0;
  height: 100vh;
}

.sidebar-header {
  padding: 0 20px;
  margin-bottom: 24px;
}

.project-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.project-id {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-size: 13.5px;
  cursor: pointer;
  transition: all .2s;
  text-align: left;
}

.nav-item:hover {
  background: var(--surface-2);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-glow);
  color: var(--accent);
  border: 1px solid rgba(212, 168, 83, 0.18);
}

.nav-item.completed .nav-step {
  background: var(--green-glow);
  color: var(--green);
}

.nav-step {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--surface-3);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border);
}

.main-content {
  overflow-y: auto;
  min-height: 100vh;
}
</style>
