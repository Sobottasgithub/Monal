class InputError(RuntimeError):
    def __init__(self, text, token=None):
        super().__init__(text)
        self.token = token

class SyntaxError(InputError):
    pass

class InterpreterError(InputError):
	pass


# this is used to signal if we reached a return statement while executing a function
# if this is not catched inside the AST implementation, this is an error (e.g. unexpected return statement outside of a function)
class ReturnFromFunction(InputError):
    def __init__(self, retval, token=None):
        self.retval = retval
        super().__init__("Unexpected return statement!", token=token)
