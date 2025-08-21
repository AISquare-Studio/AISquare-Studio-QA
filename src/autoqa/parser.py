"""
AutoQA Parser for GitHub Action
Parses PR descriptions for AutoQA tags and test steps
"""

import re
from typing import List, Dict, Any, Optional


class AutoQAParser:
    """Parser for AutoQA tags and test steps in PR descriptions"""
    
    def __init__(self):
        self.autoqa_pattern = re.compile(r'AutoQA\s*\n(.*?)(?=\n\n|\n#|\Z)', re.DOTALL | re.IGNORECASE)
        self.steps_pattern = re.compile(r'(?:Steps?:?\s*\n)?((?:\d+\..*?\n?)+)', re.DOTALL | re.IGNORECASE)
    
    def has_autoqa_tag(self, pr_body: str) -> bool:
        """Check if PR description contains AutoQA tag"""
        if not pr_body:
            return False
        
        return bool(self.autoqa_pattern.search(pr_body))
    
    def parse_test_steps(self, pr_body: str) -> List[str]:
        """Extract test steps from AutoQA section"""
        autoqa_match = self.autoqa_pattern.search(pr_body)
        if not autoqa_match:
            return []
        
        autoqa_content = autoqa_match.group(1).strip()
        
        # Extract numbered steps
        steps_match = self.steps_pattern.search(autoqa_content)
        if not steps_match:
            # Try to parse lines that start with numbers
            lines = autoqa_content.split('\n')
            steps = []
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.', line):
                    # Remove number prefix and clean up
                    step = re.sub(r'^\d+\.\s*', '', line).strip()
                    if step:
                        steps.append(step)
            return steps
        
        steps_text = steps_match.group(1)
        steps = []
        
        for line in steps_text.split('\n'):
            line = line.strip()
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


# Example usage and testing
if __name__ == "__main__":
    parser = AutoQAParser()
    
    # Test PR description
    test_pr_body = """
    ## Feature: Enhanced Login System
    
    This PR adds new login validation features.
    
    AutoQA
    Steps:
    1. Navigate to the login page
    2. Enter valid email credentials
    3. Enter valid password
    4. Click login button
    5. Verify dashboard redirect
    6. Verify welcome message appears
    
    ## Other PR Details
    - Updated validation logic
    - Added error handling
    """
    
    print("Testing AutoQA Parser:")
    print(f"Has AutoQA tag: {parser.has_autoqa_tag(test_pr_body)}")
    
    steps = parser.parse_test_steps(test_pr_body)
    print(f"Parsed steps: {steps}")
    
    scenario = parser.steps_to_scenario(steps)
    print(f"Generated scenario: {scenario}")
    
    metadata = parser.extract_metadata(test_pr_body, steps)
    print(f"Metadata: {metadata}")