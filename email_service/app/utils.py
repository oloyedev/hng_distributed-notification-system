import os
from jinja2 import Environment, FileSystemLoader


template_loader = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

def render_template(template_code: str, variables: dict):
    template = template_loader.get_template(template_code)
    return template.render(**variables)
