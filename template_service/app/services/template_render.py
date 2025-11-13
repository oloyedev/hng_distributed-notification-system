
import re
from typing import Dict, Any
from functools import reduce

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_template_with_variables(subject: str, body: str, variables: Dict[str, Any]) -> Dict:
    """
    Render template with variables
    Pure functional approach to template rendering
    
    Args:
        subject: Template subject with {{variable}} placeholders
        body: Template body with {{variable}} placeholders
        variables: Dictionary of variables to substitute
    
    Returns:
        Dict with rendered subject and body
    """
    try:
        rendered_subject = render_string(subject, variables)
        rendered_body = render_string(body, variables)
        
        return {
            "subject": rendered_subject,
            "body": rendered_body
        }
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return {
            "subject": subject,
            "body": body
        }


def render_string(template: str, variables: Dict[str, Any]) -> str:
    """
    Render a single string with variables
    Pure function
    
    Supports:
    - Simple variables: {{name}}
    - Nested variables: {{user.name}}
    - Default values: {{name|default:"Guest"}}
    """
    # Find all variable placeholders
    placeholders = find_placeholders(template)
    
    # Replace each placeholder
    rendered = reduce(
        lambda text, placeholder: replace_placeholder(text, placeholder, variables),
        placeholders,
        template
    )
    
    return rendered


def find_placeholders(template: str) -> list:
    """
    Find all {{variable}} placeholders in template
    Pure function
    """
    pattern = r'\{\{(.+?)\}\}'
    matches = re.findall(pattern, template)
    return [match.strip() for match in matches]


def replace_placeholder(template: str, placeholder: str, variables: Dict[str, Any]) -> str:
    """
    Replace a single placeholder with its value
    Pure function
    """
    
    if '|default:' in placeholder:
        var_name, default_value = parse_default_syntax(placeholder)
        value = get_nested_value(variables, var_name, default_value)
    else:
        var_name = placeholder
        value = get_nested_value(variables, var_name, f"{{{{{var_name}}}}}")
    

    return template.replace(f"{{{{{placeholder}}}}}", str(value))


def parse_default_syntax(placeholder: str) -> tuple:
    """
    Parse default value syntax: name|default:"Guest"
    Pure function
    """
    parts = placeholder.split('|default:')
    var_name = parts[0].strip()
    default_value = parts[1].strip().strip('"').strip("'") if len(parts) > 1 else ""
    
    return var_name, default_value


def get_nested_value(data: Dict, key_path: str, default: Any = None) -> Any:
    """
    Get value from nested dictionary using dot notation
    Pure function
    
    Examples:
        get_nested_value({"user": {"name": "John"}}, "user.name") -> "John"
        get_nested_value({"name": "John"}, "name") -> "John"
        get_nested_value({}, "missing", "default") -> "default"
    """
    keys = key_path.split('.')
    
    try:
        value = reduce(lambda d, key: d[key], keys, data)
        return value if value is not None else default
    except (KeyError, TypeError):
        return default


def escape_html(text: str) -> str:
    """
    Escape HTML characters
    Pure function
    """
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    return "".join(html_escape_table.get(c, c) for c in text)


def render_with_filters(template: str, variables: Dict[str, Any], filters: Dict) -> str:
    """
    Advanced rendering with custom filters
    Pure functional composition
    
    Example filters:
    - upper: {{name|upper}}
    - lower: {{name|lower}}
    - capitalize: {{name|capitalize}}
    """
    placeholders = find_placeholders(template)
    
    for placeholder in placeholders:
        value, applied_filters = parse_placeholder_with_filters(placeholder)
        
        # Get value from variables
        var_value = get_nested_value(variables, value, "")
        
        # Apply filters
        final_value = apply_filters(var_value, applied_filters, filters)
        
        # Replace in template
        template = template.replace(f"{{{{{placeholder}}}}}", str(final_value))
    
    return template


def parse_placeholder_with_filters(placeholder: str) -> tuple:
    """
    Parse placeholder with filters: name|upper|capitalize
    Pure function
    """
    parts = placeholder.split('|')
    var_name = parts[0].strip()
    filters = [f.strip() for f in parts[1:]] if len(parts) > 1 else []
    
    return var_name, filters


def apply_filters(value: Any, filter_names: list, filter_functions: Dict) -> Any:
    """
    Apply sequence of filters to value
    Pure functional composition
    """
    return reduce(
        lambda v, f: filter_functions.get(f, lambda x: x)(v),
        filter_names,
        value
    )


def filter_upper(value: str) -> str:
    """Convert to uppercase - Pure function"""
    return str(value).upper()


def filter_lower(value: str) -> str:
    """Convert to lowercase - Pure function"""
    return str(value).lower()


def filter_capitalize(value: str) -> str:
    """Capitalize first letter - Pure function"""
    return str(value).capitalize()


def filter_truncate(value: str, length: int = 50) -> str:
    """Truncate string - Pure function"""
    text = str(value)
    return text[:length] + "..." if len(text) > length else text


# Default filter registry
DEFAULT_FILTERS = {
    "upper": filter_upper,
    "lower": filter_lower,
    "capitalize": filter_capitalize,
    "truncate": filter_truncate
}


# Template validation

def validate_template_syntax(template: str) -> Dict:
    """
    Validate template syntax
    Pure function
    
    Returns:
        Dict with is_valid and errors
    """
    errors = []
    
    # Check for unclosed braces
    if template.count('{{') != template.count('}}'):
        errors.append("Unclosed template braces")
    
    # Check for valid variable names
    placeholders = find_placeholders(template)
    for placeholder in placeholders:
        if not is_valid_variable_name(placeholder):
            errors.append(f"Invalid variable name: {placeholder}")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def is_valid_variable_name(name: str) -> bool:
    """
    Check if variable name is valid
    Pure function
    """
   
    pattern = r'^[a-zA-Z0-9_.\|:"\']+$'
    return bool(re.match(pattern, name))


def extract_required_variables(template: str) -> list:

    placeholders = find_placeholders(template)
    
    required = []
    for placeholder in placeholders:
        if '|default:' not in placeholder:
            var_name = placeholder.split('|')[0].strip()
            if var_name not in required:
                required.append(var_name)
    
    return required