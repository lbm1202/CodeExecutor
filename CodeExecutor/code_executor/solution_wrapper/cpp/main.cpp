#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <tuple>
#include <stdexcept>
#include <string>
#include <map>
#include <chrono>
#include <thread>
#include <csignal>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>
#include "nlohmann/json.hpp"
#include "solution.cpp"  // 실제로는 컴파일 시점에 포함된다고 가정

using json = nlohmann::ordered_json;
using namespace std;








void handleSIGFPE(int signum) {
    std::cerr << "Caught SIGFPE ";
    
    //std::exit(EXIT_FAILURE);
}

std::tuple<long, long> get_cpu_times() {
    ifstream statFile("/proc/self/stat");
    if(!statFile.is_open()) {
        return {0, 0};
    }
    string content;
    getline(statFile, content);

    vector<string> tokens;
    {
        istringstream iss(content);
        string token;
        while (iss >> token) {
            tokens.push_back(token);
        }
    }
    // 최소 15개 이상의 필드가 있어야 utime, stime을 파싱할 수 있음
    if (tokens.size() < 15) {
        return {0, 0};
    }

    // tokens[13] -> utime, tokens[14] -> stime
    long utime = stol(tokens[13]);
    long stime = stol(tokens[14]);
    return {utime, stime};
}

long get_vmhwm() {
    ifstream statusFile("/proc/self/status");
    if(!statusFile.is_open()) {
        return 0;
    }
    string line;
    while(getline(statusFile, line)) {
        // "VmHWM:"으로 시작하는 라인 찾기
        if(line.rfind("VmHWM:", 0) == 0) {
            // 예시: "VmHWM:     123456 kB"
            istringstream iss(line);
            string label;
            long value;
            string unit;
            iss >> label >> value >> unit; // label="VmHWM:", value=..., unit="kB"
            return value;
        }
    }
    return 0;
}

int main(int argc, char* argv[]) {
    if(argc < 3) {
        cout << "Usage: " << argv[0] << " <solution_path> <testcase_path>" << endl;
        return 1;
    }
    //std::signal(SIGFPE, handleSIGFPE);
    string solutionPath = argv[1];
    string testcasePath = argv[2];
    
    ifstream testFile(testcasePath);
    if(!testFile) {
        cerr << "Failed to open testcase file: " << testcasePath << endl;
        return 1;
    }
    
    json testCases;
    testFile >> testCases;
    
    // 최종 결과 저장 변수 선언
    json allResults = json::object();

    // 각 테스트 케이스별로 실행
    for(auto& [testCaseKey, testCase] : testCases.items()) {
        if(!testCase.contains("input")) {
            cerr << "Test case " << testCaseKey << " does not contain 'input' field." << endl;
            continue;
        }
        // 입력 구성
        json inputData = testCase["input"];
        json inputValues = json::array();
        for (auto& item : inputData.items()) {
            inputValues.push_back(item.value());
        }

        // 실행 전 리소스 측정
        auto [utime_before, stime_before] = get_cpu_times();
        auto start = chrono::high_resolution_clock::now();

        bool success = true;
        string errorMessage;
        json result;
        string capturedOutput;
        
        try {
            // stdout 캡처를 위한 버퍼 교체
            std::stringstream buffer;
            auto old_buf = std::cout.rdbuf(buffer.rdbuf());
            
            // solutionWrapper 실행
            result = solutionWrapper(inputValues);
            
            // stdout 원복
            std::cout.rdbuf(old_buf);
            capturedOutput = buffer.str();
        } catch (const exception e) {
            // 예외 발생 시
            success = false;
            errorMessage = e.what();
        } catch (...) {
            // 알 수 없는 예외
            success = false;
            errorMessage = "Unknown error occurred";
        }

        // 실행 후 리소스 측정
        auto end = chrono::high_resolution_clock::now();
        double elapsed_sec = chrono::duration<double>(end - start).count();
        
        auto [utime_after, stime_after] = get_cpu_times();
        long vmhwm_after = get_vmhwm();

        // CPU 시간 사용량(utime, stime)은 tick 단위
        long used_utime = utime_after - utime_before;
        long used_stime = stime_after - stime_before;

        // VmHWM(HWM은 누적 최대치)
        long used_vmhwm = vmhwm_after; 
    
        json singleTC;
        singleTC["result"]     = result;
        singleTC["utime"]      = used_utime;
        singleTC["stime"]      = used_stime;
        singleTC["realtime"]   = elapsed_sec;
        singleTC["max_memory"] = used_vmhwm;
        singleTC["stdout"]     = !capturedOutput.empty() ? capturedOutput : "";
        singleTC["stderr"]     = !success ? json(errorMessage) : json(nullptr);

        // testCaseKey별로 결과를 allResults에 저장
        allResults[testCaseKey] = singleTC;
    }

    std::cout << allResults.dump(2) << std::endl;

    return 0;
}