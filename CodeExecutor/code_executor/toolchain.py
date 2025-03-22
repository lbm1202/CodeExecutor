import os, sys, shutil, uuid, json, resource
import subprocess
import resource
from abc import ABC, abstractmethod
from code_executor.configs.compile_config import BASE_DIR, EXECUTE_DIR
from code_executor.configs.execute_config import EXECUTION_START_MESSAGE


def set_limits():
    # 최대 메모리 사용량 제한 (bytes 단위)
    memory_limit = 500 * 1024 * 1024  # 100MB
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))

    # 최대 CPU 시간 제한 (초 단위)
    cpu_time_limit = 30  
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit, cpu_time_limit))

from code_executor.configs.compile_config import (
    #c_compile_config,
    cpp_compile_config,
    java_compile_config,
    python_compile_config,
    javascript_compile_config,
)
from code_executor.configs.execute_config import (
    #c_execute_config,
    cpp_execute_config,
    java_execute_config,
    python_execute_config,
    javascript_execute_config,
)



class BaseToolChain(ABC):
    _registry = {}

    def __init__(self, language, base_dir=None, timeout=10):
        self.timeout = timeout
        self.language = language.lower()
        self.compile_config, self.execute_config = self._get_configs()
        
        self.execute_dir, self.solution_wrapper_dir = self._generate_dirs(base_dir)
        
        
        self.solution_wrapper_path = os.path.join(self.solution_wrapper_dir, self.compile_config['solution_wrapper_fname'])
        self.tmp_solution_wrapper_path = os.path.join(self.execute_dir, self.compile_config['solution_wrapper_fname'])
        self.tmp_exe_path = os.path.join(self.execute_dir, self.compile_config['exe_fname'])
        self.tmp_solution_path = os.path.join(self.execute_dir, self.compile_config['solution_fname'])
        self.tmp_testcase_path = os.path.join(self.execute_dir, 'testcase.json')

        self.solution_code = None
        self.testcase = None

    @abstractmethod
    def compile(self):
        pass
    
    @abstractmethod
    def execute(self):
        pass
    

    def _get_configs(self):
        config_mapping = {
            "c++": (cpp_compile_config, cpp_execute_config),
            "cpp": (cpp_compile_config, cpp_execute_config),
            "java": (java_compile_config, java_execute_config),
            "python": (python_compile_config, python_execute_config),
            "javascript": (javascript_compile_config, javascript_execute_config),
        }
        try:
            return config_mapping[self.language]
        except KeyError:
            raise ValueError("Unsupported Language.")

    def _generate_dirs(self, base_dir=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        solution_wrapper_dir = os.path.join(current_dir, 'solution_wrapper', self.language)

        if base_dir is None:
            base_dir = BASE_DIR
        elif not os.path.isabs(base_dir):
            base_dir = os.path.abspath(base_dir)
        hash_id = uuid.uuid4().hex
        execute_dir = EXECUTE_DIR.format(base_dir=base_dir, hash_id=hash_id)
        return execute_dir, solution_wrapper_dir
    
    @classmethod
    def register_toolchain(cls, language):
        def decorator(subclass):
            cls._registry[language.lower()] = subclass
            return subclass
        return decorator
    
    
    @classmethod
    def create(cls, language, base_dir=None, timeout=10): #Factory method to create the appropriate toolchain instance.
        language = language.lower()
        if language not in cls._registry:
            raise ValueError("Unsupported Language.")
        return cls._registry[language](language, base_dir, timeout)


    def run_shell_command(self, command, iscompile=False):
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            #preexec_fn=set_limits
        )
        try:
            if iscompile:
                stdout, stderr = process.communicate(timeout=8000)
            else:
                stdout, stderr = process.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            stdout, stderr = '', "timeout"
        return process.returncode, stdout, stderr
    
    def run(self):
        if self.compile_config['compilable']:
            returncode, stdout, stderr = self.compile()
            if stderr:
                return ("compile", returncode, stdout, stderr)

        returncode, stdout, stderr = self.execute()
        if not stdout:
            stdout = self._generate_default_stdout()
         
        return ("execute", returncode, json.loads(stdout), stderr)
    
    def _generate_default_stdout(self):
        test_data = json.loads(self.testcase)
        all_results = {}

        for test_case_key in test_data.keys():
            all_results[test_case_key] = {
            "result": None,
            "utime": -1,
            "stime": -1,
            "realtime": -1.0,
            "max_memory": -1,
            "stdout": "",
            "stderr": "(error occured)"
        }

        return json.dumps(all_results, indent=2, ensure_ascii=False)
        


@BaseToolChain.register_toolchain("cpp")
class CppToolChain(BaseToolChain):
    def __init__(self, language, base_dir=None, timeout=10):
        super().__init__(language, base_dir, timeout)
        self.nlohmann_dir = os.path.join(self.solution_wrapper_dir, 'nlohmann')
        self.nlohmann_path = os.path.join(self.nlohmann_dir, 'json.hpp')
        self.tmp_nlohmann_dir = os.path.join(self.execute_dir, 'nlohmann')
        

    def compile(self):
        os.makedirs(self.tmp_nlohmann_dir, exist_ok=True)
        shutil.copy(self.nlohmann_path, self.tmp_nlohmann_dir)
        self.solution_wrapper = self._generate_solution_wrapper(self.testcase, self.solution_wrapper_path)

        with open(self.tmp_testcase_path, "w") as f:
            f.write(self.testcase)
        
        with open(self.tmp_solution_wrapper_path, "w") as f:
            f.writelines(self.solution_wrapper)
        
        with open(self.tmp_solution_path, "w") as f:
            f.write(self.solution_code)
        
        compile_command = self.compile_config["compile_command"].format(
            solution_wrapper_path = self.tmp_solution_wrapper_path,
            exe_path = self.tmp_exe_path
        )
        returncode, stdout, stderr = self.run_shell_command(compile_command, iscompile=True)
        return returncode, stdout, stderr

    def execute(self):
        execute_command = self.execute_config["execute_command"].format(
            exe_path = self.tmp_exe_path,
            solution_path=self.tmp_solution_path,
            testcase_path=self.tmp_testcase_path
        )
        returncode, stdout, stderr = self.run_shell_command(execute_command)
        return returncode, stdout, stderr

    def _generate_solution_wrapper(self, testcase, solution_wrapper_path):
        test_data = json.loads(testcase)
        first_case_key = next(iter(test_data))
        param_count = len(test_data[first_case_key]["input"])
        args_list = [f"args[{i}]" for i in range(param_count)]
        args_str = ", ".join(args_list)
        
        solution_wrapper_function = (
            f"auto solutionWrapper(json args){{\n"
            f"    return solution({args_str});\n"
            f"}}\n"
        )
        
        with open(solution_wrapper_path, "r") as f:
            solution_wrapper = f.readlines()
        
        solution_wrapper.insert(22, solution_wrapper_function)
        
        return solution_wrapper

@BaseToolChain.register_toolchain("java")
class JavaToolChain(BaseToolChain):
    def __init__(self, language, base_dir=None, timeout=10):
        super().__init__(language, base_dir, timeout)
        self.lib_dir = os.path.join(self.solution_wrapper_dir, self.compile_config['lib_dir_name'])
    
    def compile(self):
        shutil.copy(self.solution_wrapper_path, self.execute_dir)
        with open(self.tmp_solution_path, "w") as f:
            f.write(self.solution_code)
        with open(self.tmp_testcase_path, "w") as f:
            f.write(self.testcase)

        compile_command = self.compile_config["compile_command"].format(
            lib_dir=self.lib_dir,
            jackson_databind="jackson-databind-2.18.2.jar", # Jackson version is configurable.
            jackson_core="jackson-core-2.18.2.jar",
            jackson_annotations="jackson-annotations-2.18.2.jar",
            solution_wrapper_path=self.tmp_solution_wrapper_path,
            solution_path=self.tmp_solution_path
        )

        returncode, stdout, stderr = self.run_shell_command(compile_command, iscompile=True)
        return returncode, stdout, stderr

    def execute(self):
        execute_command = self.execute_config["execute_command"].format(
            lib_dir=self.lib_dir,
            execute_dir=self.execute_dir, # The directory path where Main.class is located. (not the file path)
            jackson_databind="jackson-databind-2.18.2.jar",
            jackson_core="jackson-core-2.18.2.jar",
            jackson_annotations="jackson-annotations-2.18.2.jar",
            exe_name=self.compile_config['exe_fname'],
            solution_path=self.tmp_solution_path,
            testcase_path=self.tmp_testcase_path
        )
        returncode, stdout, stderr = self.run_shell_command(execute_command)
        return returncode, stdout, stderr


@BaseToolChain.register_toolchain("javascript")
class JavaScriptChain(BaseToolChain):
    def __init__(self, language, base_dir=None, timeout=10):
        super().__init__(language, base_dir, timeout)

    def compile(self):
        shutil.copy(self.solution_wrapper_path, self.execute_dir)
        solution_wrapper_adder = self.solution_wrapper_dir+"/solution_adder.js"
        with open(solution_wrapper_adder, "r") as f:
            solution_wrapper_adder = f.read()
        
        self.solution_code += solution_wrapper_adder
        with open(self.tmp_solution_path, "w") as f:
            f.write(self.solution_code)
        with open(self.tmp_testcase_path, "w") as f:
            f.write(self.testcase)

        compile_command = self.compile_config["compile_command"].format(
            solution_path=self.tmp_solution_path
        )
        returncode, stdout, stderr = self.run_shell_command(compile_command, iscompile=True)
        return returncode, stdout, stderr

    def execute(self):
        execute_command = self.execute_config["execute_command"].format(
            exe_path=self.tmp_solution_wrapper_path,
            solution_path=self.tmp_solution_path,
            testcase_path=self.tmp_testcase_path
        )
        returncode, stdout, stderr = self.run_shell_command(execute_command)
        return returncode, stdout, stderr



@BaseToolChain.register_toolchain("python")
class PythonToolchain(BaseToolChain):
    def __init__(self, language, base_dir=None, timeout=10):
        super().__init__(language, base_dir, timeout)

    def compile(self):
        shutil.copy(self.solution_wrapper_path, self.execute_dir)
        with open(self.tmp_solution_path, "w") as f:
            f.write(self.solution_code)
        with open(self.tmp_testcase_path, "w") as f:
            f.write(self.testcase)

        compile_command = python_compile_config["compile_command"].format(
            solution_wrapper_path=self.tmp_solution_wrapper_path,
            solution_path = self.tmp_solution_path
        )
        returncode, stdout, stderr = self.run_shell_command(compile_command, iscompile=True)
        return returncode, stdout, stderr

    def execute(self):
        execute_command = self.execute_config["execute_command"].format(
            exe_path=self.tmp_exe_path,
            solution_path=self.tmp_solution_path,
            testcase_path=self.tmp_testcase_path
        )
        returncode, stdout, stderr = self.run_shell_command(execute_command)
        return returncode, stdout, stderr

