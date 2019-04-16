"""
语法分析
"""
from error import SyntaxError
import copy

class Syntax:

    def __init__(self):
        self.grammar = []
        self.itemSet = []
        self.DFA = []
        self.Vn = []
        self.Vt = []
    def closure(self, item):
        dot = []
        dot.append(item)
        olddot = []
        while len(dot) != len(olddot):
            olddot = copy.deepcopy(dot)
            temp = []
            for i in range(len(dot)):
                for j in range(len(self.itemSet)):
                    if dot[i].index('·')+1 < len(dot[i]) and dot[i][dot[i].index('·')+1] == self.itemSet[j][0] and self.itemSet[j][self.itemSet[j].index('>')+1] == '·':
                        temp.append(self.itemSet[j])
            for k in range(len(temp)):
                if temp[k] not in dot:
                    dot.append(temp[k])
        return dot

    def goto(self, item, a):
        for i in range(len(item)):
            if item[i] == '·' and i != len(item)-1:
                if item[i+1] == a:
                    item2 = item[:i]+item[i+1]+'·'+item[i+2:]
                    if item2 in self.itemSet:
                        return item2
        return -1

    def findItem(self, item):
        for i in range(len(self.DFA)):
            if item in self.DFA[i]:
                return i
        return -1

    def anlyse(self,syntax,text):
        for i in range(len(syntax)):
            temp = syntax[i]
            if i == 0:
                self.grammar.append('S\'->'+temp[0])
            self.grammar.append(temp)
            for j in range(len(temp)):
                if temp[j].isupper() and temp[j] not in self.Vn:
                    self.Vn.append(temp[j])
                elif temp[j].islower() and temp[j] not in self.Vt:
                    self.Vt.append(temp[j])
        self.Vn.sort()
        self.Vt.sort()
        for i in range(len(self.grammar)):
            flag = 0
            for j in range(len(self.grammar[i])):
                if self.grammar[i][j] == '>':
                    flag = 1
                if flag == 1 and self.grammar[i][j] != '>':
                    temp = self.grammar[i][:j]+'·'+self.grammar[i][j:]
                    self.itemSet.append(temp)
            self.itemSet.append(self.grammar[i]+'·')
        
        
        print(self.grammar)
        self.DFA.append(self.closure(self.itemSet[0]))
        
        oldDFA = []
        
        while len(oldDFA) != len(self.DFA):
            oldDFA = copy.deepcopy(self.DFA)
            temp = []
            tDFA = []
            for i in range(len(self.DFA)):
                for j in range(len(self.DFA[i])):
                    position = self.DFA[i][j].index('·')
                    if position != len(self.DFA[i][j]) - 1:
                        # print('@',goto(DFA[i][j], DFA[i][j][position+1]))
                        tDFA.append(self.closure(self.goto(self.DFA[i][j], self.DFA[i][j][position+1])))
            for k in range(len(tDFA)):
                if tDFA[k] not in self.DFA:
                    self.DFA.append(tDFA[k])
        
        
        print(self.DFA)
        
        for i in range(len(self.DFA)):
            for j in range(len(self.DFA[i])):
                if len(self.DFA[i][j][-1]) == '·' and len(self.DFA[i]) != 1:
                    print('非LR(0)文法')
                    break
        
        print(len(self.DFA))
        DFAtable = []
        
        for i in range(len(self.DFA)):
            table = []
            for j in range(len(self.DFA[i])):
                position = self.DFA[i][j].index('·')
                if position == len(self.DFA[i][j])-1:
                    temp = self.DFA[i][j][:-1]
        
                    table = [self.grammar.index(temp)]*(len(self.Vt)+1)
                    break
                for k in range(len(self.Vt)):
                    if self.DFA[i][j][position+1] == self.Vt[k]:
                        temp = self.Vt[k]+'S'+str(self.findItem(self.goto(self.DFA[i][j], self.Vt[k])))
                        table.append(temp)
                for m in range(len(self.Vn)):
                    if self.DFA[i][j][position+1] == self.Vn[m]:
                        temp = self.Vn[m]+str(self.findItem(self.goto(self.DFA[i][j], self.Vn[m])))
                        table.append(temp)
            DFAtable.append(table)
        
        
        # 判断是否为LR(0)文法
        flag = 0
        for i in range(len(DFAtable)):
            for j in range(len(DFAtable)):
                if len(self.DFA[i][j]) > 2:
                    print('非LR(0)文法')
                    flag = 1
                    break
            if flag == 1:
                break
        
        print(DFAtable)
        
        VtVn = self.Vt + ['#'] + self.Vn
        LR0TABLE = [[' ' for col in range(len(VtVn))] for row in range(len(self.DFA)+1)]
        
        print('------------------------------------------------')
        print('状态\t\t\t\tAction\t\t\t\t GOTO')
        
        for i in range(len(VtVn)):
            LR0TABLE[0][i] = VtVn[i]+' '
        
        
        for i in range(len(DFAtable)):
            if 0 in DFAtable[i]:
                LR0TABLE[2][VtVn.index('#')] = 'acc'
                continue
            for j in range(len(DFAtable[i])):
                try:
                    LR0TABLE[i+1][VtVn.index(DFAtable[i][j][0])] = DFAtable[i][j][1:]
                except:
                    for k in range(len(self.Vt)+1):
                        LR0TABLE[i+1][k] = 'r'+str(DFAtable[i][j])
        
        print('     ')
        for i in range(len(LR0TABLE)):
            print('    ',end=' ')
            for j in range(len(LR0TABLE[i])):
                print(LR0TABLE[i][j], end='     ')
            print('')

        string = text
        string += '#'
        status = [0]
        oper = ['#']
        action = []
        
        flag = 0
        while flag != 1:
            symbol = string[0]
            try:
                if LR0TABLE[status[-1] + 1][VtVn.index(symbol)] != ' ' and LR0TABLE[status[-1] + 1][VtVn.index(symbol)][
                    0] != 'r':
                    if LR0TABLE[status[-1] + 1][VtVn.index(symbol)] == 'acc':
                        flag = 1
                        print('接受！')
                        break
                    status.append(int(LR0TABLE[status[-1] + 1][VtVn.index(symbol)][-1]))
                    oper.append(symbol)
                    string = string[1:]
                    # action.append(LR0TABLE[status[-1] + 1][VtVn.index(symbol)])
                    print(status)
                    print(oper)
                    print('')
        
                elif LR0TABLE[status[-1] + 1][VtVn.index(symbol)][0] == 'r':
                    position = int(LR0TABLE[status[-1] + 1][VtVn.index(symbol)][1])
                    Vnc = self.grammar[position][0]
                    Grlen = len(self.grammar[position]) - self.grammar[position].index('>') - 1
                    status = status[:-Grlen]
                    oper = oper[:-Grlen]
                    oper.append(Vnc)
                    addx = int(LR0TABLE[status[-1] + 1][VtVn.index(Vnc)])
                    status.append(int(addx))
                    print(status)
                    print(oper)
                    print('')
                    # action.append(str(LR0TABLE[status[-1] + 1][VtVn.index(symbol)]))
                else:
                    print('错误')
                    break
            except ValueError as e:
                print('错误')
syntax_sm = [

    "D->Lif",
    "L->a"

]
text="aif"
syntax_new=Syntax()
syntax_new.anlyse(syntax_sm,text)
