import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.async_api import async_playwright

from conf import BASE_DIR, LOCAL_CHROME_PATH
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day


async def _upload_single_video_tencent_async(title, file, tags, publish_datetime, cookie, category, account_name, playwright, browser):
    """单个视频上传任务（腾讯视频号）- 异步版本"""
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
        await app.upload(playwright, browser)
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


async def _post_video_tencent_with_browser(tasks):
    """使用浏览器实例批量上传（腾讯视频号）"""
    results = []
    
    async with async_playwright() as playwright:
        print("[腾讯视频号] 创建浏览器实例...")
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(headless=False, executable_path=LOCAL_CHROME_PATH)
        else:
            browser = await playwright.chromium.launch(headless=False)
        print("[腾讯视频号] 浏览器实例创建成功，开始上传任务...")
        
        try:
            for task in tasks:
                try:
                    result = await _upload_single_video_tencent_async(*task, playwright, browser)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'platform': '腾讯视频号',
                        'account': task[6],
                        'video': task[1].name,
                        'status': 'failed',
                        'message': f'执行异常: {str(e)}',
                        'error_detail': traceback.format_exc()
                    })
        finally:
            await browser.close()
            print("[腾讯视频号] 浏览器已关闭")
    
    return results

def post_video_tencent(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    """
    腾讯视频号批量上传（复用浏览器实例）
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
    
    # 在异步上下文中执行所有任务
    results = asyncio.run(_post_video_tencent_with_browser(tasks))
    return results


async def _upload_single_video_douyin_async(title, file, tags, publish_datetime, cookie, category, productLink, productTitle, account_name, playwright, browser):
    """单个视频上传任务（抖音）- 异步版本"""
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
        await app.upload(playwright, browser)  # 传入browser实例
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


async def _post_video_douyin_with_browser(tasks):
    """使用浏览器实例批量上传（抖音）"""
    results = []
    
    # 使用 async with 管理 playwright 生命周期
    async with async_playwright() as playwright:
        # 创建浏览器实例
        print("[抖音] 创建浏览器实例...")
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(headless=False, executable_path=LOCAL_CHROME_PATH)
        else:
            browser = await playwright.chromium.launch(headless=False)
        print("[抖音] 浏览器实例创建成功，开始上传任务...")
        
        try:
            # 串行执行上传任务（复用浏览器）
            for task in tasks:
                try:
                    result = await _upload_single_video_douyin_async(*task, playwright, browser)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'platform': '抖音',
                        'account': task[8],
                        'video': task[1].name,
                        'status': 'failed',
                        'message': f'执行异常: {str(e)}',
                        'error_detail': traceback.format_exc()
                    })
        finally:
            # 关闭浏览器
            await browser.close()
            print("[抖音] 浏览器已关闭")
    
    return results

def post_video_DouYin(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0,
                      productLink = '', productTitle = ''):
    """
    抖音批量上传（复用浏览器实例）
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
    
    # 在异步上下文中执行所有任务
    results = asyncio.run(_post_video_douyin_with_browser(tasks))
    return results


async def _upload_single_video_ks_async(title, file, tags, publish_datetime, cookie, account_name, playwright, browser):
    """单个视频上传任务（快手）- 异步版本"""
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
        await app.upload(playwright, browser)
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


async def _post_video_ks_with_browser(tasks):
    """使用浏览器实例批量上传（快手）"""
    results = []
    
    async with async_playwright() as playwright:
        print("[快手] 创建浏览器实例...")
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(headless=False, executable_path=LOCAL_CHROME_PATH)
        else:
            browser = await playwright.chromium.launch(headless=False)
        print("[快手] 浏览器实例创建成功，开始上传任务...")
        
        try:
            for task in tasks:
                try:
                    result = await _upload_single_video_ks_async(*task, playwright, browser)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'platform': '快手',
                        'account': task[5],
                        'video': task[1].name,
                        'status': 'failed',
                        'message': f'执行异常: {str(e)}',
                        'error_detail': traceback.format_exc()
                    })
        finally:
            await browser.close()
            print("[快手] 浏览器已关闭")
    
    return results

def post_video_ks(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    """
    快手批量上传（复用浏览器实例）
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
    
    # 在异步上下文中执行所有任务
    results = asyncio.run(_post_video_ks_with_browser(tasks))
    return results

async def _upload_single_video_xhs_async(title, file, tags, publish_datetime, cookie, account_name, playwright, browser):
    """单个视频上传任务（小红书）- 异步版本"""
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
        await app.upload(playwright, browser)
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


async def _post_video_xhs_with_browser(tasks):
    """使用浏览器实例批量上传（小红书）"""
    results = []
    
    async with async_playwright() as playwright:
        print("[小红书] 创建浏览器实例...")
        if LOCAL_CHROME_PATH:
            browser = await playwright.chromium.launch(headless=False, executable_path=LOCAL_CHROME_PATH)
        else:
            browser = await playwright.chromium.launch(headless=False)
        print("[小红书] 浏览器实例创建成功，开始上传任务...")
        
        try:
            for task in tasks:
                try:
                    result = await _upload_single_video_xhs_async(*task, playwright, browser)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'platform': '小红书',
                        'account': task[5],
                        'video': task[1].name,
                        'status': 'failed',
                        'message': f'执行异常: {str(e)}',
                        'error_detail': traceback.format_exc()
                    })
        finally:
            await browser.close()
            print("[小红书] 浏览器已关闭")
    
    return results

def post_video_xhs(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    """
    小红书批量上传（复用浏览器实例）
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
    
    # 在异步上下文中执行所有任务
    results = asyncio.run(_post_video_xhs_with_browser(tasks))
    return results



# post_video("333",["demo.mp4"],"d","d")
# post_video_DouYin("333",["demo.mp4"],"d","d")