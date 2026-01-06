"""
Utility for validating and repairing JSON from LLM responses
"""

import json
import re
from typing import Tuple, Optional

class JSONValidator:
    """Validates and repairs JSON strings"""
    
    @staticmethod
    def validate_and_repair(json_str: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Validate JSON and attempt repairs if needed
        Returns: (is_valid, parsed_data, error_message)
        """
        
        # Try direct parsing first
        try:
            data = json.loads(json_str)
            return True, data, None
        except json.JSONDecodeError as e:
            error_msg = f"JSON error at position {e.pos}: {e.msg}"
        
        # Try cleaning
        cleaned = JSONValidator._clean_json(json_str)
        try:
            data = json.loads(cleaned)
            return True, data, None
        except json.JSONDecodeError:
            pass
        
        # Try aggressive repair
        repaired = JSONValidator._repair_json(cleaned)
        try:
            data = json.loads(repaired)
            return True, data, "Repaired with modifications"
        except json.JSONDecodeError as e:
            return False, None, f"Could not repair: {e.msg}"
    
    @staticmethod
    def _clean_json(json_str: str) -> str:
        """Clean common JSON formatting issues"""
        
        # Remove markdown code blocks
        json_str = re.sub(r'```json\s*', '', json_str)
        json_str = re.sub(r'```\s*', '', json_str)
        
        # Remove comments
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # Fix trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix missing commas between objects
        json_str = re.sub(r'}\s*{', '},{', json_str)
        json_str = re.sub(r']\s*{', '],{', json_str)
        json_str = re.sub(r'}\s*\[', '},[', json_str)
        
        # Fix missing commas after strings
        json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
        
        return json_str
    
    @staticmethod
    def _repair_json(json_str: str) -> str:
        """Aggressively repair malformed JSON"""
        
        # Balance braces
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        elif close_braces > open_braces:
            # Remove extra closing braces from end
            excess = close_braces - open_braces
            for _ in range(excess):
                last_brace = json_str.rfind('}')
                if last_brace != -1:
                    json_str = json_str[:last_brace] + json_str[last_brace+1:]
        
        # Balance brackets
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        elif close_brackets > open_brackets:
            excess = close_brackets - open_brackets
            for _ in range(excess):
                last_bracket = json_str.rfind(']')
                if last_bracket != -1:
                    json_str = json_str[:last_bracket] + json_str[last_bracket+1:]
        
        # Fix unquoted property names
        # Pattern: word followed by colon, not already quoted
        json_str = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_str)
        
        # Convert single quotes to double quotes (risky but often needed)
        # Be smarter about it - only in specific contexts
        lines = json_str.split('\n')
        for i, line in enumerate(lines):
            # If line has : or , it's likely a JSON line
            if ':' in line or ',' in line:
                # Replace single quotes with double quotes
                lines[i] = line.replace("'", '"')
        json_str = '\n'.join(lines)
        
        return json_str
    
    @staticmethod
    def extract_json_objects(text: str) -> list:
        """Extract all JSON objects from text"""
        
        objects = []
        brace_count = 0
        start = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start != -1:
                    potential_json = text[start:i+1]
                    try:
                        obj = json.loads(potential_json)
                        objects.append(obj)
                    except:
                        # Try to repair this object
                        try:
                            cleaned = JSONValidator._clean_json(potential_json)
                            obj = json.loads(cleaned)
                            objects.append(obj)
                        except:
                            pass
                    start = -1
        
        return objects