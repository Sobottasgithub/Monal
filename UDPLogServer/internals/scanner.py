class Token:
    def __init__(self, kind, value, text=None, row=0, col=0):
        self.kind = kind
        self.value = value
        self.text = text
        self.row = row
        self.col = col
    
    def __eq__(self, other):
        return other.kind == self.kind and other.value == self.value
    
    def __str__(self):
        return "Token.%s['%s']" % (self.kind, self.value)


class Scanner:
    def __init__(self, text):
        self.text = text
        self.tokens = []
        self.row = 1
        self.col = 0
        self.state = "start"
        self.buffer = ""
        self.text_pos = 0
        # this is sensitive to its order (multi char strings should be before its single char counterparts having the same starting char)
        self.multi_specials = (
            ("ERROR", "constVar"),
            ("WARNING", "constVar"),
            ("INFO", "constVar"),
            ("DEBUG", "constVar"),
            ("VERBOSE", "constVar"),
            ("==", "opTest"),
            ("!=", "opTest"),
            ("<=", "opTest"),
            (">=", "opTest"),
            ("??", "opTest"),
            ("?", "opTest"),
            ("(", "LP"),
            (")", "RP"),
            ("+", "opAS"),
            ("-", "opAS"),
            ("*", "opMD"),
            ("/", "opMD"),
            ("^", "opPow"),
            ("!", "opFac"),
            ("π", "constVar"),
            ("[", "LSB"),
            ("]", "RSB"),
            ("{", "LCB"),
            ("}", "RCB"),
            (";", "EC"),
            ("=", "opAssign"),
            ("<", "opTest"),
            (">", "opTest"),
            (",", "next"),
            ("@", "call"),
            (":", "opMap"),
        )
        self.keywords = {
            "sqrt": "sqrt",
            "sin": "sin",
            "let": "let",
            "if": "if",
            "else": "else",
            "elif": "elif",
            "func": "func",
            "use": "use",
            "return": "opRet",
            "import": "opImport",
            "from": "from",
            "null": "null",
            "for": "for",
            "while": "while",
            "true": "constVar",
            "false": "constVar",
        }
        self.generator = self._generator()      # initialize generator function
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return next(self.generator)             # return next result of generator function
    
    def getInputRow(self, row):
        print(row)
        try:
            return self.text.split("\n")[row-1]
        except IndexError:
            print("Index doesn't exist!")

    
    def _read(self, num):
        retval = self.text[self.text_pos : self.text_pos + num]
        self.text_pos += num
        return retval
    
    def _lookahead(self, num):
        # read num chars from input file and rewind our file cursor to its original position afterwards
        retval = self.text[self.text_pos : self.text_pos + num]
        # if we did not manage to read the whole number of bytes, return an empty readahead string to make sure it does not accidentally match the wrong multi special
        if not retval or len(retval) != num:
            return ""
        return retval
    
    def _drainBuffer(self):
        buffer = self.buffer
        self.buffer = ""
        state = self.state
        self.state = "start"
        if not len(buffer):
            return None
        if state == "num1":
            return Token("num", float(buffer), self.text, self.row, self.col-len(buffer))
        elif state == "num2":
            return Token("num", int(buffer), self.text, self.row, self.col-len(buffer))
        elif state == "str":
            # our token should not contain the enclosing quotes and the token position should be at the opening quote
            value = buffer[1:-1]
            return Token("str", value, self.text, self.row, self.col-len(value)-1)
        else:
            if buffer in self.keywords:
                return Token(self.keywords[buffer], buffer, self.text, self.row, self.col-len(buffer))
            else:
                return Token("id", buffer, self.text, self.row, self.col-len(buffer))
    
    def _generator(self):
        inComment = False
        while True:
            char = self._read(1)
            self.col += 1
            #print("CHAR: %s" % str(char))
            # handle EOF (flush buffer if not empty, then raise StopIteration afterwards)
            if not char:
                #print("EOF")
                potentialToken = self._drainBuffer()
                if potentialToken:
                    yield potentialToken
                raise StopIteration
            
            # if we are in string state, everything is part of the string until we reach the ending quotation mark
            # this is true even for newline chars
            if self.state == "str":
                self.buffer += char
                if char == "\n":
                    self.row += 1
                    self.col = 0
                elif char == '"':
                    potentialToken = self._drainBuffer()
                    if potentialToken:
                        yield potentialToken
                continue
            
            # newline is special because it increments our sel.row counter and resets self.col to zero again
            # it flushes the buffer like normal spaces handles below, though
            if char == "\n":
                potentialToken = self._drainBuffer()
                if potentialToken:
                    yield potentialToken
                self.row += 1
                self.col = 0
                inComment = False
                continue
            
            # skip over all chars of a comment
            if inComment:
                continue
            
            # comments extend until the end of our line
            if char == "#":
                potentialToken = self._drainBuffer()
                if potentialToken:
                    yield potentialToken
                inComment = True
                continue
            
            # all sorts of spaces abort collecting chars into our buffer and flush the buffer, then ignore the space
            if char == " " or char == "\t" or char == "\r":
                potentialToken = self._drainBuffer()
                if potentialToken:
                    yield potentialToken
                continue
            
            # check if our char corresponds to the beginning of a multi special and if so, use lookahead to check if the whole multi special matches
            # if everything matches, abort collecting chars into our buffer and flush it, then emit a token corresponding to the multi special
            found = False
            for specialStr, specialOp in self.multi_specials:
                if char == specialStr[0]:
                    lookahead = self._lookahead(len(specialStr)-1)
                    if lookahead == specialStr[1:]:
                        found = True
                        break
            if found:
                potentialToken = self._drainBuffer()
                if potentialToken:
                    yield potentialToken
                # we found our multi special token, move our file cursor behind this token and yield it
                self._read(len(specialStr)-1)
                yield Token(specialOp, specialStr, self.text, self.row, self.col)
                continue
            
            # this loop serves as goto surrogate (continue == goto start, break == jump to end)
            # it collects numbers and text into our buffer
            while True:
                if self.state == "start":
                    self.buffer += char
                    if char == '"':
                        self.state = "str"
                        break                           # goto end
                    elif char.isdigit():
                        self.state = "num1"
                        break                           # goto end
                    else:
                        self.state = "text"
                        break                           # goto end
                elif self.state == "num1":
                    if char.isdigit():
                        self.buffer += char
                        break                           # goto end
                    elif char == ".":
                        self.buffer += char
                        self.state = "num2"
                        break                           # goto end
                    else:
                        potentialToken = self._drainBuffer()
                        if potentialToken:
                            yield potentialToken
                        self.state = "start"
                        continue                        # goto start
                elif self.state == "num2":
                    if char.isdigit():
                        self.buffer += char
                        break                           # goto end
                    else:
                        potentialToken = self._drainBuffer()
                        if potentialToken:
                            yield potentialToken
                        self.state = "start"
                        continue                        # goto start
                elif self.state == "text":
                    self.buffer += char
                    break        