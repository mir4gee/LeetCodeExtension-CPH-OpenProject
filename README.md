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

## Known Issues

- Large input test cases might cause slight delays in test execution
- Some complex test cases might require manual formatting
- Web scraping might fail if LeetCode changes their HTML structure

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LeetCode for providing the problem database
- VS Code Extension API documentation
- Contributors and users who provide feedback

## Support

If you encounter any issues or have suggestions:
1. Check the [Known Issues](#known-issues) section
2. Open an issue in the GitHub repository
3. Provide detailed information about the problem and steps to reproduce

## Future Enhancements

- [ ] Add support for more programming languages
- [ ] Implement problem difficulty filtering
- [ ] Add code snippets for common algorithms
- [ ] Integrate with LeetCode account
- [ ] Add solution submission functionality
- [ ] Implement problem search and filtering