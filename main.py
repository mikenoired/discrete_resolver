import os
import google.generativeai as genai
from dotenv import load_dotenv
import itertools
from typing import List, Dict, Callable
from tabulate import tabulate

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
    """Generate a truth table for the given expression with intermediate steps"""
    variables = get_variables(expression)
    combinations = list(itertools.product(
        [True, False], repeat=len(variables)))

    first_values = dict(zip(variables, combinations[0]))
    final_result, steps = evaluate_step(expression, first_values)

    headers = variables + ["1", "2", "3"]
    rows = []

    for combo in combinations:
        values = dict(zip(variables, combo))
        try:
            final_result, step_results = evaluate_step(expression, values)
            row = [int(values[var]) for var in variables]
            for i in range(3):
                if i < len(step_results):
                    row.append(int(step_results[i][1]))
                else:
                    row.append("-")
            rows.append(row)
        except Exception as e:
            return f"Error evaluating expression: {str(e)}"

    table = tabulate(rows, headers=headers,
                     tablefmt="simple", numalign="center")

    step_explanations = "\nSteps:"

    rus_operators = {
        'AND': 'конъюнкция',
        'OR': 'дизъюнкция',
        'IMPLIES': 'импликация',
        'NOT': 'отрицание',
        'EQUIV': 'эквивалентность',
        'XOR': 'исключающее или'
    }

    for i, (expr, _) in enumerate(steps, 1):
        rus_expr = expr
        for eng, rus in rus_operators.items():
            rus_expr = rus_expr.replace(eng, rus)
        step_explanations += f"\n{i}. {rus_expr}"

    return table + step_explanations


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

Keep the explanation clear and concise. Remove markdown and use only Russian language for explanation."""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate explanation: {str(e)}"


def solve_discrete_math(expression: str) -> str:
    """Solve discrete mathematics expression and return truth table with steps and explanation"""
    try:
        table = generate_truth_table(expression)
        explanation = generate_solution_description(expression, table, "")
        return f"Expression: {expression}\n\n{table}\n\nExplanation:\n{explanation}"
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
        with open('result.txt', 'w', encoding='utf-8') as f:
            f.write(result)
        print(result)


if __name__ == "__main__":
    main()
