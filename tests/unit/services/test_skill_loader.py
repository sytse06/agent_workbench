"""Unit tests for SkillLoader."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.embedding_service import EmbeddingService
from agent_workbench.services.semantic_retriever import SemanticRetriever
from agent_workbench.services.skill_loader import (
    SkillDefinition,
    SkillLoader,
    _parse_skills_md,
)

_VALID_SKILLS_MD = textwrap.dedent("""\
    ---
    name: web_research
    description: "Search and retrieve content from the web."
    ---

    # Web Research Skills

    ## scrape
    Retrieve full content of a single URL.

    ## search
    Find information about a topic.
""")


def _make_retriever() -> SemanticRetriever:
    mock_es = MagicMock(spec=EmbeddingService)
    return SemanticRetriever(mock_es)


def _make_model_config() -> ModelConfig:
    return ModelConfig(provider="anthropic", model_name="claude-3-5-haiku-20241022")


# --- _parse_skills_md ---


def test_parse_skills_md_extracts_name_and_description():
    name, description, body = _parse_skills_md(_VALID_SKILLS_MD)
    assert name == "web_research"
    assert "Search and retrieve" in description


def test_parse_skills_md_body_contains_skill_headers():
    _, _, body = _parse_skills_md(_VALID_SKILLS_MD)
    assert "## scrape" in body
    assert "## search" in body


def test_parse_skills_md_raises_on_missing_frontmatter():
    with pytest.raises(ValueError, match="frontmatter"):
        _parse_skills_md("No frontmatter here.")


def test_parse_skills_md_raises_on_missing_name():
    content = "---\ndescription: desc\n---\nbody"
    with pytest.raises(ValueError, match="name"):
        _parse_skills_md(content)


def test_parse_skills_md_raises_on_missing_description():
    content = "---\nname: test\n---\nbody"
    with pytest.raises(ValueError, match="description"):
        _parse_skills_md(content)


# --- SkillLoader._load_domain ---


def test_load_domain_returns_none_for_missing_skills_md(tmp_path: Path):
    domain_dir = tmp_path / "some_domain"
    domain_dir.mkdir()
    loader = SkillLoader(tmp_path)
    assert loader._load_domain(domain_dir) is None


def test_load_domain_returns_skill_definition(tmp_path: Path):
    domain_dir = tmp_path / "web_research"
    domain_dir.mkdir()
    (domain_dir / "SKILLS.md").write_text(_VALID_SKILLS_MD)
    loader = SkillLoader(tmp_path)
    defn = loader._load_domain(domain_dir)
    assert isinstance(defn, SkillDefinition)
    assert defn.name == "web_research"
    assert defn.skills_catalog.strip() != ""


# --- SkillLoader.build_tools ---


def test_build_tools_returns_one_tool_for_web_research(tmp_path: Path):
    (tmp_path / "shared" / "web_research").mkdir(parents=True)
    (tmp_path / "shared" / "web_research" / "SKILLS.md").write_text(_VALID_SKILLS_MD)

    loader = SkillLoader(tmp_path)
    tools = loader.build_tools(
        mode="workbench",
        model_config=_make_model_config(),
        semantic_retriever=_make_retriever(),
    )
    assert len(tools) == 1
    assert tools[0].name == "web_research"


def test_build_tools_description_comes_from_frontmatter(tmp_path: Path):
    (tmp_path / "shared" / "web_research").mkdir(parents=True)
    (tmp_path / "shared" / "web_research" / "SKILLS.md").write_text(_VALID_SKILLS_MD)

    loader = SkillLoader(tmp_path)
    tools = loader.build_tools(
        mode="workbench",
        model_config=_make_model_config(),
        semantic_retriever=_make_retriever(),
    )
    assert "Search and retrieve" in tools[0].description


def test_build_tools_returns_empty_for_empty_skills_dir(tmp_path: Path):
    loader = SkillLoader(tmp_path)
    tools = loader.build_tools(
        mode="workbench",
        model_config=_make_model_config(),
        semantic_retriever=_make_retriever(),
    )
    assert tools == []


def test_build_tools_mode_specific_overrides_shared(tmp_path: Path):
    shared_md = _VALID_SKILLS_MD
    mode_md = _VALID_SKILLS_MD.replace(
        '"Search and retrieve content from the web."',
        '"Mode-specific description."',
    )

    (tmp_path / "shared" / "web_research").mkdir(parents=True)
    (tmp_path / "shared" / "web_research" / "SKILLS.md").write_text(shared_md)

    (tmp_path / "workbench" / "web_research").mkdir(parents=True)
    (tmp_path / "workbench" / "web_research" / "SKILLS.md").write_text(mode_md)

    loader = SkillLoader(tmp_path)
    tools = loader.build_tools(
        mode="workbench",
        model_config=_make_model_config(),
        semantic_retriever=_make_retriever(),
    )
    assert len(tools) == 1
    assert "Mode-specific description" in tools[0].description


def test_build_tools_unknown_domain_skipped(tmp_path: Path):
    unknown_md = _VALID_SKILLS_MD.replace("name: web_research", "name: unknown_domain")
    (tmp_path / "shared" / "unknown_domain").mkdir(parents=True)
    (tmp_path / "shared" / "unknown_domain" / "SKILLS.md").write_text(unknown_md)

    loader = SkillLoader(tmp_path)
    tools = loader.build_tools(
        mode="workbench",
        model_config=_make_model_config(),
        semantic_retriever=_make_retriever(),
    )
    assert tools == []
