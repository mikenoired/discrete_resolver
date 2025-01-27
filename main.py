import os
import google.generativeai as genai
from dotenv import load_dotenv
import itertools
from typing import List, Dict, Callable
from tabulate import tabulate
import sys
import threading
import time

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)


def conjunction(a: bool, b: bool) -> bool:
    return a and b


def disjunction(a: bool, b: bool) -> bool:
    return a or b


def implication(a: bool, b: bool) -> bool:
    return (not a) or b


def negation(a: bool) -> bool:
    return not a


def equivalence(a: bool, b: bool) -> bool:
    return a == b


def exclusive_or(a: bool, b: bool) -> bool:
    return a != b


def parse_expression(expression: str) -> str:
    replacements = {
        'конъюнкция': 'AND',
        'дизъюнкция': 'OR',
        'импликация': 'IMPLIES',
        'отрицание': 'NOT',
        'эквивалентность': 'EQUIV',
        'исключающее или': 'XOR'
    }
    parsed_expr = expression
    for rus, eng in replacements.items():
        parsed_expr = parsed_expr.replace(rus, f" {eng} ")
    return parsed_expr


def get_variables(expression: str) -> List[str]:
    replacements = {
        'конъюнкция': ' ',
        'дизъюнкция': ' ',
        'импликация': ' ',
        'отрицание': ' ',
        'эквивалентность': ' ',
        'исключающее или': ' '
    }
    cleaned_expr = expression
    for rus, eng in replacements.items():
        cleaned_expr = cleaned_expr.replace(rus, eng)

    # Now extract only Latin letters as variables
    return sorted(set(c for c in cleaned_expr if c.isalpha() and c.isascii()))


def evaluate_step(expression: str, values: Dict[str, bool]) -> tuple[bool, List[tuple[str, bool]]]:
    expr = parse_expression(expression)
    operations = {
        'AND': conjunction,
        'OR': disjunction,
        'IMPLIES': implication,
        'NOT': negation,
        'EQUIV': equivalence,
        'XOR': exclusive_or
    }

    stack = []
    value_stack = []
    steps = []
    tokens = expr.replace('(', ' ( ').replace(')', ' ) ').split()

    for token in tokens:
        if token == '(':
            continue
        elif token == ')':
            if len(stack) >= 3:
                operand2 = stack.pop()
                operator = stack.pop()
                operand1 = stack.pop()

                val2 = value_stack.pop()
                operator_name = value_stack.pop()
                val1 = value_stack.pop()

                if operator in operations:
                    result = operations[operator](operand1, operand2)
                    step_expr = f"({val1} {operator} {val2})"
                    stack.append(result)
                    value_stack.append(step_expr)
                    steps.append((step_expr, result))
            elif len(stack) >= 2 and stack[-2] == 'NOT':
                operand = stack.pop()
                operator = stack.pop()
                val = value_stack.pop()
                value_stack.pop()
                result = operations[operator](operand)
                step_expr = f"NOT({val})"
                stack.append(result)
                value_stack.append(step_expr)
                steps.append((step_expr, result))
        elif token in operations:
            stack.append(token)
            value_stack.append(token)
        else:
            if token not in values:
                raise ValueError(f"Undefined variable: {token}")
            stack.append(values[token])
            value_stack.append(token)

    while len(stack) >= 3:
        operand2 = stack.pop()
        operator = stack.pop()
        operand1 = stack.pop()

        val2 = value_stack.pop()
        operator_name = value_stack.pop()
        val1 = value_stack.pop()

        if operator in operations:
            result = operations[operator](operand1, operand2)
            step_expr = f"({val1} {operator} {val2})"
            stack.append(result)
            value_stack.append(step_expr)
            steps.append((step_expr, result))

    return stack[0], steps


def generate_truth_table(expression: str) -> str:
    variables = get_variables(expression)
    combinations = list(itertools.product(
        [True, False], repeat=len(variables)))

    first_values = dict(zip(variables, combinations[0]))
    _, steps = evaluate_step(expression, first_values)

    step_headers = []
    for i, (expr, _) in enumerate(steps, 1):
        latex_expr = expr
        for eng, latex in {
            'AND': r'\land',
            'OR': r'\lor',
            'IMPLIES': r'\rightarrow',
            'NOT': r'\neg',
            'EQUIV': r'\leftrightarrow',
            'XOR': r'\oplus'
        }.items():
            latex_expr = latex_expr.replace(eng, latex)
        step_headers.append(f"Шаг {i} (${latex_expr}$)")

    headers = variables + step_headers

    # Create markdown table header
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "|" + "|".join([":-:"] * len(headers)) + "|\n"

    for combo in combinations:
        values = dict(zip(variables, combo))
        try:
            _, step_results = evaluate_step(expression, values)
            row = ['1' if values[var] else '0' for var in variables]
            for i in range(len(step_headers)):
                if i < len(step_results):
                    row.append('1' if step_results[i][1] else '0')
                else:
                    row.append('0')
            markdown_table += "| " + " | ".join(row) + " |\n"
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"

    return markdown_table


def generate_solution_description(expression: str, table: str, steps: str) -> str:
    """Generate a detailed explanation of the solution using Gemini."""
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""As a discrete mathematics expert, explain the following logical expression and its solution:

Expression: {expression}

Truth Table:
{table}

Step-by-step evaluation:
{steps}

Please provide:
1. A brief explanation of what the expression means
2. How to read and interpret the truth table
3. An explanation of each step in the evaluation process
4. The final conclusion about when the expression is true/false

Keep the explanation clear and concise. Don't use markdown characters and use only Russian language for explanation."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate explanation: {str(e)}"


class Loader:
    def __init__(self, desc="Loading..."):
        self.desc = desc
        self.done = False
        self.spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_thread = threading.Thread(target=self._spin)

    def _spin(self):
        while not self.done:
            for char in self.spinner:
                sys.stdout.write(f'\r{char} {self.desc}')
                sys.stdout.flush()
                time.sleep(0.1)
                if self.done:
                    break

    def __enter__(self):
        self.spinner_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.done = True
        self.spinner_thread.join()
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()


def to_latex(expression: str) -> str:
    """Convert logical expression to LaTeX format."""
    replacements = {
        'конъюнкция': r'\land',
        'дизъюнкция': r'\lor',
        'импликация': r'\rightarrow',
        'отрицание': r'\neg',
        'эквивалентность': r'\leftrightarrow',
        'исключающее или': r'\oplus'
    }
    latex_expr = expression
    for rus, latex in replacements.items():
        latex_expr = latex_expr.replace(rus, latex)
    return latex_expr


def solve_discrete_math(expression: str) -> str:
    """Solve discrete mathematics expression and return truth table with steps and explanation"""
    try:
        with Loader("Generating solution..."):
            table = generate_truth_table(expression)
            explanation = generate_solution_description(expression, table, "")
            latex_expression = to_latex(expression)
            markdown_result = f"""# Решение дискретной математики

## Выражение
$${latex_expression}$$

## Таблица истинности и шаги решения
{table}

## Объяснение
{explanation}
"""
            # Save to markdown file
            with open('result.md', 'w', encoding='utf-8') as f:
                f.write(markdown_result)
            return markdown_result
    except Exception as e:
        return f"Error solving expression: {str(e)}"


def main():
    print("Discrete Mathematics Expression Solver")
    print("\nAvailable operators:")
    print("- конъюнкция (AND)")
    print("- дизъюнкция (OR)")
    print("- импликация (IMPLIES)")
    print("- отрицание (NOT)")
    print("- эквивалентность (EQUIV)")
    print("- исключающее или (XOR)")
    print("\nExample: ((A конъюнкция B) дизъюнкция C) импликация B")

    while True:
        expression = input("\nEnter logical expression (or 'q' to quit): ")
        if expression.lower() == 'q':
            break

        result = solve_discrete_math(expression)
        print("\nResult:")
        print(result)
        print(f"\nResult has been saved to 'result.md'")


if __name__ == "__main__":
    main()
