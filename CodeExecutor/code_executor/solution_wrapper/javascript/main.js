// index.js
const fs = require('fs');
const path = require('path');

function getCpuTimes() {
  /**
   * /proc/self/stat에서 14번째(utime), 15번째(stime) 필드 추출
   * (참고: man proc -> /proc/[pid]/stat)
   */
  try {
    const statContent = fs.readFileSync("/proc/self/stat", "utf8").trim();
    const tokens = statContent.split(' ');
    if (tokens.length < 15) {
      return [0, 0];
    }
    // 0-based 인덱스이므로 [13] -> utime, [14] -> stime
    const utime = parseInt(tokens[13], 10);
    const stime = parseInt(tokens[14], 10);
    return [utime, stime];
  } catch (err) {
    // /proc/self/stat 파일을 읽을 수 없는 환경(Windows 등)에서는 0 리턴
    return [0, 0];
  }
}

function getVmHWM() {
  /**
   * /proc/self/status에서 VmHWM를 찾아 kB 단위 정수로 반환
   */
  try {
    const statusContent = fs.readFileSync("/proc/self/status", "utf8");
    const lines = statusContent.split('\n');
    for (const line of lines) {
      if (line.startsWith("VmHWM:")) {
        // 라인 예) "VmHWM:	   123456 kB"
        const parts = line.split(/\s+/);
        // parts[0] = "VmHWM:", parts[1] = "123456", parts[2] = "kB"
        return parseInt(parts[1], 10);
      }
    }
    return 0;
  } catch (err) {
    // /proc/self/status 파일을 읽을 수 없는 환경(Windows 등)에서는 0 리턴
    return 0;
  }
}

/**
 * @param {Function} fn - 실행할 함수
 * @param  {...any} args - 해당 함수에 넘길 인자
 * @returns {{ result?: any, stdout: string, error?: any }}
 *   - result: fn(*args) 결과값 (정상 실행 시)
 *   - stdout: fn 실행 중 console.log로 출력된 문자열(누적)
 *   - error: 에러 메시지 / 스택 트레이스 (에러 발생 시)
 */
function runWithCapturedStdout(fn, ...args) {
  const originalLog = console.log;

  let stdoutCapture = "";
  console.log = (...logArgs) => {
    // logArgs를 문자열로 합쳐서 저장
    stdoutCapture += logArgs.join(' ') + '\n';
  };

  let result = null;
  let error = null;
  try {
    result = fn(...args);
  } catch (err) {
    error = err.stack || err.message || String(err);
  } finally {
    console.log = originalLog;
  }

  return { result, stdout: stdoutCapture, error };
}

// ----------------------------------------------------------------------------
// CLI 인자 체크
if (process.argv.length < 4) {
  console.error("Usage: node index.js <solution_path> <testcase_path>");
  process.exit(1);
}

const solutionPath = process.argv[2];
const testcasePath = process.argv[3];


// 솔루션 모듈 로드
const solutionModule = require(path.resolve(solutionPath));
// solution이 함수 자체로 export 되었는지, 혹은 { solution: function } 형태인지 확인
const solution = (typeof solutionModule === 'function')
  ? solutionModule
  : solutionModule.solution;

if (typeof solution !== 'function') {
  console.error("No valid solution function found in", solutionPath);
  process.exit(1);
}

// 테스트케이스 로드
let testData;
try {
  testData = JSON.parse(fs.readFileSync(testcasePath, 'utf8'));
} catch (err) {
  console.error("Failed to open or parse testcase file:", testcasePath, err);
  process.exit(1);
}

// 각 테스트케이스 실행
const all_results = {}
for (const [testCaseKey, testCase] of Object.entries(testData)) {
  const input = testCase.input;
  // input이 객체 형태라고 가정 -> values를 array로 변환
  const inputValues = Object.values(input);

  // 실행 전
  const [utimeBefore, stimeBefore] = getCpuTimes();
  const vmhwmBefore = getVmHWM();
  const startTime = process.hrtime.bigint(); // 나노초 단위

  // solution 실행, stdout/에러 캡쳐
  const { result, stdout, error } = runWithCapturedStdout(solution, ...inputValues);

  // 실행 후
  const endTime = process.hrtime.bigint();
  const elapsedNs = endTime - startTime;
  const elapsedSec = Number(elapsedNs) / 1e9;

  const [utimeAfter, stimeAfter] = getCpuTimes();
  const vmhwmAfter = getVmHWM();

  const usedUtime = utimeAfter - utimeBefore;
  const usedStime = stimeAfter - stimeBefore;
  const usedVmHWM = vmhwmAfter; // HWM은 누적 최대치이므로 after 값만 표시

  all_results[testCaseKey] = {
    "result": result,
    "utime": usedUtime,
    "stime": usedStime,
    "realtime": parseFloat(elapsedSec.toFixed(6)),
    "max_memory": usedVmHWM,
    "stdout": stdout ? stdout.trim() : stdout,
    "stderr": error ? error.trim() : error
  }
}
console.log(JSON.stringify(all_results, null, 2));