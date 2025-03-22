import sys
DEFAULT_TESTCASE_NAME = 'testcase.json'

# ver3.
BASE_DIR = '/workspace'
EXECUTE_DIR = '{base_dir}/executor/{hash_id}'

# ver1.
# BASE_DIR = '/workspace/executor'
# SUB_DIR = '/{hash_id}'
# BASE_TESTCASE_DIR = '{base_dir}/{problem_name}/{hash_id}/'
# BASE_RUN_DIR = BASE_DIR + '{base_dir}/{problem_name}/{hash_id}/'
# BASE_SUBMIT_DIR = BASE_DIR + '{base_dir}/{problem_name}/{hash_id}/'

# ver2.
# BASE_DIR = '/workspace/executor'
# SUB_DIR = '/{hash_id}'
# RUN_DIR = '{base_dir}/run' + SUB_DIR
# SUBMIT_DIR = '{base_dir}/submit' + SUB_DIR


c_compile_config = {
    "compilable": True,
    "compile_lang": "c",
    "solution_wrapper_fname": "main.c",
    "solution_fname": "solution.c",
    "exe_fname": "main",
    "compile_command": "/usr/bin/gcc -O2 -w -fmax-errors=3 -std=c99 {src_path} -lm -o {exe_path}"
}

cpp_compile_config = {
    "compilable": True,
    "compile_lang": "cpp",
    "solution_wrapper_fname": "main.cpp",
    "solution_fname": "solution.cpp",
    "exe_fname": "main",
    #"compile_command": "g++ -O2 -w -fmax-errors=3 -std=c++14 {solution_wrapper_path} -lm -o {exe_path}"
    "compile_command": "g++ -O2 -w -fmax-errors=3 -std=c++17 {solution_wrapper_path} -lm -lpthread -o {exe_path}"
}

java_compile_config = {
    "compilable": True,
    "compile_lang": "java",
    "solution_wrapper_fname": "Main.java",
    "solution_fname": "Solution.java",
    "exe_fname": "Main",
    "lib_dir_name": "lib",
    "compile_command": (
        "javac -cp {lib_dir}/{jackson_databind}:{lib_dir}/{jackson_core}:{lib_dir}/{jackson_annotations} "
        "{solution_wrapper_path} {solution_path}"
    )
}

python_compile_config = {
    "compilable": True,
    "compile_lang": "python",
    "solution_wrapper_fname": "main.py",
    "solution_fname": "solution.py",
    "exe_fname": f"__pycache__/main.{sys.implementation.cache_tag}.pyc",
    "compile_command": (
        "python3 -m py_compile {solution_wrapper_path} {solution_path}"
    )
}

javascript_compile_config = {
    "compilable": True,
    "compile_lang": "javascript",
    "solution_wrapper_fname": "main.js",
    "solution_fname": "solution.js",
    "exe_fname": "main.js",
    #"compile_command": None
    "compile_command": "node --check {solution_path}"
}