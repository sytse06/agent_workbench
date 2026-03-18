"""SkillLoader — loads SKILLS.md domain catalogs and builds domain tools.

Directory layout:
    skills/
    ├── shared/           loaded for all modes
    │   └── web_research/
    │       └── SKILLS.md
    └── {mode}/           loaded for specific mode only (last wins on name clash)
        └── ...

Each SKILLS.md has YAML frontmatter (name, description) followed by the
sub-skill catalog body. The body is loaded into subgraph state only — it
never enters MessagesState.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml  # type: ignore[import-untyped]

from ..models.schemas import ModelConfig
from .semantic_retriever import SemanticRetriever

logger = logging.getLogger(__name__)


@dataclass
class SkillDefinition:
    name: str
    description: str  # frontmatter → tool description the agent sees
    skills_catalog: str  # SKILLS.md body → loaded into subgraph state


def _parse_skills_md(content: str) -> tuple[str, str, str]:
    """Parse a SKILLS.md file into (name, description, body).

    Expects YAML frontmatter between --- markers followed by the catalog body.
    """
    if not content.startswith("---"):
        raise ValueError("SKILLS.md must start with YAML frontmatter (---)")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("SKILLS.md frontmatter not closed with ---")

    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()

    name = str(frontmatter.get("name", ""))
    description = str(frontmatter.get("description", ""))

    if not name:
        raise ValueError("SKILLS.md frontmatter must include 'name'")
    if not description:
        raise ValueError("SKILLS.md frontmatter must include 'description'")

    return name, description, body


class SkillLoader:
    """Loads skill domains from the skills directory and builds BaseTool wrappers."""

    def __init__(self, skills_root: Path) -> None:
        self._skills_root = skills_root

    def _load_domain(self, domain_dir: Path) -> Optional[SkillDefinition]:
        skill_file = domain_dir / "SKILLS.md"
        if not skill_file.exists():
            logger.debug("SkillLoader: no SKILLS.md in %s — skipping", domain_dir)
            return None
        try:
            content = skill_file.read_text(encoding="utf-8")
            name, description, body = _parse_skills_md(content)
            logger.info("SkillLoader: loaded domain %r from %s", name, domain_dir)
            return SkillDefinition(
                name=name, description=description, skills_catalog=body
            )
        except Exception as exc:
            logger.warning("SkillLoader: failed to load %s — %s", skill_file, exc)
            return None

    def _collect_domains(self, mode: str) -> list[SkillDefinition]:
        domains: dict[str, SkillDefinition] = {}

        # Shared skills — available in all modes
        shared_dir = self._skills_root / "shared"
        if shared_dir.exists():
            for domain_dir in sorted(shared_dir.iterdir()):
                if domain_dir.is_dir():
                    defn = self._load_domain(domain_dir)
                    if defn:
                        domains[defn.name] = defn

        # Mode-specific skills — override shared on name clash (last wins)
        mode_dir = self._skills_root / mode
        if mode_dir.exists():
            for domain_dir in sorted(mode_dir.iterdir()):
                if domain_dir.is_dir():
                    defn = self._load_domain(domain_dir)
                    if defn:
                        domains[defn.name] = defn

        return list(domains.values())

    def build_tools(
        self,
        mode: str,
        model_config: ModelConfig,
        semantic_retriever: SemanticRetriever,
        firecrawl_client: Optional[Any] = None,
    ) -> list[Any]:
        """Build one BaseTool per skill domain for the given mode.

        Args:
            mode: Active app mode ("workbench" | "seo_coach").
            model_config: LLM config for match_skill_node and synthesize_node.
            semantic_retriever: Shared embedding + selection pipeline.
            firecrawl_client: Optional FirecrawlClient (None → execute_node stubbed).
        """
        domains = self._collect_domains(mode)
        tools = []
        for defn in domains:
            tool = _build_domain_tool(
                defn, model_config, semantic_retriever, firecrawl_client
            )
            if tool is not None:
                tools.append(tool)
        logger.info(
            "SkillLoader: built %d tool(s) for mode=%r: %s",
            len(tools),
            mode,
            [t.name for t in tools],
        )
        return tools


def _build_domain_tool(
    defn: SkillDefinition,
    model_config: ModelConfig,
    semantic_retriever: SemanticRetriever,
    firecrawl_client: Optional[Any],
) -> Optional[Any]:
    if defn.name == "web_research":
        from .web_research_graph import WebResearchGraph, WebResearchTool

        graph = WebResearchGraph(
            skills_catalog=defn.skills_catalog,
            semantic_retriever=semantic_retriever,
            model_config=model_config,
            firecrawl_client=firecrawl_client,
        )
        return WebResearchTool(graph=graph, description=defn.description)

    logger.warning("SkillLoader: no handler for domain %r — skipping", defn.name)
    return None
