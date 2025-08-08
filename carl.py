iota_counter=0

def iota(reset=False):
    global iota_counter
    if reset:
        iota_counter = 0
    result = iota_counter
    iota_counter += 1
    return result

OP_PUSH = iota(True)
OP_PLUS = iota()
OP_MINUS = iota()
OP_DUMP = iota()
OP_EQUALS = iota()
OP_IF = iota()
OP_ELSE = iota()
OP_END = iota()
OP_DUP = iota()
OP_GREATER = iota()
OP_WHILE = iota()
OP_DO = iota()

#--- Parser ---

def push(x):
    return OP_PUSH, x

def plus():
    return OP_PLUS,

def minus():
    return OP_MINUS,

def equals():
    return OP_EQUALS,

def dump():
    return OP_DUMP,

def iff():
    return OP_IF,

def elze():
    return OP_ELSE,

def end():
    return OP_END,

def dup():
    return OP_DUP,

def greater():
    return OP_GREATER,

def wile():
    return OP_WHILE,

def do():
    return OP_DO,

def parse_token(token):
    file_path, row, col, word = token
    if word == "+":
        return plus()
    elif word == "-":
        return minus()
    elif word == ".":
        return dump()
    elif word == "=":
        return equals()
    elif word == "if":
        return iff()
    elif word == "else":
        return elze()
    elif word == "end":
        return end()
    elif word == "dup":
        return dup()
    elif word == ">":
        return greater()
    elif word == "while":
        return wile()
    elif word == "do":
        return do()
    else:
        try:
            return push(int(word))
        except ValueError as err:
            print("%s:%d:%d: %s" % (file_path, row, col, err))
            exit(1)

def cross_reference_blocks(program):
    stack = []
    for ip in range(len(program)):
        op = program[ip]
        if op[0] == OP_IF:
            stack.append(ip)
        elif op[0] == OP_ELSE:
            if_ip = stack.pop()
            assert program[if_ip][0] == OP_IF, "`else` can only be used in `if`-blocks"
            program[if_ip] = OP_IF, ip + 1
            stack.append(ip)
        elif op[0] == OP_END:
            block_ip = stack.pop()
            if program[block_ip][0] == OP_IF or program[block_ip][0] == OP_ELSE:
                program[block_ip] = program[block_ip][0], ip
                program[ip] = OP_END, ip + 1
            elif program[block_ip][0] == OP_DO:
                assert len(program[block_ip]) >= 2, "..."
                program[ip] = OP_END, program[block_ip][1]
                program[block_ip] = OP_DO, ip + 1
            else:
                assert False, "´end´ can only close `if`, `else` or `do` blocks for now"
        elif op[0] == OP_WHILE:
            stack.append(ip)
        elif op[0] == OP_DO:
            while_ip = stack.pop()
            program[ip] = OP_DO, while_ip
            stack.append(ip)
    print(program)
    return program

#--- Lexer ---

def find_col(line, start, predicate):
    while start < len(line) and not predicate(line[start]):
        start += 1
    return start

def lex_line(line):
    col = find_col(line, 0, lambda x: not x.isspace())
    while col < len(line):
        col_end = find_col(line, col, lambda x: x.isspace())
        yield col, line[col:col_end]
        col = find_col(line, col_end, lambda x: not x.isspace())

def lex_file(file_path):
    with open(file_path, "r") as f:
        for (row, line) in enumerate(f.readlines()):
            for (col, token) in lex_line(line.split("//")[0]):
                yield file_path, row, col, token

def load_program(file_path):
    return cross_reference_blocks([parse_token(token) for token in lex_file(file_path)])

def simulate_program(program):
    stack = []
    ip = 0
    while ip < len(program):
        op = program[ip]
        if op[0] == OP_PUSH:
            stack.append(op[1])
            ip += 1
        elif op[0] == OP_PLUS:
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
            ip += 1
        elif op[0] == OP_MINUS:
            a = stack.pop()
            b = stack.pop()
            stack.append(b - a)
            ip += 1
        elif op[0] == OP_DUMP:
            a = stack.pop()
            print(a)
            ip += 1
        elif op[0] == OP_EQUALS:
            a = stack.pop()
            b = stack.pop()
            stack.append(int(a == b))
            ip += 1
        elif op[0] == OP_IF:
            a = stack.pop()
            if a == 0:
                assert len(op) >= 2, "`if` instruction..."
                ip = op[1]
            else:
                ip += 1
        elif op[0] == OP_ELSE:
            assert len(op) >= 2, "`else` instruction..."
            ip = op[1]
        elif op[0] == OP_END:
            assert len(op) >= 2, "`end` instruction..."
            ip = op[1]
        elif op[0] == OP_DUP:
            a = stack.pop()
            stack.append(a)
            stack.append(a)
            ip += 1
        elif op[0] == OP_GREATER:
            a = stack.pop()
            b = stack.pop()
            stack.append(int(b > a))
            ip += 1
        elif op[0] == OP_WHILE:
            ip += 1
        elif op[0] == OP_DO:
            a = stack.pop()
            if a == 0:
                assert len(op) >= 2, "`do` instruction..."
                ip = op[1]
            else:
                ip += 1
        else:
            assert False, "unreachable"

def main():
    file_path = "foo.txt"
    program = load_program(file_path)
    simulate_program(program)

if __name__ == "__main__":
    main()
