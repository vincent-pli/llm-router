import logging
import os.path
import setuptools


def get_install_requirements(require_f_paths, env_dir='environments'):
    reqs = []
    for path in require_f_paths:
        target_f = os.path.join(env_dir, path)
        if not os.path.exists(target_f):
            logging.warning(f'target file does not exist: {target_f}')
        else:
            with open(target_f, 'r', encoding='utf-8') as fin:
                reqs += [x.strip() for x in fin.read().splitlines()]
    reqs = [x for x in reqs if not x.startswith('#')]
    return reqs

min_requires = get_install_requirements(['minimal_requires.txt'])
version = '2024-2'

with open('README.md', encoding='utf-8') as f:
    readme_md = f.read()

setuptools.setup(
    name='py-llm-router',
    version=version,
    url='https://github.com/vincent-pli/llm-router',
    author='vincent-pli',
    description='Route for public LLM and om-pre LLM.',
    long_description=readme_md,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(exclude=['tests*']),
    entry_points={
        'console_scripts': [
            'lr-start = tool_legacy.process_data:main',
        ]
    },
    install_requires=min_requires,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ],
)
