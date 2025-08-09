import sys

iota_counter = 0

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
OP_MEM = iota()
OP_LOAD = iota()
OP_STORE = iota()
OP_SYSCALL1 = iota()
OP_SYSCALL3 = iota()

MEM_CAPACITY = 640000  # should be enough for everyone

#--- Parser ---

def parse_token(token):
    file_path, row, col, word = token
    loc = file_path, row + 1, col + 1
    if word == "+":
        return {"type": OP_PLUS, "loc": loc}
    elif word == "-":
        return {"type": OP_MINUS, "loc": loc}
    elif word == "dump":
        return {"type": OP_DUMP, "loc": loc}
    elif word == "=":
        return {"type": OP_EQUALS, "loc": loc}
    elif word == "if":
        return {"type": OP_IF, "loc": loc}
    elif word == "else":
        return {"type": OP_ELSE, "loc": loc}
    elif word == "end":
        return {"type": OP_END, "loc": loc}
    elif word == "dup":
        return {"type": OP_DUP, "loc": loc}
    elif word == ">":
        return {"type": OP_GREATER, "loc": loc}
    elif word == "while":
        return {"type": OP_WHILE, "loc": loc}
    elif word == "do":
        return {"type": OP_DO, "loc": loc}
    elif word == "mem":
        return {"type": OP_MEM, "loc": loc}
    elif word == ",":
        return {"type": OP_LOAD, "loc": loc}
    elif word == ".":
        return {"type": OP_STORE, "loc": loc}
    elif word == "syscall1":
        return {"type": OP_SYSCALL1, "loc": loc}
    elif word == "syscall3":
        return {"type": OP_SYSCALL3, "loc": loc}
    else:
        try:
            return {"type": OP_PUSH, "value": int(word), "loc": loc}
        except ValueError as err:
            print("%s:%d:%d: %s" % (file_path, row, col, err))
            exit(1)

def cross_reference_blocks(program):
    stack = []
    for ip in range(len(program)):
        op = program[ip]
        if op["type"] == OP_IF:
            stack.append(ip)
        elif op["type"] == OP_ELSE:
            if_ip = stack.pop()
            if program[if_ip]["type"] != OP_IF:
                print("`else` can only be used in `if`-blocks")
                exit(1)
            program[if_ip]["jmp"] = ip + 1
            stack.append(ip)
        elif op["type"] == OP_END:
            block_ip = stack.pop()
            if program[block_ip]["type"] == OP_IF or program[block_ip]["type"] == OP_ELSE:
                program[block_ip]["jmp"] = ip
                program[ip]["jmp"] = ip + 1
            elif program[block_ip]["type"] == OP_DO:
                assert len(program[block_ip]) >= 2, "..."
                program[ip]["jmp"] = program[block_ip]["jmp"]
                program[block_ip]["jmp"] = ip + 1
            else:
                print("´end´ can only close `if`, `else` or `do` blocks for now")
                exit(1)
        elif op["type"] == OP_WHILE:
            stack.append(ip)
        elif op["type"] == OP_DO:
            while_ip = stack.pop()
            program[ip]["jmp"] = while_ip
            stack.append(ip)
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
    mem = bytearray(MEM_CAPACITY)
    ip = 0
    while ip < len(program):
        op = program[ip]
        ip += 1
        if op["type"] == OP_PUSH:
            stack.append(op["value"])
        elif op["type"] == OP_PLUS:
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
        elif op["type"] == OP_MINUS:
            a = stack.pop()
            b = stack.pop()
            stack.append(b - a)
        elif op["type"] == OP_DUMP:
            a = stack.pop()
            print(a)
        elif op["type"] == OP_EQUALS:
            a = stack.pop()
            b = stack.pop()
            stack.append(int(a == b))
        elif op["type"] == OP_IF:
            a = stack.pop()
            if a == 0:
                assert len(op) >= 2, "`if` instruction expects a ´jmp´ field"
                ip = op["jmp"]
        elif op["type"] == OP_ELSE:
            assert len(op) >= 2, "`else` instruction expects a ´jmp´ field"
            ip = op["jmp"]
        elif op["type"] == OP_END:
            assert len(op) >= 2, "`end` instruction expects a ´jmp´ field"
            ip = op["jmp"]
        elif op["type"] == OP_DUP:
            a = stack.pop()
            stack.append(a)
            stack.append(a)
        elif op["type"] == OP_GREATER:
            a = stack.pop()
            b = stack.pop()
            stack.append(int(b > a))
        elif op["type"] == OP_WHILE:
            pass
        elif op["type"] == OP_DO:
            a = stack.pop()
            if a == 0:
                assert len(op) >= 2, "`do` instruction..."
                ip = op["jmp"]
        elif op["type"] == OP_MEM:
            stack.append(0)
        elif op["type"] == OP_LOAD:
            addr = stack.pop()
            byte = mem[addr]
            stack.append(byte)
        elif op["type"] == OP_STORE:
            value = stack.pop()
            addr = stack.pop()
            mem[addr] = value & 0xFF
        elif op["type"] == OP_SYSCALL1:
            assert False, "not implemented"
        elif op["type"] == OP_SYSCALL3:
            syscall_number = stack.pop()
            arg1 = stack.pop()
            arg2 = stack.pop()
            arg3 = stack.pop()
            if syscall_number == 1:
                fd = arg1
                buf = arg2
                count = arg3
                s = mem[buf:buf + count].decode("utf-8")
                if fd == 1:
                    print(s, end="")
                elif fd == 2:
                    print(s, end="", file=sys.stderr)
                else:
                    assert False, "unknown file descriptor %d" % fd
            else:
                assert False, "unknown syscall number %d" % syscall_number
        else:
            assert False, "unreachable"

def main():
    file_path = "foo.txt"
    program = load_program(file_path)
    simulate_program(program)

if __name__ == "__main__":
    main()
