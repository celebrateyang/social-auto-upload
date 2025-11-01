import json
import pathlib
import random
import tempfile
import subprocess
import time
from biliup.plugins.bili_webup import BiliBili, Data

from utils.log import bilibili_logger

# 导入配置（如果存在）
try:
    from .config import *
except ImportError:
    # 使用默认配置
    UPLOAD_THREAD_NUM = 3
    UPLOAD_LINE = 'AUTO'
    AUTO_COVER = True
    COVER_TIME_OFFSET = '00:00:01'
    DEFAULT_TAGS = ['知识分享', '学习']
    MAX_TAGS = 12
    MAX_TAG_LENGTH = 20
    MAX_TITLE_LENGTH = 80
    MAX_DESC_LENGTH = 2000
    MAX_RETRY_TIMES = 3
    RETRY_DELAY = 5


def extract_keys_from_json(data):
    """Extract specified keys from the provided JSON data."""
    keys_to_extract = ["SESSDATA", "bili_jct", "DedeUserID__ckMd5", "DedeUserID", "access_token"]
    extracted_data = {}

    # Extracting cookie data
    for cookie in data['cookie_info']['cookies']:
        if cookie['name'] in keys_to_extract:
            extracted_data[cookie['name']] = cookie['value']

    # Extracting access_token (optional, set to None if not found)
    if "access_token" in data.get('token_info', {}):
        extracted_data['access_token'] = data['token_info']['access_token']
    else:
        # Set to None instead of omitting, to avoid KeyError
        extracted_data['access_token'] = None

    return extracted_data


def read_cookie_json_file(filepath: pathlib.Path):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = json.load(file)
        return content


def random_emoji():
    emoji_list = ["🍏", "🍎", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍈", "🍒", "🍑", "🍍", "🥭", "🥥", "🥝",
                  "🍅", "🍆", "🥑", "🥦", "🥒", "🥬", "🌶", "🌽", "🥕", "🥔", "🍠", "🥐", "🍞", "🥖", "🥨", "🥯", "🧀", "🥚", "🍳", "🥞",
                  "🥓", "🥩", "🍗", "🍖", "🌭", "🍔", "🍟", "🍕", "🥪", "🥙", "🌮", "🌯", "🥗", "🥘", "🥫", "🍝", "🍜", "🍲", "🍛", "🍣",
                  "🍱", "🥟", "🍤", "🍙", "🍚", "🍘", "🍥", "🥮", "🥠", "🍢", "🍡", "🍧", "🍨", "🍦", "🥧", "🍰", "🎂", "🍮", "🍭", "🍬",
                  "🍫", "🍿", "🧂", "🍩", "🍪", "🌰", "🥜", "🍯", "🥛", "🍼", "☕️", "🍵", "🥤", "🍶", "🍻", "🥂", "🍷", "🥃", "🍸", "🍹",
                  "🍾", "🥄", "🍴", "🍽", "🥣", "🥡", "🥢"]
    return random.choice(emoji_list)


def extract_video_cover(video_path: pathlib.Path, time_offset: str = "00:00:01") -> pathlib.Path:
    """
    从视频中提取封面图片
    
    Args:
        video_path: 视频文件路径
        time_offset: 提取封面的时间点，默认第1秒
    
    Returns:
        封面图片的临时文件路径，如果失败返回 None
    """
    try:
        # 创建临时文件
        temp_cover = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_cover_path = pathlib.Path(temp_cover.name)
        temp_cover.close()
        
        # 使用 ffmpeg 提取封面
        cmd = [
            'ffmpeg',
            '-ss', time_offset,
            '-i', str(video_path),
            '-vframes', '1',
            '-q:v', '2',  # 高质量
            '-y',  # 覆盖已存在文件
            str(temp_cover_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode == 0 and temp_cover_path.exists():
            bilibili_logger.info(f"成功从视频提取封面: {temp_cover_path}")
            return temp_cover_path
        else:
            bilibili_logger.warning("封面提取失败")
            return None
            
    except FileNotFoundError:
        bilibili_logger.warning("ffmpeg 未安装，无法提取封面")
        return None
    except Exception as e:
        bilibili_logger.warning(f"封面提取出错: {e}")
        return None


class BilibiliUploader(object):
    def __init__(self, cookie_data, file: pathlib.Path, title, desc, tid, tags, dtime, 
                 cover_path=None, auto_cover=None, upload_thread_num=None, lines=None):
        """
        B站视频上传器
        
        Args:
            cookie_data: Cookie 数据字典
            file: 视频文件路径
            title: 视频标题
            desc: 视频描述
            tid: 分区 ID
            tags: 标签列表或逗号分隔的字符串
            dtime: 定时发布时间戳（0表示立即发布）
            cover_path: 自定义封面路径（可选）
            auto_cover: 是否自动从视频提取封面（None则使用配置文件）
            upload_thread_num: 上传线程数（None则使用配置文件）
            lines: 上传线路（None则使用配置文件）
        """
        self.upload_thread_num = upload_thread_num if upload_thread_num else UPLOAD_THREAD_NUM
        self.copyright = 1
        self.lines = lines if lines else UPLOAD_LINE
        self.cookie_data = cookie_data
        self.file = file
        self.title = title
        self.desc = desc
        self.tid = tid
        self.tags = tags
        self.dtime = dtime
        self.cover_path = cover_path
        self.auto_cover = auto_cover if auto_cover is not None else AUTO_COVER
        self._temp_cover = None  # 临时封面文件，用于清理
        self._init_data()

    def _init_data(self):
        self.data = Data()
        self.data.copyright = self.copyright
        self.data.source = ""  # 原创视频，source 为空
        
        # 处理标题：限制在配置的最大长度以内
        title = self.title[:MAX_TITLE_LENGTH] if len(self.title) > MAX_TITLE_LENGTH else self.title
        if not title or len(title.strip()) == 0:
            title = "未命名视频"
        self.data.title = title
        
        # 处理描述：限制在配置的最大长度以内
        desc = self.desc[:MAX_DESC_LENGTH] if len(self.desc) > MAX_DESC_LENGTH else self.desc
        self.data.desc = desc if desc else ""
        
        self.data.tid = self.tid
        
        # 处理标签：确保是列表且至少有2个标签
        if isinstance(self.tags, str):
            tag_list = [t.strip() for t in self.tags.split(',') if t.strip()]
        elif isinstance(self.tags, list):
            tag_list = [str(t).strip() for t in self.tags if str(t).strip()]
        else:
            tag_list = []
        
        # 如果标签少于2个，添加默认标签
        if len(tag_list) < 2:
            tag_list.extend(DEFAULT_TAGS[:2 - len(tag_list)])
        
        # B站标签限制：使用配置中的限制
        tag_list = tag_list[:MAX_TAGS]
        tag_list = [t[:MAX_TAG_LENGTH] for t in tag_list]
        
        # set_tag 方法接受列表
        self.data.set_tag(tag_list)
        self.data.dtime = self.dtime

    def upload(self):
        try:
            with BiliBili(self.data) as bili:
                bili.login_by_cookies(self.cookie_data)
                
                # 处理封面图片
                cover_to_upload = self.cover_path
                
                # 如果没有提供封面且开启了自动封面，则从视频提取
                if not cover_to_upload and self.auto_cover:
                    bilibili_logger.info("尝试从视频提取封面...")
                    self._temp_cover = extract_video_cover(self.file)
                    if self._temp_cover:
                        cover_to_upload = self._temp_cover
                
                # 上传封面
                if cover_to_upload:
                    try:
                        cover_url = bili.cover_up(str(cover_to_upload))
                        self.data.cover = cover_url
                        bilibili_logger.info("封面上传成功")
                    except Exception as e:
                        bilibili_logger.warning(f"封面上传失败: {e}")
                
                # 上传视频文件
                video_part = bili.upload_file(str(self.file), lines=self.lines,
                                              tasks=self.upload_thread_num)
                video_part['title'] = self.title
                self.data.append(video_part)
                
                # 使用网页端API提交（只需要 bili_jct，不需要 access_token）
                ret = bili.submit(submit_api='web')
                
                if ret.get('code') == 0:
                    bilibili_logger.success(f'[+] {self.file.name} 上传成功')
                    return True
                else:
                    bilibili_logger.error(f'[-] {self.file.name} 上传失败: {ret.get("message")}')
                    return False
                    
        finally:
            # 清理临时封面文件
            if self._temp_cover and self._temp_cover.exists():
                try:
                    self._temp_cover.unlink()
                    bilibili_logger.info("临时封面已清理")
                except Exception as e:
                    bilibili_logger.warning(f"清理临时封面失败: {e}")
