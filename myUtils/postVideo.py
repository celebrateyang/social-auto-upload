import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day


def _upload_single_video_tencent(title, file, tags, publish_datetime, cookie, category, account_name):
    """单个视频上传任务（腾讯视频号）"""
    result = {
        'platform': '腾讯视频号',
        'account': account_name,
        'video': file.name,
        'status': 'success',
        'message': '',
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': ''
    }
    
    try:
        print(f"[腾讯视频号] 开始上传: {account_name} - {file.name}")
        app = TencentVideo(title, str(file), tags, publish_datetime, cookie, category)
        asyncio.run(app.main(), debug=False)
        result['status'] = 'success'
        result['message'] = '上传成功'
        print(f"[腾讯视频号] 上传成功: {account_name} - {file.name}")
    except Exception as e:
        result['status'] = 'failed'
        result['message'] = str(e)
        result['error_detail'] = traceback.format_exc()
        print(f"[腾讯视频号] 上传失败: {account_name} - {file.name} - {str(e)}")
    finally:
        result['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return result


def post_video_tencent(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    """
    腾讯视频号批量上传（支持并发）
    返回: list of dict，每个dict包含上传结果
    """
    # 生成文件的完整路径
    account_files = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    
    # 生成发布时间
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    
    # 准备所有上传任务
    tasks = []
    for cookie in account_files:
        account_name = cookie.stem
        for index, file in enumerate(files):
            tasks.append((title, file, tags, publish_datetimes[index], cookie, category, account_name))
    
    # 并发执行上传任务（最多3个并发）
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_upload_single_video_tencent, *task): task for task in tasks}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                task = futures[future]
                results.append({
                    'platform': '腾讯视频号',
                    'account': task[6],
                    'video': task[1].name,
                    'status': 'failed',
                    'message': f'执行异常: {str(e)}',
                    'error_detail': traceback.format_exc()
                })
    
    return results


def _upload_single_video_douyin(title, file, tags, publish_datetime, cookie, category, productLink, productTitle, account_name):
    """单个视频上传任务（抖音）"""
    result = {
        'platform': '抖音',
        'account': account_name,
        'video': file.name,
        'status': 'success',
        'message': '',
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': ''
    }
    
    try:
        print(f"[抖音] 开始上传: {account_name} - {file.name}")
        app = DouYinVideo(title, str(file), tags, publish_datetime, cookie, category, productLink, productTitle)
        asyncio.run(app.main(), debug=False)
        result['status'] = 'success'
        result['message'] = '上传成功'
        print(f"[抖音] 上传成功: {account_name} - {file.name}")
    except Exception as e:
        result['status'] = 'failed'
        result['message'] = str(e)
        result['error_detail'] = traceback.format_exc()
        print(f"[抖音] 上传失败: {account_name} - {file.name} - {str(e)}")
    finally:
        result['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return result


def post_video_DouYin(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0,
                      productLink = '', productTitle = ''):
    """
    抖音批量上传（支持并发）
    返回: list of dict，每个dict包含上传结果
    """
    # 生成文件的完整路径
    account_files = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    
    # 生成发布时间
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    
    # 准备所有上传任务
    tasks = []
    for cookie in account_files:
        account_name = cookie.stem  # 使用文件名作为账号名称
        for index, file in enumerate(files):
            tasks.append((title, file, tags, publish_datetimes[index], cookie, category, productLink, productTitle, account_name))
    
    # 并发执行上传任务（最多3个并发）
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_upload_single_video_douyin, *task): task for task in tasks}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                task = futures[future]
                results.append({
                    'platform': '抖音',
                    'account': task[8],
                    'video': task[1].name,
                    'status': 'failed',
                    'message': f'执行异常: {str(e)}',
                    'error_detail': traceback.format_exc()
                })
    
    return results


def _upload_single_video_ks(title, file, tags, publish_datetime, cookie, account_name):
    """单个视频上传任务（快手）"""
    result = {
        'platform': '快手',
        'account': account_name,
        'video': file.name,
        'status': 'success',
        'message': '',
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': ''
    }
    
    try:
        print(f"[快手] 开始上传: {account_name} - {file.name}")
        app = KSVideo(title, str(file), tags, publish_datetime, cookie)
        asyncio.run(app.main(), debug=False)
        result['status'] = 'success'
        result['message'] = '上传成功'
        print(f"[快手] 上传成功: {account_name} - {file.name}")
    except Exception as e:
        result['status'] = 'failed'
        result['message'] = str(e)
        result['error_detail'] = traceback.format_exc()
        print(f"[快手] 上传失败: {account_name} - {file.name} - {str(e)}")
    finally:
        result['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return result


def post_video_ks(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    """
    快手批量上传（支持并发）
    返回: list of dict，每个dict包含上传结果
    """
    # 生成文件的完整路径
    account_files = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    
    # 生成发布时间
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    
    # 准备所有上传任务
    tasks = []
    for cookie in account_files:
        account_name = cookie.stem
        for index, file in enumerate(files):
            tasks.append((title, file, tags, publish_datetimes[index], cookie, account_name))
    
    # 并发执行上传任务（最多3个并发）
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_upload_single_video_ks, *task): task for task in tasks}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                task = futures[future]
                results.append({
                    'platform': '快手',
                    'account': task[5],
                    'video': task[1].name,
                    'status': 'failed',
                    'message': f'执行异常: {str(e)}',
                    'error_detail': traceback.format_exc()
                })
    
    return results

def _upload_single_video_xhs(title, file, tags, publish_datetime, cookie, account_name):
    """单个视频上传任务（小红书）"""
    result = {
        'platform': '小红书',
        'account': account_name,
        'video': file.name,
        'status': 'success',
        'message': '',
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': ''
    }
    
    try:
        print(f"[小红书] 开始上传: {account_name} - {file.name}")
        app = XiaoHongShuVideo(title, file, tags, publish_datetime, cookie)
        asyncio.run(app.main(), debug=False)
        result['status'] = 'success'
        result['message'] = '上传成功'
        print(f"[小红书] 上传成功: {account_name} - {file.name}")
    except Exception as e:
        result['status'] = 'failed'
        result['message'] = str(e)
        result['error_detail'] = traceback.format_exc()
        print(f"[小红书] 上传失败: {account_name} - {file.name} - {str(e)}")
    finally:
        result['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return result


def post_video_xhs(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    """
    小红书批量上传（支持并发）
    返回: list of dict，每个dict包含上传结果
    """
    # 生成文件的完整路径
    account_files = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    file_num = len(files)
    
    # 生成发布时间
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(file_num, videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = 0
    
    # 准备所有上传任务
    tasks = []
    for cookie in account_files:
        account_name = cookie.stem
        for file in files:
            tasks.append((title, file, tags, publish_datetimes, cookie, account_name))
    
    # 并发执行上传任务（最多3个并发）
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_upload_single_video_xhs, *task): task for task in tasks}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                task = futures[future]
                results.append({
                    'platform': '小红书',
                    'account': task[5],
                    'video': task[1].name,
                    'status': 'failed',
                    'message': f'执行异常: {str(e)}',
                    'error_detail': traceback.format_exc()
                })
    
    return results



# post_video("333",["demo.mp4"],"d","d")
# post_video_DouYin("333",["demo.mp4"],"d","d")