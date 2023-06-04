import math, os
from internals.errors import InterpreterError, ReturnFromFunction

# this class holds all state needed and gets mutated from outside
class State:
    def __init__(self, vars={}):
        self.varHeap = []
        self.scope = -1
        self.pushVarScope()
        for k in vars:
            self.setVar(k, vars[k])
    
    def __str__(self):
        return "State(%d, %s)" % (self.scope, str(self.varHeap))
    
    def pushVarScope(self, scopeDict=None):
        if not scopeDict:
            scopeDict = {}
        self.scope += 1
        self.varHeap.append(scopeDict)
    
    def popVarScope(self):
        retval = self.varHeap[self.scope]
        self.scope -= 1
        self.varHeap = self.varHeap[:-1]
        return retval
    
    def isSet(self, name, scope=None):
        if scope == None:
            scope = self.scope
        return name in self.varHeap[scope]
    
    def setVar(self, name, value, scope=None):
        if not self.isSet(name, scope):
            self.setWrappedVar(name, WrappedValue(value), scope)
        else:
            self.getWrappedVar(name, scope).set(value)      # overwrite value inside our wrapper to keep all var references intact
    
    def getVar(self, name, scope=None):
        return self.getWrappedVar(name, scope).get()        # unpack wrapped value on return
    
    def unsetVar(self, name, scope=None):
        if scope == None:
            scope = self.scope
        if name in self.varHeap[scope]:
            del self.varHeap[scope][name]
    
    def setWrappedVar(self, name, wrappedValue, scope=None):
        if scope == None:
            scope = self.scope
        self.varHeap[scope][name] = wrappedValue
    
    def getWrappedVar(self, name, scope=None):
        if scope == None:
            scope = self.scope
        assert name in self.varHeap[scope], "Unexpected access to not existing var in current scope, error in AST interpreter!"
        return self.varHeap[scope][name]

# this is used as reference-style wrapper (because in python every object is passed by reference)
# this makes it possible to reference vars present in other scopes or not even present in any scope (the use() claue in function definitions)
class WrappedValue:
    def __init__(self, value):
        self.set(value)
    
    def get(self):
        return self.value
    
    def set(self, value):
        self.value = value
    
    def __str__(self):
        return "WrappedValue(%s)" % str(self.value)

# this represents a callable function definition that can be saved into our state and passed around in vars
class Function:
    def __init__(self, argList, usedVars, definition, flags={}, token=None):
        self.argList = argList
        self.usedVars = usedVars
        self.definition = definition
        self.flags = flags                  # flags present on evaluation of the corresponding function definition
        self.token = token
    
    # this gets invoked when OpCall "calls" a defined funtion
    def call(self, args, flags={}, token=None):
        state = flags["state"]
        # open new var scope for this function call
        state.pushVarScope()
        if len(args) != len(self.argList):
            raise InterpreterError("Wrong argument count for function defined in file '%s' at line %d column %d: got %d arguments, but expected %d!" % (
                str(self.token.file if self.token else None),
                self.token.row if self.token else None,
                self.token.col if self.token else None,
                len(args),
                len(self.argList),
            ), token)
        # import used variables into our new scope (they are already wrapped values, e.g. "references")
        for varName in self.usedVars:
            state.setWrappedVar(varName, self.usedVars[varName])
        # "import" passed in values into our new scope by copying the corresponding already evaluated argument in the passed in args list
        # (OpCall() is responsible for evaluating the args before passing them in here)
        for index in range(len(self.argList)):
            # entries in argList are unwrapped values (this is needed to make BuiltinFunction and Function have the same signature for call())
            state.setVar(self.argList[index].value, args[index])
        # evaluate AST of our function (e.g. really "call" it) and catch ReturnFromFunction exceptions raised by a return statement inside our AST
        try:
            retval = self.definition(flags)
        except ReturnFromFunction as e:
            retval = e.retval;
        # close var scope again
        state.popVarScope()
        return retval
    
    def __str__(self):
        return "Function[%s, %d, %d]([%s], %s, %s)" % (
            str(self.token.file if self.token else None),
            self.token.row if self.token else None,
            self.token.col if self.token else None,
            ", ".join([token.value for token in self.argList]),
            str(self.usedVars),
            str(self.definition)
        )

# for builtin functions self.definition is a pointer to the corresponding python callable, everything else is exactly like in ordinary Functions
class BuiltinFunction(Function):
    def call(self, args, flags={}, token=None):
        if len(args) != len(self.argList):
            raise InterpreterError("Wrong argument count for predefined function: got %d arguments, but expected %d!" % (len(args), len(self.argList)), token)
        return self.definition(*args)
    
    def __str__(self):
        return "BuiltinFunction[unknown](%s, [], %s)" % (str(self.argList), str(self.definition))


class AST:
    def __init__(self, token=None):
        self.token = token
    
    def __call__(self, flags={}):
        raise NotImplementedError("Unexpected call to abstract __call__ method!")
    
    def _raiseInterpreterError(self, text, token=None):
        if not token:
            token = self.token
        raise InterpreterError(text, token=token)
    
    def __str__(self):
        return str(self.__class__.__name__)

class Const(AST):
    def __call__(self, flags={}):
        return self.value(flags)
    
    def __str__(self):
        return "%s()" % str(self.__class__.__name__)

class ConstPi(Const):
    def value(self, flags={}):
        return math.pi

class ConstFlagError(Const):
    def value(self, flags={}):
        return 1
    
class ConstFlagWarning(Const):
    def value(self, flags={}):
        return 2
    
class ConstFlagInfo(Const):
    def value(self, flags={}):
        return 4

class ConstFlagDebug(Const):
    def value(self, flags={}):
        return 8
    
class ConstFlagVerbose(Const):
    def value(self, flags={}):
        return 16

class ConstTrue(Const):
    def value(self, flags={}):
        return True

class ConstFalse(Const):
    def value(self, flags={}):
        return False

class NumType(AST):
    def __init__(self, value, token=None):
        self.value = value
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        return self.value
    
    def __str__(self):
        return "NumType(%s)" % str(self.value)

class StrType(AST):
    def __init__(self, value, token=None):
        self.value = value
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        return str(self.value)
    
    def __str__(self):
        return "StrType(%s)" % str(self.value)

class NullType(AST):
    def __init__(self, token=None):
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        return None
    
    def __str__(self):
        return "NullType"

class MapType(AST):
    def __init__(self, mapList, token=None):
        self.mapList = mapList
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        # evaluate name and value of every entry and build our dictionary 
        value = {}
        for entry in self.mapList:
            entryName = entry["name"](flags)
            entryValue = entry["value"](flags)
            # always copy dicts, we don't want to have strange python side effects in our language
            if type(entryValue) == dict:
                entryValue = entryValue.copy()
            value[entryName] = entryValue
        return value
    
    def __str__(self):
        return "MapType(%s)" % ", ".join(map(str, self.mapList))
    
class OpImport(AST):
    def __init__(self, imports, moduleName, token=None):
        self.imports = imports
        self.moduleName = moduleName
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        state = flags["state"]
        # corelang is a special module name for builtin stuff
        if self.moduleName == "corelang":
            from .corelang import corelangExports
            exportedDict = corelangExports
        else:
            from .interpreter import run
            # module imports are relative to the current directory
            currentDir = os.path.dirname(self.token.file)
            # only add "/" at the end (to separate currentDir from filePath), if the string isn't empty to not create an absolute path on empty currentDir strings
            currentDir = "%s/" % currentDir if len(currentDir) > 0 else ""
            filePath = "/".join(self.moduleName.split("."))
            exportedDict = run("%s%s.yola" % (currentDir, filePath), self.token)
            # modules return a map and we import all entries in imports from this map into our current scope
            if type(exportedDict) is not dict:
                self._raiseInterpreterError("Could not import module '%s', no exported names!" % str(self.moduleName))
        
        # import all module exports into a new var scope containing only those exported vars afterwards...
        state.pushVarScope()
        for name, value in exportedDict.items():
            # all exports are naked values because results of an ast evaluation are always naked values (see implementation of run())
            state.setVar(name, value)
        # ...then evaluate all Var() expressions in self.imports and build a dictionary with mappings of importName to the corresponding naked value...
        importedDict = {}
        for importToken, exportVar in self.imports:
            importName = importToken.value
            try:
                importedDict[importName] = exportVar(flags)
            except:
                self._raiseInterpreterError("Import Error: Could not import something as '%s' from module '%s', check your rhs!" % (str(importName), str(self.moduleName)), importToken)
        # ...leave scope again (all var expressions are evaluated now)...
        state.popVarScope()
        # ...and import the saved naked values into our current (e.g. real) scope
        for importName, importValue in importedDict.items():
            # these are still naked values
            state.setVar(importName, importValue)
    
    def __str__(self):
        return "OpImport(%s: %s)" % (str(self.moduleName), ", ".join(map(str, ["%s=%s" % (key.value, value) for key, value in self.imports])))
    
class OpLetFunc(AST):
    def __init__(self, name, subscriptList, argList, useList, definition, token=None):
        self.name = name
        self.subscriptList = subscriptList
        self.argList = argList
        self.useList = useList
        self.definition = definition
        super().__init__(token=token)
        
    # this gets invoked when our AST gets evaluated (e.g. the func declaration is evaluated, not called) and creates a function object
    # the implementation within is similar to OpLet, but significantly different to have its own copy
    def __call__(self, flags={}):
        state = flags["state"]
        
        # add a dummy value in this var scope
        # this dummy will  be filled with our Function later on and makes it possible to reference the function itself within it's use clause (allowing for recursive functions)
        if not state.isSet(self.name):
            state.setVar(self.name, {})             # always create a dict dummy value (this allows for subscripts to work seamlessly and non-subscripts will overwrite this anyway)
        
        # check if the use clause in our funcdef is valid and save their references into the function (this makes them usable even after the scope the funcdef lives in was left)
        usedVars = {}
        for varToken in self.useList:
            varName = varToken.value
            if not state.isSet(varName):
                self._raiseInterpreterError("Could not USE undefined variable '%s' from outer scope while defining new function!" % str(varName), varToken)
            usedVars[varName] = state.getWrappedVar(varName)
        func = Function(self.argList, usedVars, self.definition, flags=flags, token=self.token)
        
        # save newly created function object into our var scope
        # if a subscript was given, evaluate and use it on the left hand side
        if self.subscriptList and len(self.subscriptList):
            var = state.getVar(self.name)
            for subscript in self.subscriptList[:-1]:           # don't descend to the last one filled with func below
                subscript = subscript(flags)
                if subscript not in var:
                    var[subscript] = {}
                var = var[subscript]
            var[self.subscriptList[-1](flags)] = func           # overwrite subscripted value inside our current var scope
        else:
            state.setVar(self.name, func)
        return func     # let itself evaluates to its rhs (but additionally let has side effects on var space of course)
    
    def __str__(self):
        return "OpLetFunc(%s%s[%s](%s) := %s)" % (str(self.name), "".join(["[%s]" % str(entry) for entry in self.subscriptList]), ", ".join(map(str, self.useList)), str(self.argList), str(self.definition))

class OpReturn(AST):
    def __init__(self, retval, token=None):
        self.retval = retval
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        # evaluate return value and throw a signalling exception with this value
        # if self.retval == None this means we don't have a return value to evaluate --> return None in signalling exception
        raise ReturnFromFunction(self.retval(flags) if self.retval else None, token=self.token)
    
    def __str__(self):
        return "OpReturn(%s)" % str(self.retval)

class OpLet(AST):
    def __init__(self, name, subscriptList, value, token=None):
        self.name = name
        self.subscriptList = subscriptList
        self.value = value
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        state = flags["state"]
        
        # this evaluates the AST in self.value
        value = self.value(flags)
        
        # always copy dicts, we don't want to have strange python side effects in our language
        if type(value) == dict:
            value = value.copy()
        
        # if a subscript was given, evaluate and use it on the left hand side
        if self.subscriptList and len(self.subscriptList):
            # create new empty dict value if not already present in current var scope
            if not state.isSet(self.name):
                state.setVar(self.name, {})
            var = state.getVar(self.name)
            for subscript in self.subscriptList[:-1]:           # don't descend to the last one filled with func below
                subscript = subscript(flags)
                if subscript not in var:
                    var[subscript] = {}
                var = var[subscript]
            # a null value means "please delete this entry" otherwise set the (new) entry in our dict var
            subscript = self.subscriptList[-1](flags)
            if value == None:
                if subscript in var:
                    del var[subscript]
            else:
                var[subscript] = value
        else:
            # a null value means "please delete this entry", otherwise overwrite it
            if value == None:
                state.unsetVar(self.name)
            else:
                state.setVar(self.name, value)
        return value     # let itself evaluates to its rhs (but additionally let has side effects on var space of course)
    
    def __str__(self):
        return "OpLet(%s%s := %s)" % (str(self.name), "".join(["[%s]" % str(entry) for entry in self.subscriptList]), str(self.value))

class Var(AST):
    def __init__(self, name, subscriptList=[], token=None):
        self.name = name
        self.subscriptList = subscriptList
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        state = flags["state"]
        print(state)
        if not state.isSet(self.name):
            self._raiseInterpreterError("Tried to access unset variable '%s'!" % str(self.name))
        value = state.getVar(self.name)
        # normal var without subscripts --> simply return it
        if len(self.subscriptList) == 0:
            return value
        # var with subscripts --> dereference subscripts and return the dereferenced value
        try:
            if type(value) is not dict:
                self._raiseInterpreterError("Tried to subscript non-map variable '%s'!" % str(self.name))
            for subscript in self.subscriptList:
                subscript = subscript(flags)
                if subscript not in value or type(value) is not dict:
                    self._raiseInterpreterError("Tried to access non-existent subscript in variable '%s' or one of its map elements!" % str(self.name))
                value = value[subscript]
            return value
        except InterpreterError:
            raise
        except BaseException as e:
            self._raiseInterpreterError("Unknown index '%s' in variable '%s'!" % (str(self.subscriptList(flags)), str(self.name)))
    
    def __str__(self):
        return "VarSubscript(%s%s)" % (str(self.name), "".join(["[%s]" % str(entry) for entry in self.subscriptList]))

class CmdList(AST):
    def __init__(self, cmdList, token=None):
        self.cmdList = cmdList
        super().__init__(token=token)
    
    def evaluateAll(self, flags={}):
        # YOLA: the following code could all be written as oneliner:
        #return [cmd(flags) if cmd else None for cmd in self.cmdList]
        results = []
        for cmd in self.cmdList:
            if not cmd:
                results.append(None)                        # empty cmds evaluate to None
            else:
                results.append(cmd(flags))                  # evaluate next cmd
        return results                                      # return results of all cmds
    
    def __call__(self, flags={}):
        results = self.evaluateAll(flags)
        if len(results) == 0:
            return None
        return results[-1]                                  # only return result of last cmd
    
    def __str__(self):
        return "CmdList<%s>" % ", ".join(map(str, self.cmdList))
    
    def __len__(self):
        return len(self.cmdList)
    
    def __getitem__(self, index):
        return self.cmdList[index]
    
class OpCall(AST):
    def __init__(self, var, args, token=None):
        self.var = var
        self.args = args
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        state = flags["state"]
        # evaluate our argument list and return a result for every entry
        funcArgs = self.args.evaluateAll(flags)
        func = self.var(flags)
        if not isinstance(func, Function):
            self._raiseInterpreterError("Tried to call non-function '%s'!" % str(func))
        # call function and return its result
        #print("Calling", func, "with args:", funcArgs)
        return func.call(funcArgs, flags, token=self.token)
    
    def __str__(self):
        return "OpCall(%s, %s)" % (str(self.var), str(self.args))

class OpFor(AST):
    def __init__(self, varInit, test, varInc, body, token=None):
        self.varInit = varInit
        self.test = test
        self.varInc = varInc
        self.body = body
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        self.varInit(flags)
        lastBodyResult = None
        while self.test(flags):
            lastBodyResult = self.body(flags)
            self.varInc(flags)
        # for loops return their last body result
        return lastBodyResult
    
    def __str__(self):
        return "OpFor(%s, %s, %s){%s}" % (self.varInit, self.test, self.varInc, self.body)

class OpWhile(AST):
    def __init__(self, test, body, token=None):
        self.test = test
        self.body = body
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        lastBodyResult = None
        while self.test(flags):
            lastBodyResult = self.body(flags)
        # while loops return their last body result
        return lastBodyResult
    
    def __str__(self):
        return "OpWhile(%s){%s}" % (self.test, self.body)

class OpIf(AST):
    def __init__(self, test, ast1, ast2, token=None):
        self.test = test
        self.ast1 = ast1
        self.ast2 = ast2
        super().__init__(token=token)
    
    def __call__(self, flags={}):
        # ifs return their last branch result
        if self.test(flags):
            return self.ast1(flags)
        elif self.ast2:
            return self.ast2(flags)
    
    def __str__(self):
        return "OpIf(%s){%s}{%s}" % (self.test, self.ast1, self.ast2)

class OpBin(AST):
    def __init__(self, left, right, token=None):
        self.left = left
        self.right = right
        super().__init__(token=token)
    
    def operator(self, left, right):
        raise NotImplementedError("Unexpected call to abstract binary operator method!")
    
    def __call__(self, flags={}):
        # evaluate left and  right hand arguments and use self.operator() on the evaluated values then return the result
        return self.operator(self.left(flags), self.right(flags))
    
    def __str__(self):
        return "%s(%s, %s)" % (str(self.__class__.__name__), str(self.left), str(self.right))

class OpUn(AST):
    def __init__(self, arg, token=None):
        self.arg = arg
        super().__init__(token=token)
    
    def operator(self, arg):
        raise NotImplementedError("Unexpected call to abstract unary operator method!")
    
    def __call__(self, flags={}):
        # evaluate single argument and use self.operator() on the evaluated value then return the result
        return self.operator(self.arg(flags))
    
    def __str__(self):
        return "%s(%s)" % (str(self.__class__.__name__), str(self.arg))

class OpAdd(OpBin):
    def operator(self, left, right):
        # we want to support merging maps using "+" operator
        if type(left) == dict and type(right) == dict:
            retval = {}
            retval.update(left)
            retval.update(right)
            return retval
        # if normal addition does not work, simply concatenate as strings
        try:
            return left + right
        except:
            return str(left) + str(right)

class OpSub(OpBin):
    def operator(self, left, right):
        return left - right

class OpMul(OpBin):
    def operator(self, left, right):
        return left * right

class OpDiv(OpBin):
    def operator(self, left, right):
        return left / right

class OpPow(OpBin):
    def operator(self, left, right):
        return left ** right

class OpSqrt(OpUn):
    def operator(self, arg):
        return math.sqrt(arg)

class OpSin(OpUn):
    def operator(self, arg):
        return math.sin(arg)

class OpCos(OpUn):
    def operator(self, arg):
        return math.cos(arg)

class OpFac(OpUn):
    def operator(self, arg):
        return math.factorial(arg)

class OpEq(OpBin):
    def operator(self, left, right):
        return left == right

class OpNeq(OpBin):
    def operator(self, left, right):
        return left != right

class OpLt(OpBin):
    def operator(self, left, right):
        return left < right

class OpGt(OpBin):
    def operator(self, left, right):
        return left > right

class OpLte(OpBin):
    def operator(self, left, right):
        return left <= right

class OpGte(OpBin):
    def operator(self, left, right):
        return left >= right

class OpTestIn(OpBin):
    def operator(self, left, right):
        return left in right

# this is special because it overwrites __call__() directly instead of operator() as you would normally do
class OpIsSet(OpUn):
    def __call__(self, flags={}):
        # return true, if we succeed to evaluate arg and its NOT None, false otherwise
        try:
            value = self.arg(flags)
            return value != None
        except:
            return False
