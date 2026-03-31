from __future__ import annotations

from .models import AssessmentResult, ProjectProfile


def assess_project(profile: ProjectProfile) -> AssessmentResult:
    score = 100
    strengths: list[str] = []
    gaps: list[str] = []
    recommendations: list[str] = []

    if profile.language != "unknown":
        strengths.append(f"已识别主要语言：{profile.language}")
    else:
        score -= 20
        gaps.append("未识别主要语言")
        recommendations.append("补充语言和构建工具信息，再执行初始化。")

    if profile.source_paths:
        strengths.append(f"已识别源码目录：{', '.join(profile.source_paths)}")
    else:
        score -= 15
        gaps.append("未识别源码目录")
        recommendations.append("在初始化前确认源码目录，避免文档和 runbook 写错。")

    if profile.test_paths:
        strengths.append(f"已识别测试目录：{', '.join(profile.test_paths)}")
    else:
        score -= 15
        gaps.append("未识别测试目录")
        recommendations.append("尽快明确测试入口，避免 harness 只剩文档没有验证链。")

    if profile.ci_paths:
        strengths.append(f"已识别 CI 入口：{', '.join(profile.ci_paths)}")
    else:
        score -= 10
        gaps.append("未识别 CI 配置")
        recommendations.append("接入 harness 后尽快把 check/test 命令纳入 CI。")

    for label, command in [
        ("运行命令", profile.run_command),
        ("测试命令", profile.test_command),
        ("检查命令", profile.check_command),
        ("CI 命令", profile.ci_command),
    ]:
        if command != "TODO":
            strengths.append(f"{label}已识别：{command}")
        else:
            score -= 10
            gaps.append(f"{label}未识别")
            recommendations.append(f"初始化时手动确认{label}，避免生成的 runbook 不可执行。")

    if profile.has_production:
        strengths.append("已探测到生产相关信号")
    else:
        recommendations.append("如果项目已有线上环境，请在初始化时显式标记 has_production。")

    if profile.external_systems:
        strengths.append(f"检测到外部系统：{', '.join(profile.external_systems)}")
    else:
        recommendations.append("如果项目依赖数据库、队列或第三方 API，请在初始化后补到 docs/architecture.md。")

    readiness = "high" if score >= 80 else "medium" if score >= 55 else "low"
    return AssessmentResult(
        score=max(score, 0),
        readiness=readiness,
        strengths=strengths,
        gaps=gaps,
        recommendations=recommendations,
    )
