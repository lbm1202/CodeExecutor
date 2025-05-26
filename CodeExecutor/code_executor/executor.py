import json
from code_executor.toolchain import BaseToolChain
from code_executor.directory_manager import DirectoryManager, CleanupPolicy

# CleanupPolicy options:
# - NONE: no cleanup performed.
# - HASH_ONLY: only perform hash-based cleanup.
# - SAFE_ALL: perform all safe cleanups.

#test
class CodeExecutor:
    def __init__(self, language, solution_code, testcase, base_dir=None, timeout=10, cleanup_policy=CleanupPolicy.NONE):
        self.toolchain = BaseToolChain.create(language, base_dir, timeout)
        self.cleanup_policy = cleanup_policy
        self.toolchain.timeout = timeout
        self.toolchain.solution_code = solution_code
        # print("1:", test_case)
        # print("2:", json.dumps(test_case))
        # print("======")
        if isinstance(testcase, str):
            self.toolchain.testcase = testcase
        else:
            self.toolchain.testcase = json.dumps(testcase)

    def compile(self):
        self.toolchain.compile()
    
    def execute(self):
        self.toolchain.execute()

    def run(self):
        with DirectoryManager(self.toolchain.execute_dir,
                              cleanup_policy=self.cleanup_policy):
            return self.toolchain.run()
