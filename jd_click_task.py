#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cron: 59 9,19 * * *
new Env('定时抢券任务');
"""
import os
import json
import time
import random
import requests
import threading
from datetime import datetime, timedelta

# --- 配置读取 ---
# 从环境变量中获取 JD_COOKIE，支持多个账号，用 & 或换行符分隔
jd_cookies = os.getenv('JD_COOKIE', '').split('&')
if not jd_cookies or jd_cookies == ['']:
    print("错误：未找到 JD_COOKIE 环境变量。请在青龙面板配置中添加。")
    exit()

# 从环境变量中获取点击任务的URL
click_url = os.getenv('JD_CLICK_URL')
if not click_url:
    print("错误：未找到 JD_CLICK_URL 环境变量。请配置任务所需的URL。")
    exit()

# 从环境变量中获取点击任务的请求体 (Body)
click_body_str = os.getenv('JD_CLICK_BODY')
if not click_body_str:
    print("错误：未找到 JD_CLICK_BODY 环境变量。请配置任务所需的请求体。")
    exit()

# 从环境变量中获取 User-Agent
user_agent = os.getenv('JD_CLICK_USER_AGENT', 'jdapp;iPhone;10.0.2;14.3;network/wifi;model/iPhone12,1;osVer/14.3.1;appBuild/88631;')

# 【新增】抢券时间配置，用逗号分隔，例如 "10:00:00,20:00:00"
target_times_str = os.getenv('JD_CLICK_TARGET_TIMES')

def do_click_task(cookie, index, session):
    """
    执行单个账号的点击任务
    使用 session 来复用TCP连接，提高效率
    """
    nickname = cookie.split('pt_pin=')[1].split(';')[0]
    
    headers = {
        'Cookie': cookie,
        'User-Agent': user_agent,
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': '*/*',
        'Accept-Language': 'zh-cn',
        'Connection': 'keep-alive',
        'Host': click_url.split('/')[2]
    }

    try:
        body_data = json.dumps(json.loads(click_body_str))
    except json.JSONDecodeError:
        body_data = click_body_str

    try:
        # 记录发送前的时间戳
        start_time = datetime.now()
        print(f"账号 {index} ({nickname}) 于 {start_time.strftime('%H:%M:%S.%f')} 发送请求...")
        
        response = session.post(click_url, headers=headers, data=body_data, timeout=5)
        response.raise_for_status()
        
        end_time = datetime.now()
        print(f"账号 {index} ({nickname}) 于 {end_time.strftime('%H:%M:%S.%f')} 收到响应, 耗时 {(end_time - start_time).total_seconds():.3f} 秒。")
        
        # 尝试打印JSON响应
        try:
            print(f"  响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"  响应内容 (非JSON): {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"账号 {index} ({nickname}) 请求失败: {e}")
    except Exception as e:
        print(f"账号 {index} ({nickname}) 发生未知错误: {e}")

def normal_mode():
    """常规模式，按顺序依次执行任务"""
    print("=== 检测到未配置抢券时间，进入常规顺序执行模式 ===")
    print(f"共找到 {len(jd_cookies)} 个账号。")
    
    with requests.Session() as session:
        for i, cookie in enumerate(jd_cookies, 1):
            do_click_task(cookie, i, session)
            if i < len(jd_cookies):
                delay = random.uniform(2, 5)
                print(f"\n任务完成，随机延迟 {delay:.2f} 秒后继续下一个账号...\n")
                time.sleep(delay)
    
    print("\n=== 所有账号常规任务执行完毕 ===\n")

def rush_mode(target_times):
    """抢券模式，在指定时间并发执行任务"""
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    
    # 计算今天内所有有效的目标时间点
    valid_targets = []
    for t_str in target_times:
        try:
            target_dt = datetime.strptime(f"{today_str} {t_str}", '%Y-%m-%d %H:%M:%S')
            valid_targets.append(target_dt)
        except ValueError:
            print(f"警告：跳过无效的时间格式 '{t_str}'")

    if not valid_targets:
        print("错误：未找到任何有效的抢券时间配置。")
        return

    # 找到下一个最近的抢券时间
    future_targets = [t for t in valid_targets if t > now]
    if not future_targets:
        print("今天的所有抢券时间点已过。")
        # 可选：可以配置为等待第二天的第一个时间点
        # next_day_target = valid_targets[0] + timedelta(days=1)
        # print(f"等待明天的第一个抢券时间: {next_day_target.strftime('%Y-%m-%d %H:%M:%S')}")
        # future_targets.append(next_day_target)
        return
        
    next_target_time = min(future_targets)
    
    print(f"=== 进入抢券模式 ===")
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"下一个抢券时间: {next_target_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 计算需要休眠的时间，提前 200 毫秒唤醒以准备请求
    sleep_duration = (next_target_time - now).total_seconds() - 0.2
    
    if sleep_duration > 0:
        print(f"程序将休眠 {sleep_duration:.2f} 秒，请保持运行...")
        time.sleep(sleep_duration)
    
    # 精准等待到最后一刻
    while datetime.now() < next_target_time:
        time.sleep(0.001) # 毫秒级等待

    print(f"\n时间到！于 {datetime.now().strftime('%H:%M:%S.%f')} 开始并发执行所有账号任务！\n")
    
    threads = []
    with requests.Session() as session:
        for i, cookie in enumerate(jd_cookies, 1):
            thread = threading.Thread(target=do_click_task, args=(cookie, i, session))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
            
    print("\n=== 所有账号抢券任务执行完毕 ===\n")

def main():
    if target_times_str:
        # 如果配置了抢券时间，进入抢券模式
        target_times = [t.strip() for t in target_times_str.split(',')]
        rush_mode(target_times)
    else:
        # 否则，进入常规模式
        normal_mode()

if __name__ == '__main__':
    main()
