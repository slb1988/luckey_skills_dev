"""Policy engine for skill activation rules."""

import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config
from engine.skill_evaluator import SkillRanking


class ActivationPlan(BaseModel):
    """Plan for which skills to activate."""
    activated: List[str]
    rejected: List[str]
    execution_order: List[str]


class PolicyEngine:
    """Apply policy rules to skill rankings."""

    def __init__(self):
        self.config = Config
        self._conflicts_cache: Dict = {}
        self._dependencies_cache: Dict = {}

    def load_registry(self, registry_type: str) -> dict:
        """Load JSON from registry directory."""
        registry_path = self.config.get_registry_path(f"skill_{registry_type}.json")

        if not registry_path.exists():
            return {}

        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {registry_type} registry: {e}", file=sys.stderr)
            return {}

    def apply_threshold(
        self,
        rankings: List[SkillRanking],
        threshold: float
    ) -> Tuple[List[SkillRanking], List[SkillRanking]]:
        """Filter rankings by confidence threshold."""
        activated = [r for r in rankings if r.confidence >= threshold]
        rejected = [r for r in rankings if r.confidence < threshold]
        return activated, rejected

    def resolve_conflicts(
        self,
        activated: List[SkillRanking]
    ) -> Tuple[List[str], List[str]]:
        """Remove conflicting skills, keeping higher confidence ones."""
        if not self._conflicts_cache:
            self._conflicts_cache = self.load_registry("conflicts")

        conflicts = self._conflicts_cache.get("conflicts", [])
        activated_names = {r.skill: r.confidence for r in activated}
        to_remove = set()

        for conflict in conflicts:
            conflict_skills = conflict.get("skills", [])
            present = [s for s in conflict_skills if s in activated_names]

            if len(present) > 1:
                # Sort by confidence, remove all but the highest
                present_sorted = sorted(present, key=lambda s: activated_names[s], reverse=True)
                to_remove.update(present_sorted[1:])

                reason = conflict.get("reason", "Conflict detected")
                print(
                    f"Conflict resolved: keeping {present_sorted[0]}, "
                    f"removing {present_sorted[1:]}. Reason: {reason}",
                    file=sys.stderr
                )

        kept = [r.skill for r in activated if r.skill not in to_remove]
        removed = list(to_remove)

        return kept, removed

    def resolve_dependencies(self, activated: List[str]) -> List[str]:
        """Add missing dependencies to activated list."""
        if not self._dependencies_cache:
            self._dependencies_cache = self.load_registry("dependencies")

        dependencies = self._dependencies_cache.get("dependencies", {})
        result = set(activated)
        added = []

        for skill in activated:
            deps = dependencies.get(skill, [])
            for dep in deps:
                if dep not in result:
                    result.add(dep)
                    added.append(dep)

        if added:
            print(f"Added dependencies: {added}", file=sys.stderr)

        return list(result)

    def determine_execution_order(self, activated: List[str]) -> List[str]:
        """Determine execution order using topological sort."""
        if not self._dependencies_cache:
            self._dependencies_cache = self.load_registry("dependencies")

        dependencies = self._dependencies_cache.get("dependencies", {})

        # Build adjacency list
        graph: Dict[str, List[str]] = {skill: [] for skill in activated}
        in_degree: Dict[str, int] = {skill: 0 for skill in activated}

        for skill in activated:
            deps = dependencies.get(skill, [])
            for dep in deps:
                if dep in activated:
                    graph[dep].append(skill)
                    in_degree[skill] += 1

        # Topological sort (Kahn's algorithm)
        queue = [skill for skill in activated if in_degree[skill] == 0]
        result = []

        while queue:
            # Sort for deterministic order
            queue.sort()
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for circular dependencies
        if len(result) != len(activated):
            print("Warning: Circular dependency detected, using input order", file=sys.stderr)
            return sorted(activated)

        return result

    def apply_policies(self, rankings: List[SkillRanking]) -> ActivationPlan:
        """Main entry point: apply all policies."""
        threshold = self.config.CONFIDENCE_THRESHOLD

        # Apply threshold
        activated_rankings, rejected_rankings = self.apply_threshold(rankings, threshold)

        # Resolve conflicts
        activated_names, conflict_removed = self.resolve_conflicts(activated_rankings)

        # Update rejected list with conflict removals
        rejected_names = [r.skill for r in rejected_rankings] + conflict_removed

        # Resolve dependencies
        activated_with_deps = self.resolve_dependencies(activated_names)

        # Determine execution order
        execution_order = self.determine_execution_order(activated_with_deps)

        return ActivationPlan(
            activated=activated_with_deps,
            rejected=rejected_names,
            execution_order=execution_order
        )
