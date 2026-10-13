from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import random
import copy
import os


app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR, "templates")
)


# =========================================================
# SUDOKU LOGIC
# =========================================================

def is_safe(board, row, col, num):

    # Check row
    for i in range(9):
        if board[row][i] == num:
            return False

    # Check column
    for i in range(9):
        if board[i][col] == num:
            return False

    # Check 3x3 box
    start_row = (row // 3) * 3
    start_col = (col // 3) * 3

    for i in range(start_row, start_row + 3):
        for j in range(start_col, start_col + 3):
            if board[i][j] == num:
                return False

    return True


def solve(board, row=0, col=0):

    if row == 9:
        return True

    next_row = row
    next_col = col + 1

    if next_col == 9:
        next_row += 1
        next_col = 0

    # Already filled
    if board[row][col] != 0:
        return solve(board, next_row, next_col)

    for num in range(1, 10):

        if is_safe(board, row, col, num):

            board[row][col] = num

            if solve(board, next_row, next_col):
                return True

            board[row][col] = 0

    return False


def generate_full_board(board, row=0, col=0):

    if row == 9:
        return True

    next_row = row
    next_col = col + 1

    if next_col == 9:
        next_row += 1
        next_col = 0

    numbers = list(range(1, 10))
    random.shuffle(numbers)

    for num in numbers:

        if is_safe(board, row, col, num):

            board[row][col] = num

            if generate_full_board(board, next_row, next_col):
                return True

            board[row][col] = 0

    return False


def create_puzzle(full_board, cells_to_remove):

    puzzle = copy.deepcopy(full_board)

    removed = 0

    while removed < cells_to_remove:

        row = random.randint(0, 8)
        col = random.randint(0, 8)

        if puzzle[row][col] != 0:

            puzzle[row][col] = 0
            removed += 1

    return puzzle


def generate_puzzle(cells_to_remove):

    board = [
        [0 for _ in range(9)]
        for _ in range(9)
    ]

    generate_full_board(board)

    return create_puzzle(board, cells_to_remove)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_blanks(difficulty):

    if difficulty == "easy":
        return 30

    if difficulty == "hard":
        return 50

    return 40


def generate_game(difficulty):

    blanks = get_blanks(difficulty)

    puzzle = generate_puzzle(blanks)

    solution = copy.deepcopy(puzzle)

    solve(solution)

    return puzzle, solution


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):

    difficulty = "medium"

    puzzle, solution = generate_game(difficulty)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "board": puzzle,
            "solution": solution,
            "original": puzzle,
            "difficulty": difficulty,
            "message": ""
        }
    )


# =========================================================
# NEW GAME
# =========================================================

@app.post("/new", response_class=HTMLResponse)
def new_game(
    request: Request,
    difficulty: str = Form("medium")
):

    puzzle, solution = generate_game(difficulty)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "board": puzzle,
            "solution": solution,
            "original": puzzle,
            "difficulty": difficulty,
            "message": ""
        }
    )


# =========================================================
# CHECK ANSWER
# =========================================================

@app.post("/check", response_class=HTMLResponse)
async def check_answer(request: Request):

    form = await request.form()

    difficulty = form.get("difficulty", "medium")

    original = [
        [0 for _ in range(9)]
        for _ in range(9)
    ]

    board = [
        [0 for _ in range(9)]
        for _ in range(9)
    ]


    # Get original puzzle
    for row in range(9):

        for col in range(9):

            value = form.get(
                f"original_{row}_{col}",
                "0"
            )

            original[row][col] = int(value)


    # Get user's answers
    for row in range(9):

        for col in range(9):

            value = form.get(
                f"cell_{row}_{col}",
                ""
            )

            if value and str(value).isdigit():

                number = int(value)

                if 1 <= number <= 9:
                    board[row][col] = number


    # Generate solution
    solution = copy.deepcopy(original)

    solve(solution)


    # Check answers
    correct = True

    for row in range(9):

        for col in range(9):

            # Only check empty cells
            if original[row][col] == 0:

                if board[row][col] != solution[row][col]:

                    correct = False


    if correct:

        message = "🎉 Correct! You solved the Sudoku!"

    else:

        message = "❌ Some answers are incorrect."


    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "board": board,
            "solution": solution,
            "original": original,
            "difficulty": difficulty,
            "message": message
        }
    )


# =========================================================
# SOLVE
# =========================================================

@app.post("/solve", response_class=HTMLResponse)
async def solve_game(request: Request):

    form = await request.form()

    difficulty = form.get("difficulty", "medium")

    original = [
        [0 for _ in range(9)]
        for _ in range(9)
    ]


    # Get original puzzle
    for row in range(9):

        for col in range(9):

            value = form.get(
                f"original_{row}_{col}",
                "0"
            )

            original[row][col] = int(value)


    # Solve puzzle
    solution = copy.deepcopy(original)

    solve(solution)


    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "board": solution,
            "solution": solution,
            "original": original,
            "difficulty": difficulty,
            "message": "Solution displayed."
        }
    )