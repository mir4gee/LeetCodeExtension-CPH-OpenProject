import os
import subprocess
import sys
import json

def compile_cpp(cpp_path, output_path):
    try:
        compile_result = subprocess.run(
            ['g++', cpp_path, '-o', output_path],
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            return False, f"Compilation failed: {compile_result.stderr}"
        return True, ""
    except Exception as e:
        return False, f"Compilation error: {str(e)}"

def run_test_cases(testcase_dir, cpp_path):
    executable_path = os.path.join(testcase_dir, 'solution')
    
    success, error_msg = compile_cpp(cpp_path, executable_path)
    if not success:
        return {"Compilation": error_msg}

    input_files = sorted([f for f in os.listdir(testcase_dir) if f.startswith("input_") and f.endswith(".txt")])
    output_files = sorted([f for f in os.listdir(testcase_dir) if f.startswith("output_") and f.endswith(".txt")])

    if not input_files or not output_files:
        return {"Error": "No input or output files found in the test cases directory."}

    if len(input_files) != len(output_files):
        return {"Error": "The number of input files does not match the number of output files."}

    results = {}

    for index, input_file in enumerate(input_files):
        input_path = os.path.join(testcase_dir, input_file)
        expected_output_path = os.path.join(testcase_dir, f"output_{index + 1}.txt")
        temp_output_path = os.path.join(testcase_dir, f"temp_output_{index + 1}.txt")

        try:
            with open(input_path, "r") as infile:
                input_data = infile.read()

            process = subprocess.Popen(
                [executable_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=input_data)

            if process.returncode != 0:
                results[f"Testcase {index + 1}"] = f"Runtime Error: {stderr.strip()}"
                continue

            with open(temp_output_path, "w") as temp_outfile:
                temp_outfile.write(stdout.strip())

            with open(expected_output_path, "r") as expected_outfile:
                expected_output = expected_outfile.read().strip()

            print(expected_output)
            print(stdout.strip())
            if stdout.strip() == expected_output:
                results[f"Testcase {index + 1}"] = "Passed"
            else:
                results[f"Testcase {index + 1}"] = "Failed"
                results[f"Testcase {index + 1} Details"] = {
                    "Expected": expected_output,
                    "Got": stdout.strip()
                }

        except Exception as e:
            results[f"Testcase {index + 1}"] = f"Error: {str(e)}"

    try:
        if os.path.exists(executable_path):
            os.remove(executable_path)
    except Exception as e:
        print(f"Warning: Failed to remove executable: {e}")

    return results

def save_results_to_json(results, output_file):
 
    with open(output_file, "w") as json_file:
        json.dump(results, json_file, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_testcases.py <testcase_dir> <cpp_path>")
        sys.exit(1)

    testcase_dir = sys.argv[1]
    cpp_path = sys.argv[2]

    if not os.path.isdir(testcase_dir):
        print(f"Error: {testcase_dir} is not a valid directory.")
        sys.exit(1)

    if not os.path.isfile(cpp_path):
        print(f"Error: C++ file not found at {cpp_path}")
        sys.exit(1)

    results = run_test_cases(testcase_dir, cpp_path)
    json_output_path = os.path.join(testcase_dir, "results.json")
    save_results_to_json(results, json_output_path)