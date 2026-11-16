# 食品批次追溯深度登记

规模：中型。使用者为食品厂追溯数据专员。原料到货、投料、分装和损耗来自车间台账，质量人员以疑似污染原料推演召回范围。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 台账采信 | 执行台账采信并检查逐行依据 | `/intake` / `POST /api/intake` | `app/modules/intake/service.py` `app/modules/intake/reader.py` | `tests/test_intake.py` |
| M2 计量契约 | 执行计量契约并检查逐行依据 | `/contract` / `POST /api/contract` | `app/modules/contract/service.py` `app/modules/contract/coerce.py` | `tests/test_contract.py` |
| M3 投料谱系 | 执行投料谱系并检查逐行依据 | `/genealogy` / `POST /api/genealogy` | `app/modules/genealogy/service.py` `app/modules/genealogy/graph.py` | `tests/test_genealogy.py` |
| M4 召回推演 | 执行召回推演并检查逐行依据 | `/recall` / `POST /api/recall` | `app/modules/recall/service.py` `app/modules/recall/traverse.py` | `tests/test_recall.py` |
| M5 质量隔离 | 执行质量隔离并检查逐行依据 | `/quarantine` / `POST /api/quarantine` | `app/modules/quarantine/service.py` `app/modules/quarantine/checks.py` | `tests/test_quarantine.py` |
| M6 物料对账 | 执行物料对账并检查逐行依据 | `/reconcile` / `POST /api/reconcile` | `app/modules/reconcile/service.py` `app/modules/reconcile/balance.py` | `tests/test_reconcile.py` |
| M7 批次归档 | 执行批次归档并检查逐行依据 | `/batches` / `POST /api/runs` | `app/modules/batches/service.py` `app/modules/batches/archive.py` | `tests/test_batches.py` |

## 陷阱登记

| TRAP | 现象 | 朴素实现会怎样 | 本项目处理 | 处理位置 | 测试 |
|---|---|---|---|---|---|
| TRAP-01 | 历史GB18030 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_legacy` |
| TRAP-02 | UTF-8首列BOM | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_bom` |
| TRAP-03 | 引号内换行 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_multiline_counterexample` |
| TRAP-04 | 分段重复表头 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_repeated_header` |
| TRAP-05 | 半行列数不齐 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_column_count` |
| TRAP-06 | 全角数字千分位 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/contract/coerce.py` | `tests/test_contract.py::test_nfkc` |
| TRAP-07 | 空值哨兵 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/contract/coerce.py` | `tests/test_contract.py::test_sentinel` |
| TRAP-08 | 编号前导零 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/contract/coerce.py` | `tests/test_contract.py::test_identifier_preserved` |
| TRAP-10 | 二进制浮点误差 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/contract/coerce.py` | `tests/test_contract.py::test_decimal_exact` |
| TRAP-14 | 同版异值冲突 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/genealogy/graph.py` | `tests/test_genealogy.py::test_conflicts` |
| TRAP-15 | 克千克混用 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/contract/coerce.py` | `tests/test_contract.py::test_unit` |
| TRAP-16 | 截断引号 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_broken_quotes` |
| TRAP-18 | 空文件三态 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/intake/reader.py` | `tests/test_intake.py::test_three_empty_states` |
| TRAP-19 | 事件顺序改变裁决 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/genealogy/graph.py` | `tests/test_genealogy.py::test_order_invariant` |
| TRAP-20 | 谱系环 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/genealogy/graph.py` | `tests/test_genealogy.py::test_cycle` |
| TRAP-21 | 来源失联 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/modules/quarantine/checks.py` | `tests/test_quarantine.py::test_orphan` |
| TRAP-26 | 旧版复核覆盖 | 静默接受或丢失证据 | 明确归一、拒绝或保留诊断 | `app/store.py` | `tests/test_batches.py::test_optimistic_lock` |

## 对账规则

输入业务行=有效投料+隔离行+重复/旧版/撤回行。空行和重复表头独立记录，不计入业务行。每个目标批次投入=产出+损耗；中间批次可领用不得大于产出。汇总是生产发生量，多个工序发生量会累积，同一物料在不同工序分别出现。

## 设计取舍

同事件最高版本优先，最高版本异值则全部隔离；环边按固定的来源、目标、事件顺序隔离，保留相同输入的稳定裁决。物料校验失败按整张配方隔离，并向下游传播失联，避免错误配方进入召回图。追溯使用最短可达路径，不用配比推算污染浓度；原料批次以 R- 前缀标识，非原料必须有生产来源。

## 已知不覆盖

不连接车间设备，不自动认定污染浓度，不处理跨厂未交付的原料图；2MB/15000行上限内流式CSV解析，图计算保留受限边集。
