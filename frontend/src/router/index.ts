/**
 * 路由配置
 */
import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/projects',
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('@/views/project/ProjectList.vue'),
    meta: { title: '我的项目' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' },
  },
  {
    path: '/project/:id',
    component: () => import('@/layouts/ProjectLayout.vue'),
    children: [
      {
        path: '',
        redirect: { name: 'Outline' },
      },
      {
        path: 'import',
        name: 'Import',
        component: () => import('@/views/import/DocumentImport.vue'),
        meta: { title: '导入招文', step: 1 },
      },
      {
        path: 'outline',
        name: 'Outline',
        component: () => import('@/views/outline/OutlineWorkbench.vue'),
        meta: { title: '大纲工作台', step: 2 },
      },
      {
        path: 'generate',
        name: 'Generate',
        component: () => import('@/views/generate/GenerateWorkspace.vue'),
        meta: { title: '内容生成', step: 3 },
      },
      {
        path: 'review',
        name: 'Review',
        component: () => import('@/views/review/ReviewWorkspace.vue'),
        meta: { title: '审查导出', step: 4 },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
