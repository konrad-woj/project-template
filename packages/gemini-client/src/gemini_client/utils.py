import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape


def format_prompt(prompt_template: str, **kwargs) -> str:
    """Fills in information into the prompt template.

    Args:
        prompt_template: Template string with <<placeholder>> markers
        **kwargs: Values to fill in. Extra kwargs without placeholders are silently ignored.

    Returns:
        Formatted prompt string

    Raises:
        ValueError: If required placeholders are not provided in kwargs
    """
    prompt = prompt_template
    placeholders = set(re.findall(r"<<.*?>>", prompt))

    for key, value in kwargs.items():
        placeholder = f"<<{key}>>"
        if placeholder in prompt:
            prompt = prompt.replace(placeholder, value)
            placeholders.discard(placeholder)
        # Silently ignore kwargs without corresponding placeholders (for backward compatibility)

    # check if any original placeholders were not filled
    if len(placeholders) > 0:
        raise ValueError(f"Missing value for placeholders: {', '.join(placeholders)}")

    return prompt


def extract_json_content(text: str) -> str | None:
    """Extract string part enclosed in ```json (...) ```"""
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        result = match.group(1).strip()
        return result
    return None


def create_jinja_environment(templates_dir: Path | str) -> Environment:
    """Create a Jinja2 environment for rendering prompt templates.

    Args:
        templates_dir: Directory containing Jinja2 template files

    Returns:
        Configured Jinja2 Environment
    """
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_prompt_template(template_path: Path | str, **kwargs) -> str:
    """Render a Jinja2 prompt template with the given variables.

    Args:
        template_path: Path to the Jinja2 template file (.j2)
        **kwargs: Variables to pass to the template

    Returns:
        Rendered prompt string

    Example:
        >>> render_prompt_template("prompts/dummy.j2", examples=[...], my_variable="my_value")
        'You are an expert in my_value! Based on the following examples...\nExample 1:\n\n...'
    """
    template_path = Path(template_path)
    env = create_jinja_environment(template_path.parent)
    template = env.get_template(template_path.name)
    return template.render(**kwargs)


def render_prompt_from_string(template_string: str, **kwargs) -> str:
    """Render a Jinja2 template string with the given variables.

    Args:
        template_string: Jinja2 template as a string
        **kwargs: Variables to pass to the template

    Returns:
        Rendered prompt string

    Example:
        >>> render_prompt_from_string("Hello {{ name }}!", name="World")
        'Hello World!'
    """
    template = Template(template_string)
    return template.render(**kwargs)
