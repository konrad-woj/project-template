import tempfile
from pathlib import Path

import pytest

from gemini_client.utils import (
    create_jinja_environment,
    format_prompt,
    render_prompt_from_string,
    render_prompt_template,
)

TEMPLATE = "OCR: <<ocr_text>>, Tag: <<tag>>"


def test_multiple_placeholders_filled_correctly():
    result = format_prompt(TEMPLATE, ocr_text="Sample OCR with this tricky part: <<blank>>", tag="Sample Tag")
    assert result == "OCR: Sample OCR with this tricky part: <<blank>>, Tag: Sample Tag"


def test_missing_keyword_raises_error():
    with pytest.raises(ValueError) as excinfo:
        format_prompt(TEMPLATE, ocr_text="Sample OCR with this tricky part: <<blank>>")
    assert "Missing value for placeholders: <<tag>>" in str(excinfo.value)


def test_unused_keyword_is_silently_ignored():
    """Test that unused kwargs are silently ignored (for backward compatibility)."""
    result = format_prompt(
        TEMPLATE, ocr_text="Sample OCR with this tricky part: <<blank>>", tag="Sample Tag", extra="Extra"
    )
    # Should complete successfully without raising, and extra kwarg should be ignored
    assert "<<tag>>" not in result  # Placeholder should be replaced
    assert "Sample Tag" in result


# Tests for Jinja2 utilities


class TestCreateJinjaEnvironment:
    """Tests for create_jinja_environment function."""

    def test_creates_environment_with_correct_loader(self):
        """Test that environment is created with FileSystemLoader."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = create_jinja_environment(tmpdir)
            assert env is not None
            assert env.trim_blocks is True
            assert env.lstrip_blocks is True

    def test_accepts_path_object(self):
        """Test that function accepts Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path_obj = Path(tmpdir)
            env = create_jinja_environment(path_obj)
            assert env is not None

    def test_accepts_string_path(self):
        """Test that function accepts string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env = create_jinja_environment(tmpdir)
            assert env is not None


class TestRenderPromptFromString:
    """Tests for render_prompt_from_string function."""

    def test_renders_simple_template(self):
        """Test rendering a simple template."""
        template = "Hello {{ name }}!"
        result = render_prompt_from_string(template, name="World")
        assert result == "Hello World!"

    def test_renders_template_with_multiple_variables(self):
        """Test rendering template with multiple variables."""
        template = "{{ greeting }} {{ name }}, you are {{ age }} years old."
        result = render_prompt_from_string(template, greeting="Hello", name="Alice", age=30)
        assert result == "Hello Alice, you are 30 years old."

    def test_renders_template_with_list(self):
        """Test rendering template with list iteration."""
        template = "Items: {% for item in items %}{{ item }}{% if not loop.last %}, {% endif %}{% endfor %}"
        result = render_prompt_from_string(template, items=["apple", "banana", "cherry"])
        assert result == "Items: apple, banana, cherry"

    def test_renders_template_with_conditionals(self):
        """Test rendering template with conditional logic."""
        template = "{% if show %}Visible{% else %}Hidden{% endif %}"
        result_true = render_prompt_from_string(template, show=True)
        result_false = render_prompt_from_string(template, show=False)
        assert result_true == "Visible"
        assert result_false == "Hidden"

    def test_renders_empty_template(self):
        """Test rendering an empty template."""
        result = render_prompt_from_string("")
        assert result == ""

    def test_renders_template_without_variables(self):
        """Test rendering a template with no variables."""
        template = "This is a static string."
        result = render_prompt_from_string(template)
        assert result == "This is a static string."

    def test_renders_template_with_nested_dict(self):
        """Test rendering template with nested dictionary."""
        template = "User: {{ user.name }}, Age: {{ user.age }}"
        result = render_prompt_from_string(template, user={"name": "Bob", "age": 25})
        assert result == "User: Bob, Age: 25"

    def test_handles_missing_variable_gracefully(self):
        """Test that missing variables render as empty strings by default."""
        template = "Hello {{ missing_var }}!"
        result = render_prompt_from_string(template)
        assert result == "Hello !"


class TestRenderPromptTemplate:
    """Tests for render_prompt_template function."""

    def test_renders_template_from_file(self):
        """Test rendering a template from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test template file
            template_path = Path(tmpdir) / "test_template.j2"
            template_path.write_text("Hello {{ name }}!")

            # Render the template
            result = render_prompt_template(template_path, name="World")
            assert result == "Hello World!"

    def test_renders_complex_template_from_file(self):
        """Test rendering a complex template with loops and conditionals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test template file
            template_path = Path(tmpdir) / "complex_template.j2"
            template_content = """
You are analyzing data.

{% if priority_fields %}
**Priority Fields:**
{% for field in priority_fields %}
* {{ field.name }} - {{ field.description }}
{% endfor %}
{% endif %}

{% if optional_fields %}
**Optional Fields:**
{% for field in optional_fields %}
* {{ field.name }} - {{ field.description }}
{% endfor %}
{% endif %}
""".strip()
            template_path.write_text(template_content)

            # Render the template
            result = render_prompt_template(
                template_path,
                priority_fields=[
                    {"name": "FIELD1", "description": "First field"},
                    {"name": "FIELD2", "description": "Second field"},
                ],
                optional_fields=[{"name": "FIELD3", "description": "Third field"}],
            )

            assert "**Priority Fields:**" in result
            assert "* FIELD1 - First field" in result
            assert "* FIELD2 - Second field" in result
            assert "**Optional Fields:**" in result
            assert "* FIELD3 - Third field" in result

    def test_renders_template_with_string_path(self):
        """Test that function accepts string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test template file
            template_path = Path(tmpdir) / "test_template.j2"
            template_path.write_text("Hello {{ name }}!")

            # Render using string path
            result = render_prompt_template(str(template_path), name="World")
            assert result == "Hello World!"

    def test_renders_template_with_path_object(self):
        """Test that function accepts Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test template file
            template_path = Path(tmpdir) / "test_template.j2"
            template_path.write_text("Hello {{ name }}!")

            # Render using Path object
            result = render_prompt_template(template_path, name="World")
            assert result == "Hello World!"

    def test_renders_template_without_variables(self):
        """Test rendering a template file with no variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test template file
            template_path = Path(tmpdir) / "static_template.j2"
            template_path.write_text("This is a static template.")

            # Render without variables
            result = render_prompt_template(template_path)
            assert result == "This is a static template."

    def test_raises_error_for_nonexistent_template(self):
        """Test that error is raised for non-existent template."""
        from jinja2 import TemplateNotFound

        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to render a non-existent template
            template_path = Path(tmpdir) / "nonexistent.j2"

            with pytest.raises(TemplateNotFound):
                render_prompt_template(template_path, name="World")

    def test_trim_and_lstrip_blocks_enabled(self):
        """Test that trim_blocks and lstrip_blocks work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test template with whitespace
            template_path = Path(tmpdir) / "whitespace_template.j2"
            template_content = """
            {% if true %}
            Line 1
            {% endif %}
            {% if true %}
            Line 2
            {% endif %}
            """.strip()
            template_path.write_text(template_content)

            # Render the template
            result = render_prompt_template(template_path)

            # With trim_blocks and lstrip_blocks, extra whitespace should be removed
            assert "Line 1" in result
            assert "Line 2" in result
