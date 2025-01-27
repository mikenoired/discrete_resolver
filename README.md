# Discrete Mathematics Expression Solver

A Python program that helps solve and analyze logical expressions in discrete mathematics. The program generates truth tables, provides step-by-step evaluations, and offers detailed explanations of logical operations using Google's Gemini AI.

## Features

- Support for multiple logical operators:
  - Конъюнкция (AND)
  - Дизъюнкция (OR)
  - Импликация (IMPLIES)
  - Отрицание (NOT)
  - Эквивалентность (EQUIV)
  - Исключающее или (XOR)
- Interactive command-line interface
- Truth table generation
- Step-by-step evaluation
- AI-powered explanations in Russian
- Results saved to file

## Requirements

- Python 3.6+
- Google Gemini API key

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

Run the program:
```bash
python main.py
```

Enter logical expressions using Russian operator names. For example:
```
((A конъюнкция B) дизъюнкция C) импликация B
```

The program will:
1. Generate a truth table
2. Show step-by-step evaluation
3. Provide a detailed explanation
4. Save the results to `result.md`

Type 'q' to quit the program.

## Example Output

The program generates:
- Truth tables showing all possible combinations of variables
- Intermediate calculation steps
- Detailed explanations of the logical operations
- Final conclusions about when the expression is true/false

## License

This project is open source and available under the MIT License.
