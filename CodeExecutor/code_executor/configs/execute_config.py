# CodeExecutor/toolchain/execute_config.py
EXECUTION_START_MESSAGE=r"""  ____          _      _____                     _             
 / ___|___   __| | ___| ____|_  _____  ___ _   _| |_ ___  _ __ 
| |   / _ \ / _` |/ _ \  _| \ \/ / _ \/ __| | | | __/ _ \| '__|
| |__| (_) | (_| |  __/ |___ >  <  __/ (__| |_| | || (_) | |   
 \____\___/ \__,_|\___|_____/_/\_\___|\___|\__,_|\__\___/|_|   """

default_env = ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]

# C 언어 실행 설정
c_execute_config = {
    "command": "{exe_path}",
    "seccomp_rule": "c_cpp",
    "env": default_env
}

# C++ 언어 실행 설정
cpp_execute_config = {
    "execute_command": "{exe_path} {solution_path} {testcase_path}",
    "seccomp_rule": "c_cpp",
    "env": default_env
}

# Java 언어 실행 설정
java_execute_config = {
    #"command": "/usr/bin/java -cp {exe_dir} -XX:MaxRAM={max_memory}k -Dfile.encoding=UTF-8 -Djava.security.policy==/etc/java_policy -Djava.awt.headless=true Main",
    "execute_command": (
        "java -cp {execute_dir}:{lib_dir}/{jackson_databind}:{lib_dir}/{jackson_core}:{lib_dir}/{jackson_annotations} "
        "{exe_name} {solution_path} {testcase_path}" # {solution_path} is for debugging.
    ),
    "seccomp_rule": None,
    "env": default_env,
    "memory_limit_check_only": 1
}

# JavaScript 실행 설정 (컴파일 단계 없음)
javascript_execute_config = {
    "execute_command": "node {exe_path} {solution_path} {testcase_path}",
    "seccomp_rule": None,
    "env": ["NO_COLOR=true"] + default_env,
    "memory_limit_check_only": 1
}

# Python 언어 실행 설정
python_execute_config = {
    #"command": "/usr/bin/python3 {exe_path}",
    "execute_command": "python3 {exe_path} {solution_path} {testcase_path}",
    "seccomp_rule": None,
    "env": ["PYTHONIOENCODING=UTF-8"] + default_env
}
