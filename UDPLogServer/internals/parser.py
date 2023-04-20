from .ast import *
from .scanner import Token
from .errors import SyntaxError

class Parser:
    def __init__(self, scanner):
        self.scanner = scanner
        self.currentToken = None        # initial value needed for acceptIt
        self.acceptIt()                 # "accept" currently empty currentToken and fill in the first real token
    
    def _raiseSyntaxError(self):
        if self.currentToken:
           raise SyntaxError("%s not expected!" % str(self.currentToken), self.currentToken)
        else:
            self.lastToken.col += 1
            raise SyntaxError("Unexpected EOF after %s!" % str(self.lastToken), self.lastToken)
    
    def acceptIt(self):
        accepted = self.currentToken
        #if accepted:
        #    print("ACCEPTED: %s" % str(accepted))
        try:
            self.currentToken = next(self.scanner, None)
        except:
            self.currentToken = None
        self.lastToken = accepted
        return accepted
    
    def accept(self, kind):
        if self.testKind(kind):
            return self.acceptIt()
        else:
            self._raiseSyntaxError()
    
    def testKind(self, kind):
        if not self.currentToken:                   # EOT never has the right kind
            return False
        return self.currentToken.kind == kind
    
    def testEOT(self):
        return not self.currentToken
    
    def parse(self):
        if self.testEOT():
            return None
        ast = self.parseCommandList("EC")
        if not self.testEOT():
            self._raiseSyntaxError()
        return ast
    
    def parseCommandList(self, cmdDelimiter, eotMarker=None):
        cmdList = []
        while not self.testEOT() and (not eotMarker or not self.testKind(eotMarker)):
            ast = self.parseCommand(cmdDelimiter, eotMarker)
            cmdList.append(ast)
        return CmdList(cmdList)
    
    def parseCommand(self, cmdDelimiter, eotMarker=None):
        if self.testKind("opImport"):               # import statement
            return self.parseImport()
        elif self.testKind("opRet"):                # return statement
            token = self.acceptIt()
            retvalAst = None
            # allow empty retvals, too
            if not ((eotMarker and self.testKind(eotMarker)) or self.testKind(cmdDelimiter)):
                if self.testKind("if"):
                    retvalAst = self.parseIf()
                elif self.testKind("for"):
                    retvalAst = self.parseFor()
                elif self.testKind("while"):
                    retvalAst = self.parseWhile()
                else:
                    retvalAst = self.parseAdd()
            return OpReturn(retvalAst, token=token)
        elif self.testKind("for"):                  # for statement
            return self.parseFor()
        elif self.testKind("while"):                # while statement
            return self.parseWhile()
        elif self.testKind("let"):                  # let statement
            retval = self.parseLet()
            # accept eotMarker (if given) instead of cmdDelimiter --> cmdDelimiter must be given, if no eotMarker was found
            if not (eotMarker and self.testKind(eotMarker)):
                self.accept(cmdDelimiter)
            return retval
        elif self.testKind("if"):                   # if statement
            return self.parseIf()
        elif self.testKind(cmdDelimiter):           # empty command
            self.acceptIt()
            return None
        else:                                       # simple math term
            ast = self.parseAdd()
            # accept eotMarker (if given) instead of cmdDelimiter --> cmdDelimiter must be given, if no eotMarker was found
            if not (eotMarker and self.testKind(eotMarker)):
                self.accept(cmdDelimiter)           # even math terms must be terminated by ";" (e.g. end command)
            return ast
    
    def parseArgumentList(self, argDelimiter, eotMarker=None):
        argumentList = []
        while not self.testEOT() and (not eotMarker or not self.testKind(eotMarker)):
            identifier = self.accept("id")
            argumentList.append(identifier)
            if not self.testEOT() and (not eotMarker or not self.testKind(eotMarker)):
                self.accept(argDelimiter)
        return argumentList
    
    def parseMapList(self, mapDelimiter, eotMarker=None):
        mapList = []
        index = 0
        while not self.testEOT() and (not eotMarker or not self.testKind(eotMarker)):
            valueAst = self.parseAdd()
            if self.testKind("opMap"):
                nameAst = valueAst
                self.accept("opMap")
                valueAst = self.parseAdd()
            else:
                nameAst = NumType(index)
                index += 1
            if not eotMarker or not self.testKind(eotMarker):
                self.accept(mapDelimiter)
            mapList.append({"name": nameAst, "value":valueAst})
        return mapList
    
    def parseTest(self):
        # list of test operation literals usable in if statements
        testOps = {
            "==": OpEq,
            "!=": OpNeq,
            "<": OpLt,
            ">": OpGt,
            "<=": OpLte,
            ">=": OpGte,

        }
        x1 = self.parseAdd()
        if not self.testKind("opTest"):         # possibly raw boolean value --> test for equality with true
            return OpEq(x1, ConstTrue())
        x2 = self.accept("opTest")
        test = testOps[x2.value]
        # unary tests don't need a value to test against
        if issubclass(test, OpUn):
            return test(x1)
        x3 = self.parseAdd()
        return test(x1, x3)
        #if self.testKind("opBool"):
        #    operatorToken = self.acceptIt()
        #    boolOperator = testOps[operatorToken.value]
        #    
        #return 
    
    def parseSubscriptList(self, eotMarker=None):
        subscriptList = []
        while not self.testEOT() and (not eotMarker or not self.testKind(eotMarker)) and (self.testKind("opMap") or self.testKind("LSB")):
            if self.testKind("opMap"):
                self.acceptIt()
                #self.accept("next")                             # accept opMap
                # interprete id token as string
                strToken = self.accept("id")
                subscriptList.append(StrType(strToken.value))
            else:
                self.acceptIt()                                  # accept LSB
                subscriptList.append(self.parseAdd())
                self.accept("RSB")
        return subscriptList
    
    def parseVar(self):
        token = self.accept("id")
        subscriptList = self.parseSubscriptList()
        return Var(token.value, subscriptList, token=token)
    
    def parseImportList(self, argDelimiter, eotMarker=None):
        imports = []
        while not self.testEOT() and (not eotMarker or not self.testKind(eotMarker)):
            identifier = self.accept("id")
            if self.testKind("opAssign"):
                self.acceptIt()
                exportVar = self.parseVar()
            else:
                exportVar = Var(identifier.value, [], token=identifier)
            imports.append((identifier, exportVar))     # save as tuple in a list preserving the order in which the imports were listed
            if not self.testEOT() and (not eotMarker or not self.testKind(eotMarker)):
                self.accept(argDelimiter)
        return imports
    '''
    def parseImport(self):
        token = self.accept("opImport")
        importList = self.parseImportList("next", "from")
        self.accept("from")
        moduleToken = self.accept("id")
        self.accept("EC")
        return OpImport(importList, moduleToken.value, token=token)
    '''
    def parseFor(self):
        token = self.accept("for")
        self.accept("LP")
        varInit = self.parseLet(False)
        self.accept("EC")
        test = self.parseTest()
        self.accept("EC")
        varInc = self.parseLet(False)
        self.accept("RP")
        self.accept("LCB")
        body = self.parseCommandList("EC", "RCB")
        self.accept("RCB")
        return OpFor(varInit, test, varInc, body, token=token)
    '''
    def parseWhile(self):
        token = self.accept("while")
        self.accept("LP")
        test = self.parseTest()
        self.accept("RP")
        self.accept("LCB")
        body = self.parseCommandList("EC", "RCB")
        self.accept("RCB")
        return OpWhile(test, body, token=token)
    '''
    def parseLet(self, withLet=True):
        if withLet:
            letToken = self.accept("let")
        varToken = self.accept("id")
        subscriptList = self.parseSubscriptList()
        self.accept("opAssign")
        if self.testKind("func"):               # this is a function definition
            token = self.acceptIt()
            self.accept("LP")
            argList = self.parseArgumentList("next", "RP")
            self.accept("RP")
            useList = []
            if self.testKind("use"):
                self.acceptIt()
                self.accept("LP")
                useList = self.parseArgumentList("next", "RP")
                self.accept("RP")
            self.accept("LCB")
            funcAst = self.parseCommandList("EC", "RCB")
            self.accept("RCB")
            return OpLetFunc(varToken.value, subscriptList, argList, useList, funcAst, token=token)
        else:                                   # this is a "normal" var
            # allow ifs, fors and whiles in right hand sides of let statements (rust is a language also supporting ifs in the rhs)
            if self.testKind("if"):
                ast = self.parseIf()
            elif self.testKind("for"):
                ast = self.parseFor()
            elif self.testKind("while"):
                ast = self.parseWhile()
            else:
                ast = self.parseAdd()
        return OpLet(varToken.value, subscriptList, ast, token=letToken if withLet else varToken)
    
    def parseIf(self):
        ifList = []                             # this will contain all if/elif statements as tuple(testOp, ast)
        token = self.acceptIt()
        self.accept("LP")
        testIf = self.parseTest()
        self.accept("RP")
        self.accept("LCB")
        astIf = self.parseCommandList("EC", "RCB")
        self.accept("RCB")
        ifList.append({"test": testIf, "ast": astIf, "token": token})
        
        # add every new elif statement to our ifList
        while self.testKind("elif"):
            token = self.acceptIt()
            self.accept("LP")
            testElif = self.parseTest()
            self.accept("RP")
            self.accept("LCB")
            astElif = self.parseCommandList("EC", "RCB")
            self.accept("RCB")
            ifList.append({"test": testElif, "ast": astElif, "token": token})
        
        # handle else statement (this is independent of our ifList)
        astElse = None
        if self.testKind("else"):
            self.acceptIt()
            self.accept("LCB")
            astElse = self.parseCommandList("EC", "RCB")
            self.accept("RCB")
        
        # coalesce our ifList into a tree of OpIf instances and return the resulting AST (do this in reverse order to be semantically correct)
        ast = OpIf(ifList[-1]["test"], ifList[-1]["ast"], astElse, token=ifList[-1]["token"])
        if len(ifList) > 1:                     # only if at least one elif is present
            ifList = ifList[:-1]                # remove last entry already handled above
            ifList.reverse()
            for entry in ifList:
                ast = OpIf(entry["test"], entry["ast"], ast, token=entry["token"])
        return ast
    
    #add = mul add'
    def parseAdd(self):
        x1 = self.parseMul()
        return self.parseAddX(x1)
    
    #add' = ε
    #add' = "+" mul add'
    #add' = "-" mul add'
    def parseAddX(self, heap):
        if self.testEOT():                  # EOT --> epsilon production
            return heap
        if not self.testKind("opAS"):       # epsilon production
            return heap
        x1 = self.acceptIt()
        x2 = self.parseMul()
        if x1.value == "+":
            return self.parseAddX(OpAdd(heap, x2, token=x1))
        else:
            return self.parseAddX(OpSub(heap, x2, token=x1))
    
    #mul = term mul'
    def parseMul(self):
        x1 = self.parseTerm()
        return self.parseMulX(x1)
    
    #mul' = ε
    #mul' = "^" term mul'
    #mul' = "*" term mul'
    #mul' = "/" term mul'
    def parseMulX(self, heap):
        if self.testEOT():                    # EOT --> epsilon production
            return heap
        elif self.testKind("LP"):             # omitted '*' via '(', do not accept it, but let parseTerm() handle it
            x1 = self.currentToken
            x2 = self.parseTerm()
            return self.parseMulX(OpMul(heap, x2, token=x1))
        elif self.testKind("constVar"):       # omitted '*' via const var, do not accept it, but let parseTerm() handle it
            x1 = self.currentToken
            x2 = self.parseTerm()
            return self.parseMulX(OpMul(heap, x2, token=x1))
        elif self.testKind("opMD"):
            x1 = self.acceptIt()
            x2 = self.parseTerm()
            if x1.value == "*":
                return self.parseMulX(OpMul(heap, x2, token=x1))
            else:
                return self.parseMulX(OpDiv(heap, x2, token=x1))
        elif self.testKind("opPow"):
            x1 = self.acceptIt()
            x2 = self.parseTerm()
            return self.parseMulX(OpPow(heap, x2, token=x1))
        else:                                 # epsilon production
            return heap

    #term = term'
    #term = term' "!"
    def parseTerm(self):
        x1 = self.parseTermX()
        if self.testKind("opFac"):
            self.acceptIt()
            return OpFac(x1)
        return x1
    
    #term' = <num>
    #term' = "(" add ")"
    def parseTermX(self):
        constVarToASTTable = {
            "true": ConstTrue,
            "false": ConstFalse,
        }
        if self.testKind("LP"):
            self.acceptIt()
            # this is needed because our scanner does not detect negative numbers (e.g. "[…](-3)[…]" or "-3[…]" at the beginning of our input)
            if self.testKind("opAS") and self.currentToken.value == "-":
                self.acceptIt()
                subterm = self.parseAddX(self.parseMulX(OpSub(NumType(0), self.parseTerm())))
            else:
                subterm = self.parseAdd()
            self.accept("RP")
            return subterm
        # this is needed because our scanner does not detect negative numbers (e.g. "[…](-3)[…]" or "-3[…]" at the beginning of our input)
        elif self.testKind("opAS") and self.currentToken.value == "-":
            self.acceptIt()
            return self.parseAddX(self.parseMulX(OpSub(NumType(0), self.parseTerm())))
        elif self.testKind("num"):
            token = self.acceptIt()
            return NumType(token.value, token=token)
        elif self.testKind("str"):
            token = self.acceptIt()
            return StrType(token.value, token=token)
        elif self.testKind("null"):
            token = self.acceptIt()
            return NullType(token=token)
        elif self.testKind("call"):             # "@" before id --> this is a function call
            callToken = self.acceptIt()
            var = self.parseVar()
            self.accept("LP")
            argsAst = self.parseCommandList("next", "RP")
            self.accept("RP")
            return OpCall(var, argsAst, token=callToken)
        elif self.testKind("id"):               # identifier: var name or function name
            return self.parseVar()
        elif self.testKind("constVar"):         # const var with predefined value
            token = self.acceptIt()
            if token.value in constVarToASTTable:
                return constVarToASTTable[token.value](token=token)
        elif self.testKind("LSB"):              # map literal
            token  = self.acceptIt()
            mapLiteral = self.parseMapList("next", "RSB")
            self.accept("RSB")
            return MapType(mapLiteral, token=token)
        elif self.testKind("sqrt"):
            x1 = self.acceptIt()
            if not self.testKind("LP"):         # only check, but don't accept it, yet (e.g. look ahead)
                self._raiseSyntaxError()        # sqrt needs an opening parenthesis after it
            x2 = self.parseTerm()
            return OpSqrt(x2, token=x1)
        elif self.testKind("sin"):
            x1 = self.acceptIt()
            if not self.testKind("LP"):         # only check, but don't accept it, yet (e.g. look ahead)
                self._raiseSyntaxError()        # sin needs an opening parenthesis after it
            x2 = self.parseTerm()
            return OpSin(x2, token=x1)
        elif self.testKind("cos"):
            x1 = self.acceptIt()
            if not self.testKind("LP"):         # only check, but don't accept it, yet (e.g. look ahead)
                self._raiseSyntaxError()        # cos needs an opening parenthesis after it
            x2 = self.parseTerm()
            return OpCos(x2, token=x1)
        
        self._raiseSyntaxError()
