/**
 * 项目状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectApi } from '@/api/project'
import type { Project } from '@/types'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)

  const projectId = computed(() => currentProject.value?.id || '')

  async function fetchProjects(status?: string) {
    loading.value = true
    try {
      const res = await projectApi.list({ status })
      projects.value = res.data.data.list
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id: string) {
    loading.value = true
    try {
      const res = await projectApi.get(id)
      currentProject.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function createProject(data: {
    name: string
    project_type?: string
    project_scale?: string
    project_info?: string
  }) {
    const res = await projectApi.create(data)
    const project = res.data.data
    projects.value.unshift(project as Project)
    return project as Project
  }

  async function updateProject(id: string, data: Record<string, unknown>) {
    const res = await projectApi.update(id, data)
    currentProject.value = res.data.data as Project
  }

  async function deleteProject(id: string) {
    await projectApi.delete(id)
    projects.value = projects.value.filter(p => p.id !== id)
  }

  return {
    projects,
    currentProject,
    loading,
    projectId,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
  }
})
