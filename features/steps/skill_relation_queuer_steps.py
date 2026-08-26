from pathlib import Path

from behave import given, then, when

from ai_skill_manager.entities.skill_kind import SkillKind
from ai_skill_manager.entities.skill_v2 import Skill
from ai_skill_manager.models.skill_relation_queuer import SkillRelationQueuer


@given("relation discovery is enabled")
def step_relation_discovery_enabled(context):
    context.add_relations = True


@given("relation discovery is disabled")
def step_relation_discovery_disabled(context):
    context.add_relations = False


@given("no skills are queued yet")
def step_no_skills_queued(context):
    context.queuer = SkillRelationQueuer(add_relations=context.add_relations)
    context.decision = None


@given('a skill named "{name}" is already queued at "{path}"')
def step_skill_already_queued(context, name, path):
    context.queuer = SkillRelationQueuer(add_relations=context.add_relations)
    skill = Skill(name=name, path=Path(path).resolve(), kind=SkillKind.dir)
    context.queuer.handle(skill)
    context.decision = None


@when('the queuer handles a linked skill named "{name}"')
def step_handle_linked_skill(context, name):
    skill = Skill(
        name=name,
        path=Path(f"/tmp/skills/{name}").resolve(),
        kind=SkillKind.dir,
    )
    context.decision = context.queuer.handle(skill)


@when('the queuer handles the same skill at "{path}"')
def step_handle_same_skill_at_path(context, path):
    skill = Skill(name="linked-skill", path=Path(path).resolve(), kind=SkillKind.dir)
    context.decision = context.queuer.handle(skill)


@when('the queuer handles a different skill named "{name}" at "{path}"')
def step_handle_different_skill(context, name, path):
    skill = Skill(name=name, path=Path(path).resolve(), kind=SkillKind.dir)
    context.decision = context.queuer.handle(skill)


@then("the skill is queued")
def step_skill_is_queued(context):
    assert context.decision.queued is True
    assert context.decision.error is None


@then("the skill is not queued")
def step_skill_is_not_queued(context):
    assert context.decision.queued is False


@then("the skill is not queued again")
def step_skill_is_not_queued_again(context):
    assert context.decision.queued is False


@then("there is no error")
def step_no_error(context):
    assert context.decision.error is None


@then('the error reports a conflict with "{name}"')
def step_error_reports_conflict(context, name):
    assert context.decision.error is not None
    assert name in context.decision.error
    assert "already queued" in context.decision.error


@then('the error reports the skill is not in configured sources')
def step_error_not_in_configured_sources(context):
    assert context.decision.error is not None
    assert "configured sources" in context.decision.error
