<template>
  <section class="demo-shell">
    <header class="demo-header">
      <div>
        <p class="eyebrow">挑战杯 · 现场功能演示</p>
        <h1>图织天网</h1>
        <p>面向电信欺诈的图异常检测与证据约束智能研判系统</p>
      </div>
      <div class="header-state">
        <span class="service-state"><i :class="{ online: serviceReady }"></i>{{ serviceReady ? '服务正常' : '服务待检查' }}</span>
        <span :class="['demo-tag', caseMode]">{{ modeLabel }}</span>
      </div>
    </header>

    <section class="truth-strip" aria-label="当前技术与数据状态">
      <article v-for="item in statusItems" :key="item.label" :class="['truth-item', item.tone]">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.detail }}</small>
      </article>
    </section>

    <div class="flow-strip" aria-label="智能研判演示闭环">
      <div class="flow-label">
        <span>本机功能演示链路</span>
        <strong v-if="report">{{ selectedId }} · {{ totalDurationLabel }}</strong>
        <strong v-else>等待研判对象</strong>
      </div>
      <div class="flow-steps">
        <span v-for="(step, index) in steps" :key="step.name" :class="['flow-step', step.status]">
          <i>{{ index + 1 }}</i>
          {{ step.name }}
          <small v-if="step.duration !== null">{{ formatDuration(step.duration) }}</small>
        </span>
      </div>
    </div>

    <div class="demo-grid">
      <aside class="demo-panel selector-panel">
        <h3>研判对象</h3>
        <div class="source-note">
          <strong>{{ modeLabel }}</strong>
          <span>{{ modeDescription }}</span>
          <small>报告生成：{{ llmStatusLabel }}</small>
          <small>固定合成样例；未执行实时图模型推理。</small>
        </div>
        <div v-if="risk" class="current-case">
          <span>当前对象</span>
          <strong>{{ risk.user_id }} · {{ riskLabel(risk.risk_level) }}</strong>
          <small>{{ dataBoundaryText }}</small>
        </div>
        <label>
          用户编号
          <input v-model.trim="manualId" :placeholder="inputPlaceholder" @keyup.enter="runAssessment(manualId)" />
        </label>
        <button class="primary-action" :disabled="loading" @click="runAssessment(manualId || selectedId)">
          {{ loading ? '研判中...' : '开始智能研判' }}
        </button>
        <div class="case-list">
          <button
            v-for="user in displayUsers"
            :key="user.user_id"
            :class="['case-button', user.risk_level, { active: user.user_id === selectedId }]"
            @click="runAssessment(user.user_id)"
          >
            <strong>{{ user.user_id }}</strong>
            <span>{{ riskLabel(user.risk_level) }}</span>
            <small>{{ percent(user.anomaly_score) }}</small>
            <em>{{ sourceText(user) }}</em>
          </button>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <ol class="step-list">
          <li v-for="step in steps" :key="step.name" :class="step.status">{{ step.name }}</li>
        </ol>
      </aside>

      <section class="demo-panel metrics-panel" v-if="risk">
        <div class="panel-title">
          <h3>风险总览</h3>
          <span :class="['risk-pill', risk.risk_level]">{{ riskLabel(risk.risk_level) }}</span>
        </div>
        <div class="data-line">
          <span>数据来源：{{ risk.data_source }}</span>
          <strong>{{ risk.is_demo_data ? '合成原型演示' : '真实模型输出样例' }}</strong>
        </div>
        <div class="metric-grid">
          <div v-for="item in metricCards" :key="item.label">
            <span>{{ item.label }}</span>
            <strong :class="item.tone">{{ item.value }}</strong>
            <small>{{ item.note }}</small>
          </div>
        </div>
      </section>

      <section class="demo-panel graph-panel" v-if="graph">
        <div class="panel-title">
          <h3>关系图谱</h3>
          <span class="muted">{{ graph.nodes.length }} 节点 / {{ graph.edges.length }} 边 · 点击节点查看详情</span>
        </div>
        <div class="graph-legend">
          <span><i class="target"></i>目标节点</span>
          <span><i class="core"></i>疑似核心</span>
          <span><i class="high"></i>高风险</span>
          <span><i class="medium"></i>中风险</span>
          <span><i class="low"></i>低风险</span>
        </div>
        <div ref="chartEl" class="echarts-graph" role="img" aria-label="关系图谱"></div>
        <div class="node-detail" v-if="activeNode">
          <strong>{{ activeNode.id }}</strong>
          <span>{{ activeNode.label }}</span>
          <span>{{ riskLabel(activeNode.risk_level) }}</span>
          <span>分数 {{ Number(activeNode.risk_score || 0).toFixed(2) }}</span>
          <span>联系次数 {{ activeNode.communication_count }}</span>
          <span>{{ activeNode.relation }}</span>
          <span>{{ activeNode.is_suspected_group ? '疑似团伙成员' : '普通关联对象' }}</span>
        </div>
      </section>

      <section class="demo-panel evidence-panel" v-if="risk">
        <div class="panel-title">
          <h3>风险证据卡</h3>
          <span class="evidence-source">仅依据结构化指标与图关系</span>
        </div>
        <div class="evidence-card">
          <div><span>风险对象</span><strong>{{ risk.user_id }}</strong></div>
          <div><span>风险等级</span><strong>{{ riskLabel(risk.risk_level) }}</strong></div>
          <div><span>异常分数</span><strong>{{ risk.anomaly_score.toFixed(2) }}</strong></div>
          <div><span>邻居风险比例</span><strong>{{ percent(risk.neighbor_risk_ratio) }}</strong></div>
        </div>

        <h4>样例事实</h4>
        <ol class="evidence-list">
          <li v-for="item in visibleEvidenceFacts" :key="item.text">
            <strong>样例事实</strong>
            <span>{{ item.text }}</span>
            <small>对应指标：{{ item.metric }}</small>
            <small>来源字段：{{ item.source }}；置信类型：{{ item.confidence }}</small>
          </li>
        </ol>

        <h4>系统推断</h4>
        <ul class="evidence-list">
          <li v-for="item in visibleInferenceItems" :key="item.text">
            <strong>系统推断</strong>
            <span>{{ item.text }}</span>
            <small>推断依据：{{ item.metric }}</small>
            <small>来源字段：{{ item.source }}</small>
          </li>
        </ul>
        <button
          v-if="hasCollapsibleEvidence"
          class="evidence-toggle"
          @click="showAllEvidence = !showAllEvidence"
        >
          {{ showAllEvidence ? '收起次要证据' : `展开全部证据（另有${hiddenEvidenceCount}条）` }}
        </button>

        <div class="review-box">
          <strong>复核建议</strong>
          <span>{{ risk.review_suggestion }}</span>
          <small v-if="reviewTrace">来源字段：{{ reviewTrace.source }}；置信类型：{{ reviewTrace.confidence }}</small>
        </div>
      </section>

      <section class="demo-panel group-panel" v-if="risk">
        <h3>疑似团伙分析</h3>
        <div class="group-summary">
          <div><span>团伙标识</span><strong>{{ risk.group_features.group_id || '未发现' }}</strong></div>
          <div><span>核心节点</span><strong>{{ risk.group_features.core_node || '-' }}</strong></div>
          <div><span>成员数量</span><strong>{{ risk.group_features.member_count }}</strong></div>
          <div><span>关系密度</span><strong>{{ Number(risk.group_features.density || 0).toFixed(2) }}</strong></div>
        </div>
        <ul>
          <li v-for="item in risk.group_features.features" :key="item">{{ item }}</li>
        </ul>
        <p class="suggestion">{{ risk.review_suggestion }}</p>
      </section>

      <section class="demo-panel report-panel" v-if="report">
        <div class="panel-title">
          <h3>研判报告</h3>
          <div>
            <button class="secondary" @click="copyReport">复制</button>
            <button class="secondary" @click="downloadReport">下载</button>
          </div>
        </div>
        <div class="report-meta">
          <span>生成方式：{{ reportProviderLabel }}</span>
          <span>{{ report.is_demo_data ? '原型演示数据' : '内置脱敏测试集样例' }}</span>
          <span>结论边界：辅助研判，不替代人工复核</span>
          <span>本机接口耗时：{{ totalDurationLabel }}</span>
        </div>
        <p v-if="report.safety_warnings?.length" class="provider-warning">
          {{ report.safety_warnings.join('；') }}
        </p>
        <pre>{{ report.report }}</pre>
        <p v-if="copyState" class="muted">{{ copyState }}</p>
      </section>
    </div>
  </section>
</template>

<script setup>
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { api } from '../api/client'

const users = ref([])
const caseMode = ref('demo')
const selectedId = ref('U1003')
const manualId = ref('U1003')
const risk = ref(null)
const graph = ref(null)
const report = ref(null)
const evidenceCard = ref(null)
const llmStatus = ref(null)
const healthStatus = ref(null)
const error = ref('')
const loading = ref(false)
const copyState = ref('')
const chartEl = ref(null)
const activeNode = ref(null)
const showAllEvidence = ref(false)
let chart = null
let chartResizeObserver = null

const steps = ref([
  { name: '加载关系图谱', status: 'pending', duration: null },
  { name: '执行风险检测', status: 'pending', duration: null },
  { name: '生成证据卡', status: 'pending', duration: null },
  { name: '形成研判报告', status: 'pending', duration: null },
])

const modeLabel = computed(() => '合成原型样例 · 非真实检测')
const modeDescription = computed(() => '使用低、中、高三类合成样例演示图谱、证据卡与报告流程。')
const inputPlaceholder = computed(() => 'U1001 / U1002 / U1003')
const displayUsers = computed(() => users.value)
const apiPrefix = computed(() => '/api/users')
const llmStatusLabel = computed(() => '本地规则模板')
const reportProviderLabel = computed(() => '本地规则模板')

const serviceReady = computed(() => healthStatus.value?.service === 'ok')
const totalDuration = computed(() => (
  steps.value.reduce((sum, step) => sum + (step.duration || 0), 0)
))
const totalDurationLabel = computed(() => (
  totalDuration.value ? formatDuration(totalDuration.value) : '等待运行'
))
const statusItems = computed(() => [
 {label:'展示范围',value:'功能原型',detail:'风险总览、关系图谱、证据卡、研判报告',tone:'prototype'},
 {label:'数据来源',value:'合成样例',detail:'不包含四川数据集或真实用户数据',tone:'prototype'},
 {label:'报告生成',value:'本地规则模板',detail:'模板整理固定字段，未调用大语言模型',tone:'verified'},
 {label:'运行方式',value:'本地服务',detail:'无需云端接口或 API Key',tone:'verified'},
])

const metricCards = computed(() => {
  if (!risk.value) return []
  return [
    { label: '异常分数', value: risk.value.anomaly_score.toFixed(4), note: '合成样例固定值', tone: risk.value.risk_level },
    { label: '风险等级', value: riskLabel(risk.value.risk_level), note: '阈值映射结果', tone: risk.value.risk_level },
    { label: '属性差异示意值', value: risk.value.attribute_curvature.toFixed(4), note: risk.value.is_demo_data ? '原型指标' : '特征差异代理值' },
    { label: '邻居风险比例', value: percent(risk.value.neighbor_risk_ratio), note: '可追踪邻域统计' },
    { label: '相似度差', value: risk.value.similarity_gap.toFixed(4), note: '节点与邻域风险差' },
    { label: '行为偏离度', value: risk.value.behavior_deviation.toFixed(4), note: '结构化派生指标' },
    { label: '高风险关联节点', value: String(risk.value.high_risk_neighbors), note: '当前可追踪范围' },
    { label: '疑似团伙规模', value: String(risk.value.suspected_group_size), note: '候选社区，不是定性结论' },
  ]
})

const evidenceWithMetrics = computed(() => {
  if (!risk.value) return []
  const facts = (evidenceCard.value?.evidence_trace || []).filter(item => item.category === 'model_fact')
  if (facts.length) return facts.map(traceDisplay)
  const source = evidenceCard.value?.evidence || risk.value.evidence || []
  return source.map(text => ({ text, metric: evidenceMetric(text), source: 'evidence', confidence: '结构化字段' }))
})
const inferenceItems = computed(() => {
  const inferences = (evidenceCard.value?.evidence_trace || []).filter(item => item.category === 'system_inference')
  if (inferences.length) return inferences.map(traceDisplay)
  return (evidenceCard.value?.abnormal_behaviors || risk.value?.abnormal_behaviors || []).map(text => ({
    text,
    metric: '风险指标与局部图关系',
    source: 'abnormal_behaviors / related_nodes',
    confidence: '系统推断',
  }))
})
const visibleEvidenceFacts = computed(() => (
  showAllEvidence.value ? evidenceWithMetrics.value : evidenceWithMetrics.value.slice(0, 3)
))
const visibleInferenceItems = computed(() => (
  showAllEvidence.value ? inferenceItems.value : inferenceItems.value.slice(0, 2)
))
const hiddenEvidenceCount = computed(() => (
  Math.max(0, evidenceWithMetrics.value.length - 3)
    + Math.max(0, inferenceItems.value.length - 2)
))
const hasCollapsibleEvidence = computed(() => hiddenEvidenceCount.value > 0)
const reviewTrace = computed(() => {
  const item = (evidenceCard.value?.evidence_trace || []).find(entry => entry.category === 'review_suggestion')
  return item ? traceDisplay(item) : null
})
const dataBoundaryText = computed(() => {
  if (!risk.value) return ''
  return risk.value.is_demo_data
    ? '合成原型样例，用于演示完整流程'
    : '内置四川脱敏测试集预测样例，不是生产数据'
})

function riskLabel(value) {
  return { low: '低风险', medium: '中风险', high: '高风险' }[value] || value
}

function percent(value) {
  return `${Math.round(Number(value || 0) * 100)}%`
}

function formatDuration(milliseconds) {
  if (milliseconds >= 1000) return `${(milliseconds / 1000).toFixed(2)} s`
  return `${Math.max(1, Math.round(milliseconds))} ms`
}

function sourceText(user) {
  if (!user) return ''
  return user.is_demo_data ? '原型演示数据' : '真实模型样例'
}

function evidenceMetric(text) {
  if (!risk.value) return '结构化输入'
  if (text.includes('异常分数') || text.includes('置信分数')) return `异常分数 ${risk.value.anomaly_score.toFixed(2)}`
  if (text.includes('邻居') || text.includes('邻居风险')) return `邻居风险比例 ${percent(risk.value.neighbor_risk_ratio)}，高风险邻居 ${risk.value.high_risk_neighbors}`
  if (text.includes('相似度') || text.includes('风险差')) return `相似度差 ${risk.value.similarity_gap.toFixed(2)}`
  if (text.includes('行为')) return `行为偏离度 ${risk.value.behavior_deviation.toFixed(2)}`
  if (text.includes('团伙') || text.includes('图谱') || text.includes('邻域')) return `疑似团伙规模 ${risk.value.suspected_group_size}`
  if (text.includes('属性曲率') || text.includes('特征')) return `属性曲率/代理值 ${risk.value.attribute_curvature.toFixed(2)}`
  return `数据来源 ${risk.value.data_source}`
}

function traceDisplay(item) {
  return {
    text: item.text,
    metric: metricRefsText(item.metric_refs),
    source: (item.source_fields || []).join(' / ') || '结构化输入',
    confidence: confidenceText(item.confidence),
  }
}

function metricRefsText(refs) {
  const entries = Object.entries(refs || {})
  if (!entries.length) return '结构化输入'
  return entries.map(([key, value]) => {
    if (typeof value === 'number') return `${key}=${Number(value).toFixed(value > 1 ? 0 : 4)}`
    return `${key}=${value}`
  }).join('；')
}

function confidenceText(value) {
  return { measured: '结构化指标', derived: '派生推断', advisory: '复核建议' }[value] || value || '结构化输入'
}

function resetSteps() {
  steps.value = steps.value.map(step => ({ ...step, status: 'pending', duration: null }))
}

async function runStep(index, action) {
  steps.value = steps.value.map((step, idx) => ({
    ...step,
    status: idx < index ? 'done' : idx === index ? 'running' : 'pending',
  }))
  const startedAt = performance.now()
  try {
    const result = await action()
    const duration = performance.now() - startedAt
    steps.value = steps.value.map((step, idx) => (
      idx === index ? { ...step, status: 'done', duration } : step
    ))
    return result
  } catch (cause) {
    const duration = performance.now() - startedAt
    steps.value = steps.value.map((step, idx) => (
      idx === index ? { ...step, status: 'failed', duration } : step
    ))
    throw cause
  }
}

async function loadUsers() { users.value = await api('/api/users') }
async function loadLLMStatus() { llmStatus.value = await api('/api/llm/status') }
async function loadRuntimeStatus() { healthStatus.value = await api('/api/health') }

async function runAssessment(userId) {
  const id = (userId || '').trim()
  if (!id) return
  loading.value = true
  error.value = ''
  copyState.value = ''
  showAllEvidence.value = false
  report.value = null
  evidenceCard.value = null
  resetSteps()
  selectedId.value = id
  manualId.value = id
  try {
    graph.value = await runStep(0, () => api(`${apiPrefix.value}/${encodeURIComponent(id)}/graph`))
    risk.value = await runStep(1, () => api(`${apiPrefix.value}/${encodeURIComponent(id)}/risk`))
    evidenceCard.value = await runStep(2, () => api(`${apiPrefix.value}/${encodeURIComponent(id)}/evidence-card`))
    report.value = await runStep(3, () => api(`${apiPrefix.value}/${encodeURIComponent(id)}/report`, { method: 'POST' }))
    activeNode.value = graph.value.nodes.find(node => node.id === id) || null
    await nextTick()
    renderGraph()
  } catch (e) {
    error.value = e.message || '研判失败'
  } finally {
    loading.value = false
  }
}

function renderGraph() {
  if (!chartEl.value || !graph.value) return
  if (!chart) {
    chart = echarts.init(chartEl.value)
    chartResizeObserver = new ResizeObserver(() => chart?.resize())
    chartResizeObserver.observe(chartEl.value)
    chart.on('click', params => {
      if (params.dataType === 'node') activeNode.value = params.data.raw
    })
  }
  const categories = [
    { name: '目标' },
    { name: '核心' },
    { name: '桥接' },
    { name: '高风险' },
    { name: '中风险' },
    { name: '低风险' },
  ]
  const categoryIndex = node => {
    if (node.role === 'target') return 0
    if (node.role === 'core') return 1
    if (node.role === 'bridge') return 2
    if (node.risk_level === 'high') return 3
    if (node.risk_level === 'medium') return 4
    return 5
  }
  chart.setOption({
    color: ['#2563eb', '#111827', '#7c3aed', '#dc2626', '#d97706', '#16a34a'],
    tooltip: {
      formatter(params) {
        if (params.dataType === 'edge') return `${params.data.source} -> ${params.data.target}<br/>联系次数：${params.data.value}`
        const node = params.data.raw
        return `${node.id}<br/>${riskLabel(node.risk_level)}<br/>联系次数：${node.communication_count}<br/>${node.is_suspected_group ? '疑似团伙成员' : '普通关联对象'}`
      },
    },
    legend: [{ data: categories.map(item => item.name), bottom: 0 }],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        categories,
        force: { repulsion: 180, gravity: 0.18, edgeLength: [65, 120] },
        label: {
          show: true,
          formatter: '{b}',
          fontSize: 11,
          position: 'right',
          distance: 6,
        },
        labelLayout: { hideOverlap: true },
        emphasis: { focus: 'adjacency' },
        lineStyle: { color: '#94a3b8', opacity: 0.75, width: 1.4 },
        data: graph.value.nodes.map(node => ({
          id: node.id,
          name: node.id,
          value: node.risk_score,
          category: categoryIndex(node),
          symbolSize: node.role === 'target' ? 58 : 28 + node.risk_score * 20,
          raw: node,
        })),
        links: graph.value.edges.map(edge => ({
          source: edge.source,
          target: edge.target,
          value: edge.weight,
          lineStyle: { width: Math.max(1, Math.min(6, edge.weight / 8)) },
        })),
      },
    ],
  })
}

async function copyReport() {
  if (!report.value?.report) return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(report.value.report)
    } else {
      const area = document.createElement('textarea')
      area.value = report.value.report
      document.body.appendChild(area)
      area.select()
      document.execCommand('copy')
      document.body.removeChild(area)
    }
    copyState.value = '已复制报告'
  } catch (e) {
    copyState.value = '复制失败，请手动选择报告文本'
  }
}

function downloadReport() {
  if (!report.value?.report) return
  const blob = new Blob([report.value.report], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedId.value}_研判报告.md`
  link.click()
  URL.revokeObjectURL(url)
}

watch(graph, () => nextTick(renderGraph))

onMounted(async () => {
  try {
    await Promise.all([loadUsers(), loadLLMStatus(), loadRuntimeStatus()])
    await runAssessment(selectedId.value)
  } catch (e) {
    error.value = e.message || '加载失败'
  }
})

onBeforeUnmount(() => {
  chartResizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.demo-shell { display: flex; flex-direction: column; gap: 14px; }
.demo-header { background: #ffffff; border-bottom: 3px solid #1d4ed8; padding: 14px 2px 16px; display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; }
.demo-header h1 { margin: 2px 0 5px; font-size: 30px; line-height: 1.15; }
.demo-header p { margin: 0; color: #475569; }
.eyebrow { font-size: 12px; letter-spacing: 0; color: #1d4ed8; font-weight: 700; }
.header-state { display: flex; align-items: center; justify-content: flex-end; gap: 10px; flex-wrap: wrap; }
.service-state { border: 1px solid #dbe3ef; border-radius: 999px; padding: 6px 10px; color: #475569; font-size: 12px; font-weight: 700; }
.service-state i { width: 8px; height: 8px; border-radius: 50%; background: #ef4444; display: inline-block; margin-right: 6px; }
.service-state i.online { background: #16a34a; }
.demo-tag { border: 1px solid #f59e0b; color: #92400e; background: #fffbeb; border-radius: 999px; padding: 6px 10px; white-space: nowrap; font-weight: 700; }
.demo-tag.real { border-color: #2563eb; color: #1d4ed8; background: #eff6ff; }
.truth-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid #dbe3ef; border-radius: 8px; background: #ffffff; overflow: hidden; }
.truth-item { padding: 12px 14px; display: grid; gap: 3px; min-height: 66px; border-left: 3px solid #2563eb; }
.truth-item + .truth-item { border-top: 0; }
.truth-item.prototype { border-left-color: #7c3aed; }
.truth-item.pending { border-left-color: #d97706; background: #fffbeb; }
.truth-item span { color: #64748b; font-size: 11px; font-weight: 700; }
.truth-item strong { color: #0f172a; font-size: 14px; overflow-wrap: anywhere; }
.truth-item small { color: #64748b; line-height: 1.35; }
.flow-strip { background: #ffffff; border: 1px solid #dbe3ef; border-radius: 8px; padding: 11px 12px; display: grid; grid-template-columns: 180px minmax(0, 1fr); gap: 12px; align-items: center; }
.flow-label { display: grid; gap: 3px; }
.flow-label span { color: #64748b; font-size: 11px; font-weight: 700; }
.flow-label strong { color: #0f172a; font-size: 13px; }
.flow-steps { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }
.flow-step { border: 1px solid #cbd5e1; background: #f8fafc; color: #475569; border-radius: 7px; padding: 7px 8px; font-size: 12px; font-weight: 700; display: flex; align-items: center; gap: 5px; min-width: 0; }
.flow-step i { width: 20px; height: 20px; border-radius: 50%; background: #e2e8f0; display: inline-grid; place-items: center; font-size: 10px; font-style: normal; flex: 0 0 auto; }
.flow-step small { margin-left: auto; color: inherit; font-weight: 600; white-space: nowrap; }
.flow-step.running { border-color: #93c5fd; background: #eff6ff; color: #1d4ed8; }
.flow-step.done { border-color: #86efac; background: #f0fdf4; color: #166534; }
.flow-step.failed { border-color: #fecaca; background: #fef2f2; color: #991b1b; }
.demo-grid { display: grid; grid-template-columns: 280px minmax(0, 1fr) minmax(320px, 0.8fr); gap: 14px; align-items: start; }
.demo-panel { min-width: 0; background: #ffffff; border: 1px solid #dbe3ef; border-radius: 8px; padding: 16px; box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05); }
.selector-panel { grid-row: span 3; position: sticky; top: 12px; }
.graph-panel { min-height: 460px; }
.report-panel { grid-column: 2 / span 2; }
.panel-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
h3 { margin: 0 0 12px; font-size: 17px; }
.mode-switch { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 10px; }
.mode-switch button { border: 1px solid #cbd5e1; background: #f8fafc; color: #334155; border-radius: 8px; padding: 8px; font-weight: 700; }
.mode-switch button.active { border-color: #2563eb; background: #eff6ff; color: #1d4ed8; }
.source-note { border: 1px solid #dbeafe; background: #f8fafc; border-radius: 8px; padding: 10px; display: grid; gap: 4px; margin-bottom: 12px; }
.source-note strong { font-size: 13px; color: #1d4ed8; }
.source-note span { font-size: 12px; color: #475569; line-height: 1.45; }
.source-note small { font-size: 11px; color: #64748b; line-height: 1.4; }
.current-case { border-left: 4px solid #2563eb; background: #f8fafc; border-radius: 6px; padding: 10px; display: grid; gap: 3px; margin-bottom: 12px; }
.current-case span, .current-case small { color: #64748b; font-size: 12px; }
.current-case strong { color: #0f172a; }
.case-list { display: grid; gap: 8px; margin: 12px 0; }
.case-button { display: grid; grid-template-columns: 1fr auto; gap: 4px 8px; text-align: left; border: 1px solid #cbd5e1; background: #f8fafc; color: #1f2937; border-radius: 8px; padding: 10px; }
.case-button small { color: #64748b; }
.case-button em { grid-column: 1 / span 2; color: #64748b; font-size: 12px; font-style: normal; }
.case-button.active { outline: 3px solid #bfdbfe; }
.case-button.high { border-color: #fecaca; }
.case-button.medium { border-color: #fde68a; }
.case-button.low { border-color: #bbf7d0; }
.primary-action { width: 100%; margin: 8px 0; }
.step-list { margin: 12px 0 0; padding-left: 20px; color: #64748b; }
.step-list .running { color: #2563eb; font-weight: 700; }
.step-list .done { color: #15803d; font-weight: 700; }
.risk-pill { border-radius: 999px; padding: 5px 10px; font-weight: 700; }
.risk-pill.high { background: #fee2e2; color: #991b1b; }
.risk-pill.medium { background: #fef3c7; color: #92400e; }
.risk-pill.low { background: #dcfce7; color: #166534; }
.data-line { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 10px; margin-bottom: 12px; font-size: 13px; color: #475569; }
.data-line strong { color: #0f172a; }
.metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.metric-grid div, .group-summary div, .evidence-card div { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 7px; padding: 10px; min-height: 66px; box-sizing: border-box; }
.metric-grid span, .group-summary span, .evidence-card span { display: block; color: #64748b; font-size: 12px; margin-bottom: 4px; }
.metric-grid strong { display: block; color: #0f172a; font-size: 19px; line-height: 1.2; }
.metric-grid strong.high { color: #b91c1c; background: transparent; }
.metric-grid strong.medium { color: #b45309; background: transparent; }
.metric-grid strong.low { color: #15803d; background: transparent; }
.metric-grid small { display: block; color: #64748b; font-size: 10px; margin-top: 3px; line-height: 1.3; }
.graph-legend { display: flex; flex-wrap: wrap; gap: 8px 12px; color: #475569; font-size: 12px; margin-bottom: 8px; }
.graph-legend span { display: inline-flex; align-items: center; gap: 5px; }
.graph-legend i { width: 10px; height: 10px; border-radius: 999px; display: inline-block; }
.graph-legend .target { background: #2563eb; }
.graph-legend .core { background: #111827; }
.graph-legend .high { background: #dc2626; }
.graph-legend .medium { background: #d97706; }
.graph-legend .low { background: #16a34a; }
.echarts-graph { width: 100%; min-height: 400px; }
.node-detail { display: flex; flex-wrap: wrap; gap: 8px; padding-top: 10px; border-top: 1px solid #e2e8f0; }
.node-detail span { background: #f1f5f9; border-radius: 999px; padding: 4px 8px; }
.evidence-card, .group-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; }
.evidence-panel h4 { margin: 14px 0 8px; font-size: 14px; color: #0f172a; }
.evidence-source { border: 1px solid #bfdbfe; background: #eff6ff; color: #1d4ed8; border-radius: 999px; padding: 4px 8px; font-size: 11px; font-weight: 700; }
.evidence-list { display: grid; gap: 8px; padding-left: 0; list-style: none; }
.evidence-list li { border: 1px solid #e2e8f0; background: #f8fafc; border-radius: 8px; padding: 10px; display: grid; gap: 5px; }
.evidence-list li strong { color: #1d4ed8; font-size: 12px; }
.evidence-list li span { color: #1f2937; line-height: 1.5; }
.evidence-list li small { color: #64748b; }
.evidence-toggle { width: 100%; margin: 2px 0 12px; border: 1px solid #bfdbfe; background: #eff6ff; color: #1d4ed8; border-radius: 7px; font-weight: 700; }
.review-box { border-left: 4px solid #16a34a; background: #f0fdf4; padding: 10px; border-radius: 6px; display: grid; gap: 4px; }
.review-box strong { color: #166534; }
.suggestion { background: #eef2ff; border-left: 4px solid #4f46e5; padding: 10px; margin-bottom: 0; }
.report-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
.report-meta span { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 999px; color: #475569; padding: 5px 9px; font-size: 12px; }
.provider-warning { border-left: 4px solid #d97706; background: #fffbeb; color: #92400e; padding: 9px 10px; }
pre { white-space: pre-wrap; word-break: break-word; background: #0f172a; color: #e2e8f0; border-radius: 8px; padding: 14px; max-height: 460px; overflow: auto; }
.secondary { background: #e2e8f0; color: #334155; }
@media (max-width: 980px) {
  .truth-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .flow-strip { grid-template-columns: 1fr; }
  .demo-grid { grid-template-columns: 1fr; }
  .selector-panel { position: static; grid-row: auto; }
  .report-panel { grid-column: auto; }
}
@media (max-width: 640px) {
  .demo-header { display: grid; }
  .header-state { justify-content: flex-start; }
  .truth-strip, .flow-steps { grid-template-columns: 1fr; }
  .metric-grid { grid-template-columns: 1fr 1fr; }
}
</style>
