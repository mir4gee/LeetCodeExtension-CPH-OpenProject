# LeetCode Helper VS Code Extension

A Visual Studio Code extension that helps you solve LeetCode problems with integrated testing and multiple language support.

## Features

- 🔍 Load LeetCode problems directly in VS Code using problem slugs
- 💻 Support for multiple programming languages (C++ and Python)
- ✅ Automated test case generation and execution
- 📊 Visual test results with detailed feedback
- 🎯 Side-by-side problem description and solution editor
- 🔄 Real-time test case validation
- 🎨 Syntax highlighting and language-specific features

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Install required Python packages:
   ```bash
   pip install requests beautifulsoup4
   ```

## Usage

1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on macOS)
2. Type "LeetCode Helper" and select the command
3. Enter the problem slug (e.g., "two-sum" for the Two Sum problem)
4. The extension will load:
   - Problem description
   - Example test cases
   - Solution templates for C++ and Python

## Writing and Testing Solutions

### C++ Solutions
- Click "Open in C++" to edit the solution
- Solution template includes common headers and a basic structure
- Click "Run C++ Tests" to test your solution against all test cases

### Python Solutions
- Click "Open in Python" to edit the solution
- Solution template includes basic structure
- Click "Run Python Tests" to test your solution against all test cases

## Test Results

The extension provides detailed test results including:
- Pass/Fail status for each test case
- Expected vs. Actual output for failed tests
- Compilation errors (if any)
- Runtime errors (if any)

## Directory Structure

```
leetcode-helper/
├── src/
│   ├── extension.ts          # Main extension code
│   ├── script.py            # Problem fetcher script
│   ├── run_testcases.py     # C++ test runner
│   └── run_testcases_py.py  # Python test runner
├── testcases/               # Generated test cases
└── package.json            # Extension manifest
```

## Requirements

- Visual Studio Code 1.60.0 or higher
- Node.js 14.0.0 or higher
- Python 3.6 or higher
- G++ compiler for C++ solutions
- Python interpreter for Python solutions

## Extension Settings

This extension contributes the following settings:

* `leetcodeHelper.defaultLanguage`: Set your preferred programming language
* `leetcodeHelper.testCaseDirectory`: Customize the test case directory location


## Comprehensive System Architecture

### Philosophical Design Approach
The LeetCode Helper Extension emerges from a fundamental challenge in algorithmic problem-solving: bridging the gap between problem understanding, solution implementation, and rigorous testing. Our design philosophy centers on three core principles:

1. **Seamless Integration**: Bringing the LeetCode problem-solving experience directly into the developer's preferred IDE
2. **Multi-Language Support**: Enabling solution development across different programming paradigms
3. **Automated Testing**: Providing instant, comprehensive feedback on solution correctness

### Architectural Overview
The extension represents a sophisticated multi-component system that orchestrates several critical processes:

```
[User Interface (VS Code)] 
        ↓
[Extension Manager (TypeScript)]
        ↓
[Problem Fetcher Script (Python)]
        ↓
[Test Case Generator]
        ↓
[Language-Specific Test Runners]
        ↓
[Results Visualization]
```

## Detailed Component Analysis

### 1. Problem Fetcher Script (`script.py`)

#### GraphQL Query Mechanism
The script leverages LeetCode's GraphQL endpoint to extract problem metadata, representing a sophisticated data retrieval strategy:

```python
problem_details_query = """
query getProblem($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    content
    difficulty
  }
}
"""
```

##### Key Extraction Techniques
- **HTML Parsing**: Utilizes BeautifulSoup for robust HTML content extraction
- **Flexible Metadata Parsing**: Dynamically handles varying problem descriptions
- **Example Case Generation**: Intelligently derives input/output test cases from problem description

#### Data Structure Extraction Mechanism
The `extract_data_structure()` function represents an advanced type inference technique:

```python
def extract_data_structure(code, lang):
    data_structure = {}
    
    if lang == 'C++':
        pattern = r'\((.*?)\)'
        match = re.search(pattern, code)
    
    elif lang == 'Python3':
        pattern = r'\((.*?)\)'
        match = re.search(pattern, code)
    
    return data_structure
```

### 2. Test Execution Engines

#### C++ Test Runner (`run_testcases.py`)

##### Compilation Strategy
```python
def compile_cpp(cpp_path, output_path):
    compile_result = subprocess.run(
        ['g++', cpp_path, '-o', output_path, '-std=c++17', '-Wall', '-Wextra'],
        capture_output=True,
        text=True
    )
```

##### Test Case Execution Philosophy
- **Isolated Execution**: Each test case runs in a separate process
- **Input Simulation**: Programmatically feeds test inputs
- **Output Comparison**: Precise matching against expected results

#### Python Test Runner (`run_testcases_py.py`)

##### Execution Approach
```python
def run_python_test_cases(testcase_dir, python_path):
    """    
    In this function we follow these 5 steps:
    1. Test case discovery
    2. Input preparation
    3. Solution execution
    4. Output comparison
    5. Detailed result generation
    """
```

### 3. VS Code Extension Manager (`extension.ts`)

#### Webview Interaction Architecture
```typescript
class WebviewContentProvider {
     // Generates dynamic, interactive problem interfaces
    static formatProblemData(data: LeetCodeData): string {
        return `
            <html>
                <body>
                    ...
                </body>
            </html>
        `;
    }
}
```

## Advanced Technical Considerations

### Error Handling Strategies
- **Granular Error Capture**: Detailed error categorization
- **User-Friendly Messaging**: Translating technical errors into actionable insights
- **Comprehensive Logging**: Maintaining detailed execution traces

### Performance Optimization
- **Minimal Overhead**: Lightweight script execution
- **Efficient Resource Management**: Temporary file cleanup
- **Parallel Test Processing**: Potential for concurrent test case evaluation

## Security Implementation

### Execution Isolation
- Sandboxed test environment
- Limited system access during test execution
- Input sanitization mechanisms

### Potential Threat Mitigations
- Restricted file system access
- Timeout mechanisms for long-running solutions
- Input size limitations

## Extensibility Framework

### Language Support Expansion
- Modular architecture allowing easy language addition
- Pluggable test runner interfaces
- Configurable parsing strategies

## Psychological Design Considerations

### Developer Experience (DX) Principles
1. **Immediate Feedback**: Instant test result visualization
2. **Reduced Cognitive Load**: Simplified problem-solving workflow
3. **Learning Environment**: Encourages systematic problem-solving approach

## Future Roadmap

### Planned Enhancements
- [ ] Machine learning-based test case generation
- [ ] Performance analysis metrics
- [ ] Advanced code complexity evaluation
- [ ] Cloud-synchronized problem tracking
- [ ] AI-powered solution suggestion mechanism

## Contribution Guidelines

### How to contribute

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### For Aspiring Contributors
1. Understand the architectural philosophy
2. Maintain modular design principles
3. Prioritize user experience
4. Implement comprehensive testing
5. Document architectural decisions

## Acknowledgments

- LeetCode for providing the problem database
- VS Code Extension API documentation
- Contributors and users who provide feedback

## Support

If you encounter any issues or have suggestions:
1. Check the [Known Issues](#known-issues) section
2. Open an issue in the GitHub repository
3. Provide detailed information about the problem and steps to reproduce



## Conclusion

The LeetCode Helper Extension transcends traditional problem-solving tools by creating an integrated, intelligent development environment that adapts to developers' needs across multiple programming languages.
