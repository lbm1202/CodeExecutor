from .executor import CodeExecutor
from code_executor.configs.execute_config import EXECUTION_START_MESSAGE


r"""
▐▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▌
▐  ██████╗ ██████╗ ██████╗ ███████╗███████╗██╗  ██╗███████╗ ██████╗██╗   ██╗████████╗ ██████╗ ██████╗  ▌
▐ ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝╚██╗██╔╝██╔════╝██╔════╝██║   ██║╚══██╔══╝██╔═══██╗██╔══██╗ ▌
▐ ██║     ██║   ██║██║  ██║█████╗  █████╗   ╚███╔╝ █████╗  ██║     ██║   ██║   ██║   ██║   ██║██████╔╝ ▌
▐ ██║     ██║   ██║██║  ██║██╔══╝  ██╔══╝   ██╔██╗ ██╔══╝  ██║     ██║   ██║   ██║   ██║   ██║██╔══██╗ ▌
▐ ╚██████╗╚██████╔╝██████╔╝███████╗███████╗██╔╝ ██╗███████╗╚██████╗╚██████╔╝   ██║   ╚██████╔╝██║  ██║ ▌
▐  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝ ▌
▐▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▌
"""
__title__ = 'CodeExecutor'
__version__ = '1.0.0' # InitVersion
__author__ = ''                                                                                      


def test():
    testcase = """{
  "1": {
    "input": {
      "m": 1,
      "n": 2
    },
    "output": 3
  },
  "2": {
    "input": {
      "m": 3,
      "n": 4
    },
    "output": 7
  }
}"""
    cpp_code = """#include <vector>
using namespace std;
int solution(int a, int b) {
	return a+b;
}
"""
    java_code = """public class Solution {
    public int solution(int a, int b) {
        return a+b;
    }
}
"""
    python_code="""def solution(a, b):
    return a+b"""
    javascript_code="""function solution(a, b) {
	return a+b;
}"""
    print(EXECUTION_START_MESSAGE)
    print()
    code_executor = CodeExecutor(
        language="cpp",
        solution_code=cpp_code,
        testcase=testcase,
        base_dir='./'
    )
    _, _, stdout, stderr = code_executor.run()
    print("cpp")
    print(stdout)
    print("error")
    print(stderr)
    print()
    code_executor = CodeExecutor(
        language="java",
        solution_code=java_code,
        testcase=testcase,
        base_dir='./'
    )
    _, _, stdout, stderr = code_executor.run()
    print("java")
    print(stdout)
    print("error")
    print(stderr)
    print()
    code_executor = CodeExecutor(
        language="javascript",
        solution_code=javascript_code,
        testcase=testcase,
        base_dir='./'
    )
    _, _, stdout, stderr = code_executor.run()
    print("javascript")
    print(stdout)
    print("error")
    print(stderr)
    print()
    code_executor = CodeExecutor(
        language="python",
        solution_code=python_code,
        testcase=testcase,
        base_dir='./'
    )
    _, _, stdout, stderr = code_executor.run()
    print("python")
    print(stdout)
    print("error")
    print(stderr)
    print()
