import os, shutil


class CleanupPolicy:
    NONE = "none"
    HASH_ONLY = "hash"
    SAFE_ALL = "all"


class DirectoryManager:
    def __init__(self, execute_dir, cleanup_policy=CleanupPolicy.NONE):
        self.execute_dir = execute_dir
        self.cleanup_policy = cleanup_policy

    def __enter__(self):
        os.makedirs(self.execute_dir, exist_ok=True)
        #print(f"\nDirectories created: {self.execute_dir}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.cleanup_policy == CleanupPolicy.NONE:
            pass

        elif self.cleanup_policy == CleanupPolicy.HASH_ONLY:
            shutil.rmtree(self.execute_dir, ignore_errors=True)

        elif self.cleanup_policy == CleanupPolicy.SAFE_ALL:
            shutil.rmtree(self.execute_dir, ignore_errors=True)
            #print(f"Directories removed: {self.execute_dir}")
            
            execute_parent = os.path.dirname(self.execute_dir)
            try: # 상위 디렉토리가 빈 경우에만 제거 시도 (예: run, submit 디렉토리)
                os.rmdir(execute_parent)
                #print(f"Removed parent directory: {execute_parent}")
            except Exception:
                pass

            