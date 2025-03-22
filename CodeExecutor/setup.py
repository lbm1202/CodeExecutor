"""
from setuptools import setup, find_packages

setup(
    name='CodeExecutor',
    version='0.0.1',
    description='Code Executor package for python',
    packages=find_packages(),
    python_requires='>=3.6',
)
"""

from setuptools import setup, find_packages

setup(
    name='CodeExecutor',
    version='1.0.0',
    description='A code execution package supporting multiple languages.',
    author='CJH & CYH',  # 작성자 이름 입력
    packages=find_packages(),
    include_package_data=True,  
    package_data={
        'code_executor': [
            'configs/*',
            'solution_wrapper/**/*', 
        ]
    },
    install_requires=[
        # 필요한 의존성이 있다면 여기에 추가
    ],
    entry_points={
        'console_scripts': [
            # 콘솔 스크립트를 추가
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)