"""Render service context data into Markdown documents."""
from __future__ import annotations

from .models import ServiceContext


def _fmt_table(header: tuple[str, str], rows: dict[str, list[str]]) -> str:
    lines = [f"| {header[0]} | {header[1]} |", "|--------|-----------|"]
    for svc, eps in sorted(rows.items()):
        lines.append(f"| {svc} | {', '.join(f'`{e}`' for e in eps)} |")
    return "\n".join(lines)


def generate_service_context_md(ctx: ServiceContext) -> str:
    lines = [f"# 服务上下文 — {ctx.name}\n", "> 本文件由 `harness sync` 自动生成，请勿手动编辑。\n"]
    lines.append("## 基本信息\n")
    lines.append(f"- 服务名：{ctx.name}")
    if ctx.owner:
        lines.append(f"- 负责人：{ctx.owner}")
    if ctx.summary:
        lines.append(f"- 职责：{ctx.summary}")
    lines.append("\n## 对外接口\n")
    lines.extend(f"- `{ep}`" for ep in ctx.provides) if ctx.provides else lines.append("（尚未在 dependency-graph 中记录）")
    lines.append("\n## 上游服务（谁调我）\n")
    lines.append(_fmt_table(("调用方", "调用的接口"), ctx.upstreams) if ctx.upstreams else "（暂无已知上游）")
    lines.append("\n## 下游服务（我调谁）\n")
    lines.append(_fmt_table(("被调方", "调用的接口"), ctx.downstreams) if ctx.downstreams else "（暂无已知下游）")
    lines.append("\n## 接口变更影响范围\n")
    if ctx.upstreams:
        lines.append(f"修改对外接口时需协调：**{', '.join(sorted(ctx.upstreams.keys()))}**")
    else:
        lines.append("当前无已知调用方，变更影响范围较小。")
    lines.append("")
    return "\n".join(lines)


def generate_microservice_rule(ctx: ServiceContext) -> str:
    impact = ", ".join(sorted(ctx.upstreams.keys())) if ctx.upstreams else "（暂无已知调用方）"
    return (
        f"# 微服务协作规则\n\n"
        f"本服务（{ctx.name}）是微服务集群的一部分。跨服务上下文见 `docs/service-context.md`。\n\n"
        f"## 何时需要跨服务上下文\n\n"
        f"- 修改 docs/service-context.md 中列出的对外接口时\n"
        f"- 排查涉及上下游服务的问题时\n"
        f"- 需要了解请求的数据流方向时\n\n"
        f"## 接口变更规则\n\n"
        f"- 先查 docs/service-context.md 确认调用方：{impact}\n"
        f"- 接口变更必须向后兼容，或提前协调上游调用方\n"
        f"- 变更后通知 meta repo 更新 dependency-graph，然后重新运行 `harness sync`\n"
    )
