"""
AutoQA Parser for GitHub Action
Parses PR descriptions for AutoQA tags and test steps
"""

import re
from typing import List, Dict, Any, Optional


class AutoQAParser:
    """Parser for AutoQA tags and test steps in PR descriptions"""
    
    def __init__(self):
        # Support both old and new AutoQA formats
        # Old format: AutoQA\n1. step1\n2. step2
        # New format: AutoQA:scenario-name\n1. step1\n2. step2
        self.autoqa_pattern_new = re.compile(r'AutoQA:([^\n]+)\n(.*?)(?=\n\s*###|\n\s*##|\n\s*#|\nAutoQA:|\Z)', re.DOTALL | re.IGNORECASE)
        self.autoqa_pattern_old = re.compile(r'AutoQA\s*\n(.*?)(?=\n\s*###|\n\s*##|\n\s*#|\nAutoQA|\Z)', re.DOTALL | re.IGNORECASE)
        self.steps_pattern = re.compile(r'(?:Steps?:?\s*\n)?((?:\d+\..*?\n?)+)', re.DOTALL | re.IGNORECASE)
    
    def has_autoqa_tag(self, pr_body: str) -> bool:
        """Check if PR description contains AutoQA tag"""
        if not pr_body:
            return False
        
        # Check for both old and new AutoQA formats
        has_new_format = bool(re.search(r'AutoQA:[^\n]+', pr_body, re.IGNORECASE))
        has_old_format = bool(re.search(r'AutoQA\s*\n', pr_body, re.IGNORECASE))
        
        return has_new_format or has_old_format
    
    def parse_test_steps(self, pr_body: str) -> List[str]:
        """Extract test steps from AutoQA section"""
        all_steps = []
        
        # Try new format first (AutoQA:scenario-name)
        autoqa_matches_new = self.autoqa_pattern_new.findall(pr_body)
        if autoqa_matches_new:
            for scenario_name, autoqa_content in autoqa_matches_new:
                steps = self._extract_steps_from_content(autoqa_content)
                all_steps.extend(steps)
        
        # Try old format (AutoQA)
        autoqa_matches_old = self.autoqa_pattern_old.findall(pr_body)
        if autoqa_matches_old:
            for autoqa_content in autoqa_matches_old:
                steps = self._extract_steps_from_content(autoqa_content)
                all_steps.extend(steps)
        
        return all_steps
    
    def _extract_steps_from_content(self, autoqa_content: str) -> List[str]:
        """Extract numbered steps from AutoQA content"""
        autoqa_content = autoqa_content.strip()
        
        # Split content and stop at next markdown section
        lines = autoqa_content.split('\n')
        step_lines = []
        
        for line in lines:
            line = line.strip()
            # Stop if we hit a markdown heading
            if re.match(r'^\s*#{1,6}\s', line):
                break
            # Stop if we hit a markdown list that's not numbered
            if re.match(r'^\s*[-*]\s', line):
                break
            step_lines.append(line)
        
        # Extract numbered steps from the relevant lines
        steps = []
        for line in step_lines:
            if re.match(r'^\d+\.', line):
                # Remove number prefix and clean up
                step = re.sub(r'^\d+\.\s*', '', line).strip()
                if step:
                    steps.append(step)
        
        return steps
    
    def steps_to_scenario(self, steps: List[str]) -> Dict[str, Any]:
        """Convert parsed steps to test scenario format"""
        if not steps:
            return {}
        
        # Generate scenario name from first step or generic name
        scenario_name = self._generate_scenario_name(steps)
        
        # Create scenario in test_data.yaml format
        scenario = {
            'name': scenario_name,
            'description': f"AutoQA generated test with {len(steps)} steps",
            'steps': steps,
            'expected_result': f"All {len(steps)} steps should execute successfully"
        }
        
        return scenario
    
    def _generate_scenario_name(self, steps: List[str]) -> str:
        """Generate a descriptive scenario name from steps"""
        if not steps:
            return "AutoQA Generated Test"
        
        first_step = steps[0].lower()
        
        # Extract key actions/pages from first step
        if 'login' in first_step:
            return "AutoQA Login Test"
        elif 'signup' in first_step or 'register' in first_step:
            return "AutoQA Signup Test"
        elif 'dashboard' in first_step:
            return "AutoQA Dashboard Test"
        elif 'navigate' in first_step:
            return "AutoQA Navigation Test"
        else:
            return "AutoQA Generated Test"
    
    def extract_metadata(self, pr_body: str, steps: List[str]) -> Dict[str, Any]:
        """Extract metadata for the generated test"""
        return {
            'source': 'AutoQA PR Description',
            'step_count': len(steps),
            'scenario_type': self._detect_scenario_type(steps),
            'complexity': self._assess_complexity(steps)
        }
    
    def _detect_scenario_type(self, steps: List[str]) -> str:
        """Detect the type of test scenario from steps"""
        steps_text = ' '.join(steps).lower()
        
        if 'login' in steps_text:
            return 'login'
        elif 'signup' in steps_text or 'register' in steps_text:
            return 'signup'
        elif 'dashboard' in steps_text:
            return 'dashboard'
        elif 'form' in steps_text:
            return 'form'
        else:
            return 'general'
    
    def _assess_complexity(self, steps: List[str]) -> str:
        """Assess complexity based on number of steps and content"""
        step_count = len(steps)
        
        if step_count <= 3:
            return 'simple'
        elif step_count <= 6:
            return 'medium'
        else:
            return 'complex'