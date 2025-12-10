import os
import datetime
import requests

WEBHOOK_KEY = os.getenv("WECHAT_WEBHOOK_KEY", "").strip()
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
FORCE_SEND = os.getenv("FORCE_SEND", "false").lower() == "true"

# 基础日期（从这个日期开始计算4天周期）
BASE_DATE = datetime.datetime(2025,12, 7)  # 可以修改为您想要的开始日期

def should_send_today():
    """判断今天是否需要发送（4天一次）"""
    today = datetime.datetime.now()
    
    # 计算天数差
    days_diff = (today - BASE_DATE).days
    
    # 每4天一次：0, 4, 8, 12, ... 天
    return days_diff % 4 == 0


def send_msg(content):
    """发送消息到企业微信"""
    
    if TEST_MODE:
        print(f"[TEST MODE] 模拟发送消息: {content}")
        return {"errcode": 0, "errmsg": "test mode"}
    
    if not WEBHOOK_KEY:
        print("错误: Webhook Key 未设置")
        return {"errcode": -1, "errmsg": "Webhook Key not set"}
    
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WEBHOOK_KEY}"
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"消息发送结果: {response.text}")
        return response.json()
    except Exception as e:
        print(f"发送消息时出错: {e}")
        return {"errcode": -1, "errmsg": str(e)}


def is_within_reminder_hours():
    """检查是否在提醒时间范围内（UTC 12:00-13:00）"""
    now = datetime.datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # UTC 12:00-13:00 = 北京时间 20:00-21:00
    reminder_start_hour = 12
    reminder_end_hour = 13
    
    if reminder_start_hour <= current_hour < reminder_end_hour:
        return True
    elif current_hour == reminder_start_hour - 1 and current_minute >= 30:
        # UTC 11:30-12:00 也允许发送
        return True
    
    return False


def send_duty_reminder():
    """发送填写值班表的提醒"""
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 检查是否在提醒时间内或是否强制发送
    if not is_within_reminder_hours() and not FORCE_SEND:
        print(f"当前时间不在提醒时间内 ({current_time})，跳过发送")
        return
    
    # 检查是否满足4天一次的频率
    if not should_send_today() and not FORCE_SEND:
        print(f"今天不满足4天一次的发送条件，跳过发送")
        return
    
    # 构建消息内容
    prefix_parts = []
    if TEST_MODE:
        prefix_parts.append("[测试]")
    if FORCE_SEND:
        if not is_within_reminder_hours() or not should_send_today():
            prefix_parts.append("[强制发送]")
    
    prefix = "".join(prefix_parts)
    content = f"{prefix}记得填写值班表\n时间: {current_time}"
    
    result = send_msg(content)
    
    if result.get("errcode") == 0:
        print(f"提醒发送成功")
    else:
        print(f"提醒发送失败: {result.get('errmsg')}")


if __name__ == "__main__":
    print(f"今天是第 {(datetime.datetime.now() - BASE_DATE).days} 天")
    print(f"是否应该发送: {should_send_today()}")
    send_duty_reminder()
    print("任务执行完成")