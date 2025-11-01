import asyncio
import sqlite3

from playwright.async_api import async_playwright

from myUtils.auth import check_cookie
from utils.base_social_media import set_init_script
import uuid
from pathlib import Path
from conf import BASE_DIR

# 抖音登录
async def douyin_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        original_url = page.url
        img_locator = page.get_by_role("img", name="二维码")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put("500")
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(3, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO user_info (type, filePath, userName, status)
                                VALUES (?, ?, ?, ?)
                                ''', (3, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")


# 视频号登录
async def get_tencent_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        original_url = page.url

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        # 等待 iframe 出现（最多等 60 秒）
        iframe_locator = page.frame_locator("iframe").first

        # 获取 iframe 中的第一个 img 元素
        img_locator = iframe_locator.get_by_role("img").first

        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(2,f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO user_info (type, filePath, userName, status)
                                VALUES (?, ?, ?, ?)
                                ''', (2, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 快手登录
async def get_ks_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击“立即登录”按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                        INSERT INTO user_info (type, filePath, userName, status)
                                        VALUES (?, ?, ?, ?)
                                        ''', (4, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")

# 小红书登录
async def xiaohongshu_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO user_info (type, filePath, userName, status)
                           VALUES (?, ?, ?, ?)
                           ''', (1, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 用户状态已记录")
        status_queue.put("200")


# TikTok登录
async def get_tiktok_cookie(id, status_queue):
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB',
            ],
            'headless': False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login?lang=en")
        await page.pause()
        
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        
        await page.close()
        await context.close()
        await browser.close()
        
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_info (type, filePath, userName, status)
                VALUES (?, ?, ?, ?)
            ''', (5, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ TikTok用户状态已记录")
        status_queue.put("200")


# Bilibili登录
async def get_bilibili_cookie(id, status_queue):
    """
    Bilibili使用浏览器登录方式
    会打开浏览器让用户扫码登录，然后保存cookie
    """
    try:
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        cookie_file = cookies_dir / f"{uuid_v1}.json"
        
        print(f"[Bilibili] 准备打开浏览器进行登录...")
        print(f"[Bilibili] Cookie文件将保存到: {cookie_file}")
        
        # 使用playwright打开浏览器进行登录
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            context = await set_init_script(context)
            page = await context.new_page()
            
            # 访问B站登录页面
            await page.goto("https://passport.bilibili.com/login")
            
            print("[Bilibili] 请在浏览器中扫码登录...")
            print("[Bilibili] 登录完成后，点击调试器的继续按钮...")
            
            # 暂停，等待用户登录
            await page.pause()
            
            # 登录成功后，访问创作中心页面获取 access_token
            print("[Bilibili] 正在获取 access_token...")
            access_token = None
            
            try:
                # 先从当前页面的 cookies 中尝试获取
                current_cookies = await context.cookies()
                for cookie in current_cookies:
                    if cookie['name'] == 'ac_time_value':
                        access_token = cookie['value']
                        print(f"[Bilibili] ✅ 从登录页面 cookie 获取到 access_token (前20位): {access_token[:20]}...")
                        break
                
                # 如果还没有，访问创作中心
                if not access_token:
                    print("[Bilibili] 登录页面未找到 token，正在访问创作中心...")
                    await page.goto("https://member.bilibili.com/platform/home")
                    await page.wait_for_timeout(3000)  # 等待更长时间
                    
                    # 再次检查 cookies
                    current_cookies = await context.cookies()
                    for cookie in current_cookies:
                        if cookie['name'] == 'ac_time_value':
                            access_token = cookie['value']
                            print(f"[Bilibili] ✅ 从创作中心 cookie 获取到 access_token (前20位): {access_token[:20]}...")
                            break
                    
                    # 尝试从 localStorage
                    if not access_token:
                        try:
                            access_token = await page.evaluate("() => localStorage.getItem('ac_time_value')")
                            if access_token:
                                print(f"[Bilibili] ✅ 从 localStorage 获取到 access_token (前20位): {access_token[:20]}...")
                        except:
                            pass
                    
                    # 尝试从页面变量
                    if not access_token:
                        try:
                            access_token = await page.evaluate("""() => {
                                // 尝试多个可能的位置
                                return window.access_token || 
                                       window.__INITIAL_STATE__?.access_token ||
                                       window.accessToken;
                            }""")
                            if access_token:
                                print(f"[Bilibili] ✅ 从页面变量获取到 access_token (前20位): {access_token[:20]}...")
                        except:
                            pass
                
            except Exception as e:
                print(f"[Bilibili] 获取 access_token 时出错: {e}")
                import traceback
                traceback.print_exc()
            
            # 保存cookie
            await context.storage_state(path=str(cookie_file))
            
            await page.close()
            await context.close()
            await browser.close()
        
        # 检查cookie文件是否成功生成
        if cookie_file.exists():
            print("[Bilibili] ✅ Cookie文件生成成功")
            
            # 需要转换cookie格式以适配biliup的要求
            import json
            with open(cookie_file, 'r', encoding='utf-8') as f:
                playwright_cookies = json.load(f)
            
            # 转换为biliup需要的格式
            bilibili_cookie_data = {
                "cookie_info": {
                    "cookies": []
                },
                "token_info": {}
            }
            
            # 提取关键cookie
            for cookie in playwright_cookies.get('cookies', []):
                if cookie['name'] in ['SESSDATA', 'bili_jct', 'DedeUserID__ckMd5', 'DedeUserID', 'ac_time_value']:
                    bilibili_cookie_data['cookie_info']['cookies'].append({
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie.get('domain', '.bilibili.com'),
                        'path': cookie.get('path', '/')
                    })
                    # 如果是 ac_time_value，也作为 access_token
                    if cookie['name'] == 'ac_time_value':
                        access_token = cookie['value']
            
            # 添加 access_token 到 token_info
            if access_token:
                bilibili_cookie_data['token_info']['access_token'] = access_token
                print(f"[Bilibili] ✅ 成功获取 access_token")
            else:
                print(f"[Bilibili] ⚠️  未找到 access_token，上传可能会失败")
            
            # 保存转换后的格式
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(bilibili_cookie_data, f, ensure_ascii=False, indent=2)
            
            # 保存到数据库
            with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_info (type, filePath, userName, status)
                    VALUES (?, ?, ?, ?)
                ''', (6, f"{uuid_v1}.json", id, 1))
                conn.commit()
                print("✅ Bilibili用户状态已记录")
            
            status_queue.put("200")
        else:
            print("[Bilibili] ❌ Cookie文件未生成，登录可能失败")
            status_queue.put("500")
            
    except Exception as e:
        print(f"[Bilibili] ❌ 登录失败: {e}")
        import traceback
        traceback.print_exc()
        status_queue.put("500")


# 百家号登录
async def get_baijiahao_cookie(id, status_queue):
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://baijiahao.baidu.com/builder/theme/bjh/login")
        await page.pause()
        
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        
        await page.close()
        await context.close()
        await browser.close()
        
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_info (type, filePath, userName, status)
                VALUES (?, ?, ?, ?)
            ''', (7, f"{uuid_v1}.json", id, 1))
            conn.commit()
            print("✅ 百家号用户状态已记录")
        status_queue.put("200")


# a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# print(a)
