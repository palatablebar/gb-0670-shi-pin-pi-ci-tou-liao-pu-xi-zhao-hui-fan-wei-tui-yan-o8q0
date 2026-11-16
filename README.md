# 禾链 · 食品批次追溯

食品厂追溯数据专员把投料台账整理为可复核的原料、半成品和成品谱系，在疑似污染时推演召回范围，并检查产出与损耗守恒。

七个模块：台账采信、计量契约、投料谱系、召回推演、质量隔离、物料对账、批次归档。各模块有页面和独立API，原始行号与原因码贯穿全流程。

核心规则：按事件最高版裁决撤回与冲突，图遍历检测循环；以十进制数量校验每张配方及领用上限；失败配方整体隔离；召回仅沿有效边传播，给出最短证据路径。

## 启动

```sh
docker compose up --build
```

打开 http://localhost:18209 。首次访问自动登记脏样例，无需自备文件。修改端口可复制.env.example为.env。SQLite位于records命名卷，重启保留批次与复核记录。仅在确认放弃本项目全部记录后使用`docker compose down -v`重建。

## 验证

```sh
docker compose config --quiet
docker compose exec -T app pytest -q
```

本地也可安装requirements.txt后运行`pytest -q`；`uvicorn app.main:app --port 8000`启动本地服务。

## 页面与接口

| 页面 | 动作接口 |
|---|---|
| /intake | POST /api/intake |
| /contract | POST /api/contract |
| /genealogy | POST /api/genealogy |
| /recall | POST /api/recall |
| /quarantine | POST /api/quarantine |
| /reconcile | POST /api/reconcile |
| /batches | POST /api/runs |

`POST /api/runs`接收sample（clean/dirty/legacy）、seeds，或text/source_b64自定义CSV。`POST /api/runs/{id}/rerun`按原始字节与参数重跑。`POST /api/runs/{id}/review`带version、state和note复核；陈旧版本返回409。`GET /api/runs/{id}/evidence.csv`导出唯一证据清单。完整字段见/docs接口文档及docs/DATA-DICTIONARY.md。

源码按app/modules业务模块划分；tests随项目交付；sample_data提供48笔干净样例与多种异常；演示步骤见docs/SCENARIOS.md，深度登记见docs/DEPTH.md。

已知边界：仅处理2MB、15000行以内台账；不推断污染浓度、不连接设备；外购原料须用R-前缀，缺失的跨厂图不会自动补齐。
