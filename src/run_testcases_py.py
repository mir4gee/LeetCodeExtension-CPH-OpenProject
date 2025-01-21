import os
import subprocess
import sys
import json

def run_python_test_cases(testcase_dir, python_path):
    if not os.path.isfile(python_path):
        return {"Error": f"Python file not found at {python_path}"}

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
                ['python3', python_path],
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

            print(f"Expected output: {expected_output}")
            print(f"Actual output: {stdout.strip()}")
            
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

    return results

def run_test_cases(testcase_dir, source_path):
    file_extension = os.path.splitext(source_path)[1].lower()
    
    if file_extension == '.py':
        return run_python_test_cases(testcase_dir, source_path)
    else:
        return {"Error": f"Unsupported file type: {file_extension}"}

def save_results_to_json(results, output_file):
    with open(output_file, "w") as json_file:
        json.dump(results, json_file, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_testcases.py <testcase_dir> <source_path>")
        sys.exit(1)

    testcase_dir = sys.argv[1]
    source_path = sys.argv[2]

    if not os.path.isdir(testcase_dir):
        print(f"Error: {testcase_dir} is not a valid directory.")
        sys.exit(1)

    if not os.path.isfile(source_path):
        print(f"Error: Source file not found at {source_path}")
        sys.exit(1)

    results = run_test_cases(testcase_dir, source_path)
    json_output_path = os.path.join(testcase_dir, "results.json")
    save_results_to_json(results, json_output_path)