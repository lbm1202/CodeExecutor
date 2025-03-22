import sys
import json
import importlib.util
import io
import contextlib
import traceback
import time

def get_cpu_times():
    """
    /proc/self/stat에서 utime(14번째 필드), stime(15번째 필드)를 읽어서 반환.
    """
    with open("/proc/self/stat", "r", encoding="utf-8") as f:
        data = f.read().split()
        # /proc/[pid]/stat 파일 형식 (참고: man proc)
        # data[13] -> utime
        # data[14] -> stime
        utime = int(data[13])
        stime = int(data[14])
    return utime, stime

def get_vmhwm():
    """
    /proc/self/status에서 VmHWM 값을 찾아 정수로 반환.
    """
    vmhwm = 0
    with open("/proc/self/status", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("VmHWM:"):
                # 형식: VmHWM:   123456 kB
                parts = line.split()
                vmhwm = int(parts[1])  # kB 단위
                break
    return vmhwm

def run_solution(solution_func, *args):
    """
    solution 함수를 실행하면서 stdout을 캡쳐하고,
    에러가 발생하면 에러 메시지도 캡쳐한다.
    (result, stdout_output, error_msg)를 튜플로 반환한다.
    """
    captured_output = io.StringIO()
    error_msg = None
    result = None
    
    try:
        with contextlib.redirect_stdout(captured_output):
            result = solution_func(*args)
    except Exception as e:
        # 에러 발생 시 traceback 캡쳐
        error_msg = traceback.format_exc()
    
    output_str = captured_output.getvalue()
    return result, output_str, error_msg

def main():
    if len(sys.argv) < 3:
        print("Usage: python <script> <solution_path> <testcase_path>")
        sys.exit(1)
    
    solution_path = sys.argv[1]
    testcase_path = sys.argv[2]
    
    # solution.py 모듈 동적 로드
    spec = importlib.util.spec_from_file_location("Solution", solution_path)
    solution_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(solution_module)
    solution = solution_module.solution
    
    # 테스트케이스 로드
    with open(testcase_path, "r", encoding="utf-8") as f:
        root = json.load(f)
    
    # 결과가 담길 배열 생성
    all_results = {}

    # 각 테스트케이스에 대해 실행
    for test_case_key, test_case in root.items():
        input_data = test_case["input"]
        input_values = list(input_data.values())
        
        # 실행 전 자원 측정
        utime_before, stime_before = get_cpu_times()
        vmhwm_before = get_vmhwm()
        
        # 실제 시간 측정(시작)
        start_time = time.perf_counter()
        
        # solution 실행(출력/에러 캡쳐)
        result, captured_stdout, error_msg = run_solution(solution, *input_values)
        
        # 실제 시간 측정(종료)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        
        # 실행 후 자원 측정
        utime_after, stime_after = get_cpu_times()
        vmhwm_after = get_vmhwm()
        
        # CPU 시간 사용량 계산 (tick 단위)
        used_utime = utime_after - utime_before
        used_stime = stime_after - stime_before
        
        # VmHWM은 프로세스 전체 생애에서 "최대 사용량"의 누적 기록
        # 테스트케이스 단위로는 단순 참고로 after 값만 출력(혹은 diff 확인)
        used_vmhwm = vmhwm_after

        all_results[test_case_key] = {
            "result": result,
            "utime": used_utime,
            "stime": used_stime,
            "realtime": float(f"{elapsed_time:.6f}"),
            "max_memory": used_vmhwm,
            "stdout": captured_stdout.strip() if captured_stdout else captured_stdout,
            "stderr": error_msg.strip() if error_msg else error_msg
        }
    # 모든 테스트케이스 한번에 출력    
    print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()