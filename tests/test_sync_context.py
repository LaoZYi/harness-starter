from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_harness.sync_context import (
    _distribute_domain,
    _distribute_plugins,
    detect_meta_root,
    extract_service_context,
    find_service_name,
    generate_microservice_rule,
    generate_service_context_md,
    load_meta,
    resolve_meta,
    run_sync,
    run_sync_all,
)

_REGISTRY_YAML = """\
payment-service:
  repo: {repo_payment}
  owner: 支付团队
  summary: 处理支付创建、查询和退款
  port: 8001
  status: active

order-service:
  repo: {repo_order}
  owner: 交易团队
  summary: 管理订单生命周期
  port: 8002
  status: active

notification-service:
  repo: /tmp/notification-service
  owner: 基础设施
  summary: 发送通知
  port: 8003
  status: active
"""

_GRAPH_YAML = """\
payment-service:
  provides:
    - POST /api/payments/create
    - GET /api/payments/{id}
  consumes:
    - notification-service: POST /api/notify

order-service:
  provides:
    - POST /api/orders
    - GET /api/orders/{id}
  consumes:
    - payment-service: POST /api/payments/create
    - notification-service: POST /api/notify

notification-service:
  provides:
    - POST /api/notify
  consumes: []
"""


def _create_meta(tmpdir: Path, repo_payment: str = "/tmp/p", repo_order: str = "/tmp/o") -> Path:
    meta = tmpdir / "meta"
    (meta / "services").mkdir(parents=True)
    reg = _REGISTRY_YAML.format(repo_payment=repo_payment, repo_order=repo_order)
    (meta / "services" / "registry.yaml").write_text(reg, encoding="utf-8")
    (meta / "services" / "dependency-graph.yaml").write_text(_GRAPH_YAML, encoding="utf-8")
    return meta


class LoadMetaTests(unittest.TestCase):
    def test_loads_registry_and_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = _create_meta(Path(tmpdir))
            registry, graph = load_meta(meta)
        self.assertIn("payment-service", registry)
        self.assertIn("order-service", graph)
        self.assertEqual(registry["payment-service"]["owner"], "支付团队")

    def test_empty_meta_returns_empty_dicts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry, graph = load_meta(Path(tmpdir))
        self.assertEqual(registry, {})
        self.assertEqual(graph, {})


class DetectMetaTests(unittest.TestCase):
    def test_detects_from_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = _create_meta(Path(tmpdir))
            result = detect_meta_root(meta)
        self.assertEqual(result, meta.resolve())

    def test_returns_none_for_non_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = detect_meta_root(Path(tmpdir))
        self.assertIsNone(result)


class FindServiceNameTests(unittest.TestCase):
    def test_matches_from_project_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "some-dir"
            target.mkdir()
            (target / ".agent-harness").mkdir()
            (target / ".agent-harness" / "project.json").write_text(
                json.dumps({"project_name": "payment-service"}), encoding="utf-8"
            )
            result = find_service_name(target, {"payment-service": {}, "order-service": {}})
        self.assertEqual(result, "payment-service")

    def test_matches_from_dirname(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "order-service"
            target.mkdir()
            result = find_service_name(target, {"payment-service": {}, "order-service": {}})
        self.assertEqual(result, "order-service")

    def test_returns_none_when_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "unknown"
            target.mkdir()
            result = find_service_name(target, {"payment-service": {}})
        self.assertIsNone(result)


class ExtractContextTests(unittest.TestCase):
    def test_extracts_provides_and_downstreams(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = _create_meta(Path(tmpdir))
            registry, graph = load_meta(meta)
        ctx = extract_service_context("payment-service", registry, graph)
        self.assertEqual(ctx.name, "payment-service")
        self.assertIn("POST /api/payments/create", ctx.provides)
        self.assertIn("notification-service", ctx.downstreams)

    def test_extracts_upstreams(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = _create_meta(Path(tmpdir))
            registry, graph = load_meta(meta)
        ctx = extract_service_context("payment-service", registry, graph)
        self.assertIn("order-service", ctx.upstreams)

    def test_notification_has_two_upstreams(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = _create_meta(Path(tmpdir))
            registry, graph = load_meta(meta)
        ctx = extract_service_context("notification-service", registry, graph)
        self.assertIn("payment-service", ctx.upstreams)
        self.assertIn("order-service", ctx.upstreams)


class GenerateOutputTests(unittest.TestCase):
    def test_service_context_md_contains_key_info(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = _create_meta(Path(tmpdir))
            registry, graph = load_meta(meta)
        ctx = extract_service_context("payment-service", registry, graph)
        md = generate_service_context_md(ctx)
        self.assertIn("payment-service", md)
        self.assertIn("order-service", md)
        self.assertIn("POST /api/payments/create", md)

    def test_microservice_rule_mentions_callers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            meta = _create_meta(Path(tmpdir))
            registry, graph = load_meta(meta)
        ctx = extract_service_context("payment-service", registry, graph)
        rule = generate_microservice_rule(ctx)
        self.assertIn("order-service", rule)


class DistributePluginsTests(unittest.TestCase):
    def test_copies_shared_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            meta = root / "meta"
            (meta / "shared-plugins" / "rules").mkdir(parents=True)
            (meta / "shared-plugins" / "rules" / "conventions.md").write_text("# Conv", encoding="utf-8")
            (meta / "shared-plugins" / "templates" / "docs").mkdir(parents=True)
            (meta / "shared-plugins" / "templates" / "docs" / "shared.md").write_text("# Shared", encoding="utf-8")
            target = root / "service"
            target.mkdir()
            written = _distribute_plugins(meta, target)
            self.assertIn(".claude/rules/conventions.md", written)
            self.assertIn("docs/shared.md", written)
            self.assertEqual((target / ".claude" / "rules" / "conventions.md").read_text(encoding="utf-8"), "# Conv")

    def test_no_plugins_dir_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            written = _distribute_plugins(Path(tmpdir), Path(tmpdir) / "svc")
        self.assertEqual(written, [])


class SyncEndToEndTests(unittest.TestCase):
    def test_sync_generates_all_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            meta = _create_meta(root)
            # Add a shared plugin
            (meta / "shared-plugins" / "rules").mkdir(parents=True)
            (meta / "shared-plugins" / "rules" / "team.md").write_text("# Team rule", encoding="utf-8")
            service = root / "payment-service"
            service.mkdir()
            written = run_sync(service, meta)
            self.assertIn("docs/service-context.md", written)
            self.assertIn(".claude/rules/microservice.md", written)
            self.assertIn(".claude/rules/team.md", written)
            self.assertTrue((service / "docs" / "service-context.md").exists())

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            meta = _create_meta(root)
            service = root / "payment-service"
            service.mkdir()
            written = run_sync(service, meta, dry_run=True)
            self.assertTrue(len(written) >= 2)
            self.assertFalse((service / "docs" / "service-context.md").exists())

    def test_stores_meta_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            meta = _create_meta(root)
            service = root / "payment-service"
            service.mkdir()
            (service / ".agent-harness").mkdir()
            (service / ".agent-harness" / "project.json").write_text('{"project_name": "payment-service"}', encoding="utf-8")
            run_sync(service, meta)
            data = json.loads((service / ".agent-harness" / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(data["meta_repo"], str(meta.resolve()))

    def test_sync_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payment = root / "payment-service"
            payment.mkdir()
            order = root / "order-service"
            order.mkdir()
            meta = _create_meta(root, repo_payment=str(payment), repo_order=str(order))
            results = run_sync_all(meta)
            self.assertIn("payment-service", results)
            self.assertIn("order-service", results)
            self.assertTrue((payment / "docs" / "service-context.md").exists())
            self.assertTrue((order / "docs" / "service-context.md").exists())


class DistributeDomainTests(unittest.TestCase):
    def test_copies_domain_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            meta = root / "meta"
            domain_dir = meta / "business" / "domains" / "payment"
            domain_dir.mkdir(parents=True)
            (domain_dir / "glossary.md").write_text("# 术语表", encoding="utf-8")
            (domain_dir / "rules.md").write_text("# 规则", encoding="utf-8")
            target = root / "service"
            target.mkdir()
            written = _distribute_domain(meta, target, "payment")
            self.assertIn("docs/domain/glossary.md", written)
            self.assertIn("docs/domain/rules.md", written)
            self.assertEqual((target / "docs" / "domain" / "glossary.md").read_text(encoding="utf-8"), "# 术语表")

    def test_nonexistent_domain_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            written = _distribute_domain(Path(tmpdir), Path(tmpdir) / "svc", "nonexistent")
        self.assertEqual(written, [])

    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            written = _distribute_domain(root, root / "svc", "../../etc")
            self.assertEqual(written, [])

    def test_rejects_dotdot_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            written = _distribute_domain(root, root / "svc", "..")
            self.assertEqual(written, [])

    def test_handles_binary_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            meta = root / "meta"
            domain_dir = meta / "business" / "domains" / "assets"
            domain_dir.mkdir(parents=True)
            (domain_dir / "diagram.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20)
            target = root / "service"
            target.mkdir()
            written = _distribute_domain(meta, target, "assets")
            self.assertIn("docs/domain/diagram.png", written)
            self.assertEqual((target / "docs" / "domain" / "diagram.png").read_bytes()[:4], b"\x89PNG")


class SyncRelativePathTests(unittest.TestCase):
    def test_sync_all_resolves_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            payment = root / "payment-service"
            payment.mkdir()
            order = root / "order-service"
            order.mkdir()
            meta = root / "meta"
            (meta / "services").mkdir(parents=True)
            reg = _REGISTRY_YAML.format(
                repo_payment="../payment-service",
                repo_order="../order-service",
            )
            (meta / "services" / "registry.yaml").write_text(reg, encoding="utf-8")
            (meta / "services" / "dependency-graph.yaml").write_text(_GRAPH_YAML, encoding="utf-8")
            results = run_sync_all(meta)
            self.assertIn("payment-service", results)
            self.assertIn("order-service", results)
            self.assertTrue((payment / "docs" / "service-context.md").exists())


class SyncDomainIntegrationTests(unittest.TestCase):
    def test_sync_distributes_domain_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            service = root / "payment-service"
            service.mkdir()
            meta = root / "meta"
            (meta / "services").mkdir(parents=True)
            reg = (
                "payment-service:\n"
                f"  repo: {service}\n"
                "  domain: payment\n"
                "  owner: test\n"
                "  summary: test\n"
            )
            (meta / "services" / "registry.yaml").write_text(reg, encoding="utf-8")
            (meta / "services" / "dependency-graph.yaml").write_text(
                "payment-service:\n  provides:\n    - GET /api/test\n", encoding="utf-8"
            )
            domain_dir = meta / "business" / "domains" / "payment"
            domain_dir.mkdir(parents=True)
            (domain_dir / "glossary.md").write_text("# 支付术语", encoding="utf-8")
            written = run_sync(service, meta)
            self.assertIn("docs/domain/glossary.md", written)
            self.assertEqual(
                (service / "docs" / "domain" / "glossary.md").read_text(encoding="utf-8"),
                "# 支付术语",
            )

    def test_sync_skips_domain_when_not_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            service = root / "payment-service"
            service.mkdir()
            meta = root / "meta"
            (meta / "services").mkdir(parents=True)
            reg = (
                "payment-service:\n"
                f"  repo: {service}\n"
                "  owner: test\n"
                "  summary: test\n"
            )
            (meta / "services" / "registry.yaml").write_text(reg, encoding="utf-8")
            (meta / "services" / "dependency-graph.yaml").write_text(
                "payment-service:\n  provides:\n    - GET /api/test\n", encoding="utf-8"
            )
            written = run_sync(service, meta)
            self.assertFalse(any("domain" in f for f in written))


if __name__ == "__main__":
    unittest.main()
