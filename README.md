# 医药圈AI使用情况调查 - 结果页

## 这是什么

微信群问卷调查的实时结果展示页。
- 问卷平台：腾讯问卷
- 结果页地址：https://pharma-ai-survey.vercel.app
- 代码仓库：https://github.com/050808zhouyu-prog/pharma-ai-survey

## 更新数据流程

1. 在腾讯问卷后台导出 .sav 文件
2. 把 .sav 文件路径告诉我（如：`/Users/zhouyu/个人文件夹/公众号文章/问卷调查结果/xxx.sav`）
3. 我会运行更新脚本并自动部署

## 手动更新命令

```bash
cd ~/pharma-ai-survey
python3 update.py <sav文件路径>
git add . && git commit -m "update: N份回复" && git push
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `index.html` | 结果展示页（Vercel部署的页面） |
| `update.py` | 数据更新脚本，读取.sav文件生成新的index.html |

## 注意事项

- 腾讯问卷导出的.sav文件包含全部原始记录（含试答），可能比回收量多几条
- 脚本会自动计算每题的百分比分布和AI渗透率
- Vercel免费部署，不需要额外付费
