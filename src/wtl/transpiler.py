import ast
import re

class Transpilation:
    DEFAULT_FILENAME = "<WTL transpiler input>"

    def __init__(self, source, filename=None):
        if filename is None:
            filename = self.DEFAULT_FILENAME
        self.filename = filename
        self.lines = source.split("\n")

    def run(self):
        while (source := self._parse_or_fix_one()) is None:
            pass
        return source

    def _parse_or_fix_one(self):
        try:
            source = "\n".join(self.lines)
            ast.parse(source, filename=self.filename)
            return source

        except SyntaxError as e:
            if e.filename != self.filename:
                raise  # Only operate on our own input
            line_index = e.lineno - 1
            if line_index < 0:
                raise  # Should not happen
            line = self.lines[line_index]
            offset = e.offset - 1
            if offset < 0:
                raise  # Should not happen
            new_line = self._fixup(line, offset)
            if new_line is None:
                raise  # _fixup couldn't fix it
            if new_line == line:
                raise  # _fixup thinks it's fixed, but it's not!
            self.lines[line_index] = new_line

    HEX_COLOR = re.compile(r"^#((:?[0-9A-Fa-f]{3}){1,2})\b")

    def _fixup_hex_color(self, match):
        digits = match.group(1)
        if len(digits) == 3:
            digits = [d * d for d in list(digits)]
        elif len(digits) == 6:
            digits = [digits[:2], digits[2:4], digits[4:]]
        else:
            raise ValueError
        return f"Color(0x{', 0x'.join(digits)})"

    def _fixup(self, line, offset):
        preamble = line[:offset]
        line = line[offset:]
        if not preamble.rstrip().endswith("="):
            return
        match = self.HEX_COLOR.match(line)
        if match is None:
            return
        postamble = line[len(match.group(0)):]
        rewrite = self._fixup_hex_color(match)
        return f"{preamble}{rewrite}{postamble}"

def transpile(*args, **kwargs):
    return Transpilation(*args, **kwargs).run()

def _test_hex_color(text):
    print(f"{text:10} {Transpilation.HEX_COLOR.match(text)}")

def _test_hex_color_regexp():
    test = "#abcdef123"
    for i in range(len(test)):
        chk = test[:i]
        _test_hex_color(chk)
        chk += " " + test[i:]
        _test_hex_color(chk)

def _test_transpilation():
    print(transpile("""
BLUE = #07519b
TEAL = #075275

warp.colors = [BLACK]*6 + [TEAL]*15 + [BLUE, TEAL]*8 + [BLUE]*17
# warp.colors = 6*BLACK + [TEAL]*15 + (BLUE, TEAL)*8 + [BLUE]*17 ???
warp.colors += reversed(warp.colors)  # Mirror
warp.colors = warp.colors[1:-1]  # Lose selvedges
"""))

if __name__ == "__main__":
    # test_hex_color_regexp()
    _test_transpilation()
