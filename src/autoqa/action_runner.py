#!/usr/bin/env python3
"""
GitHub Action Runner for AutoQA
Executes in target repository context while using AISquare-Studio-QA components
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add action components to path - must be before other src imports
action_path = Path(os.getenv("ACTION_PATH", "."))
sys.path.insert(0, str(action_path))

# noqa comments tell flake8 these imports are intentionally after path manipulation
from src.autoqa.action_reporter import ActionReporter  # noqa: E402
from src.autoqa.criteria_generator import TestCriteriaGenerator  # noqa: E402
from src.autoqa.cross_repo_manager import CrossRepoManager  # noqa: E402
from src.autoqa.gap_analysis_db import GapAnalysisDB  # noqa: E402
from src.autoqa.gap_driven_generator import GapDrivenGenerator  # noqa: E402
from src.autoqa.parser import AutoQAParser  # noqa: E402
from src.crews.qa_crew import QACrew  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

logger = get_logger(__name__)


class ActionRunner:
    """Main runner for GitHub Action execution in target repository"""

    def __init__(self):
        self.target_repo = os.getenv("TARGET_REPOSITORY")
        self.target_workspace = Path(os.getenv("GITHUB_WORKSPACE"))
        self.action_path = Path(os.getenv("ACTION_PATH"))

        # Initialize components
        self.parser = AutoQAParser()

        # Get model configuration from environment (defaults to gpt-4.1)
        model_name = os.getenv("OPENAI_MODEL_NAME", "openai/gpt-4.1")
        self.qa_crew = QACrew(model_name=model_name)

        self.cross_repo = CrossRepoManager(
            target_workspace=self.target_workspace, action_path=self.action_path
        )
        self.reporter = ActionReporter()

        # Environment configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {
            "github_token": os.getenv("GITHUB_TOKEN"),
            "openai_api_key": os.getenv(
                "OPENAI_API_KEY"
            ),  # Accessed from repository secrets automatically
            "target_repo_path": os.getenv("TARGET_REPO_PATH", "."),
            "staging_url": os.getenv("STAGING_URL"),
            "staging_email": os.getenv("STAGING_EMAIL", "test@example.com"),
            "staging_password": os.getenv("STAGING_PASSWORD", "password123"),
            "git_user_name": os.getenv("GIT_USER_NAME", "AutoQA Bot"),
            "git_user_email": os.getenv("GIT_USER_EMAIL", "rabia.tahirr@opengrowth.com"),
            "pr_body": os.getenv("PR_BODY", ""),
            "test_directory": os.getenv("TEST_DIRECTORY", "tests/generated"),
            "execution_mode": os.getenv("EXECUTION_MODE", "generate").lower(),
            # Active execution settings
            "use_active_execution": os.getenv("USE_ACTIVE_EXECUTION", "true").lower() == "true",
            "max_retries": int(os.getenv("MAX_RETRIES", "2")),
            "headless": os.getenv("HEADLESS_MODE", "true").lower() == "true",
            # Auto-criteria settings (Proposal 16)
            "auto_criteria_fallback": (
                os.getenv("AUTO_CRITERIA_FALLBACK", "false").lower() == "true"
            ),
            "auto_criteria_mode": os.getenv("AUTO_CRITERIA_MODE", "suggest"),
            "auto_criteria_threshold": int(os.getenv("AUTO_CRITERIA_THRESHOLD", "85")),
            "auto_criteria_approval": os.getenv("AUTO_CRITERIA_APPROVAL", "reaction"),
            "pr_number": os.getenv("PR_NUMBER", ""),
        }

        return config

    def execute(self) -> Dict[str, Any]:
        """Main execution flow for AutoQA action"""
        try:
            logger.info(f"AutoQA Action starting for repository: {self.target_repo}")
            logger.info(f"Execution Mode: {self.config['execution_mode']}")

            # Validate required configuration
            validation_error = self._validate_config()
            if validation_error:
                return validation_error

            # Handle 'suite' mode (Regression only)
            if self.config["execution_mode"] == "suite":
                return self._execute_suite_mode()

            # Handle 'auto-criteria' mode (Proposal 16)
            if self.config["execution_mode"] == "auto-criteria":
                return self._execute_auto_criteria_mode()

            # Handle 'gap-driven' mode (memory-based coverage gap testing)
            if self.config["execution_mode"] == "gap-driven":
                return self._execute_gap_driven_mode()

            # Handle 'gap-analysis' mode (database-backed workflow gap report)
            if self.config["execution_mode"] == "gap-analysis":
                return self._execute_gap_analysis_mode()

            # Parse and validate PR body
            parse_result = self._parse_and_validate_pr()

            # If no autoqa block found and auto-criteria is not explicitly
            # disabled, try the auto-criteria workflow as a fallback
            if not parse_result.get("autoqa_block_found", True):
                if self.config.get("auto_criteria_fallback", False):
                    logger.info("No AutoQA block found — falling back to auto-criteria generation")
                    return self._execute_auto_criteria_mode()

            if "error" in parse_result:
                return self._set_outputs(parse_result)

            metadata = parse_result["metadata"]
            steps = parse_result["steps"]
            etag = parse_result["etag"]

            # Generate test using CrewAI
            existing_code = self._load_existing_code(metadata)
            generation_result = self._generate_test_code(steps, metadata, existing_code)

            if not generation_result["success"]:
                return self._handle_generation_failure(generation_result)

            # Execute, commit, report, and return outputs
            return self._finalize_generation(
                generation_result,
                metadata,
                etag,
            )

        except Exception as e:
            logger.error(f"AutoQA Action failed: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return self._set_outputs({"test_generated": "false", "error": str(e)})

    def _validate_config(self):
        """Validate required configuration. Returns error output or None."""
        if not self.config["openai_api_key"]:
            return self._set_outputs(
                {
                    "test_generated": "false",
                    "error": "OPENAI_API_KEY not found in repository secrets",
                }
            )

        if not self.config["staging_url"]:
            logger.warning("STAGING_URL not provided, using default for testing")
            self.config["staging_url"] = "https://stg-home.aisquare.studio"

        return None

    def _execute_suite_mode(self) -> Dict[str, Any]:
        """Handle suite-only execution mode."""
        logger.info("Running full test suite (Regression Mode)...")
        suite_results = self._run_test_suite()

        logger.info("Generating Suite Result comment...")
        self.reporter.create_suite_comment(suite_results)

        suite_failed = not suite_results.get("success", False)
        outputs = {
            "test_generated": "false",
            "suite_results": json.dumps(suite_results),
            "tests_failed": "true" if suite_failed else "false",
        }
        if suite_failed:
            outputs["error"] = "Test suite failed"

        return self._set_outputs(outputs)

    def _execute_auto_criteria_mode(self) -> Dict[str, Any]:
        """Generate test criteria from PR diff and post for review (Proposal 16).

        Workflow:
          1. Fetch PR diff via GitHub API
          2. Feed diff to LLM to generate test criteria
          3. Post suggested criteria as a PR comment
          4. Check if developer has approved (reaction / comment / label)
          5. If approved, proceed with test generation using the criteria
          6. If auto-proceed is enabled and confidence is high, skip approval
        """
        pr_number = self._get_pr_number()
        if not pr_number:
            return self._set_outputs(
                {
                    "test_generated": "false",
                    "error": "PR number not available for auto-criteria mode",
                }
            )

        logger.info(f"Running auto-criteria generation for PR #{pr_number}...")

        # Build criteria generator config from action config
        criteria_config = {
            "mode": self.config.get("auto_criteria_mode", "suggest"),
            "auto_proceed_threshold": self.config.get("auto_criteria_threshold", 85),
            "approval_mechanism": self.config.get("auto_criteria_approval", "reaction"),
        }

        generator = TestCriteriaGenerator(
            github_token=self.config["github_token"],
            target_repo=self.target_repo,
            config=criteria_config,
        )

        # Fetch PR title for context
        pr_info = generator.diff_analyzer.get_pr_info(pr_number)
        pr_title = pr_info.get("title", "") if pr_info else ""

        # Generate criteria from diff
        result = generator.generate_criteria(
            pr_number=pr_number,
            pr_title=pr_title,
        )

        if not result.get("success"):
            error = result.get("error", "Auto-criteria generation failed")
            logger.error(f"Auto-criteria generation failed: {error}")
            return self._set_outputs({"test_generated": "false", "error": error})

        criteria = result.get("criteria", [])

        if not criteria:
            logger.info("No user-facing flows detected — posting notice")
            if result.get("comment_body"):
                generator.post_criteria_comment(pr_number, result["comment_body"])
            return self._set_outputs(
                {
                    "test_generated": "false",
                    "message": "No user-facing flows detected in PR",
                }
            )

        # Post suggested criteria as PR comment
        comment_body = result.get("comment_body", "")
        if comment_body:
            generator.post_criteria_comment(pr_number, comment_body)
            logger.info("Posted suggested criteria comment on PR")

        # Check if we should auto-proceed
        if generator.should_auto_proceed(criteria):
            logger.info("All criteria meet auto-proceed threshold — proceeding without approval")
            return self._run_criteria_flows(criteria)

        # Check for existing approval
        approval = generator.check_approval(pr_number)
        if approval.get("approved"):
            logger.info(
                f"Developer approval detected via {approval['mechanism']}"
                " — proceeding with test generation"
            )
            return self._run_criteria_flows(criteria)

        # Not yet approved — exit and wait for next trigger
        logger.info("Criteria posted — waiting for developer approval before generating tests")
        return self._set_outputs(
            {
                "test_generated": "false",
                "message": "Auto-criteria posted for review. Approve to trigger test generation.",
                "criteria": json.dumps(criteria),
            }
        )

    def _execute_gap_driven_mode(self) -> Dict[str, Any]:
        """Generate tests for uncovered modules identified by the memory tracker.

        Workflow:
          1. Load memory and identify coverage gaps
          2. Read source code of uncovered modules
          3. Use LLM to generate test criteria for each gap
          4. Post suggested criteria as a PR comment
          5. If auto-proceed is enabled and confidence is high, generate tests
          6. Otherwise wait for developer approval
        """
        logger.info("Running gap-driven test generation from memory coverage gaps...")

        gap_config = {
            "mode": self.config.get("auto_criteria_mode", "suggest"),
            "auto_proceed_threshold": self.config.get("auto_criteria_threshold", 85),
            "approval_mechanism": self.config.get("auto_criteria_approval", "reaction"),
        }

        generator = GapDrivenGenerator(
            project_root=str(self.target_workspace),
            github_token=self.config["github_token"],
            target_repo=self.target_repo,
            config=gap_config,
        )

        # Generate criteria from coverage gaps
        result = generator.generate_criteria_for_gaps()

        if not result.get("success"):
            error = result.get("error", "Gap-driven generation failed")
            logger.error(f"Gap-driven generation failed: {error}")
            return self._set_outputs({"test_generated": "false", "error": error})

        criteria = result.get("criteria", [])

        if not criteria:
            logger.info("No testable flows found in uncovered modules")
            pr_number = self._get_pr_number()
            if pr_number and result.get("comment_body"):
                generator.post_criteria_comment(pr_number, result["comment_body"])
            return self._set_outputs(
                {
                    "test_generated": "false",
                    "message": result.get("message", "No testable flows in uncovered modules"),
                    "gaps_found": str(result.get("gaps_found", 0)),
                }
            )

        # Post criteria comment on the PR
        pr_number = self._get_pr_number()
        comment_body = result.get("comment_body", "")
        if pr_number and comment_body:
            generator.post_criteria_comment(pr_number, comment_body)
            logger.info("Posted gap-driven criteria comment on PR")

        # Check if we should auto-proceed
        if generator.should_auto_proceed(criteria):
            logger.info(
                "All gap-driven criteria meet auto-proceed threshold — proceeding without approval"
            )
            return self._run_criteria_flows(criteria)

        # If no PR context, just return the criteria
        if not pr_number:
            logger.info("No PR context — returning criteria for manual review")
            return self._set_outputs(
                {
                    "test_generated": "false",
                    "message": "Gap-driven criteria generated. No PR to post to.",
                    "criteria": json.dumps(criteria),
                    "gaps_found": str(result.get("gaps_found", 0)),
                }
            )

        # Not yet approved — exit and wait for next trigger
        logger.info("Gap-driven criteria posted — waiting for developer approval")
        return self._set_outputs(
            {
                "test_generated": "false",
                "message": (
                    "Gap-driven criteria posted for review. Approve to trigger test generation."
                ),
                "criteria": json.dumps(criteria),
                "gaps_found": str(result.get("gaps_found", 0)),
            }
        )

    def _execute_gap_analysis_mode(self) -> Dict[str, Any]:
        """Execute gap analysis and persist results to a SQLite database.

        Similar to suite mode, this scans the repository for existing and
        missing test workflows and writes the findings into a local SQLite
        database.  The database is created automatically if it does not
        already exist, making this safe to run on repositories that have
        AutoQA tests but have never used the gap-analysis feature.

        Returns:
            Action outputs with ``gap_analysis_results`` JSON string.
        """
        logger.info("Running gap analysis (database-backed workflow report)...")

        gap_db = GapAnalysisDB(
            project_root=str(self.target_workspace),
            test_dir=self.config.get("test_directory", "tests"),
            source_dirs=["src"],
        )

        results = gap_db.run_analysis()

        logger.info(
            "Gap analysis complete — "
            f"{results['present_count']} present, "
            f"{results['missing_count']} missing, "
            f"{results['coverage_pct']}% coverage"
        )

        return self._set_outputs(
            {
                "test_generated": "false",
                "gap_analysis_results": json.dumps(results),
                "error": None,
            }
        )

    def _get_pr_number(self) -> Optional[str]:
        """Resolve the current PR number from config or environment."""
        pr_number = self.config.get("pr_number") or os.getenv("PR_NUMBER")
        if pr_number:
            return str(pr_number)

        # Try to extract from GITHUB_REF
        github_ref = os.getenv("GITHUB_REF", "")
        if "/pull/" in github_ref:
            return github_ref.split("/pull/")[1].split("/")[0]

        return None

    def _run_criteria_flows(self, criteria: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute test generation for each approved criteria flow.

        Builds a synthetic ``autoqa`` block for each criterion and feeds
        it through the standard generation pipeline.
        """
        all_results = []

        for c in criteria:
            flow_name = c.get("flow_name", "unknown")
            logger.info(f"Generating test for flow: {flow_name}")

            metadata = {
                "flow_name": flow_name,
                "tier": c.get("tier", "C"),
                "area": c.get("area", "general"),
            }
            steps = c.get("steps", [])

            # Validate metadata
            is_valid, errors = self.parser.validate_metadata(metadata)
            if not is_valid:
                logger.warning(f"Skipping flow {flow_name}: " + ", ".join(errors))
                all_results.append({"flow_name": flow_name, "success": False, "error": errors})
                continue

            # Compute ETag
            etag = self.parser.compute_etag(metadata, steps)
            metadata["etag"] = etag
            metadata["steps"] = steps

            # Generate test code
            existing_code = self._load_existing_code(metadata)
            generation_result = self._generate_test_code(steps, metadata, existing_code)

            if not generation_result.get("success"):
                all_results.append(
                    {
                        "flow_name": flow_name,
                        "success": False,
                        "error": generation_result.get("error"),
                    }
                )
                continue

            # Finalise: execute, commit, report
            outputs = self._finalize_generation(generation_result, metadata, etag)
            all_results.append(
                {
                    "flow_name": flow_name,
                    "success": outputs.get("test_generated") == "true",
                    "outputs": outputs,
                }
            )

        # Summarise
        success_count = sum(1 for r in all_results if r.get("success"))
        total = len(all_results)
        overall_success = success_count > 0

        return self._set_outputs(
            {
                "test_generated": "true" if overall_success else "false",
                "auto_criteria_results": json.dumps(all_results),
                "message": f"Auto-criteria: {success_count}/{total} flows generated successfully",
            }
        )

    def _parse_and_validate_pr(self) -> Dict[str, Any]:
        """Parse and validate the PR body. Returns metadata/steps or error dict."""
        if not self.parser.has_autoqa_tag(self.config["pr_body"]):
            logger.info("No AutoQA fenced metadata block found in PR description")
            return {
                "test_generated": "false",
                "autoqa_block_found": False,
                "message": "No AutoQA metadata block found",
            }

        autoqa_block = self.parser.extract_autoqa_block(self.config["pr_body"])
        if not autoqa_block:
            logger.error("Failed to extract AutoQA block from PR body")
            return {"test_generated": "false", "error": "Failed to parse AutoQA block"}

        metadata = autoqa_block["metadata"]
        steps = autoqa_block["steps"]

        logger.info(f"Parsed AutoQA block: {self.parser.get_metadata_summary(metadata)}")
        logger.info(f"Steps: {len(steps)}")

        is_valid, validation_errors = self.parser.validate_metadata(metadata)
        if not is_valid:
            error_message = "Metadata validation failed:\n" + "\n".join(
                f"  - {err}" for err in validation_errors
            )
            logger.error(error_message)
            return {"test_generated": "false", "error": error_message}

        logger.info("✓ Metadata validation passed")

        etag = self.parser.compute_etag(metadata, steps)
        metadata["etag"] = etag
        metadata["steps"] = steps
        logger.info(f"Computed ETag: {etag}")

        return {"metadata": metadata, "steps": steps, "etag": etag}

    def _load_existing_code(self, metadata: Dict[str, Any]):
        """Load existing test code for context if available."""
        logger.info("Generating test code with CrewAI...")

        existing_test_path = self.cross_repo.find_test_for_flow(metadata)
        existing_code = None
        if existing_test_path:
            logger.info(f"Found existing test: {existing_test_path}")
            try:
                existing_code = existing_test_path.read_text()
                logger.info("Loaded existing test code for context")
            except Exception as e:
                logger.warning(f"Failed to read existing test: {e}")
        return existing_code

    def _get_execution_result(self, generation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution result, normalizing active vs legacy mode output."""
        if generation_result.get("metadata", {}).get("execution_mode") == "active_iterative":
            logger.info("Using execution results from active iterative execution...")
            raw = generation_result.get("execution_result", {})

            error = None
            if not raw.get("success"):
                details = generation_result.get("execution_result", {}).get("step_details", [{}])
                error = details[-1].get("error") if details else None

            return {
                "success": raw.get("success", False),
                "execution_time": raw.get("total_execution_time", 0),
                "screenshot_path": raw.get("final_screenshot"),
                "completed_steps": raw.get("completed_steps", 0),
                "failed_steps": raw.get("failed_steps", 0),
                "retry_summary": raw.get("retry_summary", {}),
                "error": error,
            }
        else:
            logger.info("Executing generated test on staging (legacy mode)...")
            return self._execute_test(generation_result["code"])

    def _finalize_generation(
        self,
        generation_result: Dict[str, Any],
        metadata: Dict[str, Any],
        etag: str,
    ) -> Dict[str, Any]:
        """Commit test, run suite, post PR comment, and return outputs."""
        execution_result = self._get_execution_result(generation_result)

        # Step 7: Only commit test file if execution succeeded
        test_file_path = None
        if execution_result["success"]:
            logger.info("✅ Test execution passed - committing to repository...")
            test_file_path = self.cross_repo.commit_test_file(
                code=generation_result["code"],
                metadata=metadata,
            )
            logger.info(f"Test file committed: {test_file_path}")
        else:
            logger.warning("❌ Test execution failed - skipping commit")
            logger.warning(f"Error: {execution_result.get('error', 'Unknown error')}")
            test_file_path = self._generate_preview_path(metadata)

        # Step 8: Run existing tests only if new test passed and mode is 'all'
        suite_results = self._maybe_run_suite(execution_result)

        # Step 9: ALWAYS generate PR comment (success or failure)
        self._post_pr_comments(
            generation_result,
            execution_result,
            suite_results,
            test_file_path,
            metadata,
        )

        # Step 10: Set outputs (success or failure)
        return self._build_outputs(
            execution_result,
            test_file_path,
            suite_results,
            metadata,
            etag,
        )

    def _maybe_run_suite(self, execution_result: Dict[str, Any]) -> Dict:
        """Conditionally run the full test suite."""
        if execution_result["success"] and self.config["execution_mode"] == "all":
            logger.info("New test passed. Running full test suite...")
            return self._run_test_suite()
        elif self.config["execution_mode"] == "generate":
            logger.info("Skipping full test suite (Execution Mode: generate)")
        elif not execution_result["success"]:
            logger.info("New test failed. Skipping full test suite.")
        return {}

    def _post_pr_comments(
        self,
        generation_result: Dict[str, Any],
        execution_result: Dict[str, Any],
        suite_results: Dict[str, Any],
        test_file_path,
        metadata: Dict[str, Any],
    ) -> None:
        """Post generation and suite PR comments."""
        logger.info("Generating PR comment with results...")

        if self.config["execution_mode"] != "suite":
            self.reporter.create_pr_comment(
                generation_result=generation_result,
                execution_result=execution_result,
                suite_results=suite_results,
                test_file_path=(
                    str(test_file_path) if test_file_path else "Not committed (test failed)"
                ),
                metadata=metadata,
            )

        if suite_results:
            logger.info("Generating Suite Result comment...")
            self.reporter.create_suite_comment(suite_results)

    def _build_outputs(
        self,
        execution_result: Dict[str, Any],
        test_file_path,
        suite_results: Dict[str, Any],
        metadata: Dict[str, Any],
        etag: str,
    ) -> Dict[str, Any]:
        """Build and set final action outputs."""
        test_generated = "true" if execution_result["success"] else "false"
        outputs = {
            "test_generated": test_generated,
            "test_file_path": str(test_file_path) if test_file_path else "",
            "test_results": json.dumps(execution_result),
            "suite_results": json.dumps(suite_results),
            "generation_metadata": json.dumps(metadata),
            "screenshot_path": execution_result.get("screenshot_path", ""),
            "etag": etag,
            "flow_name": metadata.get("flow_name", ""),
            "tier": metadata.get("tier", ""),
            "area": metadata.get("area", ""),
        }

        if not execution_result["success"]:
            outputs["error"] = execution_result.get("error", "Test execution failed")
            outputs["tests_failed"] = "true"
        else:
            outputs["tests_failed"] = "false"

        return self._set_outputs(outputs)

    def _generate_test_code(
        self, steps: List[str], metadata: Dict[str, Any], existing_code: str = None
    ) -> Dict[str, Any]:
        """
        Generate test code using CrewAI components

        Args:
            steps: List of test steps
            metadata: AutoQA metadata with flow_name, tier, area, etag
            existing_code: Optional existing test code for context

        Returns:
            Generation result dict with code and metadata
        """
        try:
            # Convert steps to scenario format with metadata
            scenario = self.parser.steps_to_scenario(steps, metadata)

            # Check if active execution is enabled
            if self.config.get("use_active_execution", True):
                logger.info("Using ACTIVE ITERATIVE EXECUTION mode")

                # Create test configuration for active execution
                base_url = self.config.get(
                    "staging_url", "https://stg-home.aisquare.studio"
                ).rstrip("/")
                test_config = {
                    "base_url": base_url,
                    "login_url": f"{base_url}/login",
                    "email": self.config.get("staging_email", "test@example.com"),
                    "password": self.config.get("staging_password", "password123"),
                    "headless": self.config.get("headless", True),
                    "timeout": 30000,
                    "max_retries": self.config.get("max_retries", 2),
                }

                # Use active execution
                result = self.qa_crew.run_active_autoqa_scenario(
                    scenario=scenario, config=test_config, existing_code=existing_code
                )

                if not result.get("success"):
                    return {
                        "success": False,
                        "error": result.get("error", "Active execution failed"),
                    }

                # Enhance result with metadata
                enhanced_metadata = {
                    "flow_name": metadata.get("flow_name", ""),
                    "tier": metadata.get("tier", ""),
                    "area": metadata.get("area", ""),
                    "etag": metadata.get("etag", ""),
                    "steps": steps,
                    "scenario": scenario,
                    "generated_at": self.parser.format_iso8601_timestamp(),
                    "execution_mode": "active_iterative",
                    "execution_summary": result.get("execution_summary", {}),
                    "retry_summary": result.get("retry_summary", {}),
                }

                return {
                    "success": True,
                    "code": result.get("generated_code", ""),
                    "metadata": enhanced_metadata,
                    "execution_result": result,  # Include full execution result
                }

            else:
                # Use existing single-pass generation (legacy mode)
                logger.info("Using LEGACY single-pass generation mode")
                result = self.qa_crew.run_autoqa_scenario(scenario)

                # Enhance result with full metadata
                enhanced_metadata = {
                    "flow_name": metadata.get("flow_name", ""),
                    "tier": metadata.get("tier", ""),
                    "area": metadata.get("area", ""),
                    "etag": metadata.get("etag", ""),
                    "steps": steps,
                    "scenario": scenario,
                    "generated_at": self.parser.format_iso8601_timestamp(),
                    "validation_result": result.get("validation_result", ""),
                    "execution_mode": "legacy",
                }

                return {
                    "success": result.get("success", False),
                    "code": result.get("generated_code", ""),
                    "metadata": enhanced_metadata,
                }

        except Exception as e:
            logger.error(f"Test code generation failed: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            return {"success": False, "error": f"CrewAI generation failed: {str(e)}"}

    def _execute_test(self, test_code: str) -> Dict[str, Any]:
        """Execute generated test on staging environment"""
        try:
            # Validate required config
            if not self.config.get("staging_url"):
                return {"success": False, "error": "STAGING_URL is required but not provided"}

            # Create test configuration for staging
            base_url = self.config["staging_url"].rstrip("/")
            test_config = {
                "base_url": base_url,
                "login_url": f"{base_url}/login",
                "email": self.config.get("staging_email", "test@example.com"),
                "password": self.config.get("staging_password", "password123"),
                "headless": True,
                "timeout": 30000,
            }

            # Execute using existing executor
            result = self.qa_crew.execute_generated_test(test_code, test_config)

            return result

        except Exception as e:
            return {"success": False, "error": f"Test execution failed: {str(e)}"}

    def _run_test_suite(self) -> Dict[str, Any]:
        """Run full test suite in target repository"""
        try:
            # Discover tests in target repository
            test_files = self.cross_repo.discover_tests()

            if not test_files:
                return {"message": "No existing tests found"}

            # Execute test suite using pytest
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    "-n",
                    "auto",  # Run in parallel using all available cores
                    str(self.target_workspace / self.config["test_directory"]),
                    "-v",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file=test_results.json",
                ],
                cwd=self.target_workspace,
                capture_output=True,
                text=True,
            )

            # Parse results
            results_file = self.target_workspace / "test_results.json"
            if results_file.exists():
                with open(results_file, "r") as f:
                    suite_data = json.load(f)

                # Extract detailed results
                detailed_results = []
                for test in suite_data.get("tests", []):
                    # Get test name (nodeid usually looks like tests/autoqa/A/test_login.py::TestLogin::test_login)
                    nodeid = test.get("nodeid", "unknown")
                    name = nodeid.split("::")[-1] if "::" in nodeid else nodeid

                    # Get error message if failed
                    error_message = ""
                    if test.get("outcome") == "failed":
                        # Try to get short error message
                        if "call" in test and "crash" in test["call"]:
                            error_message = test["call"]["crash"].get("message", "")
                        # Fallback to longrepr if available
                        if not error_message and "call" in test and "longrepr" in test["call"]:
                            error_message = str(test["call"]["longrepr"])

                    detailed_results.append(
                        {
                            "name": name,
                            "nodeid": nodeid,
                            "outcome": test.get("outcome", "unknown"),
                            "duration": test.get("call", {}).get("duration", 0),
                            "error": error_message,
                        }
                    )

                summary = suite_data.get("summary", {})
                passed = summary.get("passed", 0)
                failed = summary.get("failed", 0)
                skipped = summary.get("skipped", 0)
                total = passed + failed + skipped

                return {
                    "success": result.returncode == 0,
                    "total_tests": total,
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "execution_time": suite_data.get("duration", 0),
                    "detailed_results": detailed_results,
                }

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except Exception as e:
            return {"success": False, "error": f"Test suite execution failed: {str(e)}"}

    def _generate_preview_path(self, metadata: Dict[str, Any]) -> str:
        """
        Generate preview path for failed tests (not committed)

        Args:
            metadata: AutoQA metadata

        Returns:
            Preview path string showing where test would be created
        """
        tier = metadata.get("tier", "B")
        area = metadata.get("area", "general")
        flow_name = metadata.get("flow_name", "unknown")

        if area and area != "general":
            return f"tests/autoqa/{tier}/{area}/test_{flow_name}.py"
        else:
            return f"tests/autoqa/{tier}/general/test_{flow_name}.py"

    def _handle_generation_failure(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle test generation failure"""
        logger.error(f"Test generation failed: {result.get('error', 'Unknown error')}")
        return self._set_outputs(
            {"test_generated": "false", "error": result.get("error", "Test generation failed")}
        )

    def _set_outputs(self, outputs: Dict[str, str]) -> Dict[str, Any]:
        """Set GitHub Action outputs"""
        # Set outputs for GitHub Actions
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a") as f:
                for key, value in outputs.items():
                    # Escape multiline values
                    if "\n" in str(value):
                        f.write(f"{key}<<EOF\n{value}\nEOF\n")
                    else:
                        f.write(f"{key}={value}\n")

        # Also log for visibility
        logger.info("Action Outputs:")
        for key, value in outputs.items():
            logger.info(f"  {key}: {value}")

        return outputs


def main():
    """Main entry point for GitHub Action"""
    runner = ActionRunner()
    result = runner.execute()

    # Exit with appropriate code
    # Test failures exit 0 so subsequent steps (artifact uploads, commits) still run.
    # The action.yml has a final step that re-checks tests_failed and fails the action.
    if result.get("tests_failed") == "true":
        logger.warning("Tests failed — deferring failure to final action step")
        sys.exit(0)
    elif result.get("test_generated") == "false" and result.get("error"):
        # Non-test errors (config, generation, unexpected) fail immediately
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
