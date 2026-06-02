<script setup lang="ts">
/**
 * 系统设置页面
 */
import { ref, onMounted } from 'vue'
import { settingsApi, type AISettings } from '@/api/settings'

interface Preset {
  label: string
  icon: string
  ai_base_url: string
  ai_model: string
  ai_api_key_prefix: string
}

const presets: Preset[] = [
  { label: 'DeepSeek', icon: '🔮', ai_base_url: 'https://api.deepseek.com', ai_model: 'deepseek-chat', ai_api_key_prefix: 'sk-' },
  { label: 'MiMo Token Plan', icon: '🤖', ai_base_url: 'https://token-plan-cn.xiaomimimo.com/v1', ai_model: 'mimo-v2.5-pro', ai_api_key_prefix: 'tp-' },
  { label: 'OpenAI', icon: '🧠', ai_base_url: 'https://api.openai.com/v1', ai_model: 'gpt-4o', ai_api_key_prefix: 'sk-' },
]

const settings = ref<AISettings>({
  ai_api_key: '',
  ai_base_url: 'https://api.deepseek.com',
  ai_model: 'deepseek-chat',
  ai_temperature: '0.7',
  app_name: '奇易AI编标',
})
const loading = ref(false)
const saving = ref(false)
const toast = ref('')
const showKey = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await settingsApi.getAll()
    settings.value = res.data.data
  } finally {
    loading.value = false
  }
})

async function save() {
  saving.value = true
  try {
    await settingsApi.update(settings.value)
    showToast('设置已保存')
  } catch {
    showToast('保存失败')
  } finally {
    saving.value = false
  }
}

function applyPreset(p: Preset) {
  settings.value.ai_base_url = p.ai_base_url
  settings.value.ai_model = p.ai_model
  showToast(`已切换到 ${p.label}`)
}

function showToast(msg: string) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 2500)
}
</script>

<template>
  <div class="settings-page">
    <header class="page-header">
      <h2>⚙️ 系统设置</h2>
      <button class="btn btn-primary" :disabled="saving" @click="save">
        <span v-if="saving" class="spinner"></span>
        {{ saving ? '保存中…' : '💾 保存设置' }}
      </button>
    </header>

    <div v-if="loading" class="loading-state">加载中…</div>

    <template v-else>
      <!-- 快速接入 -->
      <section class="settings-section">
        <h3>🚀 快速接入</h3>
        <p class="section-desc">选择预设方案一键填入配置，再填入 API Key 即可</p>

        <div class="preset-grid">
          <button
            v-for="p in presets" :key="p.label"
            class="preset-btn"
            :class="{ active: settings.ai_base_url === p.ai_base_url }"
            @click="applyPreset(p)"
          >
            <span class="preset-icon">{{ p.icon }}</span>
            <span class="preset-label">{{ p.label }}</span>
            <span class="preset-model">{{ p.ai_model }}</span>
          </button>
        </div>
      </section>

      <!-- AI 模型配置 -->
      <section class="settings-section">
        <h3>🤖 AI 模型配置</h3>

        <div class="form-grid">
          <div class="form-group">
            <label>API Key <span class="required">*</span></label>
            <div class="key-input-row">
              <input
                v-model="settings.ai_api_key"
                :type="showKey ? 'text' : 'password'"
                class="form-input"
                placeholder="sk-... 或 tp-..."
              />
              <button class="btn-ghost btn-sm" @click="showKey = !showKey">
                {{ showKey ? '🙈' : '👁️' }}
              </button>
            </div>
            <span class="form-hint">DeepSeek: sk-xxx | MiMo: tp-xxx | 留空则使用 .env 默认值</span>
          </div>

          <div class="form-group">
            <label>Base URL</label>
            <input v-model="settings.ai_base_url" class="form-input" placeholder="https://api.deepseek.com" />
            <span class="form-hint">API 服务地址</span>
          </div>

          <div class="form-group">
            <label>模型名称</label>
            <input v-model="settings.ai_model" class="form-input" placeholder="deepseek-chat" />
            <span class="form-hint">deepseek-chat / mimo-v2.5-pro / gpt-4o 等</span>
          </div>

          <div class="form-group">
            <label>Temperature</label>
            <input v-model="settings.ai_temperature" type="number" step="0.1" min="0" max="2" class="form-input" placeholder="0.7" />
            <span class="form-hint">0-2，越高越有创造性，越低越稳定（推荐 0.7）</span>
          </div>
        </div>
      </section>

      <!-- 应用配置 -->
      <section class="settings-section">
        <h3>📋 应用配置</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>应用名称</label>
            <input v-model="settings.app_name" class="form-input" placeholder="奇易AI编标" />
          </div>
        </div>
      </section>

      <!-- 预留 -->
      <section class="settings-section disabled">
        <h3>📚 方案库配置（开发中）</h3>
        <p class="section-desc">后期实现：从方案库中调用历史方案作为生成参考</p>
      </section>
    </template>

    <div v-if="toast" class="toast">{{ toast }}</div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-header h2 { font-size: 22px; }

.settings-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-bottom: 16px;
}

.settings-section h3 { font-size: 15px; color: var(--text-primary); margin-bottom: 4px; }

.section-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 16px;
  font-family: var(--font-mono);
}

.settings-section.disabled { opacity: .5; pointer-events: none; }

/* ── 预设按钮 ── */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.preset-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all .2s;
  color: var(--text-secondary);
}

.preset-btn:hover {
  border-color: rgba(212, 168, 83, 0.3);
  background: var(--accent-glow);
}

.preset-btn.active {
  border-color: var(--accent);
  background: var(--accent-glow);
}

.preset-icon { font-size: 20px; }

.preset-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.preset-model {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}

/* ── 表单 ── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  margin-bottom: 6px;
  font-weight: 500;
}

.required { color: var(--red); }

.key-input-row {
  display: flex;
  gap: 6px;
}

.key-input-row .form-input { flex: 1; }

.form-input {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  padding: 9px 12px;
  font-family: var(--font-mono);
  font-size: 13px;
  outline: none;
  transition: border-color .2s;
}

.form-input:focus { border-color: rgba(212, 168, 83, 0.35); }

.form-hint {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  font-family: var(--font-mono);
}

.spinner {
  display: inline-block;
  width: 14px; height: 14px;
  border: 2px solid rgba(0,0,0,.2);
  border-top-color: var(--bg);
  border-radius: 50%;
  animation: spin .6s linear infinite;
  vertical-align: middle;
  margin-right: 4px;
}

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

.loading-state {
  text-align: center;
  padding: 60px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
</style>
