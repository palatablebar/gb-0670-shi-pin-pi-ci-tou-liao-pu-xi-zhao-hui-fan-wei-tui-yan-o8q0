# 禾链 · 食品批次追溯

食品厂追溯数据专员把投料台账整理为可复核的原料、半成品和成品谱系，在疑似污染时推演召回范围，并检查产出与损耗守恒。

七个模块：台账采信、计量契约、投料谱系、召回推演、质量隔离、物料对账、批次归档。各模块有页面和独立API，原始行号与原因码贯穿全流程。修订裁决是叠加在批次归档之上的部分重发流程，入口在召回页与`/amendments`。

核心规则：按事件最高版裁决撤回与冲突，图遍历检测循环；以十进制数量校验每张配方及领用上限；失败配方整体隔离；召回仅沿有效边传播，给出最短证据路径。

修订裁决（部分重发）：供应商只重发部分事件时，未出现的旧行不能被默认为撤回或沿用。登记修订须显式选择模式——`pending`（默认，未现旧行保持在图中但标记待核查）、`retain`（显式沿用）、`withdraw`（未现旧行退出传播图）。基线全部原始行与修订新行逐行合并后，复用同一套契约/谱系/隔离规则；对每个末端成品给出`keep`保留、`remove`移除、`review`待核查三态结论，并附基线/修订可达性、确认状态与最短证据路径行号，依据可逐条复核。修订以内容寻址幂等键存入独立`amendments`表：同一份修订重跑只复用既有记录，不新增、覆盖或丢失；任一异常随连接回滚，基线运行记录与原始行不变。

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

修订接口：`POST /api/amendments/{baseline_id}`接收text/source_b64、seeds与mode（pending/retain/withdraw）；`GET /api/amendments`列修订；`GET /api/amendments/{id}`取裁决；`GET /api/amendments/{id}/evidence.csv`导出含成品三态、未提及旧行处置、有效边来源与隔离原始行的修订证据清单。修订事件的revision必须高于基线且event_id须在基线存在，否则分别记`AMEND_STALE_REVISION`、`AMEND_UNKNOWN_EVENT`并隔离。

源码按app/modules业务模块划分；tests随项目交付；sample_data提供48笔干净样例与多种异常；演示步骤见docs/SCENARIOS.md，深度登记见docs/DEPTH.md。

已知边界：仅处理2MB、15000行以内台账；不推断污染浓度、不连接设备；外购原料须用R-前缀，缺失的跨厂图不会自动补齐。
