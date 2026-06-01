# 奇易AI编标 - 开发规范文档

> **重要**：所有开发必须严格遵循本规范，AI辅助开发也不例外。

---

## 一、项目结构规范

### 1.1 目录命名
- 全部小写，单词用连字符 `-` 分隔
- 示例：`bid-parser`、`outline-agent`

### 1.2 文件命名

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| Vue组件 | PascalCase | `OutlineEditor.vue` |
| Python模块 | snake_case | `outline_service.py` |
| TypeScript文件 | camelCase | `useOutlineStore.ts` |
| 常量文件 | UPPER_CASE | `API_ENDPOINTS.ts` |
| 测试文件 | 与源文件同名 + `.test` | `outline_service.test.py` |

### 1.3 目录结构

```
frontend/src/
├── api/                    # API调用（只放接口定义）
│   ├── project.ts
│   └── outline.ts
├── components/             # 组件
│   ├── common/             # 通用基础组件
│   └── outline/            # 业务组件
├── composables/            # 组合式函数（业务逻辑复用）
│   └── useOutline.ts
├── stores/                 # 状态管理（一个模块一个文件）
│   └── project.ts
├── types/                  # TypeScript类型定义
│   └── outline.ts
├── utils/                  # 纯工具函数（无状态）
│   └── format.ts
└── views/                  # 页面（按路由模块分组）
    └── outline/
        └── OutlineWorkbench.vue

backend/app/
├── api/v1/                 # 路由层（只做参数校验和响应）
├── schemas/                # Pydantic模型（请求/响应）
├── services/               # 业务逻辑层（核心逻辑）
├── repositories/           # 数据访问层（数据库操作）
├── agents/                 # Agent相关
│   ├── orchestrator.py     # 调度器
│   ├── agents/             # 各Agent实现
│   └── tools/              # Agent工具
├── prompts/                # Prompt模板（独立管理）
└── db/models/              # 数据库模型
```

---

## 二、代码规范

### 2.1 Python后端规范

```python
# ✅ 正确示例

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OutlineNode(BaseModel):
    """大纲节点模型"""
    
    id: str = Field(..., description="节点ID")
    title: str = Field(..., min_length=1, max_length=200, description="节点标题")
    level: int = Field(..., ge=1, le=4, description="层级 1-4")
    parent_id: Optional[str] = Field(None, description="父节点ID")
    sort_order: int = Field(0, description="排序序号")
    

class OutlineService:
    """大纲服务"""
    
    def __init__(self, repo: OutlineRepository):
        self.repo = repo
    
    async def get_outline_tree(self, project_id: str) -> list[OutlineNode]:
        """获取大纲树结构
        
        Args:
            project_id: 项目ID
            
        Returns:
            大纲节点列表（树形结构）
        """
        nodes = await self.repo.get_by_project(project_id)
        return self._build_tree(nodes)
    
    def _build_tree(self, nodes: list[OutlineNode]) -> list[OutlineNode]:
        """构建树结构（私有方法用下划线前缀）"""
        # 实现逻辑
        pass
```

**Python规范要点**：
1. **必须有类型注解** - 所有函数参数和返回值
2. **必须有文档字符串** - 类和公共方法用docstring
3. **异步优先** - 数据库操作、外部调用用async
4. **单一职责** - 一个函数只做一件事
5. **错误处理** - 用自定义异常，不要吞异常

### 2.2 Vue3前端规范

```vue
<script setup lang="ts">
/**
 * 大纲编辑器组件
 * 功能：展示和编辑大纲树结构
 */

import { ref, computed } from 'vue'
import { useOutlineStore } from '@/stores/outline'
import type { OutlineNode } from '@/types/outline'

// Props定义
interface Props {
  projectId: string
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

// Emits定义
const emit = defineEmits<{
  'update:outline': [nodes: OutlineNode[]]
  'node-click': [node: OutlineNode]
}>()

// Store
const outlineStore = useOutlineStore()

// 状态
const expandedKeys = ref<Set<string>>(new Set())

// 计算属性
const treeData = computed(() => outlineStore.outlineTree)

// 方法
function handleNodeClick(node: OutlineNode) {
  emit('node-click', node)
}

// 暴露给父组件
defineExpose({
  refresh: () => outlineStore.fetchOutline(props.projectId)
})
</script>

<template>
  <div class="outline-editor">
    <!-- 模板内容 -->
  </div>
</template>

<style scoped>
.outline-editor {
  /* 样式 */
}
</style>
```

**Vue3规范要点**：
1. **必须用 `<script setup>`** - 不用Options API
2. **必须用TypeScript** - 不允许any
3. **Props和Emits必须定义类型** - 用interface
4. **组件职责单一** - 超过300行考虑拆分
5. **样式用scoped** - 避免全局污染

### 2.3 TypeScript规范

```typescript
// ✅ 类型定义文件 types/outline.ts

/** 大纲节点状态 */
export type OutlineStatus = 'draft' | 'confirmed' | 'locked'

/** 大纲节点 */
export interface OutlineNode {
  id: string
  title: string
  level: 1 | 2 | 3 | 4
  parentId: string | null
  sortOrder: number
  status: OutlineStatus
  content?: string
  children?: OutlineNode[]
}

/** 创建大纲节点请求 */
export interface CreateOutlineRequest {
  title: string
  level: number
  parentId?: string
}

// ❌ 禁止的写法
// let data: any
// function handle(data: object)
```

---

## 三、Git提交规范

### 3.1 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 3.2 Type类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(outline): 添加大纲编辑功能` |
| `fix` | 修复bug | `fix(parser): 修复PDF解析乱码问题` |
| `docs` | 文档 | `docs: 更新API文档` |
| `style` | 格式调整 | `style: 统一代码缩进` |
| `refactor` | 重构 | `refactor(agent): 重构Agent调度逻辑` |
| `test` | 测试 | `test(outline): 添加大纲服务单元测试` |
| `chore` | 构建/工具 | `chore: 更新依赖版本` |

### 3.3 示例

```
feat(outline): 实现大纲树形编辑器

- 支持拖拽调整顺序
- 支持新增/删除节点
- 支持4层级展示

Closes #123
```

---

## 四、API设计规范

### 4.1 RESTful风格

```
GET    /api/v1/projects              # 获取项目列表
POST   /api/v1/projects              # 创建项目
GET    /api/v1/projects/{id}         # 获取项目详情
PUT    /api/v1/projects/{id}         # 更新项目
DELETE /api/v1/projects/{id}         # 删除项目

GET    /api/v1/projects/{id}/outline           # 获取大纲
POST   /api/v1/projects/{id}/outline           # 创建大纲节点
PUT    /api/v1/projects/{id}/outline/{nodeId}  # 更新节点
DELETE /api/v1/projects/{id}/outline/{nodeId}  # 删除节点

POST   /api/v1/projects/{id}/outline/generate  # AI生成大纲
POST   /api/v1/projects/{id}/outline/chat      # 大纲对话调整

POST   /api/v1/projects/{id}/sections/{nodeId}/generate  # 生成章节内容
GET    /api/v1/projects/{id}/sections/{nodeId}/stream     # 流式获取内容
```

### 4.2 响应格式

```json
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "xxx",
    "title": "施工方案"
  }
}

// 错误响应
{
  "code": 40001,
  "message": "大纲层级不能超过4层",
  "data": null
}

// 分页响应
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [],
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

### 4.3 错误码规范

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 40001 | 参数错误 |
| 40003 | 无权限 |
| 40004 | 资源不存在 |
| 50001 | 服务器内部错误 |
| 50002 | AI服务调用失败 |

---

## 五、Agent开发规范

### 5.1 Agent职责划分

```
Orchestrator (总调度)
├── ParserAgent      # 只负责文档解析
├── ScoringAgent     # 只负责评分点提取
├── OutlineAgent     # 只负责大纲生成/调整
├── WriterAgent      # 只负责内容写作
└── ReviewerAgent    # 只负责质量审查
```

### 5.2 Agent开发模板

```python
# backend/app/agents/base.py

from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from typing import Any

class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent描述"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行任务
        
        Args:
            input_data: 输入数据
            
        Returns:
            输出数据
        """
        pass
    
    def _validate_input(self, data: dict, required_keys: list[str]) -> None:
        """校验输入数据"""
        missing = [k for k in required_keys if k not in data]
        if missing:
            raise ValueError(f"缺少必要参数: {missing}")
```

### 5.3 Prompt管理规范

```python
# backend/app/prompts/outline_prompts.py

OUTLINE_GENERATE_PROMPT = """
# 角色
你是一位资深的施工技术标编写专家，擅长根据招标要求生成技术标大纲。

# 任务
根据以下信息生成技术标大纲结构：

## 项目概况
- 项目名称：{project_name}
- 工程类型：{project_type}
- 建设规模：{project_scale}

## 评分要求
{scoring_criteria}

## 输出要求
1. 大纲层级不超过4层
2. 必须覆盖所有评分要点
3. 符合施工技术标规范
4. 章节设置合理，逻辑清晰

# 输出格式
请以JSON格式输出大纲结构：
```json
[
  {{
    "title": "章节标题",
    "level": 1,
    "children": [
      {{
        "title": "子章节标题",
        "level": 2
      }}
    ]
  }}
]
```
"""

OUTLINE_REFINE_PROMPT = """
# 角色
你是大纲调整助手，根据用户反馈修改大纲。

# 当前大纲
{current_outline}

# 用户反馈
{user_feedback}

# 调整要求
1. 保持原有层级结构
2. 只修改用户提到的部分
3. 确保调整后大纲完整性

# 输出修改后的完整大纲（JSON格式）
"""
```

**Prompt规范要点**：
1. **模板独立管理** - 放在`prompts/`目录
2. **变量用花括号** - `{variable_name}`
3. **角色和任务明确** - 每个prompt开头说明
4. **输出格式固定** - 明确要求JSON/Markdown等格式

---

## 六、数据库规范

### 6.1 表命名
- 小写下划线：`outline_nodes`、`section_contents`
- 复数形式：用`s`结尾

### 6.2 字段命名
- 小写下划线：`created_at`、`project_id`
- 外键：`{关联表单数}_id`
- 布尔：`is_xxx` 或 `has_xxx`

### 6.3 必备字段

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
created_at  TIMESTAMP DEFAULT NOW()
updated_at  TIMESTAMP DEFAULT NOW()
is_deleted  BOOLEAN DEFAULT FALSE  -- 软删除
```

---

## 七、测试规范

### 7.1 测试覆盖率要求
- 核心业务逻辑：>= 80%
- Agent相关：>= 70%
- 工具函数：>= 90%

### 7.2 测试命名

```python
# 测试文件：test_outline_service.py

class TestOutlineService:
    """大纲服务测试"""
    
    async def test_get_outline_tree_should_return_nested_structure(self):
        """获取大纲树应该返回嵌套结构"""
        # Arrange
        # Act
        # Assert
        pass
    
    async def test_create_node_should_fail_when_level_exceeds_4(self):
        """创建节点应该失败当层级超过4"""
        pass
```

---

## 八、文档规范

### 8.1 代码注释
- 复杂逻辑必须加注释
- 注释说明"为什么"而不是"是什么"
- 中文注释

### 8.2 API文档
- 使用FastAPI自动生成OpenAPI文档
- 每个接口必须有description

### 8.3 README文档
- 项目介绍
- 快速开始
- 目录结构说明
- 开发/部署指南

---

## 九、禁止事项

### ❌ 绝对禁止

1. **不写类型注解** - Python/TypeScript必须有类型
2. **用any类型** - TypeScript禁止any
3. **吞异常** - `except: pass` 是禁止的
4. **硬编码** - 配置放环境变量或配置文件
5. **超过500行的文件** - 必须拆分
6. **超过100行的函数** - 必须拆分
7. **提交前不测试** - 必须本地验证通过
8. **直接操作数据库** - 必须通过Repository层

### ⚠️ 需要谨慎

1. **引入新依赖** - 需要说明理由
2. **修改数据库结构** - 需要用migration
3. **修改Prompt** - 需要记录变更原因
4. **修改Agent流程** - 需要说明影响范围

---

## 十、代码审查清单

提交PR前自查：

- [ ] 代码符合命名规范
- [ ] 有完整的类型注解
- [ ] 有必要的注释/文档
- [ ] 有对应的测试用例
- [ ] 本地测试通过
- [ ] 没有硬编码的值
- [ ] 没有遗留的print/debug
- [ ] 错误处理完善
- [ ] 符合单一职责原则

---

**最后更新**：2025-01-01
**维护者**：项目负责人
