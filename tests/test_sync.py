"""Tests for services/sync.py."""

import shutil
import tempfile
import unittest
from pathlib import Path

from ai_skill_manager.adapters.models.adapter_message import AdapterMessage
from ai_skill_manager.adapters.rules.abs_adapter import absAdapter
from ai_skill_manager.entities import LocalSource, Skill, SkillFormat
from ai_skill_manager.service.sync import remove_orphans, run_sync
from ai_skill_manager.functions.hash import compute_skill_hash
from ai_skill_manager.functions.managed_state import tag_managed
from ai_skill_manager.sync_exception import SyncFailedError


class TestRunSync(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.source_dir = self.tmpdir / "source"
        self.source_dir.mkdir()
        self.target_dir = self.tmpdir / "target"

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _dir_skill(self, name: str):
        skill_dir = self.source_dir / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}\n")
        return skill_dir

    def test_rewrites_cross_skill_link(self):
        a = self._dir_skill("skill-a")
        b = self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[link to b](../skill-b/SKILL.md)\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["skills_count"], 2)
        self.assertEqual(result["links_replaced"], 1)
        synced_a = (self.target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link to b](skill-b/SKILL.md)", synced_a)

    def test_rewrites_repo_absolute_link_to_own_nested_file_ignoring_name_collision(self):
        # EN: A repo-absolute link to a file nested inside the *same* skill
        # must resolve as a self-link, even when an unrelated skill elsewhere
        # in the repo happens to be named after one of the path's
        # intermediate segments (here "templates"). The old heuristic
        # resolved such links by re-parsing them against the *copied* tree,
        # which - for repo-absolute links with a prefix not preserved by the
        # (flattened) copy - reclassified this self-link as a cross-skill
        # link and then risked matching the nearest same-named skill instead
        # of walking out to the true owning skill.
        # RU: Repo-absolute ссылка на файл, вложенный внутрь *того же*
        # скилла, должна резолвиться как self-ссылка, даже если где-то ещё в
        # репозитории есть несвязанный скилл, названный так же, как один из
        # промежуточных сегментов пути (здесь "templates"). Старая эвристика
        # резолвила такие ссылки, повторно парся их относительно
        # *скопированного* дерева, что для repo-absolute ссылок с префиксом,
        # не сохраняющимся при (уплощённом) копировании, переклассифицировало
        # эту self-ссылку в межскилловую и рисковало совпасть с ближайшим
        # одноимённым скиллом вместо того, чтобы дойти до настоящего
        # владеющего скилла.
        feature_dir = self.source_dir / "skills" / "create-feature"
        feature_dir.mkdir(parents=True)
        templates_dir = feature_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "plan.md").write_text("# Plan\n")
        (feature_dir / "SKILL.md").write_text(
            "---\nname: create-feature\n---\n# Create feature\n"
            "[plan](skills/create-feature/templates/plan.md)\n"
        )

        # An unrelated skill whose name collides with the intermediate
        # "templates" path segment used inside create-feature's own folder.
        templates_skill_dir = self.source_dir / "templates"
        templates_skill_dir.mkdir()
        (templates_skill_dir / "SKILL.md").write_text(
            "---\nname: templates\n---\n# Templates\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["skills_count"], 2)
        synced = (self.target_dir / "create-feature" / "SKILL.md").read_text()
        self.assertIn("[plan](create-feature/templates/plan.md)", synced)

    def test_rewrites_cross_skill_link_with_repo_path_above_target_dir(self):
        # EN: When repo_path is above target_dir, links include the target_dir
        # prefix in repo-absolute form.
        # RU: Когда repo_path выше target_dir, ссылки включают префикс target_dir
        # в repo-absolute форме.
        a = self._dir_skill("skill-a")
        b = self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[link to b](../skill-b/SKILL.md)\n"
        )

        target_dir = self.target_dir / "agents" / "skills"
        result = run_sync(
            [LocalSource(scan_path=self.source_dir)],
            target_dir,
            repo_path=self.target_dir,
        )

        self.assertEqual(result["skills_count"], 2)
        self.assertEqual(result["links_replaced"], 1)
        synced_a = (target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link to b](agents/skills/skill-b/SKILL.md)", synced_a)

    def test_rewrites_internal_link(self):
        skill = self._dir_skill("skill")
        (skill / "template.md").write_text("# Template\n")
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[template](./template.md)\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["links_replaced"], 1)
        synced = (self.target_dir / "skill" / "SKILL.md").read_text()
        self.assertIn("[template](skill/template.md)", synced)

    def test_rewrites_wiki_link(self):
        a = self._dir_skill("skill-a")
        b = self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[[../skill-b/SKILL.md|link to b]]\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["links_replaced"], 1)
        synced_a = (self.target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link to b](skill-b/SKILL.md)", synced_a)

    def test_skips_external_url(self):
        skill = self._dir_skill("skill")
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[external](https://example.com)\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["links_replaced"], 0)
        synced = (self.target_dir / "skill" / "SKILL.md").read_text()
        self.assertIn("[external](https://example.com)", synced)

    def test_raises_on_invalid_link(self):
        skill = self._dir_skill("skill")
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[bad](../nowhere.md)\n"
        )

        with self.assertRaises(SyncFailedError) as ctx:
            run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        shutil.rmtree(ctx.exception.staging_dir, ignore_errors=True)
        self.assertFalse(self.target_dir.exists())

    def test_handles_flat_skill(self):
        md = self.source_dir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n")

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertEqual(result["skills_count"], 1)
        self.assertTrue((self.target_dir / "guide" / "SKILL.md").exists())

    def test_copies_repo_absolute_linked_file_from_flat_skill(self):
        # EN: When source repo_path differs from target repo_path, repo-absolute
        # links authored in the source must still resolve to the original file
        # and be copied into files/ instead of raising a path-not-found error.
        # RU: Когда repo_path источника отличается от целевого repo-absolute
        # ссылки, созданные в источнике, должны разрешаться в исходный файл
        # и копироваться в files/, а не вызывать ошибку "path not found".
        skill_dir = self.source_dir / "skills" / "create-feature"
        skill_dir.mkdir(parents=True)
        templates_dir = skill_dir / "templates"
        templates_dir.mkdir(parents=True)
        (templates_dir / "Impementation plan.md").write_text("# Plan\n")
        (skill_dir / "create-feature.skill.md").write_text(
            "---\nname: create-feature\n---\n# Create feature\n"
            "[[skills/create-feature/templates/Impementation plan.md|Impementation plan.md]]\n"
        )

        result = run_sync(
            [LocalSource(scan_path=self.source_dir, repo_path=self.source_dir)],
            self.target_dir,
            repo_path=self.target_dir,
        )

        self.assertEqual(result["skills_count"], 1)
        self.assertEqual(result["links_replaced"], 1)
        synced = (self.target_dir / "create-feature" / "SKILL.md").read_text()
        self.assertIn(
            "[Impementation plan.md](./files/Impementation plan.md)", synced
        )
        self.assertTrue(
            (self.target_dir / "create-feature" / "files" / "Impementation plan.md").exists()
        )

    def test_copies_non_markdown_files(self):
        skill = self._dir_skill("skill")
        (skill / "template.md").write_text("# Template\n")
        (skill / "data.json").write_text('{"key": "value"}\n')
        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill\n[template](./template.md)\n"
        )

        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertTrue((self.target_dir / "skill" / "data.json").exists())
        self.assertEqual(
            (self.target_dir / "skill" / "data.json").read_text(),
            '{"key": "value"}\n',
        )

    def test_copies_skipped_subdirectories(self):
        # EN: Subdirectories listed in skip_folder must still be copied as part
        # of the directory skill, even though they are excluded from nested-skill
        # detection.
        # RU: Поддиректории из skip_folder должны всё равно копироваться
        # вместе с директориальным навыком, несмотря на исключение из
        # обнаружения вложенных навыков.
        skill = self._dir_skill("skill")
        examples = skill / "examples"
        examples.mkdir()
        (examples / "sample.md").write_text("# Sample\n")
        (skill / "SKILL.md").write_text("---\nname: skill\n---\n# Skill\n")

        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertTrue((self.target_dir / "skill" / "examples" / "sample.md").exists())

    def test_preserves_link_fragments(self):
        a = self._dir_skill("skill-a")
        b = self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[link](../skill-b/SKILL.md#section)\n"
        )

        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        synced_a = (self.target_dir / "skill-a" / "SKILL.md").read_text()
        self.assertIn("[link](skill-b/SKILL.md#section)", synced_a)

    def test_progress_callback_called(self):
        self._dir_skill("skill-a")
        self._dir_skill("skill-b")
        events = []

        run_sync(
            [LocalSource(scan_path=self.source_dir)],
            self.target_dir,
            progress=lambda *args: events.append(args),
        )

        stages = [stage for stage, _, _ in events]
        self.assertIn("discover", stages)
        self.assertIn("validate", stages)
        self.assertIn("copy", stages)
        self.assertIn("adapt", stages)
        self.assertIn("write_managed_state", stages)
        self.assertIn("remove_orphans", stages)

    def test_skips_unchanged_skill_on_second_sync(self):
        skill = self._dir_skill("skill")
        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        target_file = self.target_dir / "skill" / "SKILL.md"
        target_file.write_text("---\nname: skill\n---\n# stale\n")

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertIn("# stale", target_file.read_text())
        self.assertEqual(result["skipped_count"], 1)

    def test_skips_unchanged_flat_skill_on_second_sync(self):
        md = self.source_dir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n")
        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        target_file = self.target_dir / "guide" / "SKILL.md"
        target_file.write_text("---\nname: guide\n---\n# stale\n")

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertIn("# stale", target_file.read_text())
        self.assertEqual(result["skipped_count"], 1)

    def test_re_copies_when_source_changes(self):
        skill = self._dir_skill("skill")
        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        (skill / "SKILL.md").write_text(
            "---\nname: skill\n---\n# Skill updated\n"
        )

        result = run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertIn("# Skill updated", (self.target_dir / "skill" / "SKILL.md").read_text())
        self.assertEqual(result["skipped_count"], 0)

    def test_managed_state_hash_is_source_hash(self):
        skill = self._dir_skill("skill")
        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        from ai_skill_manager.service.discover import discover

        discovered = discover([LocalSource(scan_path=self.source_dir)])
        source_skill = discovered[0]
        state_file = self.target_dir / "skill" / ".ai-skills-managed"
        import json

        state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["hash"], compute_skill_hash(source_skill))

    def test_re_copies_when_adapter_version_changes(self):
        class NoopAdapterV1(absAdapter):
            @classmethod
            def version(cls):
                return "1.0.0"

            def adapt(self, old_skill, new_skill):
                return AdapterMessage(message="noop", params={})

        class NoopAdapterV2(absAdapter):
            @classmethod
            def version(cls):
                return "2.0.0"

            def adapt(self, old_skill, new_skill):
                return AdapterMessage(message="noop", params={})

        skill = self._dir_skill("skill")
        run_sync(
            [LocalSource(scan_path=self.source_dir)],
            self.target_dir,
            adapters=[NoopAdapterV1],
        )

        target_file = self.target_dir / "skill" / "SKILL.md"
        target_file.write_text("---\nname: skill\n---\n# stale\n")

        run_sync(
            [LocalSource(scan_path=self.source_dir)],
            self.target_dir,
            adapters=[NoopAdapterV2],
        )

        self.assertNotIn("# stale", target_file.read_text())

    def test_copies_when_target_is_unmanaged(self):
        skill = self._dir_skill("skill")
        unmanaged_target = self.target_dir / "skill"
        unmanaged_target.mkdir(parents=True)
        (unmanaged_target / "SKILL.md").write_text(
            "---\nname: skill\n---\n# stale\n"
        )

        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertNotIn("# stale", (unmanaged_target / "SKILL.md").read_text())

    def test_force_copies_unchanged_skill(self):
        skill = self._dir_skill("skill")
        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        target_file = self.target_dir / "skill" / "SKILL.md"
        target_file.write_text("---\nname: skill\n---\n# stale\n")

        result = run_sync(
            [LocalSource(scan_path=self.source_dir)],
            self.target_dir,
            force=True,
        )

        self.assertNotIn("# stale", target_file.read_text())
        self.assertEqual(result["skipped_count"], 0)

    def test_force_copies_unchanged_flat_skill(self):
        md = self.source_dir / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide\n")
        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        target_file = self.target_dir / "guide" / "SKILL.md"
        target_file.write_text("---\nname: guide\n---\n# stale\n")

        result = run_sync(
            [LocalSource(scan_path=self.source_dir)],
            self.target_dir,
            force=True,
        )

        self.assertNotIn("# stale", target_file.read_text())
        self.assertEqual(result["skipped_count"], 0)

    def _staging_dir(self) -> Path:
        return self.target_dir.parent / f".ai-skill-manager-tmp-{self.target_dir.name}"

    def test_staging_dir_removed_after_successful_sync(self):
        self._dir_skill("skill")

        run_sync([LocalSource(scan_path=self.source_dir)], self.target_dir)

        self.assertFalse(self._staging_dir().exists())
        self.assertTrue((self.target_dir / "skill" / "SKILL.md").exists())

    def test_dry_run_materializes_and_reports_but_leaves_target_untouched(self):
        # EN: Dry-run must actually materialize skills (so link conversion
        # errors are caught, matching the check/sync contract) but must
        # never touch target_dir or leave the staging directory behind.
        # RU: Dry-run должен реально материализовать скиллы (чтобы ошибки
        # конвертации ссылок были пойманы, в соответствии с контрактом
        # check/sync), но никогда не должен трогать target_dir или оставлять
        # после себя staging-директорию.
        a = self._dir_skill("skill-a")
        self._dir_skill("skill-b")
        (a / "SKILL.md").write_text(
            "---\nname: skill-a\n---\n# A\n[link to b](../skill-b/SKILL.md)\n"
        )

        result = run_sync(
            [LocalSource(scan_path=self.source_dir)], self.target_dir, dry_run=True
        )

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["links_replaced"], 1)
        self.assertFalse(self.target_dir.exists())
        self.assertFalse(self._staging_dir().exists())

    def test_materialization_failure_raises_and_preserves_staging(self):
        # EN: An adapter failure must fail the whole sync, leave target_dir
        # untouched, and keep the staging directory around for inspection.
        # RU: Ошибка адаптера должна приводить к неудаче всей синхронизации,
        # оставлять target_dir нетронутым и сохранять staging-директорию для
        # изучения.
        class ExplodingAdapter(absAdapter):
            @classmethod
            def version(cls) -> str:
                return "1.0.0"

            def adapt(self, old_skill, new_skill):
                raise RuntimeError("boom")

        self._dir_skill("skill")

        with self.assertRaises(SyncFailedError) as ctx:
            run_sync(
                [LocalSource(scan_path=self.source_dir)],
                self.target_dir,
                adapters=[ExplodingAdapter],
            )

        error = ctx.exception
        self.assertEqual(len(error.errors), 1)
        self.assertIn("boom", error.errors[0].message)
        self.assertFalse(self.target_dir.exists())
        self.assertTrue(error.staging_dir.exists())
        self.assertTrue((error.staging_dir / "skill" / "SKILL.md").exists())
        shutil.rmtree(error.staging_dir)


class TestRemoveOrphans(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.target_dir = self.tmpdir / "target"
        self.target_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _skill(self, name: str) -> Skill:
        skill_dir = self.target_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_file.write_text(f"---\nname: {name}\n---\n# {name}\n")
        return Skill(
            file_path=skill_file,
            folder_path=skill_dir,
            source_path=self.target_dir,
            source=LocalSource(scan_path=self.target_dir),
            format=SkillFormat.Agent,
        )

    def test_removes_managed_orphan_skill(self):
        orphan = self.target_dir / "orphan"
        orphan.mkdir()
        tag_managed(orphan)

        kept = self._skill("kept")

        removed = remove_orphans(self.target_dir, [kept])

        self.assertFalse(orphan.exists())
        self.assertTrue(kept.folder_path.exists())
        self.assertEqual(removed, [orphan.resolve()])

    def test_keeps_unmanaged_directories(self):
        unmanaged = self.target_dir / "unmanaged"
        unmanaged.mkdir()

        kept = self._skill("kept")

        remove_orphans(self.target_dir, [kept])

        self.assertTrue(unmanaged.exists())
        self.assertTrue(kept.folder_path.exists())

    def test_keeps_copied_managed_skill(self):
        skill = self._skill("skill")
        tag_managed(skill.folder_path)

        remove_orphans(self.target_dir, [skill])

        self.assertTrue(skill.folder_path.exists())

    def test_progress_callback_called(self):
        orphan = self.target_dir / "orphan"
        orphan.mkdir()
        tag_managed(orphan)

        kept = self._skill("kept")
        events = []

        remove_orphans(
            self.target_dir,
            [kept],
            progress=lambda *args: events.append(args),
        )

        self.assertEqual(
            events,
            [
                ("remove_orphans", 0, 2),
                ("remove_orphans", 1, 2),
                ("remove_orphans", 2, 2),
            ],
        )
