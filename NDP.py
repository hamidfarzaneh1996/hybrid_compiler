
from code_structure import *
from operation import * 
from NDPOps import *
import enum 


class NDPKernel:
    def __init__ (self, inputVars, name):
        self.type = type
        self.vars = inputVars
        self.name = name
        self.ins = []

    def addIns(self, ins):
        self.ins += ins


        
class NDPSystem:
    serial_loop_counter = 0
    ndp_temp_reg_counter = 0
    host_temp_reg_counter = 0
    ndp_kernel_count = 0

    def __init__ (self):
        self.hostKernels = []
        self.ndpKernels = {}
    
    def addHostKernel(self, kernel):
        self.hostKernels += [kernel]

    def addNDPKernel(self, kernel):
        self.ndpKernels += [kernel]
    
    def evalDic(self, variableDic, variable):
        if(variable in variableDic):
            return variableDic[variable]
        return variable 

    def parseIns(self, ins, mapsParser, isKernel, variableDic):
        if(isinstance(ins,Loop)):
            if(ins.type == LoopType.forLoop):
                res = []
                op = NDPSysOperation(NDPSysOps.MOV)
                labelOp = NDPSysOperation(NDPSysOps.LABEL)
                cmpOp = NDPSysOperation(NDPSysOps.CMP)
                cmpOp.setOutputVar("temp" +str(self.ndp_temp_reg_counter))
                jtOp = NDPSysOperation(NDPSysOps.JT)
                jtOp.setInputVars("temp"+str(self.ndp_temp_reg_counter), 1)
                self.ndp_temp_reg_counter += 1

                endLabelOp = NDPSysOperation(NDPSysOps.LABEL)
                    
               

                op.setOutputVar(ins.start.name)
                op.setInputVars(ins.start.val, 1)
                labelOp.setInputVars(self.serial_loop_counter, 1)
                self.serial_loop_counter += 1
                endLabelOp.setInputVars(self.serial_loop_counter, 1)
                cmpOp.setInputVars(ins.start.name, 1)
                cmpOp.setInputVars(ins.end.name, 2)
                jtOp.setOutputVar(self.serial_loop_counter)
                self.serial_loop_counter += 1
                res += [op, labelOp, cmpOp, jtOp]
                
                for l_ins in ins.getIns():
                    newIns, variableDic = self.parseIns(l_ins, mapsParser, isKernel, variableDic)
                    res += newIns

                addOp = NDPSysOperation(NDPSysOps.ADD)
                jOp = NDPSysOperation(NDPSysOps.J)

                addOp.setInputVars(ins.start.name, 1) 
                addOp.setInputVars(1, 2) 
                addOp.setOutputVar(ins.start.name)
                jOp.setInputVars(self.serial_loop_counter-2, 1)
                res += [addOp, jOp, endLabelOp]
                return res, variableDic
            else:
                print("parallel Loop " + ins.start.val + " " + ins.end.val)


        elif(ins.operation == SupportedOperation.affine_apply):
            return mapsParser.applyNDP(ins, isKernel, variableDic), variableDic

        elif(ins.operation == SupportedOperation.arith_index_cast):
            variableDic[ins.outputVal] = ins.inVars[1]
            return [], variableDic

        elif(ins.operation == SupportedOperation.arith_constant):
            movOp = NDPSysOperation(NDPSysOps.MOV)
            movOp.setOutputVar(ins.outputVal)
            movOp.setInputVars(self.evalDic(variableDic, ins.inVars[1]), 1)
            return [movOp], variableDic
        elif(ins.operation == SupportedOperation.arith_addf):
            addfOp = NDPSysOperation(NDPSysOps.ADDF)
            addfOp.setOutputVar(ins.outputVal)
            addfOp.setInputVars(self.evalDic(variableDic, ins.inVars[1]), 1)
            addfOp.setInputVars(self.evalDic(variableDic, ins.inVars[2]), 2)
            return [addfOp], variableDic

        elif(ins.operation == SupportedOperation.arith_mulf):
            if(isKernel):
                mulfOp = NDPSysOperation(NDPSysOps.MULF)
            else:
                mulfOp = NDPSysOperation(NDPSysOps.MULF)
            mulfOp.setOutputVar(ins.outputVal)
            mulfOp.setInputVars(self.evalDic(variableDic, ins.inVars[1]), 1)
            mulfOp.setInputVars(self.evalDic(variableDic, ins.inVars[2]), 2)
            return [mulfOp], variableDic

        elif(ins.operation == SupportedOperation.affine_load):
            if(isKernel):
                loadOp = NDPSysOperation(NDPSysOps.LOAD)
            else:
                loadOp = NDPSysOperation(NDPSysOps.LOAD)
            
            baseAddress = ins.inVars[1].split("[")[0]
            indexes = ins.inVars[1].split("[")[1][:-1].split(", ")
            for i in range (len(indexes)):
                if(indexes[i] in variableDic):
                    indexes[i] = variableDic[indexes[i]]
            loadOp.setInputVars(self.evalDic(variableDic, baseAddress), 1)
            loadOp.setInputVars(indexes, 2)
            loadOp.setOutputVar(ins.outputVal)
            loadOp.setAdditionalInfo(ins.info)
            return [loadOp], variableDic

        elif(ins.operation == SupportedOperation.affine_store):
            storeOp = NDPSysOperation(NDPSysOps.STORE)
            baseAddress = ins.inVars[2].split("[")[0]
            indexes = ins.inVars[2].split("[")[1][:-1].split(", ")
            for i in range (len(indexes)):
                if(indexes[i] in variableDic):
                    indexes[i] = variableDic[indexes[i]]
            # print(baseAddress,indexes)
            storeOp.setInputVars(self.evalDic(variableDic, baseAddress), 1)
            storeOp.setInputVars(indexes, 2)
            storeOp.setOutputVar(ins.inVars[1])
            storeOp.setAdditionalInfo(ins.info)
            return [storeOp], variableDic
        elif(ins.operation == SupportedOperation.memref_alloc):
            print("not implemented !")
        elif(ins.operation == SupportedOperation.memref_copy):
            print("not implemented !")
        else:
            print("not implemetned " + ins.operation)

        return []

        

    def addLoopStartIns(self, ins, host_temp_reg_counter, serial_loop_counter):
        res = []
        op = NDPSysOperation(NDPSysOps.MOV)
        labelOp = NDPSysOperation(NDPSysOps.LABEL)
        cmpOp = NDPSysOperation(NDPSysOps.CMP)
        cmpOp.setOutputVar("temp"+str(host_temp_reg_counter))
        jtOp = NDPSysOperation(NDPSysOps.JT)
        jtOp.setInputVars("temp"+str(host_temp_reg_counter), 1)


        op.setOutputVar(ins.start.name)
        op.setInputVars(ins.start.val, 1)
        labelOp.setInputVars(serial_loop_counter, 1)
        cmpOp.setInputVars(ins.start.name, 1)
        cmpOp.setInputVars(ins.end.name, 2)
        jtOp.setOutputVar(serial_loop_counter+1)
        return [op, labelOp, cmpOp, jtOp]
        
    def addLoopEndIns(self, ins, serial_loop_counter):
        addOp = NDPSysOperation(NDPSysOps.ADD)
        jOp = NDPSysOperation(NDPSysOps.J)
        endLabelOp = NDPSysOperation(NDPSysOps.LABEL)
        endLabelOp.setInputVars(serial_loop_counter+1, 1)

        addOp.setInputVars(ins.start.name, 1) 
        addOp.setInputVars(1, 2) 
        addOp.setOutputVar(ins.start.name)
        jOp.setInputVars(serial_loop_counter, 1)
        return [addOp, jOp, endLabelOp]

    def splitHelperHost(self, block, mapsParser):

        hostInst = []
        localVariables = {}
        variableDic = {}

        for ins in block.getIns():
            if(isinstance(ins,Loop)):
                if(ins.type == LoopType.parallel):
                    currLoopCounter = self.serial_loop_counter
                    currHostRegCounter = self.host_temp_reg_counter
                    self.serial_loop_counter += 1
                    self.host_temp_reg_counter += 1

                    localVars = [ins.start.name, ins.end.name]
                    hostInst += self.addLoopStartIns(ins, currHostRegCounter, currLoopCounter)
                    
                    j = 2 
                    tempIns = []
                    loopCount = 1
                    while(True):
                        if(len(ins.ins) == 1 and ins.ins[0].type == LoopType.parallel):
                            self.host_temp_reg_counter+=2
                            self.serial_loop_counter+=1
                            localVars += [ins.ins[0].start.name, ins.ins[0].end.name]
                            tempIns += [ins.ins[0]]
                            hostInst += self.addLoopStartIns(ins.ins[0], self.host_temp_reg_counter, self.serial_loop_counter)
                            j += 2
                            ins = ins.ins[0]
                            loopCount += 1
                        
                        else:
                            self.serial_loop_counter+=2

                            newKernel = NDPKernel(localVars, self.ndp_kernel_count)
                            for l_ins in ins.ins:
                                newKernel.addIns(self.parseIns(l_ins, mapsParser, True, variableDic)[0])
                                # print(self.parseIns(l_ins, mapsParser, True, variableDic)[0])
                            self.ndpKernels[self.ndp_kernel_count] = newKernel

                            callNDPOp = NDPSysOperation(NDPSysOps.CALL_NDP)
                            for i in range (len(localVars)):
                                callNDPOp.setInputVars(localVars[i], i)
                            callNDPOp.setOutputVar("NDPKernel" + str(self.ndp_kernel_count))
                            self.ndp_kernel_count += 1
                            hostInst+= [callNDPOp]
                            break 

                    j -= 2
                    i = 2
                    while(i <= j):
                        hostInst += self.addLoopEndIns(tempIns[-1], self.serial_loop_counter - i*2)
                        tempIns = tempIns[:-1]
                        i += 2
                    hostInst += self.addLoopEndIns(ins, currLoopCounter)
                    


                else:
                    print("Handle here1")


            elif (isinstance(ins, Operation)):
                if(ins.operation == SupportedOperation.affine_apply):
                    print("Handle here 2")
                    # seq = ""
                    # for newIns in mapsParser.apply(ins):

                    #     seq += ("\t" + newIns + "\n")
                    # instruction_sequence += (seq)

                elif(ins.operation == SupportedOperation.arith_constant):
                    newIns, variableDic = self.parseIns(ins,mapsParser, False, {})
                    hostInst += newIns
                elif(ins.operation == SupportedOperation.arith_index_cast):
                    newIns, variableDic = self.parseIns(ins,mapsParser, False, {})
                    hostInst += newIns

                elif(ins.operation == SupportedOperation.arith_addf):
                    print("Handle here 4")

                elif(ins.operation == SupportedOperation.arith_mulf):
                    print("Handle here 5")

                else:
                    print("Handle here 6")
            else:
                instruction_sequence += "Unknown\n"
        # self.printNDPIns(ndpKernels, -1)
        return hostInst 
    

    def splitToHostNDP(self, workload):
        fileName = "host_ins.txt"
        file = open(fileName, "w+")
        for module in workload.getModules():
            for func in module.getFuncs():
                # print("<-- func " + func.name + " starts -->")
                self.writeFuncArgs(func.args, file)
                hostInst = self.splitHelperHost(func, workload.mapsParser)
                self.writeFullIns(hostInst, file)
                for i in range (self.ndp_kernel_count):
                    file = open("NDPKernel"+str(i) + ".txt", "w+")
                    self.writeFullIns(self.ndpKernels[i].ins, file)
                    # print(self.ndpKernels[i].ins)
                # print("<-- func " + func.name + " ends -->")

    def writeFuncArgs(self, args, file):
        file.write("---args---\n")
        for arg in args:
            file.write(arg + " : " + args[arg].type + "\n")
        file.write("---end-args---\n")
    
    def writeFullIns(self, insArray, file):
        for ins in insArray:
    
            if(ins.getOperationType() == NDPSysOps.LABEL):
                file.write("LABEL" + str(ins.inVars[1]) + ":" + "\n")
            elif(ins.getOperationType() == NDPSysOps.LOAD):
                file.write("LOAD " + ins.getOutVar() + ", " + str(ins.inVars[1]) + str(ins.inVars[2])+ "\n")
            elif(ins.getOperationType() == NDPSysOps.STORE):
                file.write("STORE " + str(ins.getOutVar()) + ", " + str(ins.inVars[1]) + str(ins.inVars[2])+ "\n")
            elif(ins.getOperationType() == NDPSysOps.MOV):
                file.write("MOV " + ins.getOutVar() + ", " + ins.inVars[1]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.ADD):
                file.write("ADD " + str(ins.getOutVar()) + ", " + str(ins.inVars[1]) + ", " + str(ins.inVars[2])+ "\n")
            elif(ins.getOperationType() == NDPSysOps.SUB):
                file.write("SUB " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.MUL):
                file.write("MUL " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.DIV):
                file.write("DIV " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.MOD):
                file.write("MOD " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.FLOORDIV):
                file.write("FLOORDIV " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.ADDF):
                file.write("ADDF " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.SUBF):
                file.write("SUBF " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.MULF):
                file.write("MULF " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.DIVF):
                file.write("DIVF " + ins.getOutVar() + ", " + ins.inVars[1] + ", " + ins.inVars[2]+ "\n")
            elif(ins.getOperationType() == NDPSysOps.CMP):
                file.write("CMP " + str(ins.getOutVar()) + ", " + str(ins.inVars[1]) + ", " + str(ins.inVars[2])+ "\n")
            elif(ins.getOperationType() == NDPSysOps.JT):
                file.write("JT " + str(ins.getInvar(1)) + ", LABEL" + str(ins.getOutVar())+ "\n")
            elif(ins.getOperationType() == NDPSysOps.J):
                file.write("J LABEL" + str(ins.getInvar(1))+ "\n")
            elif(ins.getOperationType() == NDPSysOps.CALL_NDP):
                file.write("CALL_NDP " + ins.getOutVar() + ", " + str(ins.inVars.values())+ "\n")
            else:
                file.write("!!" + str(ins.getOperationType()))


        # print(insArray)
        # print("___END___")

