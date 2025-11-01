# Bilibili 上传配置文件

# 上传线程数（1-3，数字越大上传越快但消耗资源越多）
UPLOAD_THREAD_NUM = 3

# 上传线路选择（'AUTO', 'bda2', 'ws', 'qn'）
# AUTO: 自动选择最快线路
# bda2: 百度云
# ws: 网宿
# qn: 七牛云
UPLOAD_LINE = 'AUTO'

# 是否自动从视频提取封面
AUTO_COVER = True

# 封面提取时间点（格式：HH:MM:SS）
COVER_TIME_OFFSET = '00:00:01'

# 默认标签（当用户提供的标签少于2个时使用）
DEFAULT_TAGS = ['知识分享', '学习']

# 标签限制
MAX_TAGS = 12  # B站最多12个标签
MAX_TAG_LENGTH = 20  # 每个标签最长20字符

# 标题和描述限制
MAX_TITLE_LENGTH = 80  # B站标题最多80字符
MAX_DESC_LENGTH = 2000  # B站描述最多2000字符

# 重试配置
MAX_RETRY_TIMES = 3  # 最大重试次数
RETRY_DELAY = 5  # 重试延迟（秒）
