from internals.parser import Parser
from internals.scanner import Scanner
from internals.errors import InputError
from internals.ast import State
from internals.errors import InterpreterError

# cache already evaluated module exports and handle import cycles
cache = {}
runList = []

def _debug(text):
    #print(text)
    return

# used for better error formatting below
def _prefixRow(scanner, row, col):
    inputRow = scanner.getInputRow(row)
    # return empty text and empty padding if the row was empty (e.g. this row won't be printed at all)
    if inputRow != None:
        if inputRow.strip() == "":
            return ("", "")
        rowPrefix = "% 4d: " % row
        indentation = inputRow[:-len(inputRow.lstrip())]
        padding = indentation + (" " * (col-1-len(indentation)))
        padding = " " * len(rowPrefix) + padding
        return ("%s%s" % (rowPrefix, inputRow), padding)
    else:
        pass

def _printError(e):
    if not hasattr(e, "already_handled") or not e.already_handled:
        e.already_handled = True
        print("%s at line %d, column %d: %s" % (
            str(e.__class__.__name__),
            e.token.row,
            e.token.col,
            str(str(e)),
        ))
        # if we have a file, create a new scanner and use it to return the line corresponding to our error
        if e.token.text:
            ''' because its just one row
            scanner = Scanner(e.token.text)
            if e.token.row > 2:
                (row, padding) = _prefixRow(scanner, e.token.row-1, e.token.col)
                if row != "":
                    print(row)
            (row, padding) = _prefixRow(scanner, e.token.row, e.token.col)
            print("%s\n%s^\n%shere" % (
                row,
                padding,
                padding,
            ))
            #(row, padding) = _prefixRow(scanner, e.token.row+1, e.token.col)
            if row != "":
                print(row)'''
        print("")
        print("Interpreter backtrace:")
    raise e

def run(text, entrys, token=None):
    global cache, runList
    try:
        if text in runList:
            runList.append(text)        # add our own file to the cycle list do make the error output more meaningful
            raise InterpreterError("Import cycle detected: %s" % str(runList), token)
        runList.append(text)
        
        if str(text) in cache:
            _debug("Using cached module result of '%s'..." % str(text))
            result = cache[text]
            _debug("MODULE '%s' RESULT: %s" % (str(text), str(result)))
            runList = runList[:-1]
            return result
        else:
            cache[text] = None          # dummy value to break import cycles, will be filled with real result later on
        
        _debug("Loading file '%s'..." % str(text))
        ast = Parser(Scanner(text)).parse()
        _debug("AST: %s" % str(ast))
        _debug("Executing...")
        result = None                   # default value for an empty AST
        if ast:
            print(entrys)
            # run (sub-) module within its own state (only the result can leak into other states via import statements)
            result = ast({"state": State(entrys)})
        _debug("MODULE '%s' RESULT: %s" % (str(text), str(result)))
        cache[text] = result
        runList = runList[:-1]
        return result
    except InputError as e:
        _printError(e)
        runList = runList[:-1]
        return None
