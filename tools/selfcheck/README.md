# prd-tools 版本迭代自检工具

每次迭代（尤其是 gate/workflow/command 改动、脚本重构、新增 contract/schema 之后），跑这个工具做系统性自检，预防 v2.18.x 这类"commit 叫全盘修复，实测还剩一堆漂移"的情况。

## 怎么用

```bash
cd /path/to/prd-tools

# 全量跑（推荐发版前运行）
python3 tools/selfcheck/run.py --all

# 只跑某一类
python3 tools/selfcheck/run.py --category docs
python3 tools/selfcheck/run.py --category scripts
python3 tools/selfcheck/run.py --category contracts
python3 tools/selfcheck/run.py --category cross

# 详细输出
python3 tools/selfcheck/run.py --all -v

# 机器可读（CI 用）
python3 tools/selfcheck/run.py --all --format json
```

## 检查类别

### docs（文档自身一致性）
- D1: `workflow.md` 没有重复章节（同名 heading 出现 2 次即 fail）
- D2: `workflow.md` 里所有 ```yaml ``` 代码块不含智能引号
- D3: `SKILL.md` 提到的所有 step 文件真实存在
- D4: `SKILL.md` / `workflow.md` / `commands/*.md` 声明的 gate 脚本列表一致
- D5: step 文件内部 `<current_step>` 值与文件名数字前缀一致（允许别名表）
- D6: 数字列表无重复编号

### scripts（脚本自身健康）
- S1: 所有 `scripts/*.py` 和 `tools/**/*.py` 语法可编译
- S2: 所有 Python 文件里用到的 `yaml.` 调用前都有 `import yaml`
- S3: `*-step-gate.py` 的 `--tool-version` 默认值等于 VERSION 文件内容
- S4: 所有 gate 脚本 `--help` 可执行不报错

### contracts（契约与 schema 一致）
- C1: `plugins/*/skills/*/references/contracts/*.yaml` 全部 YAML 可解析
- C2: 每个 contract 的 `required_top_level` 字段在对应 `output-contracts.md` 描述里能找到
- C3: `validate-artifact.py` 对 dive-bff 快照产物（如果存在）能通过
- C4: 每个 schema_version 字段在声明和消费端一致

### cross（跨文件交叉一致）
- X1: `workflow.md` 声明的 step id 全部能在 step-gate 脚本 `STEP_TABLE` 里找到
- X2: SKILL.md step 列表 ⊂ workflow.md phase 列表 ⊂ step-gate STEP_TABLE（三层包含关系）
- X3: `*.contract.yaml` 的 `required_top_level` 字段全部出现在真实产物样例里（如有样例）
- X4: `VERSION` / `plugin.json` / `marketplace.json` 三处版本号一致
- X5: CHANGELOG.md 最新版本条目和 VERSION 一致

## 扩展

增加新 check：在 `checks/` 下新建 `Xn_description.py`，实现：

```python
def check() -> dict:
    """Return {status: 'pass'|'warn'|'fail', message: str, details: list, fix_hint: str}"""
    ...

META = {
    "id": "X6",
    "category": "cross",
    "description": "one-line description",
}
```

`run.py` 会自动发现并加载。

## 退出码

- `0`：全 pass（warn 也算 pass）
- `1`：有 fail
- `2`：工具自身错误（比如脚本不可执行）

## 不检查什么

- 不跑 `/prd-distill` 或 `/reference` 的完整流程（那是另一类测试，需要 PRD 输入）
- 不验证业务产物的语义正确性（需要人类判断）
- 不做版本回归（依赖 git history）
