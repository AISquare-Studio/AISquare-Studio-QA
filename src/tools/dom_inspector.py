"""
DOM Inspector Tool: Extracts selectors and inspects page structure from live pages.
"""

from typing import Any, Dict, List, Optional

from playwright.sync_api import Page

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DOMInspectorTool:
    """
    Tool for inspecting live pages and discovering selectors.
    Extracts interactive elements, form fields, and suggests best selectors.
    """

    # Selector priority (higher = better)
    SELECTOR_PRIORITY = {
        "data-testid": 100,
        "data-test": 95,
        "id": 90,
        "name": 80,
        "aria-label": 70,
        "placeholder": 60,
        "type": 50,
        "class": 40,
        "tag": 30,
        "text": 20,
        "xpath": 10,
    }

    def __init__(self, page: Page):
        """
        Initialize DOM inspector.

        Args:
            page: Playwright page instance
        """
        self.page = page

    def discover_selectors(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all interactive elements and their selectors on current page.

        Returns:
            Dict mapping element types to lists of element info with selectors
        """
        try:
            logger.info(f"Discovering selectors on page: {self.page.url}")

            discovered = {
                "buttons": self._find_buttons(),
                "inputs": self._find_inputs(),
                "links": self._find_links(),
                "forms": self._find_forms(),
                "containers": self._find_containers(),
            }

            # Log summary
            total = sum(len(elements) for elements in discovered.values())
            logger.info(f"Discovered {total} interactive elements across {len(discovered)} types")

            return discovered

        except Exception as e:
            logger.error(f"Failed to discover selectors: {str(e)}")
            return {}

    def find_best_selector_for_element(self, element_description: str) -> Optional[str]:
        """
        Find the best selector for an element based on natural language description.

        Args:
            element_description: Natural language description (e.g., "email input", "login button")

        Returns:
            Best matching CSS selector or None
        """
        try:
            # Discover elements
            discovered = self.discover_selectors()

            # Extract keywords from description
            keywords = element_description.lower().split()

            # Search for matching elements
            candidates = []

            for element_type, elements in discovered.items():
                for element in elements:
                    score = self._score_element_match(element, keywords)
                    if score > 0:
                        candidates.append((score, element["best_selector"]))

            if not candidates:
                logger.warning(f"No matching selector found for: {element_description}")
                return None

            # Return highest scoring selector
            candidates.sort(reverse=True, key=lambda x: x[0])
            best_selector = candidates[0][1]

            logger.info(
                f"Found best selector for '{element_description}': {best_selector} "
                f"(score: {candidates[0][0]})"
            )
            return best_selector

        except Exception as e:
            logger.error(f"Error finding selector for '{element_description}': {str(e)}")
            return None

    def extract_form_fields(self) -> List[Dict[str, Any]]:
        """
        Extract all form fields with their attributes and best selectors.

        Returns:
            List of form field information
        """
        return self._find_inputs()

    def get_page_structure(self) -> Dict[str, Any]:
        """
        Get comprehensive page structure information.

        Returns:
            Dict containing page structure details
        """
        try:
            return {
                "url": self.page.url,
                "title": self.page.title(),
                "interactive_elements": self.discover_selectors(),
                "forms_count": len(self._find_forms()),
                "inputs_count": len(self._find_inputs()),
                "buttons_count": len(self._find_buttons()),
                "links_count": len(self._find_links()),
            }
        except Exception as e:
            logger.error(f"Failed to get page structure: {str(e)}")
            return {}

    def _find_buttons(self) -> List[Dict[str, Any]]:
        """Find all button elements and their selectors."""
        try:
            buttons_js = """
            () => {
                const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"], [role="button"]');
                return Array.from(buttons).map(btn => ({
                    tag: btn.tagName.toLowerCase(),
                    type: btn.type || '',
                    text: btn.textContent?.trim() || '',
                    id: btn.id || '',
                    name: btn.name || '',
                    class: btn.className || '',
                    dataTestId: btn.getAttribute('data-testid') || btn.getAttribute('data-test') || '',
                    ariaLabel: btn.getAttribute('aria-label') || '',
                    visible: btn.offsetParent !== null
                }));
            }
            """

            buttons_data = self.page.evaluate(buttons_js)
            return [self._build_element_info(btn, "button") for btn in buttons_data]

        except Exception as e:
            logger.error(f"Error finding buttons: {str(e)}")
            return []

    def _find_inputs(self) -> List[Dict[str, Any]]:
        """Find all input elements and their selectors."""
        try:
            inputs_js = """
            () => {
                const inputs = document.querySelectorAll('input, textarea, select');
                return Array.from(inputs).map(input => ({
                    tag: input.tagName.toLowerCase(),
                    type: input.type || '',
                    id: input.id || '',
                    name: input.name || '',
                    class: input.className || '',
                    placeholder: input.placeholder || '',
                    dataTestId: input.getAttribute('data-testid') || input.getAttribute('data-test') || '',
                    ariaLabel: input.getAttribute('aria-label') || '',
                    value: input.value || '',
                    visible: input.offsetParent !== null
                }));
            }
            """

            inputs_data = self.page.evaluate(inputs_js)
            return [self._build_element_info(inp, "input") for inp in inputs_data]

        except Exception as e:
            logger.error(f"Error finding inputs: {str(e)}")
            return []

    def _find_links(self) -> List[Dict[str, Any]]:
        """Find all link elements and their selectors."""
        try:
            links_js = """
            () => {
                const links = document.querySelectorAll('a[href]');
                return Array.from(links).map(link => ({
                    tag: 'a',
                    href: link.href || '',
                    text: link.textContent?.trim() || '',
                    id: link.id || '',
                    class: link.className || '',
                    dataTestId: link.getAttribute('data-testid') || link.getAttribute('data-test') || '',
                    ariaLabel: link.getAttribute('aria-label') || '',
                    visible: link.offsetParent !== null
                }));
            }
            """

            links_data = self.page.evaluate(links_js)
            return [self._build_element_info(link, "link") for link in links_data]

        except Exception as e:
            logger.error(f"Error finding links: {str(e)}")
            return []

    def _find_forms(self) -> List[Dict[str, Any]]:
        """Find all form elements."""
        try:
            forms_js = """
            () => {
                const forms = document.querySelectorAll('form');
                return Array.from(forms).map(form => ({
                    tag: 'form',
                    id: form.id || '',
                    name: form.name || '',
                    class: form.className || '',
                    action: form.action || '',
                    method: form.method || '',
                    dataTestId: form.getAttribute('data-testid') || form.getAttribute('data-test') || ''
                }));
            }
            """

            forms_data = self.page.evaluate(forms_js)
            return [self._build_element_info(form, "form") for form in forms_data]

        except Exception as e:
            logger.error(f"Error finding forms: {str(e)}")
            return []

    def _find_containers(self) -> List[Dict[str, Any]]:
        """Find important container elements (divs with IDs or data-testids)."""
        try:
            containers_js = """
            () => {
                const containers = document.querySelectorAll('[data-testid], [id]');
                return Array.from(containers).slice(0, 20).map(container => ({
                    tag: container.tagName.toLowerCase(),
                    id: container.id || '',
                    class: container.className || '',
                    dataTestId: container.getAttribute('data-testid') || container.getAttribute('data-test') || '',
                    visible: container.offsetParent !== null
                }));
            }
            """

            containers_data = self.page.evaluate(containers_js)
            return [self._build_element_info(cont, "container") for cont in containers_data]

        except Exception as e:
            logger.error(f"Error finding containers: {str(e)}")
            return []

    def _build_element_info(
        self, element_data: Dict[str, Any], element_type: str
    ) -> Dict[str, Any]:
        """
        Build comprehensive element information with all possible selectors.

        Args:
            element_data: Raw element data from page evaluation
            element_type: Type of element

        Returns:
            Dict with element info and ranked selectors
        """
        selectors = self._generate_selectors(element_data)
        best_selector = self._choose_best_selector(selectors)

        return {
            "type": element_type,
            "data": element_data,
            "selectors": selectors,
            "best_selector": best_selector,
            "visible": element_data.get("visible", True),
        }

    def _generate_selectors(self, element_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate all possible selectors for an element with priority scores.

        Args:
            element_data: Element data from page

        Returns:
            List of selector dicts with type, value, and priority
        """
        selectors = []

        # data-testid (highest priority)
        if element_data.get("dataTestId"):
            selectors.append({
                "type": "data-testid",
                "value": f"[data-testid='{element_data['dataTestId']}']",
                "priority": self.SELECTOR_PRIORITY["data-testid"],
            })

        # id
        if element_data.get("id"):
            selectors.append({
                "type": "id",
                "value": f"#{element_data['id']}",
                "priority": self.SELECTOR_PRIORITY["id"],
            })

        # name attribute
        if element_data.get("name"):
            selectors.append({
                "type": "name",
                "value": f"[name='{element_data['name']}']",
                "priority": self.SELECTOR_PRIORITY["name"],
            })

        # aria-label
        if element_data.get("ariaLabel"):
            selectors.append({
                "type": "aria-label",
                "value": f"[aria-label='{element_data['ariaLabel']}']",
                "priority": self.SELECTOR_PRIORITY["aria-label"],
            })

        # placeholder
        if element_data.get("placeholder"):
            selectors.append({
                "type": "placeholder",
                "value": f"[placeholder='{element_data['placeholder']}']",
                "priority": self.SELECTOR_PRIORITY["placeholder"],
            })

        # type (for inputs)
        if element_data.get("type") and element_data["type"] not in ["text", "button"]:
            selectors.append({
                "type": "type",
                "value": f"{element_data.get('tag', 'input')}[type='{element_data['type']}']",
                "priority": self.SELECTOR_PRIORITY["type"],
            })

        # text content (for buttons/links)
        if element_data.get("text") and len(element_data["text"]) < 50:
            text = element_data["text"].replace("'", "\\'")
            selectors.append({
                "type": "text",
                "value": f"{element_data.get('tag', 'button')}:has-text('{text}')",
                "priority": self.SELECTOR_PRIORITY["text"],
            })

        # class (lower priority, can be unstable)
        if element_data.get("class") and " " not in element_data["class"][:30]:
            classes = element_data["class"].split()[:2]  # First 2 classes
            class_selector = "." + ".".join(classes)
            selectors.append({
                "type": "class",
                "value": class_selector,
                "priority": self.SELECTOR_PRIORITY["class"],
            })

        # tag (fallback)
        if element_data.get("tag"):
            selectors.append({
                "type": "tag",
                "value": element_data["tag"],
                "priority": self.SELECTOR_PRIORITY["tag"],
            })

        return selectors

    def _choose_best_selector(self, selectors: List[Dict[str, Any]]) -> str:
        """
        Choose the best selector based on priority.

        Args:
            selectors: List of selector options

        Returns:
            Best CSS selector string
        """
        if not selectors:
            return "body"  # Fallback

        # Sort by priority (descending)
        sorted_selectors = sorted(selectors, key=lambda x: x["priority"], reverse=True)
        return sorted_selectors[0]["value"]

    def _score_element_match(self, element: Dict[str, Any], keywords: List[str]) -> int:
        """
        Score how well an element matches given keywords.

        Args:
            element: Element info dict
            keywords: List of keywords from description

        Returns:
            Match score (higher = better)
        """
        score = 0
        data = element.get("data", {})

        # Convert element data to searchable text
        searchable_text = " ".join([
            str(data.get("text", "")),
            str(data.get("placeholder", "")),
            str(data.get("ariaLabel", "")),
            str(data.get("id", "")),
            str(data.get("name", "")),
            str(data.get("type", "")),
            element.get("type", ""),
        ]).lower()

        # Score based on keyword matches
        for keyword in keywords:
            if keyword in searchable_text:
                score += 10

        # Bonus for visible elements
        if element.get("visible", True):
            score += 5

        return score

    def find_relevant_elements(self, element_description: str) -> List[Dict[str, Any]]:
        """
        Find all relevant elements matching the description, without forcing a single best choice.

        Args:
            element_description: Natural language description

        Returns:
            List of relevant element dictionaries, sorted by relevance score
        """
        try:
            # Discover elements
            discovered = self.discover_selectors()

            # Extract keywords from description
            keywords = element_description.lower().split()

            # Search for matching elements
            candidates = []

            for element_type, elements in discovered.items():
                for element in elements:
                    score = self._score_element_match(element, keywords)
                    if score > 0:
                        # Add score to element info for reference
                        element_info = element.copy()
                        element_info["match_score"] = score
                        candidates.append(element_info)

            # Sort by score (descending) but return all matches
            candidates.sort(reverse=True, key=lambda x: x["match_score"])

            logger.info(f"Found {len(candidates)} relevant elements for '{element_description}'")
            return candidates

        except Exception as e:
            logger.error(f"Error finding relevant elements for '{element_description}': {str(e)}")
            return []
