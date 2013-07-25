#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
complexity.generate
-------------------

Functions for static site generation.
"""

import json
import os
import shutil

from jinja2 import FileSystemLoader
from jinja2.environment import Environment

from .exceptions import NonHTMLFileException, MissingTemplateDirException
from .utils import make_sure_path_exists, unicode_open


def get_output_filename(template_filepath, output_dir):
    """
    Given an input filename, return the corresponding output filename.
    
    :param template_filepath: Name of template file relative to template dir,
                          e.g. art/index.html
    :param output_dir: The Complexity output directory, e.g. `www/`.
    :paramtype output_dir: directory
    """

    template_filepath = os.path.normpath(template_filepath)

    basename = os.path.basename(template_filepath)
    dirname = os.path.dirname(template_filepath)

    # Base files don't have output.
    if basename.startswith('base'):
        return False
    # Put index in the root. It's a special case.
    elif basename == 'index.html':
        output_filename = os.path.join(output_dir, template_filepath)
    # Put other pages in page/index.html, for better URL formatting.
    else:
        stem = basename.split('.')[0]
        output_filename = os.path.join(
            output_dir,
            dirname,
            '{0}/index.html'.format(stem)
        )
    return output_filename

def generate_html_file(template_filepath, output_dir, env, context):
    """
    Renders and writes a single HTML file to its corresponding output location.

    :param template_filepath: Name of template file to be rendered. Should be
                              relative to template dir, e.g. art/index.html
    :param output_dir: The Complexity output directory, e.g. `www/`.
    :paramtype output_dir: directory
    :param env: Jinja2 environment with a loader already set up.
    :param context: Jinja2 context that holds template variables. See
        http://jinja.pocoo.org/docs/api/#the-context
    """

    if not template_filepath.endswith('html'):
        raise NonHTMLFileException(
            'Non-HTML file found. Make sure all files in templates/ are \
            .html files.'
        )

    # Ignore templates starting with "base". They're treated as special cases.
    if template_filepath.startswith('base'):
        return False

    tmpl = env.get_template(template_filepath)
    rendered_html = tmpl.render(**context)

    output_filename = get_output_filename(template_filepath, output_dir)
    if output_filename:
        make_sure_path_exists(os.path.dirname(output_filename))

        # Write the generated file
        with unicode_open(output_filename, 'w') as fh:
            fh.write(rendered_html)
            return True


def generate_html(templates_dir, output_dir, context=None):
    """
    Renders the HTML templates from `templates_dir`, and writes them to
    `output_dir`.

    :param templates_dir: The Complexity templates directory, e.g. `project/templates/`.
    :paramtype templates_dir: directory
    :param output_dir: The Complexity output directory, e.g. `www/`.
    :paramtype output_dir: directory
    :param context: Jinja2 context that holds template variables. See
        http://jinja.pocoo.org/docs/api/#the-context
    """

    if not os.path.exists(templates_dir):
        raise MissingTemplateDirException(
            'Your project is missing a templates/ directory containing your \
            HTML templates.'
        )

    context = context or {}
    env = Environment()
    # os.chdir(templates_dir)
    print('Templates dir is {0}'.format(templates_dir))
    env.loader = FileSystemLoader(templates_dir)

    # Create the output dir if it doesn't already exist
    make_sure_path_exists(output_dir)

    for root, dirs, files in os.walk(templates_dir):
        for f in files:
            # print(f)
            template_filepath = os.path.relpath(os.path.join(root, f), templates_dir)

            outfile = get_output_filename(template_filepath, output_dir)
            print('Copying {0} to {1}'.format(template_filepath, outfile))
            generate_html_file(template_filepath, output_dir, env, context)


def generate_context(json_dir):
    """
    Generates the context for all Complexity pages.

    :param json_dir: Directory containing `.json` file(s).
    :paramtype json_dir: directory

    Description:

        Iterates through the contents of `json_dir` and finds all JSON
        files. Loads the JSON file as a Python object with the key being the
        JSON file name.

    Example:

        Assume the following files exist::

            json/
            ├── names.json
            └── numbers.json

        Depending on their content, might generate a context as follows:

        .. code-block:: json

            contexts = {
                    "names": ['Audrey', 'Danny'],
                    "numbers": [1, 2, 3, 4]
                   }
    """
    context = {}

    json_files = os.listdir(json_dir)

    for file_name in json_files:

        if file_name.endswith('json'):

            # Open the JSON file and convert to Python object
            json_file = os.path.join(json_dir, file_name)
            with unicode_open(json_file) as f:
                obj = json.load(f)

            # Add the Python object to the context dictionary
            context[file_name[:-5]] = obj

    return context


def copy_assets(assets_dir, output_dir):
    """
    Copies static assets over from `assets_dir` to `output_dir`.

    :param assets_dir: The Complexity project assets directory, e.g. `project/assets/`.
    :paramtype assets_dir: directory
    :param output_dir: The Complexity output directory, e.g. `www/`.
    :paramtype output_dir: directory
    """
    
    assets = os.listdir(assets_dir)
    for item in assets:
        item_path = os.path.join(assets_dir, item)

        # Only copy allowed dirs
        if os.path.isdir(item_path) and item != 'scss' and item != 'less':
            new_dir = os.path.join(output_dir, item)
            print('Copying directory {0} to {1}'.format(item, new_dir))
            shutil.copytree(item_path, new_dir)
            
        # Copy over files in the root of assets_dir
        if os.path.isfile(item_path):
            new_file = os.path.join(output_dir, item)
            print('Copying file {0} to {1}'.format(item, new_file))
            shutil.copyfile(item_path, new_file)
