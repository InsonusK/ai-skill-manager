"""Tests for core synchronization logic."""

import io
import json
import shutil
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_skill_manager.core import (
    SkillSync,
    _SyncSkill,
    build_source_to_target_map,
    collect_source_files,
    copy_skill,
)
from ai_skill_manager.models import LocalSource, Skill
from ai_skill_manager.utils import is_managed


def _make_fake_archive(repo_name: str, files: dict) -> bytes:
    """Create a tar.gz archive in memory."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel_path, content in files.items():
            arcname = f"{repo_name}/{rel_path}"
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=arcname)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _skill(file_path: Path, folder_path: Path | None = None) -> Skill:
    """Helper to create a Skill and ensure it has a name in frontmatter."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        name = folder_path.name if folder_path else file_path.name[:-9]
        file_path.write_text(f"---\nname: {name}\n---\n")
    return Skill(
        file_path=file_path,
        folder_path=folder_path,
        source=LocalSource(file_path.parent),
    )


class TestBuildSourceToTargetMap(unittest.TestCase):
    def test_flat_mapping(self):
        src = Path(tempfile.mkdtemp())
        try:
            md = src / "guide.skill.md"
            md.write_text("---\nname: guide\n---\n# Guide")
            skill = _skill(md)
            sync_skill = _SyncSkill(skill=skill, target_name="guide")

            result = build_source_to_target_map([sync_skill], Path("/tgt"))

            self.assertEqual(result[md], Path("/tgt/guide/SKILL.md"))
        finally:
            shutil.rmtree(src)

    def test_directory_mapping(self):
        src = Path(tempfile.mkdtemp())
        try:
            skill_dir = src / "web"
            skill_dir.mkdir()
            (skill_dir / "web.skill.md").write_text("---\nname: web\n---\n# Web")
            (skill_dir / "extra.md").write_text("# Extra")

            skill = _skill(skill_dir / "web.skill.md", skill_dir)
            sync_skill = _SyncSkill(skill=skill, target_name="web")

            result = build_source_to_target_map([sync_skill], Path("/tgt"))

            self.assertEqual(result[skill_dir / "web.skill.md"], Path("/tgt/web/SKILL.md"))
            self.assertEqual(result[skill_dir / "extra.md"], Path("/tgt/web/extra.md"))
        finally:
            shutil.rmtree(src)

    def test_multiple_mappings(self):
        src = Path(tempfile.mkdtemp())
        try:
            flat_md = src / "a.skill.md"
            flat_md.write_text("---\nname: a\n---\n# A")
            dir_src = src / "b"
            dir_src.mkdir()
            (dir_src / "b.skill.md").write_text("---\nname: b\n---\n# B")

            skills = [
                _SyncSkill(skill=_skill(flat_md), target_name="a"),
                _SyncSkill(skill=_skill(dir_src / "b.skill.md", dir_src), target_name="b"),
            ]

            result = build_source_to_target_map(skills, Path("/tgt"))

            self.assertEqual(len(result), 2)
            self.assertEqual(result[flat_md], Path("/tgt/a/SKILL.md"))
            self.assertEqual(result[dir_src / "b.skill.md"], Path("/tgt/b/SKILL.md"))
        finally:
            shutil.rmtree(src)


class TestCollectSourceFiles(unittest.TestCase):
    def test_flat_files(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            src_a = tmp / "a.skill.md"
            src_a.write_text("---\nname: a\n---\n# A")
            src_b = tmp / "b.skill.md"
            src_b.write_text("---\nname: b\n---\n# B")

            sync_skills = [
                _SyncSkill(skill=_skill(src_a), target_name="a"),
                _SyncSkill(skill=_skill(src_b), target_name="b"),
            ]

            result = collect_source_files(sync_skills)

            self.assertEqual(result, {src_a, src_b})
        finally:
            shutil.rmtree(tmp)

    def test_directory_files(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            skill_dir = tmp / "web"
            skill_dir.mkdir()
            (skill_dir / "web.skill.md").write_text("---\nname: web\n---\n# Web")
            (skill_dir / "extra.md").write_text("# Extra")

            skill = _skill(skill_dir / "web.skill.md", skill_dir)
            sync_skill = _SyncSkill(skill=skill, target_name="web")
            result = collect_source_files([sync_skill])

            self.assertEqual(len(result), 2)
            self.assertIn(skill_dir / "web.skill.md", result)
            self.assertIn(skill_dir / "extra.md", result)
        finally:
            shutil.rmtree(tmp)


class TestCopySkill(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.source = self.tmpdir / "source"
        self.source.mkdir()
        self.target = self.tmpdir / "target"
        self.target.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_copy_flat(self):
        md = self.source / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")
        skill = _skill(md)
        sync_skill = _SyncSkill(skill=skill, target_name="guide")

        copy_skill(sync_skill, self.target, dry_run=False)

        self.assertTrue((self.target / "guide").exists())
        self.assertTrue((self.target / "guide" / "SKILL.md").exists())
        self.assertEqual((self.target / "guide" / "SKILL.md").read_text(), "---\nname: guide\n---\n# Guide")
        self.assertTrue(is_managed(self.target / "guide"))

    def test_copy_directory(self):
        skill = self.source / "web"
        skill.mkdir()
        (skill / "web.skill.md").write_text("---\nname: web\n---\n# Web")
        (skill / "extra.md").write_text("# Extra")

        sync_skill = _SyncSkill(
            skill=_skill(skill / "web.skill.md", skill),
            target_name="web",
        )
        copy_skill(sync_skill, self.target, dry_run=False)

        self.assertTrue((self.target / "web").exists())
        self.assertTrue((self.target / "web" / "SKILL.md").exists())
        self.assertTrue((self.target / "web" / "extra.md").exists())
        self.assertTrue(is_managed(self.target / "web"))

    def test_dry_run_no_changes(self):
        md = self.source / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")
        sync_skill = _SyncSkill(skill=_skill(md), target_name="guide")

        copy_skill(sync_skill, self.target, dry_run=True)

        self.assertFalse((self.target / "guide").exists())

    def test_overwrite_existing(self):
        existing = self.target / "guide"
        existing.mkdir()
        (existing / "old.md").write_text("old")

        md = self.source / "guide.skill.md"
        md.write_text("---\nname: guide\n---\n# Guide")
        sync_skill = _SyncSkill(skill=_skill(md), target_name="guide")
        copy_skill(sync_skill, self.target, dry_run=False)

        self.assertFalse((existing / "old.md").exists())
        self.assertTrue((existing / "SKILL.md").exists())

    def test_copy_directory_skill_renames_skill_md(self):
        """Directory skills with {name}.skill.md are copied with SKILL.md."""
        skill = self.source / "web"
        skill.mkdir()
        (skill / "web.skill.md").write_text("---\nname: web\n---\n# Web")
        (skill / "extra.md").write_text("# Extra")

        sync_skill = _SyncSkill(
            skill=_skill(skill / "web.skill.md", skill),
            target_name="web",
        )
        copy_skill(sync_skill, self.target, dry_run=False)

        self.assertTrue((self.target / "web").exists())
        self.assertTrue((self.target / "web" / "SKILL.md").exists())
        self.assertEqual((self.target / "web" / "SKILL.md").read_text(), "---\nname: web\n---\n# Web")
        self.assertFalse((self.target / "web" / "web.skill.md").exists())
        self.assertTrue((self.target / "web" / "extra.md").exists())


class TestSkillSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_full_sync(self):
        # Create source structure
        src = self.tmpdir / "skills-repo"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        web = src / "web"
        web.mkdir()
        (web / "web.skill.md").write_text("---\nname: web\n---\n# Web")

        # Create config
        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./skills-repo"}],
            "settings": {"target": ".agents/skills"}
        }))

        # Run sync
        sync = SkillSync(config_file=config)
        result = sync.sync()

        self.assertEqual(result["synced_count"], 2)

        # Verify structure
        target = self.tmpdir / ".agents" / "skills"
        self.assertTrue((target / "guide").exists())
        self.assertTrue((target / "web").exists())
        self.assertTrue((target / "guide" / ".ai-skills-managed").exists())

    def test_conflict_error(self):
        src = self.tmpdir / "repo"
        src.mkdir()

        a = src / "a"
        a.mkdir()
        (a / "a.skill.md").write_text("---\nname: a\n---\n# A")

        b = src / "b"
        b.mkdir()
        (b / "b.skill.md").write_text("---\nname: b\n---\n# B")

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [
                {"path": "./repo/a", "name": "same"},
                {"path": "./repo/b", "name": "same"}
            ]
        }))

        sync = SkillSync(config_file=config, on_conflict="error")

        with self.assertRaises(ValueError) as ctx:
            sync.sync()

        self.assertIn("CONFLICT", str(ctx.exception))

    def test_dry_run(self):
        src = self.tmpdir / "repo"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo"}]
        }))

        sync = SkillSync(config_file=config, dry_run=True)
        result = sync.sync()

        self.assertTrue(result["dry_run"])
        self.assertFalse((self.tmpdir / ".agents").exists())

    def test_orphan_removal(self):
        target = self.tmpdir / ".agents" / "skills"
        target.mkdir(parents=True)

        old = target / "old-skill"
        old.mkdir()
        from ai_skill_manager.utils import tag_managed
        tag_managed(old)

        src = self.tmpdir / "repo"
        src.mkdir()
        (src / "new.skill.md").write_text("---\nname: new\n---\n# New")

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo"}],
            "settings": {"remove_orphans": True}
        }))

        sync = SkillSync(config_file=config)
        sync.sync()

        self.assertFalse(old.exists())
        self.assertTrue((target / "new").exists())

    def test_skip_when_unchanged(self):
        src = self.tmpdir / "repo"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo"}]
        }))

        sync = SkillSync(config_file=config)
        result1 = sync.sync()
        self.assertEqual(result1["synced_count"], 1)
        self.assertEqual(result1["skipped_count"], 0)

        result2 = sync.sync()
        self.assertEqual(result2["synced_count"], 0)
        self.assertEqual(result2["skipped_count"], 1)

    def test_copy_when_source_changed(self):
        src = self.tmpdir / "repo"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo"}]
        }))

        sync = SkillSync(config_file=config)
        sync.sync()

        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide Updated")

        result = sync.sync()
        self.assertEqual(result["synced_count"], 1)
        self.assertEqual(result["skipped_count"], 0)

    def test_force_copies_unchanged(self):
        src = self.tmpdir / "repo"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo"}]
        }))

        sync = SkillSync(config_file=config)
        sync.sync()

        sync_force = SkillSync(config_file=config, force=True)
        result = sync_force.sync()
        self.assertEqual(result["synced_count"], 1)
        self.assertEqual(result["skipped_count"], 0)

    def test_copy_when_adapter_version_changed(self):
        src = self.tmpdir / "repo"
        src.mkdir()
        (src / "guide.skill.md").write_text("---\nname: guide\n---\n# Guide")

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{"path": "./repo"}]
        }))

        sync = SkillSync(config_file=config)
        sync.sync()

        # Simulate adapter version change
        from ai_skill_manager.utils import read_managed_state, write_managed_state
        target = self.tmpdir / ".agents" / "skills" / "guide"
        state = read_managed_state(target)
        state["adapters"][0]["version"] = 999
        write_managed_state(target, state)

        result = sync.sync()
        self.assertEqual(result["synced_count"], 1)
        self.assertEqual(result["skipped_count"], 0)

    def test_github_source_sync(self):
        """Full sync with a mocked GitHub source."""
        archive = _make_fake_archive(
            "ai-skills-master",
            {
                "skills/version-control/version-control.skill.md": "---\nname: version-control\n---\n# Version Control",
                "skills/version-control/extra.md": "# Extra",
                "skills/ansible/ansible.skill.md": "---\nname: ansible\n---\n# Ansible",
            },
        )

        def fake_download(owner, repo, tree):
            path = self.tmpdir / "fake_archive.tar.gz"
            path.write_bytes(archive)
            return path

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{
                "type": "github",
                "path": "https://github.com/owner/ai-skills",
                "tree": "master",
                "subpath": "skills",
            }],
            "settings": {"target": ".agents/skills"}
        }))

        with patch(
            "ai_skill_manager.discovery.source.github._download_archive",
            side_effect=fake_download,
        ):
            sync = SkillSync(config_file=config)
            result = sync.sync()

        self.assertEqual(result["synced_count"], 2)
        self.assertEqual(result["skipped_count"], 0)

        target = self.tmpdir / ".agents" / "skills"
        self.assertTrue((target / "version-control").exists())
        self.assertTrue((target / "version-control" / "SKILL.md").exists())
        self.assertTrue((target / "version-control" / "extra.md").exists())
        self.assertTrue((target / "ansible").exists())
        self.assertTrue((target / "ansible" / "SKILL.md").exists())

    def test_github_source_single_md_file_sync(self):
        """Sync a single .md file from a mocked GitHub source as a flat skill."""
        archive = _make_fake_archive(
            "ai-skills-master",
            {
                "docs/quickstart.skill.md": "---\nname: quickstart\n---\n# Quickstart",
            },
        )

        def fake_download(owner, repo, tree):
            path = self.tmpdir / "fake_archive.tar.gz"
            path.write_bytes(archive)
            return path

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{
                "type": "github",
                "path": "https://github.com/owner/ai-skills",
                "tree": "master",
                "subpath": "docs/quickstart.skill.md",
            }],
            "settings": {"target": ".agents/skills"}
        }))

        with patch(
            "ai_skill_manager.discovery.source.github._download_archive",
            side_effect=fake_download,
        ):
            sync = SkillSync(config_file=config)
            result = sync.sync()

        self.assertEqual(result["synced_count"], 1)
        self.assertEqual(result["skipped_count"], 0)

        target = self.tmpdir / ".agents" / "skills" / "quickstart"
        self.assertTrue(target.exists())
        self.assertTrue((target / "SKILL.md").exists())
        self.assertEqual((target / "SKILL.md").read_text(), "---\nname: quickstart\n---\n# Quickstart")

    def test_github_source_multiple_subpaths_sync(self):
        """Sync from a mocked GitHub source with multiple subpaths."""
        archive = _make_fake_archive(
            "ai-skills-master",
            {
                "skills/web/web.skill.md": "---\nname: web\n---\n# Web",
                "docs/guide.skill.md": "---\nname: guide\n---\n# Guide",
            },
        )

        def fake_download(owner, repo, tree):
            path = self.tmpdir / "fake_archive.tar.gz"
            path.write_bytes(archive)
            return path

        config = self.tmpdir / "ai-skills.yaml"
        config.write_text(json.dumps({
            "sources": [{
                "type": "github",
                "path": "https://github.com/owner/ai-skills",
                "tree": "master",
                "subpath": ["skills", "docs"],
            }],
            "settings": {"target": ".agents/skills"}
        }))

        with patch(
            "ai_skill_manager.discovery.source.github._download_archive",
            side_effect=fake_download,
        ):
            sync = SkillSync(config_file=config)
            result = sync.sync()

        self.assertEqual(result["synced_count"], 2)
        self.assertEqual(result["skipped_count"], 0)

        target = self.tmpdir / ".agents" / "skills"
        self.assertTrue((target / "web").exists())
        self.assertTrue((target / "web" / "SKILL.md").exists())
        self.assertTrue((target / "guide").exists())
        self.assertTrue((target / "guide" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
