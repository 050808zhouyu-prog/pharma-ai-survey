#!/usr/bin/env python3
"""
医药圈AI使用情况调查 - 结果页自动更新脚本
用法: python3 update.py <sav文件路径>
"""

import sys
import subprocess
import json

# 确保 pyreadstat 已安装
subprocess.run([sys.executable, "-m", "pip", "install", "pyreadstat", "-q"], check=True)

import pyreadstat
import pandas as pd
from pathlib import Path
from datetime import datetime

# ===== 配置：题目与选项的映射 =====

QUESTIONS = {
    # 多选题：Q1 使用模型
    "Q1": {
        "type": "multi",
        "title": "最常用的AI模型",
        "icon": "🤖",
        "columns": {
            "Q1_选项1": "ChatGPT / GPT-4",
            "Q1_选项2": "Claude",
            "Q1_选项3": "Gemini",
            "Q1_选项4": "DeepSeek",
            "Q1_选项5": "Kimi",
            "Q1_选项6": "豆包",
            "Q1_选项7": "GLM / 智谱清言",
            "Q1_选项8": "MiniMax / 海螺AI",
            "Q1_选项9": "其他",
        },
    },
    # 多选题：Q2 使用产品
    "Q2": {
        "type": "multi",
        "title": "使用AI的产品/方式",
        "icon": "💻",
        "columns": {
            "Q2_选项1": "网页对话",
            "Q2_选项2": "桌面客户端",
            "Q2_选项3": "AI IDE",
            "Q2_选项4": "AI IDE插件",
            "Q2_选项5": "命令行工具",
            "Q2_选项6": "其他",
        },
    },
    # 多选题：Q3 使用场景
    "Q3": {
        "type": "multi",
        "title": "使用AI的主要场景",
        "icon": "📋",
        "columns": {
            "Q3_选项1": "文献检索与综述",
            "Q3_选项2": "报告/邮件/文档撰写",
            "Q3_选项3": "翻译",
            "Q3_选项4": "数据分析/统计",
            "Q3_选项5": "编程/生信分析",
            "Q3_选项6": "药物靶点/管线调研",
            "Q3_选项7": "日常搜索",
            "Q3_选项8": "其他",
        },
    },
    # 单选题
    "Q4": {
        "type": "single",
        "title": "AI使用频率",
        "icon": "🔥",
        "options": {
            1: "每天都用",
            2: "每周几次",
            3: "每月几次",
            4: "很少用/几乎不用",
            5: "完全没用过",
        },
    },
    "Q5": {
        "type": "single",
        "title": "AI对工作效率的影响",
        "icon": "⚡",
        "options": {
            1: "非常大（>30%时间）",
            2: "比较明显（10-30%）",
            3: "有一点帮助",
            4: "几乎没感觉",
            5: "反而增加了工作量",
        },
    },
    "Q6": {
        "type": "single",
        "title": "AI使用水平",
        "icon": "📈",
        "options": {
            1: "L1 入门",
            2: "L2 日常用户",
            3: "L3 深度用户",
            4: "L4 高级用户",
        },
    },
    "Q7": {
        "type": "single",
        "title": "对AI在医药行业的预期",
        "icon": "🔮",
        "options": {
            1: "会彻底改变很多岗位",
            2: "会提升效率，但不会颠覆",
            3: "短期内影响有限",
            4: "不好说",
        },
    },
    "Q8": {
        "type": "single",
        "title": "是否已为AI工具付费",
        "icon": "💰",
        "options": {
            1: "是，正在付费",
            2: "否，但考虑过",
            3: "否，没考虑过",
        },
    },
    "Q9": {
        "type": "single",
        "title": "每月愿意为AI工具支付",
        "icon": "💳",
        "options": {
            1: "0元，只用免费的",
            2: "1-50元",
            3: "50-150元",
            4: "150-700元",
            5: "700-1500元",
            6: "1500元以上",
        },
    },
    "Q10": {
        "type": "multi",
        "title": "较少使用或不使用AI的原因",
        "icon": "🚫",
        "columns": {
            "Q10_选项1": "输出质量不够靠谱",
            "Q10_选项2": "不知道怎么用/没时间学",
            "Q10_选项3": "数据安全/隐私顾虑",
            "Q10_选项4": "所在单位不允许使用",
            "Q10_选项5": "觉得没必要",
            "Q10_选项6": "其他",
        },
    },
    "Q11": {
        "type": "single",
        "title": "职业领域",
        "icon": "🏥",
        "options": {
            1: "临床/医学",
            2: "药物研发",
            3: "BD/商务拓展/投资",
            4: "注册/法规",
            5: "市场/销售",
            6: "生产/质量/运营",
            7: "其他",
        },
    },
    "Q12": {
        "type": "single",
        "title": "工作年限",
        "icon": "📅",
        "options": {
            1: "1-3年",
            2: "4-7年",
            3: "8-15年",
            4: "15年以上",
        },
    },
}

# 用于结果页展示的题目顺序
DISPLAY_ORDER = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q11", "Q12"]


def calc_stats(df):
    """计算每道题的统计数据"""
    results = {}
    total = len(df)

    for qid, config in QUESTIONS.items():
        if config["type"] == "multi":
            counts = {}
            for col, label in config["columns"].items():
                if col in df.columns:
                    counts[label] = int(df[col].notna().sum())
                else:
                    counts[label] = 0
            # 按数量排序
            sorted_items = sorted(counts.items(), key=lambda x: -x[1])
            results[qid] = {
                "title": config["title"],
                "icon": config["icon"],
                "type": "multi",
                "items": [(label, count, round(count / total * 100)) for label, count in sorted_items if count > 0],
            }
        else:
            counts = {}
            for val, label in config["options"].items():
                if qid in df.columns:
                    counts[label] = int((df[qid] == val).sum())
                else:
                    counts[label] = 0
            sorted_items = sorted(counts.items(), key=lambda x: -x[1])
            results[qid] = {
                "title": config["title"],
                "icon": config["icon"],
                "type": "single",
                "items": [(label, count, round(count / total * 100)) for label, count in sorted_items if count > 0],
            }

    # 计算渗透率
    if "Q4" in df.columns:
        active_users = int(((df["Q4"] >= 1) & (df["Q4"] <= 4)).sum())
        results["penetration"] = round(active_users / total * 100) if total > 0 else 0
    else:
        results["penetration"] = 0

    return results, total


def generate_html(results, total, update_time):
    """生成结果页HTML"""
    items_html = ""

    for qid in DISPLAY_ORDER:
        if qid not in results:
            continue
        q = results[qid]
        items_html += f'  <div class="card">\n'
        items_html += f'    <h2>{q["icon"]} {q["title"]}</h2>\n'
        for i, (label, count, pct) in enumerate(q["items"]):
            color_idx = (i % 7) + 1
            items_html += f'    <div class="bar-group">\n'
            items_html += f'      <div class="bar-label"><span class="name">{label}</span><span class="pct">{pct}% ({count}人)</span></div>\n'
            items_html += f'      <div class="bar-track"><div class="bar-fill color-{color_idx}" style="width: {pct}%"></div></div>\n'
            items_html += f'    </div>\n'
        items_html += f'  </div>\n\n'

    # 特殊卡片：渗透率
    penetration = results.get("penetration", 0)
    penetration_card = f'''  <div class="card">
    <h2>🔥 AI使用渗透率</h2>
    <div class="highlight">
      <div class="number">{penetration}%</div>
      <div class="label">的受访者正在使用AI（共{total}人参与）</div>
    </div>
  </div>

'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>医药圈AI使用情况调查 - 结果</title>
<meta property="og:title" content="医药圈AI使用情况调查结果">
<meta property="og:description" content="共{total}位医药圈同行参与，AI渗透率{penetration}%">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f5f7fa;
    color: #333;
    line-height: 1.6;
    padding: 20px;
  }}
  .container {{ max-width: 680px; margin: 0 auto; }}
  .header {{ text-align: center; padding: 30px 0 20px; }}
  .header h1 {{ font-size: 22px; color: #1a1a1a; margin-bottom: 8px; }}
  .header .subtitle {{ font-size: 14px; color: #888; }}
  .card {{
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  .card h2 {{
    font-size: 16px;
    color: #1a1a1a;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f0f0f0;
  }}
  .highlight {{ text-align: center; padding: 20px; }}
  .highlight .number {{ font-size: 48px; font-weight: 700; color: #4f46e5; line-height: 1; }}
  .highlight .label {{ font-size: 14px; color: #888; margin-top: 6px; }}
  .bar-group {{ margin-bottom: 14px; }}
  .bar-label {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px; }}
  .bar-label .name {{ color: #333; }}
  .bar-label .pct {{ color: #888; font-weight: 500; }}
  .bar-track {{ height: 24px; background: #f0f0f0; border-radius: 6px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 6px; transition: width 0.8s ease; }}
  .color-1 {{ background: #4f46e5; }}
  .color-2 {{ background: #7c3aed; }}
  .color-3 {{ background: #2563eb; }}
  .color-4 {{ background: #0891b2; }}
  .color-5 {{ background: #059669; }}
  .color-6 {{ background: #d97706; }}
  .color-7 {{ background: #dc2626; }}
  .update-time {{ text-align: center; font-size: 12px; color: #aaa; padding: 20px 0; }}
  .footer {{ text-align: center; padding: 16px 0; font-size: 13px; color: #aaa; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 医药圈AI使用情况</h1>
    <div class="subtitle">共{total}人参与 · 实时更新</div>
  </div>
{penetration_card}{items_html}  <div class="update-time">最近更新：{update_time}</div>
  <div class="footer">纯好奇，无商业目的 · 匿名统计</div>
</div>
</body>
</html>'''
    return html


def main():
    if len(sys.argv) < 2:
        print("用法: python3 update.py <sav文件路径>")
        sys.exit(1)

    sav_path = Path(sys.argv[1])
    if not sav_path.exists():
        print(f"文件不存在: {sav_path}")
        sys.exit(1)

    # 读取数据
    df, meta = pyreadstat.read_sav(str(sav_path))
    print(f"读取到 {len(df)} 份回复")

    # 计算统计
    results, total = calc_stats(df)
    print(f"渗透率: {results['penetration']}%")

    # 生成HTML
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = generate_html(results, total, update_time)

    # 输出到index.html
    output_path = Path(__file__).parent / "index.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"结果页已更新: {output_path}")


if __name__ == "__main__":
    main()
