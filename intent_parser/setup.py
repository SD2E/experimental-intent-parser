import setuptools

setuptools.setup(
    name='intent-parser', 
    version='2.7',
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    include_package_data=True,    # include everything in source control
    entry_points={
        'console_scripts': [
            'intent_parser_server = intent_parser.server.intent_parser_server:main',
            'intent_parser.addons.ip_addon_script = intent_parser.addons.ip_addon_script:main',
            'intent_parser.addons.sync_experiment_status_table= intent_parser.addons.sync_experiment_status_table:main',
        ],
    },
)