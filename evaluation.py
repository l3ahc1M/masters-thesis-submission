import re
from typing import List


class Evaluation:
    def __init__(self, test_case):
        self.test_case = test_case

    def extract_component(self, sql: str, start_keyword: str, end_keywords: List[str]):
        """
        Extract substring between `start_keyword` and the earliest of `end_keywords`.
        Returns empty string if not found.
        """
        start_match = re.search(rf"\b{start_keyword}\b", sql, flags=re.IGNORECASE)
        if not start_match:
            return ""

        start_index = start_match.end()
        end_candidates = []

        for keyword in end_keywords:
            end_match = re.search(rf"\b{keyword}\b", sql[start_index:], flags=re.IGNORECASE)
            if end_match:
                end_candidates.append(start_index + end_match.start())

        end_index = min(end_candidates) if end_candidates else len(sql)
        return sql[start_index:end_index].strip()

    def normalize_quotes_and_commas(self, value: str):
        """
        Normalize quoted values by:
        1. Removing surrounding single or double quotes.
        2. Removing any commas and extra spaces.
        3. Removing any leading colons (':').
        Iterates until no changes are made.
        """
    
        previous_value = None
        while value != previous_value:
            previous_value = value  # Store the current value to detect changes
            
            # Remove leading colons if present
            value = value.lstrip(":").strip()
            
            # Remove surrounding single or double quotes
            value = re.sub(r"^['\"](.*)['\"]$", r"\1", value)
            
            # Remove any trailing commas and extra spaces
            value = value.rstrip(",").strip()
            
            # Remove any extra spaces around colons (if any still exist)
            value = re.sub(r"\s*[:]\s*", ":", value)  # Normalize space around colons

        
        return value
    
    def get_component_content(self, text, components):
        i = 0
        components_content = []
        text = (text + "[END]")  # sentinel to capture last component
        components.append("[END]")  # append sentinel to handle last component

        for component in components:
            component_text = self.extract_component(text, component, components)
            components_content.append({
                'Component': component,
                'Component_content': self.normalize_quotes_and_commas(component_text)
            })
            
        return components_content
    
    def perform_component_matching(self, reference, test_result, components):
        reference_components = self.get_component_content(reference, components)
        test_result_components = self.get_component_content(test_result, components)

        component_evaluation = []

        # lists are of the same length and correspond one-to-one.
        for reference_component, test_result_component in zip(reference_components, test_result_components):
            # Make sure each reference and test result component has the expected structure.
            reference_component_text = reference_component['Component_content'].lower() if 'Component_content' in reference_component else ''
            test_result_component_text = test_result_component['Component_content'].lower() if 'Component_content' in test_result_component else ''
            if len(reference_component_text) == 0:
                has_component = False
            else:
                has_component = True

            # Check for exact match between reference and actual clauses
            evaluation = {
                'component': reference_component['Component'],
                'has_component': has_component,
                'reference_content': reference_component_text,
                'test_result': test_result_component_text,
                'match': reference_component_text == test_result_component_text
            }
            component_evaluation.append(evaluation)

        self.test_case.add_component_matching_result(component_evaluation)
    
    def perform_exact_matching(self):
        num_errors = 0
        
        component_matching_results = self.test_case.get_component_matching_result()
        
        if not isinstance(component_matching_results, list):
            raise TypeError("Expected a list of dictionaries, but got something else.")

        for component in component_matching_results:
            # Check if each component is a dictionary and contains 'match'
            if isinstance(component, dict):
                if 'match' not in component:
                    raise KeyError("'match' key not found in component dictionary.")
                if component['match'] is False:
                    num_errors += 1
            else:
                raise TypeError(f"Expected component to be a dictionary, but got {type(component)}")

        self.test_case.add_exact_match_result(num_errors == 0)  # Adds True if no errors, False otherwise