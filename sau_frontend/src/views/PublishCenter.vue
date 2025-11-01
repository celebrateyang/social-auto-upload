<template>
  <div class="publish-center">
    <!-- 内容区域 -->
    <div class="publish-content">
      <div class="publish-form">
        <!-- 发布状态提示 -->
        <div v-if="publishStatus" class="publish-status">
          <el-alert
            :title="publishStatus.message"
            :type="publishStatus.type"
            :closable="false"
              show-icon
            />
          </div>

          <!-- 视频上传区域 -->
          <div class="upload-section section-border">
            <h3>视频</h3>
            <div class="upload-options">
              <el-button type="primary" @click="showUploadOptions" class="upload-btn">
                <el-icon><Upload /></el-icon>
                上传视频
              </el-button>
            </div>
            
            <!-- 已上传文件列表 -->
            <div v-if="fileList.length > 0" class="uploaded-files">
              <h4>已上传文件：</h4>
              <div class="file-list">
                <div v-for="(file, index) in fileList" :key="index" class="file-item">
                  <el-link :href="file.url" target="_blank" type="primary">{{ file.name }}</el-link>
                  <span class="file-size">{{ (file.size / 1024 / 1024).toFixed(2) }}MB</span>
                  <el-button type="danger" size="small" @click="removeFile(index)">删除</el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 上传选项弹窗 -->
          <el-dialog
            v-model="uploadOptionsVisible"
            title="选择上传方式"
            width="400px"
            class="upload-options-dialog"
          >
            <div class="upload-options-content">
              <el-button type="primary" @click="selectLocalUpload" class="option-btn">
                <el-icon><Upload /></el-icon>
                本地上传
              </el-button>
              <el-button type="success" @click="selectMaterialLibrary" class="option-btn">
                <el-icon><Folder /></el-icon>
                素材库
              </el-button>
            </div>
          </el-dialog>

          <!-- 本地上传弹窗 -->
          <el-dialog
            v-model="localUploadVisible"
            title="本地上传"
            width="600px"
            class="local-upload-dialog"
          >
            <el-upload
              class="video-upload"
              drag
              :auto-upload="true"
              :action="`${apiBaseUrl}/upload`"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              multiple
              accept="video/*"
              :headers="authHeaders"
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                将视频文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持MP4、AVI等视频格式，可上传多个文件
                </div>
              </template>
            </el-upload>
          </el-dialog>

          <!-- 素材库选择弹窗 -->
          <el-dialog
            v-model="materialLibraryVisible"
            title="选择素材"
            width="800px"
            class="material-library-dialog"
          >
            <div class="material-library-content">
              <el-checkbox-group v-model="selectedMaterials">
                <div class="material-list">
                  <div
                    v-for="material in materials"
                    :key="material.id"
                    class="material-item"
                  >
                    <el-checkbox :label="material.id" class="material-checkbox">
                      <div class="material-info">
                        <div class="material-name">{{ material.filename }}</div>
                        <div class="material-details">
                          <span class="file-size">{{ material.filesize }}MB</span>
                          <span class="upload-time">{{ material.upload_time }}</span>
                        </div>
                      </div>
                    </el-checkbox>
                  </div>
                </div>
              </el-checkbox-group>
            </div>
            <template #footer>
              <div class="dialog-footer">
                <el-button @click="materialLibraryVisible = false">取消</el-button>
                <el-button type="primary" @click="confirmMaterialSelection">确定</el-button>
              </div>
            </template>
          </el-dialog>

          <!-- 账号列表（按平台分组显示） -->
          <div class="account-section section-border">
            <h3>平台账号列表</h3>
            <div class="all-accounts-display">
              <template v-for="platform in [
                { key: 1, name: '小红书' },
                { key: 2, name: '视频号' },
                { key: 3, name: '抖音' },
                { key: 4, name: '快手' },
                { key: 5, name: 'TikTok' },
                { key: 6, name: 'Bilibili' },
                { key: 7, name: '百家号' }
              ]" :key="platform.key">
                <div 
                  v-if="allPlatformAccounts[platform.key] && allPlatformAccounts[platform.key].length > 0"
                  class="platform-accounts-group"
                >
                  <div class="platform-group-header">
                    <span class="platform-icon">{{ getPlatformIcon(platform.key) }}</span>
                    <span class="platform-name">{{ platform.name }}</span>
                    <span class="account-count">({{ allPlatformAccounts[platform.key].length }})</span>
                  </div>
                  <div class="platform-accounts-list">
                    <el-tag
                      v-for="(account, index) in allPlatformAccounts[platform.key]"
                      :key="account.id"
                      closable
                      @close="removeAccountFromPlatform(platform.key, index)"
                      class="account-tag"
                      :type="currentPlatform === platform.key ? 'primary' : 'info'"
                    >
                      {{ account.name }}
                    </el-tag>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- 平台按钮组 -->
          <div class="platform-section section-border">
            <h3>平台</h3>
            <div class="platform-buttons">
              <el-button
                v-for="platform in availablePlatforms"
                :key="platform.key"
                :type="currentPlatform === platform.key ? 'primary' : 'default'"
                @click="switchPlatform(platform.key)"
                class="platform-btn"
              >
                {{ platform.name }}
              </el-button>
            </div>

          <!-- 标题输入 -->
          <div class="title-section">
            <h3>标题</h3>
            <el-input
              v-model="title"
              type="textarea"
              :rows="3"
              placeholder="请输入标题"
              maxlength="100"
              show-word-limit
              class="title-input"
            />
          </div>

          <!-- 话题输入 -->
          <div class="topic-section">
            <h3>话题</h3>
            <div class="topic-display">
              <div class="selected-topics">
                <el-tag
                  v-for="(topic, index) in selectedTopics"
                  :key="index"
                  closable
                  @close="removeTopic(index)"
                  class="topic-tag"
                >
                  #{{ topic }}
                </el-tag>
              </div>
              <el-button 
                type="primary" 
                plain 
                @click="openTopicDialog"
                class="select-topic-btn"
              >
                添加话题
              </el-button>
            </div>
          </div>

          <!-- 添加话题弹窗 -->
          <el-dialog
            v-model="topicDialogVisible"
            title="添加话题"
            width="600px"
            class="topic-dialog"
          >
            <div class="topic-dialog-content">
              <!-- 自定义话题输入 -->
              <div class="custom-topic-input">
                <el-input
                  v-model="customTopic"
                  placeholder="输入自定义话题"
                  class="custom-input"
                  @keyup.enter="addCustomTopic"
                >
                  <template #prepend>#</template>
                </el-input>
                <el-button type="primary" @click="addCustomTopic">添加</el-button>
              </div>

              <!-- 推荐话题 -->
              <div class="recommended-topics">
                <h4>推荐话题</h4>
                <div class="topic-grid">
                  <el-button
                    v-for="topic in recommendedTopics"
                    :key="topic"
                    :type="selectedTopics?.includes(topic) ? 'primary' : 'default'"
                    @click="toggleRecommendedTopic(topic)"
                    class="topic-btn"
                  >
                    {{ topic }}
                  </el-button>
                </div>
              </div>
            </div>

            <template #footer>
              <div class="dialog-footer">
                <el-button @click="topicDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="confirmTopicSelection">确定</el-button>
              </div>
            </template>
          </el-dialog>

          <!-- 平台特定配置（根据当前选中平台动态显示） -->
          <div class="platform-config-section">
            <h3>{{ currentPlatformName }}配置</h3>
            
            <!-- 抖音配置 -->
            <div v-if="currentPlatform === 3" class="platform-config">
              <el-form label-width="100px">
                <el-form-item label="商品标题">
                  <el-input
                    v-model="productTitle"
                    placeholder="选填"
                    maxlength="200"
                  />
                </el-form-item>
                <el-form-item label="商品链接">
                  <el-input
                    v-model="productLink"
                    placeholder="选填"
                    maxlength="200"
                  />
                </el-form-item>
              </el-form>
            </div>

            <!-- 腾讯视频号配置 -->
            <div v-if="currentPlatform === 2" class="platform-config">
              <el-form label-width="100px">
                <el-form-item label="视频分区" required>
                  <el-select v-model="tencentCategory" placeholder="请选择分区">
                    <el-option label="生活" :value="1" />
                    <el-option label="美食" :value="2" />
                    <el-option label="运动" :value="3" />
                    <el-option label="出行" :value="4" />
                    <el-option label="科技" :value="5" />
                    <el-option label="教育" :value="6" />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>

            <!-- 小红书和快手通用提示 -->
            <div v-if="currentPlatform === 1 || currentPlatform === 4" class="platform-config">
              <el-empty description="该平台无需额外配置" :image-size="60" />
            </div>
          </div>

          <!-- 定时发布 -->
          <div class="schedule-section">
            <h3>定时发布</h3>
            <div class="schedule-controls">
              <el-switch
                v-model="scheduleEnabled"
                active-text="定时发布"
                inactive-text="立即发布"
              />
              <div v-if="scheduleEnabled" class="schedule-settings">
                <div class="schedule-item">
                  <span class="label">每天发布视频数：</span>
                  <el-select v-model="videosPerDay" placeholder="选择发布数量">
                    <el-option
                      v-for="num in 55"
                      :key="num"
                      :label="num"
                      :value="num"
                    />
                  </el-select>
                </div>
                <div class="schedule-item">
                  <span class="label">每天发布时间：</span>
                  <el-time-select
                    v-for="(time, index) in dailyTimes"
                    :key="index"
                    v-model="dailyTimes[index]"
                    start="00:00"
                    step="00:30"
                    end="23:30"
                    placeholder="选择时间"
                  />
                  <el-button
                    v-if="dailyTimes.length < videosPerDay"
                    type="primary"
                    size="small"
                    @click="dailyTimes.push('10:00')"
                  >
                    添加时间
                  </el-button>
                </div>
                <div class="schedule-item">
                  <span class="label">开始天数：</span>
                  <el-select v-model="startDays" placeholder="选择开始天数">
                    <el-option :label="'明天'" :value="0" />
                    <el-option :label="'后天'" :value="1" />
                  </el-select>
                </div>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button size="small" @click="cancelPublish">取消</el-button>
            <el-button size="small" type="primary" @click="confirmPublish">发布</el-button>
          </div>
          </div>

          <!-- 上传结果（可折叠） -->
          <div v-if="uploadResults && uploadResults.length > 0" class="upload-results-section">
            <el-collapse v-model="resultsCollapsed">
              <el-collapse-item name="results">
                <template #title>
                  <div class="results-header">
                    <h3>上传结果详情</h3>
                    <el-tag v-if="uploadSummary.total" type="info" size="small" class="summary-tag">
                      共 {{ uploadSummary.total }} 个任务：
                      成功 {{ uploadSummary.success }}，
                      失败 {{ uploadSummary.failed }}
                    </el-tag>
                  </div>
                </template>
                <el-table :data="uploadResults" border style="width: 100%">
                  <el-table-column prop="platform" label="平台" width="100" />
                  <el-table-column prop="account" label="账号" width="200">
                    <template #default="scope">
                      {{ scope.row.account.replace('.json', '') }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="video" label="视频文件" min-width="180">
                    <template #default="scope">
                      {{ scope.row.video.split('\\').pop().split('/').pop() }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态" width="100">
                    <template #default="scope">
                      <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                        {{ scope.row.status === 'success' ? '成功' : '失败' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="message" label="信息" min-width="150" />
                  <el-table-column prop="start_time" label="开始时间" width="160" />
                  <el-table-column prop="end_time" label="结束时间" width="160" />
                  <el-table-column label="操作" width="100">
                    <template #default="scope">
                      <el-button 
                        v-if="scope.row.status === 'failed'"
                        type="warning" 
                        size="small"
                        @click="retryUpload(scope.row)"
                      >
                        重试
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-collapse-item>
            </el-collapse>
          </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Upload, Plus, Close, Folder } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { materialApi } from '@/api/material'
import { accountApi } from '@/api/account'

// API base URL
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

// Authorization headers
const authHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
}))

// 获取应用状态管理
const appStore = useAppStore()

// 上传相关状态
const uploadOptionsVisible = ref(false)
const localUploadVisible = ref(false)
const materialLibraryVisible = ref(false)
const selectedMaterials = ref([])
const materials = computed(() => appStore.materials)



// 平台列表 - 对应后端type字段
const platforms = [
  { key: 1, name: '小红书' },
  { key: 2, name: '视频号' },
  { key: 3, name: '抖音' },
  { key: 4, name: '快手' },
  { key: 5, name: 'TikTok' },
  { key: 6, name: 'Bilibili' },
  { key: 7, name: '百家号' }
]

// 当前选中的平台（用于切换显示）
const currentPlatform = ref(1) // 默认选中小红书

// 计算属性：过滤出有账号的平台
const availablePlatforms = computed(() => {
  return platforms.filter(platform => {
    return allPlatformAccounts[platform.key] && allPlatformAccounts[platform.key].length > 0
  })
})

// 所有平台的账号（按平台分组）
const allPlatformAccounts = reactive({
  1: [], // 小红书账号
  2: [], // 视频号账号
  3: [], // 抖音账号
  4: [], // 快手账号
  5: [], // TikTok账号
  6: [], // Bilibili账号
  7: []  // 百家号账号
})

// 表单数据
const fileList = ref([]) // 后端返回的文件名列表
const displayFileList = ref([]) // 用于显示的文件列表
const title = ref('')
const selectedTopics = ref([]) // 话题列表（不带#号）
const scheduleEnabled = ref(false) // 定时发布开关
const videosPerDay = ref(1) // 每天发布视频数量
const dailyTimes = ref(['10:00']) // 每天发布时间点列表
const startDays = ref(0) // 从今天开始计算的发布天数，0表示明天，1表示后天
const publishStatus = ref(null) // 发布状态，包含message和type
const uploadResults = ref([]) // 上传结果详情
const uploadSummary = ref({}) // 上传结果统计
const resultsCollapsed = ref(['results']) // 结果区域默认展开

// 平台特定配置
const productLink = ref('') // 抖音：商品链接
const productTitle = ref('') // 抖音：商品名称
const tencentCategory = ref(1) // 腾讯视频号：分区（默认：生活）

// 获取账号状态管理
const accountStore = useAccountStore()

// 平台名称映射
const platformMap = {
  1: '小红书',
  2: '视频号',
  3: '抖音',
  4: '快手',
  5: 'TikTok',
  6: 'Bilibili',
  7: '百家号'
}

// 当前平台名称
const currentPlatformName = computed(() => platformMap[currentPlatform.value])

// 获取平台图标
const getPlatformIcon = (platformKey) => {
  const iconMap = {
    1: '📱', // 小红书
    2: '📺', // 视频号
    3: '🎵', // 抖音
    4: '📹', // 快手
    5: '🎬', // TikTok
    6: '📺', // Bilibili
    7: '📰'  // 百家号
  }
  return iconMap[platformKey]
}

// 切换平台
const switchPlatform = (platformKey) => {
  currentPlatform.value = platformKey
}

// 从指定平台移除账号
const removeAccountFromPlatform = (platformKey, index) => {
  allPlatformAccounts[platformKey].splice(index, 1)
  ElMessage.success('已移除账号')
  
  // 如果当前平台已经没有账号了，自动切换到第一个有账号的平台
  if (allPlatformAccounts[platformKey].length === 0 && currentPlatform.value === platformKey) {
    const firstAvailablePlatform = availablePlatforms.value[0]
    if (firstAvailablePlatform) {
      currentPlatform.value = firstAvailablePlatform.key
    }
  }
}

// 话题相关状态
const topicDialogVisible = ref(false)
const customTopic = ref('')

// 推荐话题列表
const recommendedTopics = [
  '游戏', '电影', '音乐', '美食', '旅行', '文化',
  '科技', '生活', '娱乐', '体育', '教育', '艺术',
  '健康', '时尚', '美妆', '摄影', '宠物', '汽车'
]

// 处理文件上传成功
const handleUploadSuccess = (response, file) => {
  if (response.code === 200) {
    // 获取文件路径
    const filePath = response.data.path || response.data
    // 从路径中提取文件名
    const filename = filePath.split('/').pop()
    
    // 保存文件信息到fileList，包含文件路径和其他信息
    const fileInfo = {
      name: file.name,
      url: materialApi.getMaterialPreviewUrl(filename), // 使用getMaterialPreviewUrl生成预览URL
      path: filePath,
      size: file.size,
      type: file.type
    }
    
    // 添加到文件列表
    fileList.value.push(fileInfo)
    
    // 更新显示列表
    displayFileList.value = [...fileList.value.map(item => ({
      name: item.name,
      url: item.url
    }))]
    
    ElMessage.success('文件上传成功')
    console.log('上传成功:', fileInfo)
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}

// 处理文件上传失败
const handleUploadError = (error) => {
  ElMessage.error('文件上传失败')
  console.error('上传错误:', error)
}

// 删除已上传文件
const removeFile = (index) => {
  // 从文件列表中删除
  fileList.value.splice(index, 1)
  
  // 更新显示列表
  displayFileList.value = [...fileList.value.map(item => ({
    name: item.name,
    url: item.url
  }))]
  
  ElMessage.success('文件删除成功')
}

// 话题相关方法
// 打开添加话题弹窗
const openTopicDialog = () => {
  topicDialogVisible.value = true
}

// 添加自定义话题
const addCustomTopic = () => {
  if (!customTopic.value.trim()) {
    ElMessage.warning('请输入话题内容')
    return
  }
  if (!selectedTopics.value.includes(customTopic.value.trim())) {
    selectedTopics.value.push(customTopic.value.trim())
    customTopic.value = ''
    ElMessage.success('话题添加成功')
  } else {
    ElMessage.warning('话题已存在')
  }
}

// 切换推荐话题
const toggleRecommendedTopic = (topic) => {
  const index = selectedTopics.value.indexOf(topic)
  if (index > -1) {
    selectedTopics.value.splice(index, 1)
  } else {
    selectedTopics.value.push(topic)
  }
}

// 删除话题
const removeTopic = (index) => {
  selectedTopics.value.splice(index, 1)
}

// 确认添加话题
const confirmTopicSelection = () => {
  topicDialogVisible.value = false
  customTopic.value = ''
  ElMessage.success('添加话题完成')
}

// 账号选择相关方法
// 打开账号选择弹窗


// 取消发布
const cancelPublish = () => {
  ElMessage.info('已取消发布')
}

// 确认发布（发布到所有未移除的账号）
const confirmPublish = async () => {
  // 数据验证
  if (fileList.value.length === 0) {
    ElMessage.error('请先上传视频文件')
    throw new Error('请先上传视频文件')
  }
  if (!title.value.trim()) {
    ElMessage.error('请输入标题')
    throw new Error('请输入标题')
  }
  
  // 检查是否有账号
  const hasAccounts = Object.values(allPlatformAccounts).some(accounts => accounts.length > 0)
  if (!hasAccounts) {
    ElMessage.error('请至少保留一个账号')
    throw new Error('请至少保留一个账号')
  }
  
  // 清空之前的结果
  uploadResults.value = []
  uploadSummary.value = {}
  
  // 为每个平台分别发布
  const allResults = []
  const errors = []
  
  for (const platformKey of platforms.map(p => p.key)) {
    const platformAccounts = allPlatformAccounts[platformKey]
    
    // 如果该平台没有账号，跳过
    if (!platformAccounts || platformAccounts.length === 0) {
      continue
    }
    
    // 根据平台准备不同的配置参数
    let platformConfig = {
      category: 0
    }
    
    if (platformKey === 2) {
      // 腾讯视频号：使用分区配置
      platformConfig.category = tencentCategory.value
    } else if (platformKey === 3) {
      // 抖音：使用商品配置
      platformConfig.productLink = productLink.value?.trim() || ''
      platformConfig.productTitle = productTitle.value?.trim() || ''
    }
    
    // 构造该平台的发布数据
    const publishData = {
      type: platformKey,
      title: title.value,
      tags: selectedTopics.value,
      fileList: fileList.value.map(file => file.path),
      accountList: platformAccounts.map(account => account.filePath),
      enableTimer: scheduleEnabled.value ? 1 : 0,
      videosPerDay: scheduleEnabled.value ? videosPerDay.value || 1 : 1,
      dailyTimes: scheduleEnabled.value ? dailyTimes.value || ['10:00'] : ['10:00'],
      startDays: scheduleEnabled.value ? startDays.value || 0 : 0,
      ...platformConfig
    }
    
    try {
      // 调用后端发布API
      const response = await fetch(`${apiBaseUrl}/postVideo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders.value
        },
        body: JSON.stringify(publishData)
      })
      
      const data = await response.json()
      
      if (data.code === 200 && data.data?.results) {
        allResults.push(...data.data.results)
      } else {
        errors.push(`${platformMap[platformKey]}: ${data.msg || '发布失败'}`)
      }
    } catch (error) {
      console.error(`${platformMap[platformKey]}发布错误:`, error)
      errors.push(`${platformMap[platformKey]}: 网络错误`)
    }
  }
  
  // 汇总所有结果
  uploadResults.value = allResults
  const total = allResults.length
  const success = allResults.filter(r => r.status === 'success').length
  const failed = total - success
  
  uploadSummary.value = { total, success, failed }
  
  // 设置发布状态
  if (errors.length > 0) {
    publishStatus.value = {
      message: `部分平台发布失败：${errors.join('; ')}`,
      type: 'error'
    }
    throw new Error(errors.join('; '))
  } else if (failed > 0) {
    publishStatus.value = {
      message: `上传完成：成功 ${success}/${total}，失败 ${failed}/${total}`,
      type: 'warning'
    }
  } else {
    publishStatus.value = {
      message: `上传成功：全部 ${total} 个任务完成`,
      type: 'success'
    }
    
    // 如果全部成功，清空当前数据
    fileList.value = []
    displayFileList.value = []
    title.value = ''
    selectedTopics.value = []
    scheduleEnabled.value = false
  }
}

// 显示上传选项
const showUploadOptions = () => {
  uploadOptionsVisible.value = true
}

// 选择本地上传
const selectLocalUpload = () => {
  uploadOptionsVisible.value = false
  localUploadVisible.value = true
}

// 选择素材库
const selectMaterialLibrary = async () => {
  uploadOptionsVisible.value = false
  
  // 如果素材库为空，先获取素材数据
  if (materials.value.length === 0) {
    try {
      const response = await materialApi.getAllMaterials()
      if (response.code === 200) {
        appStore.setMaterials(response.data)
      } else {
        ElMessage.error('获取素材列表失败')
        return
      }
    } catch (error) {
      console.error('获取素材列表出错:', error)
      ElMessage.error('获取素材列表失败')
      return
    }
  }
  
  selectedMaterials.value = []
  materialLibraryVisible.value = true
}

// 确认素材选择
const confirmMaterialSelection = () => {
  if (selectedMaterials.value.length === 0) {
    ElMessage.warning('请选择至少一个素材')
    return
  }
  
  // 将选中的素材添加到文件列表
  selectedMaterials.value.forEach(materialId => {
    const material = materials.value.find(m => m.id === materialId)
    if (material) {
      const fileInfo = {
        name: material.filename,
        url: materialApi.getMaterialPreviewUrl(material.file_path.split('/').pop()),
        path: material.file_path,
        size: material.filesize * 1024 * 1024, // 转换为字节
        type: 'video/mp4'
      }
      
      // 检查是否已存在相同文件
      const exists = fileList.value.some(file => file.path === fileInfo.path)
      if (!exists) {
        fileList.value.push(fileInfo)
      }
    }
  })
  
  // 更新显示列表
  displayFileList.value = [...fileList.value.map(item => ({
    name: item.name,
    url: item.url
  }))]
  
  const addedCount = selectedMaterials.value.length
  materialLibraryVisible.value = false
  selectedMaterials.value = []
  ElMessage.success(`已添加 ${addedCount} 个素材`)
}



// 重试单个失败的上传任务
const retryUpload = async (failedResult) => {
  ElMessageBox.confirm(
    `确认重新上传 ${failedResult.video.split('\\').pop().split('/').pop()} 到 ${failedResult.account.replace('.json', '')}（${failedResult.platform}）？`,
    '重试上传',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    // 根据平台名称获取平台key
    const platformMap = {
      '抖音': 3,
      '视频号': 2,
      '小红书': 1,
      '快手': 4,
      'TikTok': 5,
      'Bilibili': 6,
      '百家号': 7
    }
    const platformKey = platformMap[failedResult.platform]
    
    // 构造单个文件的上传数据
    const publishData = {
      type: platformKey,
      title: title.value,
      tags: selectedTopics.value,
      fileList: [failedResult.video], // 只上传失败的这个文件
      accountList: [failedResult.account], // 只用这个账号
      enableTimer: scheduleEnabled.value ? 1 : 0,
      videosPerDay: scheduleEnabled.value ? videosPerDay.value || 1 : 1,
      dailyTimes: scheduleEnabled.value ? dailyTimes.value || ['10:00'] : ['10:00'],
      startDays: scheduleEnabled.value ? startDays.value || 0 : 0,
      category: 0,
      productLink: productLink.value?.trim() || '',
      productTitle: productTitle.value?.trim() || ''
    }
    
    try {
      const response = await fetch(`${apiBaseUrl}/postVideo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders.value
        },
        body: JSON.stringify(publishData)
      })
      
      const data = await response.json()
      
      if (data.code === 200 && data.data?.results && data.data.results.length > 0) {
        const result = data.data.results[0]
        
        // 更新上传结果列表中的这一项
        const index = uploadResults.value.findIndex(
          r => r.account === failedResult.account && r.video === failedResult.video
        )
        if (index !== -1) {
          uploadResults.value[index] = result
        }
        
        // 更新统计
        if (result.status === 'success') {
          uploadSummary.value.success++
          uploadSummary.value.failed--
          ElMessage.success('重试成功！')
          
          // 如果全部成功了，更新状态
          if (uploadSummary.value.failed === 0) {
            publishStatus.value.message = `上传成功：全部 ${uploadSummary.value.total} 个任务完成`
            publishStatus.value.type = 'success'
          }
        } else {
          ElMessage.error(`重试失败：${result.message}`)
        }
      } else {
        ElMessage.error('重试失败，请检查网络连接')
      }
    } catch (error) {
      console.error('重试上传出错:', error)
      ElMessage.error('重试失败，请检查网络连接')
    }
  }).catch(() => {
    // 用户取消
  })
}

// 初始化：默认选中所有可用账号
// 初始化：从后端快速加载所有账号并按平台分组
onMounted(async () => {
  try {
    console.log('🔄 开始加载账号数据...')
    // 使用快速接口获取账号数据（不验证有效性，速度快）
    const res = await accountApi.getAccounts()
    console.log('📦 后端返回数据:', res)
    
    if (res.code === 200 && res.data) {
      console.log('📝 原始账号数据:', res.data)
      
      // 更新 accountStore
      accountStore.setAccounts(res.data)
      console.log('🏪 Store中的账号:', accountStore.accounts)
      
      // 按平台分组所有账号
      platforms.forEach(platform => {
        const platformAccounts = accountStore.accounts.filter(
          acc => acc.platform === platformMap[platform.key]
        )
        allPlatformAccounts[platform.key] = platformAccounts
        console.log(`📱 ${platformMap[platform.key]}(${platform.key}):`, platformAccounts)
      })
      
      console.log('✅ 最终分组结果:', allPlatformAccounts)
      console.log('✅ 账号加载完成:', accountStore.accounts.length, '个账号')
    } else {
      console.warn('⚠️ 未获取到账号数据')
      ElMessage.warning('未获取到账号数据，请先在账号管理页面添加账号')
    }
  } catch (error) {
    console.error('❌ 获取账号数据失败:', error)
    ElMessage.error('获取账号数据失败')
  }
})

</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.publish-center {
  display: flex;
  flex-direction: column;
  height: 100%;
  

  
  // 内容区域
  .publish-content {
    flex: 1;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 20px;
    
    // 虚线框样式 - 移到外层
    .section-border {
      border: 2px dashed #409eff !important;
      border-radius: 8px;
      padding: 20px;
      background-color: #f0f9ff;
      margin-bottom: 30px;
    }
    
    // 账号列表样式 - 平台横向，账号纵向（移到这里确保生效）
    .all-accounts-display {
      display: flex;
      flex-direction: row;
      gap: 20px;
      overflow-x: auto;
      padding-bottom: 10px;
      
      .platform-accounts-group {
        border: 1px solid #e4e7ed;
        border-radius: 8px;
        padding: 15px;
        background-color: #fafafa;
        flex-shrink: 0;
        min-width: 150px;
        max-width: 200px;
        
        .platform-group-header {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 5px;
          margin-bottom: 15px;
          font-weight: 500;
          color: #303133;
          font-size: 14px;
          padding-bottom: 10px;
          border-bottom: 2px solid #e4e7ed;
          
          .platform-icon {
            font-size: 24px;
          }
          
          .platform-name {
            font-size: 14px;
            font-weight: 600;
          }
          
          .account-count {
            color: #909399;
            font-size: 12px;
          }
        }
        
        .platform-accounts-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          
          .account-tag {
            font-size: 13px;
            padding: 8px 12px;
            cursor: default;
            width: 100%;
            justify-content: space-between;
          }
        }
      }
    }
    
    .tab-content-wrapper {
      display: flex;
      justify-content: center;
      
      .tab-content {
        width: 100%;
        max-width: 800px;
        
        h3 {
          font-size: 16px;
          font-weight: 500;
          color: $text-primary;
          margin: 0 0 10px 0;
        }
        
        .upload-section,
        .account-section,
        .platform-section,
        .title-section,
        .product-section,
        .topic-section,
        .schedule-section {
          margin-bottom: 30px;
        }
        
        .platform-checkboxes {
          display: flex;
          gap: 20px;
          flex-wrap: wrap;
          
          .platform-checkbox {
            margin-right: 0;
          }
        }

        .product-section {
          .product-name-input,
          .product-link-input {
            margin-bottom: 5px;
          }
        }
        
        .video-upload {
          width: 100%;
          
          :deep(.el-upload-dragger) {
            width: 100%;
            height: 180px;
          }
        }
        
        .account-input {
          max-width: 400px;
        }
        
        .platform-buttons {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          
          .platform-btn {
            min-width: 100px;
            height: 40px;
            font-size: 15px;
            font-weight: 500;
          }
        }
        
        // 平台特定配置样式
        .platform-config-section {
          margin-bottom: 30px;
          
          .platform-config {
            background-color: #f5f7fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 10px;
            
            :deep(.el-form-item) {
              margin-bottom: 15px;
              
              &:last-child {
                margin-bottom: 0;
              }
            }
          }
        }
        
        .title-input {
          max-width: 600px;
        }
        
        .topic-display {
          display: flex;
          flex-direction: column;
          gap: 12px;
          
          .selected-topics {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            min-height: 32px;
            
            .topic-tag {
              font-size: 14px;
            }
          }
          
          .select-topic-btn {
            align-self: flex-start;
          }
        }
        
        .schedule-controls {
          display: flex;
          flex-direction: column;
          gap: 15px;

          .schedule-settings {
            margin-top: 15px;
            padding: 15px;
            background-color: #f5f7fa;
            border-radius: 4px;

            .schedule-item {
              display: flex;
              align-items: center;
              margin-bottom: 15px;

              &:last-child {
                margin-bottom: 0;
              }

              .label {
                min-width: 120px;
                margin-right: 10px;
              }

              .el-time-select {
                margin-right: 10px;
              }

              .el-button {
                margin-left: 10px;
              }
            }
          }
        }
        
        .action-buttons {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid #ebeef5;
        }
      }
    }
  }
  
  // 上传结果详情样式
  .upload-results-section {
    margin-top: 20px;
    margin-bottom: 20px;
    
    .results-header {
      display: flex;
      align-items: center;
      gap: 15px;
      width: 100%;
      
      h3 {
        font-size: 16px;
        font-weight: 500;
        margin: 0;
        color: #303133;
      }
      
      .summary-tag {
        margin-left: auto;
      }
    }
    
    .el-collapse {
      border: none;
      
      :deep(.el-collapse-item__header) {
        background-color: #f5f7fa;
        border: 1px solid #dcdfe6;
        padding: 10px 15px;
        border-radius: 4px;
        font-weight: 500;
      }
      
      :deep(.el-collapse-item__content) {
        padding: 15px 0;
      }
    }
    
    .el-table {
      margin-top: 0;
    }
  }
  
  // 已上传文件列表样式
  .uploaded-files {
    margin-top: 20px;
    
    h4 {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 12px;
      color: #303133;
    }
    
    .file-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      
      .file-item {
        display: flex;
        align-items: center;
        padding: 10px 15px;
        background-color: #f5f7fa;
        border-radius: 4px;
        
        .el-link {
          margin-right: 10px;
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .file-size {
          color: #909399;
          font-size: 13px;
          margin-right: auto;
        }
      }
    }
  }
  
  // 添加话题弹窗样式
  .topic-dialog {
    .topic-dialog-content {
      .custom-topic-input {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
        
        .custom-input {
          flex: 1;
        }
      }
      
      .recommended-topics {
        h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
          font-weight: 500;
          color: #303133;
        }
        
        .topic-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 12px;
          
          .topic-btn {
            height: 36px;
            font-size: 14px;
            border-radius: 6px;
            min-width: 100px;
            padding: 0 12px;
            white-space: nowrap;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            
            &.el-button--primary {
              background-color: #409eff;
              border-color: #409eff;
              color: white;
            }
          }
        }
      }
    }
    
    .dialog-footer {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
    }
  }
}
</style>
