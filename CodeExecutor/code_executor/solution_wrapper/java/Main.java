import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.ObjectWriter;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.nio.file.Files;
import java.nio.file.Paths;

public class Main {
    /**
     * CPU 시간을 읽어오기 위해 /proc/self/stat의 14번(utime), 15번(stime) 필드를 파싱합니다.
     *
     * @return long[]{utime, stime} (파싱 실패 시 {0,0})
     */
    private static long[] getCpuTimes() {
        try {
            // stat 파일 형식: man proc 참고
            // 예) pid (exe) R ... [13] utime, [14] stime, ...
            String statContent = new String(Files.readAllBytes(Paths.get("/proc/self/stat"))).trim();
            String[] tokens = statContent.split("\\s+");
            if (tokens.length < 15) {
                return new long[]{0, 0};
            }
            long utime = Long.parseLong(tokens[13]);
            long stime = Long.parseLong(tokens[14]);
            return new long[]{utime, stime};
        } catch (Exception e) {
            // Windows/Mac 등에서 /proc/self/stat을 접근 불가능할 때
            return new long[]{0, 0};
        }
    }

    /**
     * /proc/self/status에서 VmHWM(High Water Mark for memory)을 읽어 kB 단위로 반환합니다.
     *
     * @return VmHWM 값(kB), 실패 시 0
     */
    private static long getVmHWM() {
        try {
            for (String line : Files.readAllLines(Paths.get("/proc/self/status"))) {
                if (line.startsWith("VmHWM:")) {
                    // 예: "VmHWM:     123456 kB"
                    String[] parts = line.split("\\s+");
                    return Long.parseLong(parts[1]); // kB 단위
                }
            }
        } catch (Exception e) {
            // Windows/Mac 등에서 /proc/self/status 접근 불가능할 때
        }
        return 0;
    }

    /**
     * System.out의 출력 결과를 캡처하기 위한 유틸 클래스.
     * start()로 캡처 시작, stopAndGetOutput()으로 캡처 중지 및 결과 획득.
     */
    private static class StdoutCapture {
        private final PrintStream originalOut;
        private final ByteArrayOutputStream buffer;
        private final PrintStream captureStream;

        public StdoutCapture() {
            this.originalOut = System.out;
            this.buffer = new ByteArrayOutputStream();
            this.captureStream = new PrintStream(buffer);
        }

        public void start() {
            System.setOut(captureStream);
        }

        public String stopAndGetOutput() {
            System.setOut(originalOut);
            captureStream.flush();
            return buffer.toString();
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.out.println("Usage: java Main <solution_path> <testcase_path>");
            return;
        }
        
        String solutionPath = args[0];    // for debugging/logging
        String testcasePath = args[1];    // testcase JSON path
        
        // JSON 파일 로드
        ObjectMapper mapper = new ObjectMapper();
        JsonNode root = mapper.readTree(new File(testcasePath));
        
        // 실제 솔루션 클래스 & 인스턴스
        // (예: public class Solution { public Object solution(...) {...}} )
        Class<?> solutionClass = Solution.class; // Solution.class를 직정 참조
        Object solutionInstance = solutionClass.getDeclaredConstructor().newInstance();
        
        // 'solution'이라는 메서드를 리플렉션으로 찾는다
        Method solutionMethod = null;
        for (Method method : solutionClass.getMethods()) {
            if (method.getName().equals("solution")) {
                solutionMethod = method;
                break;
            }
        }
        if (solutionMethod == null) {
            throw new NoSuchMethodException("No solution method found in " + solutionPath);
        }
        
        int expectedParamCount = solutionMethod.getParameterCount();
        Class<?>[] parameterTypes = solutionMethod.getParameterTypes();

        // 최종 JSON 출력을 위해, 전체 결과를 누적할 맵
        Map<String, Map<String, Object>> allResults = new LinkedHashMap<>();
        
        // JSON 루트에서 각 테스트케이스를 순회
        Iterator<Map.Entry<String, JsonNode>> testCases = root.fields();
        while (testCases.hasNext()) {
            Map.Entry<String, JsonNode> entry = testCases.next();
            String testCaseKey = entry.getKey();
            JsonNode testCase = entry.getValue();
            JsonNode inputNode = testCase.get("input");
            
            // solutionMethod 파라미터에 맞춰 인자 배열 준비
            Object[] arguments = new Object[expectedParamCount];
            if (inputNode != null && inputNode.isArray()) {
                // input이 JSON 배열인 경우
                for (int i = 0; i < expectedParamCount && i < inputNode.size(); i++) {
                    JsonNode valueNode = inputNode.get(i);
                    arguments[i] = mapper.convertValue(valueNode, parameterTypes[i]);
                }
            } else {
                // input이 JSON 객체인 경우 -> values() 순회 등
                int i = 0;
                Iterator<JsonNode> elements = inputNode.elements();
                while (elements.hasNext() && i < expectedParamCount) {
                    JsonNode valueNode = elements.next();
                    arguments[i] = mapper.convertValue(valueNode, parameterTypes[i]);
                    i++;
                }
            }
            
            // 실행 전 자원 측정
            long[] cpuBefore = getCpuTimes();
            long vmHWMBefore = getVmHWM();
            long startTime = System.nanoTime();

            // 표준 출력 캡처
            StdoutCapture capture = new StdoutCapture();
            capture.start();

            Object result = null;
            String errorStackTrace = null;
            try {
                // 리플렉션으로 메서드 호출
                result = solutionMethod.invoke(solutionInstance, arguments);
            } catch (InvocationTargetException ite) {
                // solution 내부의 예외
                Throwable cause = ite.getCause();
                if (cause != null) {
                    StringWriter sw = new StringWriter();
                    cause.printStackTrace(new PrintWriter(sw));
                    errorStackTrace = sw.toString();
                } else {
                    errorStackTrace = ite.toString();
                }
            } catch (Exception e) {
                // 리플렉션 관련 예외
                StringWriter sw = new StringWriter();
                e.printStackTrace(new PrintWriter(sw));
                errorStackTrace = sw.toString();
            }

            // stdout 캡처 중지
            String capturedOutput = capture.stopAndGetOutput();

            // 실행 후 자원 측정
            long endTime = System.nanoTime();
            double elapsedSec = (endTime - startTime) / 1e9;
            long[] cpuAfter = getCpuTimes();
            long vmHWMAfter = getVmHWM();

            long usedUtime = cpuAfter[0] - cpuBefore[0];
            long usedStime = cpuAfter[1] - cpuBefore[1];
            long usedVmHWM = vmHWMAfter; // HWM은 누적 최대치이므로 단순 after만 표시

            // 결과 출력
            Map<String, Object> testCaseResult = new LinkedHashMap<>();
            testCaseResult.put("result", result); // 솔루션 결과(성공 시), 에러면 null
            testCaseResult.put("utime", usedUtime);
            testCaseResult.put("stime", usedStime);
            testCaseResult.put("realtime", Double.parseDouble(String.format("%.6f", elapsedSec)));
            testCaseResult.put("max_memory", usedVmHWM);
            testCaseResult.put("stdout", (capturedOutput != null) ? capturedOutput.trim() : "");
            testCaseResult.put("stderr", (errorStackTrace != null) ? errorStackTrace.trim() : null);

            allResults.put(testCaseKey, testCaseResult);
        }

        ObjectWriter writer = mapper.writer().withDefaultPrettyPrinter();
        String outputJson = writer.writeValueAsString(allResults);
        System.out.println(outputJson);
    }
}