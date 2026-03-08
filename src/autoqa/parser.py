"""
AutoQA Parser for GitHub Action
Parses PR descriptions for AutoQA metadata blocks and test steps
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class AutoQAParser:
    """Parser for AutoQA metadata and test steps in PR descriptions"""

    def __init__(self):
        # New format: Fenced autoqa metadata block
        # ```autoqa
        # flow_name: user_login_success
        # tier: A
        # area: auth
        # ```
        # 1. step1
        # 2. step2
        self.autoqa_block_pattern = re.compile(
            r"```\s*autoqa\s*\n(.*?)\n```\s*\n(.*?)(?=\n```|\n##|\Z)",
            re.DOTALL | re.IGNORECASE,
        )
        self.metadata_field_pattern = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)
        self.steps_pattern = re.compile(
            r"(?:Steps?:?\s*\n)?((?:\d+\..*?\n?)+)", re.DOTALL | re.IGNORECASE
        )

        # Valid tier values from policy
        self.valid_tiers = ["A", "B", "C"]

        # Default values
        self.default_tier = "B"
        self.default_area = "general"

    def has_autoqa_tag(self, pr_body: str) -> bool:
        """Check if PR description contains AutoQA fenced metadata block"""
        if not pr_body:
            return False

        # Check for fenced autoqa metadata block
        return bool(self.autoqa_block_pattern.search(pr_body))

    def extract_autoqa_block(self, pr_body: str) -> Optional[Dict[str, Any]]:
        """
        Extract complete AutoQA block with metadata and steps

        Args:
            pr_body: PR description text

        Returns:
            Dict with 'metadata' and 'steps' keys, or None if not found
        """
        if not pr_body:
            return None

        match = self.autoqa_block_pattern.search(pr_body)
        if not match:
            return None

        metadata_block = match.group(1)
        steps_block = match.group(2)

        # Parse metadata
        metadata = self.parse_autoqa_metadata(metadata_block)

        # Parse steps
        steps = self._extract_steps_from_content(steps_block)

        if not steps:
            return None

        return {"metadata": metadata, "steps": steps}

    def parse_autoqa_metadata(self, metadata_block: str) -> Dict[str, Any]:
        """
        Parse metadata from AutoQA fenced block

        Args:
            metadata_block: Text content of metadata section

        Returns:
            Dict with flow_name, tier, area (and any additional fields)
        """
        metadata = {}

        for match in self.metadata_field_pattern.finditer(metadata_block):
            field_name = match.group(1).strip().lower()
            field_value = match.group(2).strip()
            metadata[field_name] = field_value

        # Apply defaults
        if "tier" not in metadata:
            metadata["tier"] = self.default_tier
        if "area" not in metadata:
            metadata["area"] = self.default_area

        # Normalize tier to uppercase
        if "tier" in metadata:
            metadata["tier"] = metadata["tier"].upper()

        # Normalize flow_name and area to handle spaces/special chars
        if "flow_name" in metadata:
            metadata["flow_name"] = self._normalize_identifier(metadata["flow_name"])
        if "area" in metadata:
            metadata["area"] = self._normalize_identifier(metadata["area"])

        return metadata

    def parse_test_steps(self, pr_body: str) -> List[str]:
        """
        Extract test steps from AutoQA block

        Args:
            pr_body: PR description text

        Returns:
            List of test step strings
        """
        autoqa_block = self.extract_autoqa_block(pr_body)
        if not autoqa_block:
            return []

        return autoqa_block.get("steps", [])

    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate AutoQA metadata against policy rules

        Args:
            metadata: Parsed metadata dict

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Required field: flow_name
        if "flow_name" not in metadata or not metadata["flow_name"]:
            errors.append("Missing required field: flow_name")
        elif len(metadata["flow_name"]) > 50:
            errors.append(f"flow_name too long (max 50 chars): {metadata['flow_name']}")

        # Required field: tier (with default)
        if "tier" not in metadata:
            errors.append("Missing required field: tier")
        elif metadata["tier"] not in self.valid_tiers:
            errors.append(
                f"Invalid tier value: {metadata['tier']}. Must be one of:"
                f" {', '.join(self.valid_tiers)}"
            )

        # Optional field: area (validate length if present)
        if "area" in metadata and metadata["area"]:
            if len(metadata["area"]) > 30:
                errors.append(f"area too long (max 30 chars): {metadata['area']}")

        return (len(errors) == 0, errors)

    def compute_etag(self, metadata: Dict[str, Any], steps: List[str]) -> str:
        """
        Compute ETag for idempotency checking

        ETag = SHA256(flow_name + tier + area + canonicalized_steps)

        Args:
            metadata: AutoQA metadata dict
            steps: List of test steps

        Returns:
            Full SHA256 hash as hex string
        """
        canonical_steps = self.canonicalize_steps(steps)

        payload = {
            "flow_name": metadata.get("flow_name", ""),
            "tier": metadata.get("tier", ""),
            "area": metadata.get("area", ""),
            "steps": canonical_steps,
        }

        hash_input = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def canonicalize_steps(self, steps: List[str]) -> List[str]:
        """
        Canonicalize steps for consistent ETag computation

        Normalizes whitespace and converts to lowercase for comparison

        Args:
            steps: List of test steps

        Returns:
            Canonicalized list of steps
        """
        return [" ".join(s.strip().lower().split()) for s in steps]

    def _normalize_identifier(self, value: str) -> str:
        """
        Normalize identifier to snake_case, handling spaces and special chars

        Args:
            value: Raw identifier value

        Returns:
            Normalized snake_case identifier
        """
        # Replace spaces and special chars with underscores
        normalized = re.sub(r"[^\w]+", "_", value.strip())
        # Remove leading/trailing underscores
        normalized = normalized.strip("_")
        # Convert to lowercase
        normalized = normalized.lower()
        # Collapse multiple underscores
        normalized = re.sub(r"_+", "_", normalized)

        return normalized

    def _extract_steps_from_content(self, autoqa_content: str) -> List[str]:
        """Extract numbered steps from AutoQA content"""
        autoqa_content = autoqa_content.strip()

        # Split content and stop at next markdown section or code fence
        lines = autoqa_content.split("\n")
        step_lines = []

        for line in lines:
            stripped = line.strip()
            # Stop if we hit a markdown heading
            if re.match(r"^\s*#{1,6}\s", stripped):
                break
            # Stop if we hit a code fence
            if stripped.startswith("```"):
                break
            # Stop if we hit a markdown list that's not numbered
            if re.match(r"^\s*[-*]\s", stripped):
                break
            step_lines.append(line)

        # Extract numbered steps from the relevant lines
        steps = []
        for line in step_lines:
            if re.match(r"^\d+\.", line.strip()):
                # Remove number prefix and clean up
                step = re.sub(r"^\d+\.\s*", "", line.strip()).strip()
                if step:
                    steps.append(step)

        return steps

    def steps_to_scenario(
        self, steps: List[str], metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Convert parsed steps and metadata to test scenario format

        Args:
            steps: List of test steps
            metadata: AutoQA metadata dict (optional for backward compatibility)

        Returns:
            Scenario dict with metadata included
        """
        if not steps:
            return {}

        scenario_name = (
            metadata.get("flow_name", "AutoQA Generated Test")
            if metadata
            else "AutoQA Generated Test"
        )

        # Create scenario with metadata
        scenario = {
            "name": scenario_name,
            "description": f"AutoQA generated test with {len(steps)} steps",
            "steps": steps,
            "expected_result": f"All {len(steps)} steps should execute successfully",
        }

        # Include metadata if provided
        if metadata:
            scenario["metadata"] = metadata
            scenario["tier"] = metadata.get("tier", self.default_tier)
            scenario["area"] = metadata.get("area", self.default_area)
            scenario["flow_name"] = metadata.get("flow_name", "unknown")

        return scenario

    def format_iso8601_timestamp(self) -> str:
        """
        Generate ISO8601 timestamp with timezone

        Returns:
            ISO8601 formatted timestamp string
        """
        return datetime.now(timezone.utc).astimezone().isoformat()

    def get_metadata_summary(self, metadata: Dict[str, Any]) -> str:
        """
        Generate human-readable metadata summary

        Args:
            metadata: AutoQA metadata dict

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append(f"Flow: {metadata.get('flow_name', 'unknown')}")
        lines.append(f"Tier: {metadata.get('tier', 'unknown')}")

        area = metadata.get("area", "")
        if area and area != self.default_area:
            lines.append(f"Area: {area}")

        return " | ".join(lines)
