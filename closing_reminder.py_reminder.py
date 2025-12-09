import os
import datetime
import requests

WEBHOOK_KEY = os.getenv("WECHAT_WEBHOOK_KEY", "").strip() # 从环境变量中获取 Webhook Key
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"  # 测试模式，不实际发送消息
FORCE_SEND = os.getenv("FORCE_SEND", "false").lower() == "true"  # 强制发送，无视时间范围

def send_msg(content):
    """发送消息到企业微信"""
    
    # 测试模式下不实际发送
    if TEST_MODE:
        print(f"[TEST MODE] 模拟发送消息: {content}")
        print(f"[TEST MODE] Webhook Key: {'已设置' if WEBHOOK_KEY else '未设置'}")
        print(f"[TEST MODE] 当前时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return {"errcode": 0, "errmsg": "test mode"}
    
    # 生产模式，实际发送
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


def should_send():
    """判断是否应该发送消息"""
    # 如果强制发送，则返回True
    if FORCE_SEND:
        print("强制发送模式，无视时间范围")
        return True
    
    # 否则检查当前时间是否在允许的范围内（UTC 10:00-11:00，即北京时间18:00-19:00）
    now = datetime.datetime.utcnow()
    start_time = datetime.time(10, 0, 0)  # UTC 10:00
    end_time = datetime.time(11, 0, 0)    # UTC 11:00
    
    # 如果当前时间在10:00到11:00之间
    if start_time <= now.time() <= end_time:
        return True
    else:
        print(f"当前时间 {now.strftime('%H:%M:%S')} 不在允许的发送时间范围内（UTC 10:00-11:00）")
        return False


def send_closing_reminder():
    """发送下班前工单完工确认的提醒"""
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 首先判断是否应该发送
    if not should_send():
        print("跳过发送，因为不在时间范围内且没有开启强制发送")
        return
    
    # 测试模式下添加标记
    prefix = "[测试]" if TEST_MODE else ""
    content = f"{prefix}记得填写值班表\n时间: {current_time}"
    
    result = send_msg(content)
    
    # 检查发送结果
    if result.get("errcode") == 0:
        print(f"{'测试模式' if TEST_MODE else '生产模式'} - 提醒发送成功")
    else:
        print(f"{'测试模式' if TEST_MODE else '生产模式'} - 提醒发送失败: {result.get('errmsg')}")


if __name__ == "__main__":
    print(f"开始执行{'测试' if TEST_MODE else '生产'}提醒任务")
    print(f"强制发送模式: {FORCE_SEND}")
    send_closing_reminder()
    print("任务执行完成")
