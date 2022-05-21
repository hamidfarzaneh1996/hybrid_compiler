import enum

# selected_file = "./stencils/seidel-2d/seidel-2d.mlir"
# selected_file = "./stencils/jacobi-2d/jacobi-2d.mlir"
selected_file = "./test/conv2d.mlir"

# Using enum class create enumerations
class SupportedOperation(enum.Enum):
   arith_index_cast = 1 # arith.index_cast
   arith_constant = 2 # arith.constant 
   arith_addf = 3 # arith.addf
   arith_mulf = 4 # arith.mulf

   affine_load = 11 # affine.load
   affine_store = 12 # affine.store
   affine_apply = 13 # affine.apply

   memref_alloc = 21 # memref.alloc()
   memref_copy = 22 # memref.copy
   

class SupportedTypes(enum.Enum):
   i32 = 1 
   i64 = 2 
   index = 3 
   f32 = 4
   f64 = 5
   memref = 6

class LoopType(enum.Enum):
    parallel = 1
    forLoop = 2

class Variable:
    def __init__(self, name):
        self.name = name

    def setInitVal(self, val):
        self.val= val 

    def setValType(self, type):
        self.type = type

class Operation:
    def __init__(self):
        self.inVars = {}

    def setOutputVar(self, val):
        self.outputVal = val

    def setOutputType(self, type):
        self.outputType = type 

    def setInVar(self, val, index):
        self.inVars[index] = val

    def setOperation(self, operation):
        self.operation= operation 

    def setAdditionalInfo(self, info):
        self.info = info
    
    
class Loop:
    def __init__(self, start, end):
        self.args = {}
        self.start = start
        self.end = end 
        self.forLoopCount = 0
        self.forLoops = []
        self.operations = []
        self.parallelLoopCount = 0
        self.parallelLoops=[]

    def setLoopType(self, type):
        self.type = type

    def setLoopLocalVariales(self, var ):
        self.localVariables[var.name] = var

    def addForLoop(self, forLoop):
        self.forLoops += [forLoop]
        self.forLoopCount += 1

    def addOperation(self, op):
        self.operations += [op]

    def addParallelLoop(self, parallelLoop):
        self.parallelLoops += [parallelLoop]
        self.parallelLoopCount += 1




class Function:

    def __init__(self, name):
        self.name = name
        self.args = {}
        self.forLoopCount = 0
        self.forLoops = []
        self.parallelLoopCount = 0
        self.parallelLoops = []
        self.operations = []

    def setArgsByArray(self, args):
        for arg in args:
            argName = arg.split(":")[0]
            argType = arg.split(":")[1]
            newVar = Variable(argName)
            newVar.setValType(argType)
            self.args[argName] = newVar

    def setFuncLocalVariales(self, var ):
        self.localVariables[var.name] = var
    
    def addForLoop(self, forLoop):
        self.forLoops += [forLoop]
        self.forLoopCount += 1

    def addParallelLoop(self, parallelLoop):
        self.parallelLoops += [parallelLoop]
        self.parallelLoopCount += 1

    def addOperation(self, op):
        self.operations += [op]

def handleType(typeStr):
    if (typeStr == "index"):
        return SupportedTypes.index
    elif (typeStr == "i32"):
        return SupportedTypes.i32
    elif (typeStr == "i64"):
        return SupportedTypes.i64
    elif (typeStr == "f32"):
        return SupportedTypes.f32
    elif (typeStr == "f64"):
        return SupportedTypes.f64
    elif (typeStr.find("memref")!= -1):
        return SupportedTypes.memref

    print("Not handled type " + typeStr)
    exit()

    
def parse_arith_index_cast(line):
    # print(line)
    output = line.split(" = ")[0]
    input = line.split(" ")[3]
    type = line.split(" ")[7]
    op = Operation()
    op.setInVar(input, 1)
    op.setOutputVar(output)
    op.setOperation(SupportedOperation.arith_index_cast)
    op.setOutputType(handleType(type))
    return op

def parse_arith_constant(line):
    # print(line)
    output = line.split(" = ")[0]
    input = line.split(" ")[3]
    type = line.split(" ")[5]
    op = Operation()
    op.setInVar(input, 1)
    op.setOutputVar(output)
    op.setOperation(SupportedOperation.arith_constant)
    op.setOutputType(handleType(type))
    return op

def parse_arith_addf(line):
    # print(line)
    output = line.split(" = ")[0]
    input1 = line.split(" ")[3].split(",")[0]
    input2 = line.split(" ")[4]
    type = line.split(" : ")[1]
    op = Operation()
    op.setInVar(input1, 1)
    op.setInVar(input2, 1)
    op.setOutputVar(output)
    op.setOperation(SupportedOperation.arith_addf)
    op.setOutputType(handleType(type))
    return op

def parse_arith_mulf(line):
    # print(line)
    output = line.split(" = ")[0]
    input1 = line.split(" ")[3].split(",")[0]
    input2 = line.split(" ")[4]
    type = line.split(" : ")[1]
    op = Operation()
    op.setInVar(input1, 1)
    op.setInVar(input2, 1)
    op.setOutputVar(output)
    op.setOperation(SupportedOperation.arith_mulf)
    op.setOutputType(handleType(type))
    return op

def parse_affine_load (line):
    # print(line)
    output = line.split(" = ")[0]
    input = line.split(" = ")[1].split("affine.load")[1].split(" : ")[0].strip()
    type = line.split(" : ")[1]
    op = Operation()
    op.setInVar(input, 1)
    op.setOutputVar(output)
    op.setOperation(SupportedOperation.affine_load)
    op.setOutputType(handleType(type))
    op.setAdditionalInfo(type)
    return op

def parse_affine_store (line):
    # print(line)
    type = line.split(" : ")[-1]
    line = "".join(line.split(" : ")[:-1])
    input1 = line.split("affine.store")[1].split(", ")[0]
    input2 = ", ".join(line.split("affine.store")[1].split(", ")[1:])
    op = Operation()
    op.setInVar(input1, 1)
    op.setInVar(input2, 2)
    op.setOperation(SupportedOperation.affine_store)
    op.setOutputType(handleType(type))
    op.setAdditionalInfo(type)
    return op

def parse_affine_apply (line):
    # print(line)
    output = line.split(" = ")[0]
    input = line.split(" = ")[1].split("affine.apply")[1].strip()
    op = Operation()
    op.setInVar(input, 1)
    op.setOutputVar(output)
    op.setOperation(SupportedOperation.affine_apply)
    return op

def parse_memref_alloc (line):
    # print(line)
    output = line.split(" = ")[0]
    input = line.split(" = ")[1].split("memref.alloc()")[1].split(" : ")[0].strip()
    type = line.split(" : ")[-1]
    op = Operation()
    op.setInVar(input, 1)
    op.setOutputVar(output)
    op.setOperation(SupportedOperation.memref_alloc)
    op.setOutputType(handleType(type))
    op.setAdditionalInfo(type)
    return op

def parse_memref_copy (line):
    # print(line)
    line = line[12:]
    fromVar = line.split(" : ")[0].split(", ")[0]
    toVar = line.split(" : ")[0].split(", ")[1]
    outputType1 = line.split(" : ")[1].split(" to ")[0]
    outputType2 = line.split(" : ")[1].split(" to ")[1]
    # print(fromVar, toVar, outputType1, outputType2)
    op = Operation()
    op.setInVar(fromVar, 1)
    op.setOutputVar(toVar)
    op.setOperation(SupportedOperation.memref_copy)
    op.setOutputType(handleType(outputType1))
    op.setAdditionalInfo(outputType1 + " " + outputType2)
    return op

def parseOperation(line):
    # print(line)
    operation = line.split(" = ")[1].split(" ")[0]
    if(operation == "arith.index_cast"):
        return parse_arith_index_cast(line)
    elif(operation == "arith.constant"):
        return parse_arith_constant(line)
    elif(operation == "arith.addf"):
        return parse_arith_addf(line)
    elif(operation == "arith.mulf"):
        return parse_arith_mulf(line)
    elif(operation == "affine.load"):
        return parse_affine_load(line)
    elif(operation == "affine.apply"):
        return parse_affine_apply(line)
    elif(operation == "memref.alloc()"):
        return parse_memref_alloc(line)

    else:
        print("not handled " + operation)
        print(line)
        exit()

def parseNoOutOperation(line):
    if(line.startswith("affine.store")):
        return parse_affine_store(line)
    elif(line.startswith("memref.copy")):
        return parse_memref_copy(line)

def parseIns(inputFile, block):
    line = ""
    while(True):
        line = inputFile.readline().strip()
        print(line)
        if(line == "}" or line == "return"):
            return

        if(line.startswith("affine.for") or line.startswith("affine.parallel")):
            line = line[11:]
            startVarStr = line.split("to")[0].replace(" ", "")
            startVar = Variable(startVarStr.split("=")[0])
            startVar.setInitVal(startVarStr.split("=")[1])

            endVarStr = line.split("to")[1].replace(" ", "")[:-1]
            endVar = Variable(endVarStr.split("=")[0])
            
            newForLoop = Loop(startVar, endVar)
            parseIns(inputFile, newForLoop)
            if(line.startswith("affine.for")):
                block.addForLoop(newForLoop) 
                newForLoop.setLoopType(LoopType.forLoop)
            else:
                block.addParallelLoop(newForLoop) 
                newForLoop.setLoopType(LoopType.parallel)
            continue


        if(line.startswith("%")):
            block.addOperation(parseOperation(line))
        elif (line.startswith("affine.store")):
            block.addOperation(parseNoOutOperation(line))
        elif (line.startswith("memref.copy")):
            block.addOperation(parseNoOutOperation(line))
        else:
            print("not handled " + line)

       


    

def parseIR(fileName):
    file = open(fileName, "r")

    # parse_state = PARSE_STATE_NEUTRAL
    loopNestIndex = 0  

    while(True):
        line = file.readline()
        if(len(line)==0):
            return
            
        line = line[:-1].strip()
        if(line.startswith("func")):

            func_name = line.split(" ")[1].split("(")[0][1:]
            currFunc = Function(func_name)
                
            argSets = line.split("(")[1].split(")")[0].replace(" ", "").split(",")
            currFunc.setArgsByArray(argSets)    

            print("func " + func_name + " started")

            parseIns(file, currFunc)

            continue
  

parseIR(selected_file)





