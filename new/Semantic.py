# -*- coding: utf-8 -*-
"""Syntax Analyzer ver.20190415
This program is used to analyze syntax which follows the MIT open source agreement.

@Author:YunMao

How to use it?
"""
import json
from pprint import pprint
from copy import deepcopy
from lexical import Lexical
from lexical import Token
from error import SyntaxError


class Semantic:
    def __init__(self, name):
        """构造非终结符的属性
        参数：
        --------
        s_type: 综合属性
        """
        self.token_name = name
        self.s_type = ''
        self.s_value = ''
        self.s_addr = ''
        self.s_width = 0
        self.s_offset = 0
        self.i_offset = 0
        self.i_next = 0
        self.s_truelist = []
        self.s_falselist = []
        self.s_instr=0
        self.s_nextlist=[]

class Syntax:
    terminator = set()

    def get_error(self):
        """
        获取错误
        :return: 错误原因
        """
        return self.__error

    def __init__(self, log_level=2, sharp='#', point='.', acc='acc', productions_file='C:\\Users\\YunMao\\Desktop\\Coding\\Compiler\\new\\productions1.txt'):
        self.__error = list()
        self.log_level = log_level  # log显示等级（仅因为显示太多烦）
        with open(productions_file, 'r') as f:
            lines = f.readlines()
            self.start = json.loads(lines[0])
            self.productions = json.loads(lines[1])
        self.nonterminals = self.productions.keys()

        self.get_terminator()  # 获取终结符集合
        self.sharp = sharp
        self.first = {nontermainal: {} for nontermainal in self.nonterminals}
        self.follow = {nontermainal: set()
                       for nontermainal in self.nonterminals}
        self.get_first_follow()  # 构建First和Follow集合

        # 计算项
        self.new_start = self.start + "'"
        self.point = point
        self.items = {key: list() for key in self.nonterminals}
        self.get_items()

        # 计算文法的状态
        self.status_list = [
            self.closure([(self.new_start, [self.point, self.start])]), ]
        self.analyse_table = dict()
        self.acc = acc
        self.get_analyse_table()

    def get_terminator(self):
        '''获取终结符集合
        '''
        for nonterminal in self.nonterminals:
            for right in self.productions[nonterminal]:
                for sign in right:
                    if sign not in self.nonterminals and len(sign) > 0:
                        self.terminator.add(sign)
        # print(self.terminator)

    def get_first_follow(self):
        '''first集合
        '''
        # 产生式右部首字符为终结符号
        for nontermainal in self.nonterminals:
            for right in self.productions[nontermainal]:
                if right[0] in self.terminator:
                    self.first[nontermainal][right[0]] = right
        # 非终结符
        while True:
            last_first = deepcopy(self.first)  # 为保证所有的First集不再变化
            for nontermainal in self.nonterminals:
                new_dict = {}
                for right in self.productions[nontermainal]:  # 取X->Y的产生式右部
                    if right[0] in self.terminator:
                        # it means the right[0] is already in nontermainal, which is termainal.
                        new_dict = self.first[nontermainal]
                        continue
                    if right[0] != '':
                        # 加入右侧不是空
                        for i, sign in enumerate(right):  # 遍历右侧
                            if sign in self.nonterminals:
                                first_ = self.first[sign]
                                if i == (len(right)-1):
                                    for key in first_.keys():
                                        new_dict.update({key: right})
                                else:
                                    for key in first_.keys():
                                        if key != '':
                                            new_dict.update({key: right})
                                if '' not in first_.keys():
                                    break
                    else:
                        new_dict.update({'': ''})
                self.first[nontermainal].update(new_dict)
            if last_first == self.first:
                break
        # pprint(self.first)
        for i in self.terminator:  # 特殊处理终结符，等价于书上的FIRST级中包含终结符。
            self.first[i]=({i:i})
        # 起始符号follow集
        self.follow[self.start].add(self.sharp)  # 若S是开始符，则$ 属于FOLLOW(S)
        # 循环直到follow集不再变化
        while True:
            last_follow = deepcopy(self.follow)
            for nontermainal in self.nonterminals:
                for right in self.productions[nontermainal]:
                    if right[0] == '':
                        continue
                    for i, sign in enumerate(right):
                        if sign in self.terminator:
                            continue
                        if i == len(right) - 1:
                            # 若A→αB，那么FOLLOW(A)中所有符号都在FOLLOW(B)中。
                            self.follow[sign] |= self.follow[nontermainal]
                        else:
                            next_first = {
                                key for key in self.first[right[i + 1]].keys()}
                            next_first_without_null = {
                                key for key in self.first[right[i + 1]].keys() if key != ''}
                            # 若A→αBβ,那么将所有FIRST(β)中除了ε之外的所有符号都在FOLLOW(B)中。
                            new_i = i + 1
                            self.follow[sign] |= next_first_without_null
                            while '' in next_first and new_i<len(right)-1:
                                next_first = {
                                    key for key in self.first[right[new_i + 1]].keys()}
                                next_first_without_null = {
                                    key for key in self.first[right[new_i + 1]].keys() if key != ''}
                                self.follow[sign] |= next_first_without_null
                            print(sign)
                            print("test1")
                            print(next_first)
                            print("test2")
                            print(next_first_without_null)
                            # 若A→αBβ且FIRST(β)中包含ε，那么FOLLOW(A)中所有符号都在FOLLOW(B)中。
                            if '' in next_first:
                                self.follow[sign] |= self.follow[nontermainal]
            if last_follow == self.follow:
                break
        if self.log_level >= 0:
            print('first:')
            pprint(self.first)
            print('follow:')
            pprint(self.follow)

    def get_items(self):
        '''
        项
        '''
        # 增广文法
        self.items[self.new_start] = [
            [self.point, self.start], [self.start, self.point]]
        for nonterminal in self.nonterminals:
            for right in self.productions[nonterminal]:
                # 对空特殊处理
                if right[0] == '':
                    self.items[nonterminal].append([self.point])
                    continue
                for i in range(len(right)):
                    self.items[nonterminal].append(
                        right[:i] + [self.point] + right[i:]
                    )
                self.items[nonterminal].append(right + [self.point])
        if self.log_level >= 2:
            print('items:')
            pprint(self.items)

    # 求输入项集的闭包
    def closure(self, production_list):
        ret = production_list.copy()
        for production in production_list:
            right = production[1]
            i = 0
            # 找分割点
            while i < len(right) and right[i] != self.point:
                i += 1
            # 如果分割点后是非终结符
            if i + 1 < len(right) and right[i + 1] in self.nonterminals:
                # 寻找该非终结符的项
                for item in self.items[right[i + 1]]:
                    if self.point == item[0] and (right[i + 1], item) not in ret:
                        ret.append((right[i + 1], item))
        if ret == production_list:
            return ret
        else:
            return self.closure(ret)
    # 实现goto函数

    def goto(self, production_list, sign):
        # 和求闭包大致相同，sign：goto的目标
        new_production_list = list()
        for production in production_list:
            right = production[1]
            i = 0
            while i < len(right) and right[i] != self.point:
                i += 1
            if i + 1 < len(right) and right[i + 1] == sign:
                # 后移point
                new_right = list(right)
                temp = new_right[i]
                new_right[i] = new_right[i + 1]
                new_right[i + 1] = temp

                if (production[0], new_right) not in new_production_list:
                    new_production_list.append((production[0], new_right))
                i += 1
        # 返回新的状态的闭包
        return self.closure(new_production_list)

    # 求解项目集与分析表
    def get_analyse_table(self):
        # count_index指示现有状态集个数
        # index是正在分析的状态的索引
        count_index = 0
        index = 0
        while True:
            # 接受符号及其对应项目
            receive_sign_dict = {}
            # 从状态集中选出
            for (left, right) in self.status_list[index]:
                # 找到分隔符
                i = 0
                while i < len(right) and right[i] != self.point:
                    i += 1
                # 如果分隔符不在末尾，将则其后的符号为接受符号
                if i + 1 < len(right):
                    # key：分隔符后的接受的字符，value：产生式
                    if right[i + 1] not in receive_sign_dict.keys():
                        receive_sign_dict[right[i + 1]] = [(left, right)]
                    elif (left, right) not in receive_sign_dict[right[i + 1]]:
                        receive_sign_dict[right[i + 1]].append((left, right))
                # 如果分隔符在末尾
                else:
                    # 左边是拓广文法的起始符号则标记接受
                    if left == self.new_start:
                        self.analyse_table[index] = {self.sharp: [self.acc]}
                    # 否则找到对应的产生式
                    else:
                        production_index = 0  # 产生式下标
                        # 遍历产生式，if A->α.属于I[i],则所有的over属于FOLLOW(A)加入到ACTION[i,over]=r[j]
                        for left_ in self.nonterminals:
                            for right_ in self.productions[left_]:
                                if right == ["S","NN", "S","."] and right_ == ["S","NN", "S"]:
                                    print("stop")
                                new_right = deepcopy(right)
                                if new_right == [self.point]:
                                    new_right = ['']
                                else:
                                    new_right.remove(self.point)
                                if (left, new_right) == (left_, right_):
                                    # print('new_right')
                                    # print(new_right)
                                    # 根据左部的follow集将r填入分析表
                                    if index not in self.analyse_table.keys():
                                        self.analyse_table[index] = {
                                            over: [production_index,
                                                'r', (left_, right_)]
                                            for over in (self.follow[left_])
                                        }
                                    else:
                                        self.analyse_table[index].update( {
                                            over: [production_index,
                                                'r', (left_, right_)]
                                            for over in (self.follow[left_])
                                        })
                                production_index += 1
            # 遍历接受符号
            for sign, production_set in receive_sign_dict.items():
                # 用函数goto求出新的状态
                new_status = self.goto(production_set, sign)
                new_action = []
                # 如果新状态没有和已有的状态重复，则加入状态列表
                if new_status not in self.status_list:
                    self.status_list.append(new_status)
                    count_index += 1
                    new_action.append(count_index)
                else:
                    # 如果已有状态则获取状态的标号
                    new_action.append(self.status_list.index(new_status))
                # 更新分析表
                for production in production_set:
                    new_action.append(production)
                    # print('flag')
                    # print(production)
                if index not in self.analyse_table.keys():
                    self.analyse_table[index] = {sign: new_action}
                else:
                    self.analyse_table[index].update({sign: new_action})
            # 如果没有状态可以分析，结束循环
            index += 1
            if index > count_index:
                break
        if self.log_level >= 2:
            production_index = 0  # 产生式下标
            for left_ in self.nonterminals:
                for right_ in self.productions[left_]:
                    print(production_index, left_, right_)
                    production_index += 1
            print('stauts list:')
            pprint(self.status_list)
            print('analyse table:')
            pprint(self.analyse_table)

    def analyse_yufa(self):
        if self.log_level >= 1:
            print('grammar analyse:')
        # 初始化输入串列表、状态栈、符号栈
        sharp = Token(self.sharp, 0, 0, 0, 0)
        self.tag_list.append(sharp)
        string_index = 0
        status_stack = [0]
        sign_stack = [self.sharp]

        three_addr_dict = {}
        three_addr_key = 0
        temp_index = 0  # 临时变量
        # 不停分析直到接受
        while self.analyse_table[status_stack[-1]][self.tag_list[string_index].token_type][0] != self.acc:
            # 如果不是r，则为s

            if 'r' != self.analyse_table[status_stack[-1]][self.tag_list[string_index].token_type][1]:
                # push
                status_stack.append(
                    self.analyse_table[status_stack[-1]][self.tag_list[string_index].token_type][0])
                sign_stack.append(self.tag_list[string_index])
                string_index += 1
                if self.log_level >= 9:
                    pprint(status_stack)
                    for i in range(len(sign_stack)):
                        if i != 0:
                            print(sign_stack[i].token_name)

            else:
                # 为r，取出对应产生式的左部与右部
                left = self.analyse_table[status_stack[-1]
                                          ][self.tag_list[string_index].token_type][2][0]
                right = self.analyse_table[status_stack[-1]
                                           ][self.tag_list[string_index].token_type][2][1]
                # 语义分析
                # TO-DO
                #print("语义分析")

                #print(self.analyse_table[status_stack[-1]]
                #      [self.tag_list[string_index].token_type][0])
                # 产生式下标
                production_index = self.analyse_table[status_stack[-1]
                                                      ][self.tag_list[string_index].token_type][0]
                # 新建语义分析
                N_left = Semantic(left)
                top = len(sign_stack)-1

                #id_index = sign_stack[len(sign_stack)-4]
                # self.symtable_list[id_index.token_symindex].lex_type = semantic_dict['L'].s_type
                # self.symtable_list[id_index.token_symindex].lex_kind = "简单变量"

                if (production_index == 3):
                    N_left.s_width = 4
                    N_left.s_type = 'int'

                if (production_index == 4):
                    N_left.s_width = 8
                    N_left.s_type = 'float'
                if (production_index == 5):
                    index = sign_stack[len(sign_stack)-4]
                    error_line = index.token_line
                    if self.symtable_list[index.token_symindex].lex_type == 'None':
                        self.__error.append(SyntaxError(
                            '标识符'+index.token_name+'未定义', str(error_line)))
                        break
                    self.symtable_list[index.token_symindex].lex_val = sign_stack[top-1].s_value
                    #self.symtable_list[index.token_symindex].lex_val = semantic_dict['E'].s_value
                    # print(index.token_name, '=',
                    #      semantic_dict['E'][-1].s_value)
                    # print(self.tag_list[id_index].token_name)
                    #print(sign_stack[top - 3].token_name,
                         # '=', sign_stack[top - 1].s_addr)
                    three_addr_dict[three_addr_key]=sign_stack[top - 3].token_name+'='+sign_stack[top - 1].s_addr
                    three_addr_key+=1
                if (production_index == 6):
                    for i in sign_stack[top - 5].s_truelist:
                        three_addr_dict[i]+= str(sign_stack[top - 3].s_instr)
                    N_left.s_nextlist=list(set(sign_stack[top - 5].s_falselist+sign_stack[top - 1].s_nextlist))
                if (production_index == 7):
                    for i in sign_stack[top - 11].s_truelist:
                        three_addr_dict[i]+= str(sign_stack[top - 9].s_instr)
                    for i in sign_stack[top - 11].s_falselist:
                        three_addr_dict[i]+= str(sign_stack[top - 3].s_instr)
                    temp=list(set(sign_stack[top - 7].s_nextlist+sign_stack[top - 5].s_nextlist))
                    N_left.s_nextlist=list(set(temp+sign_stack[top - 1].s_nextlist))
                if (production_index == 8):
                    for i in sign_stack[top - 1].s_nextlist:
                        three_addr_dict[i]+= str(sign_stack[top - 7].s_instr)
                    for i in sign_stack[top - 5].s_truelist:
                        three_addr_dict[i]+= str(sign_stack[top - 3].s_instr)
                    N_left.s_nextlist=sign_stack[top - 5].s_falselist
                    three_addr_dict[three_addr_key]='goto '+str(sign_stack[top - 7].s_instr)
                    three_addr_key+=1
                if (production_index == 9):
                    for i in sign_stack[top - 2].s_nextlist:
                        three_addr_dict[i]+= str(sign_stack[top - 1].s_instr)
                    N_left.s_nextlist = sign_stack[top].s_nextlist
                if (production_index == 10):
                    N_left.s_truelist=[three_addr_key]
                    three_addr_dict[three_addr_key]='if '+sign_stack[top - 2].s_addr+'>'+sign_stack[top].s_addr+' goto '
                    three_addr_key+=1
                    N_left.s_falselist=[three_addr_key]
                    three_addr_dict[three_addr_key]='goto '
                    three_addr_key+=1
                if (production_index == 11):
                    N_left.s_truelist=[three_addr_key]
                    three_addr_dict[three_addr_key]='if '+sign_stack[top - 2].s_addr+'<'+sign_stack[top].s_addr+' goto '
                    three_addr_key+=1
                    N_left.s_falselist=[three_addr_key]
                    three_addr_dict[three_addr_key]='goto '
                    three_addr_key+=1
                if (production_index == 12):
                    N_left.s_truelist=[three_addr_key]
                    three_addr_dict[three_addr_key]='if '+sign_stack[top - 2].s_addr+'>='+sign_stack[top].s_addr+' goto '
                    three_addr_key+=1
                    N_left.s_falselist=[three_addr_key]
                    three_addr_dict[three_addr_key]='goto '
                    three_addr_key+=1
                if (production_index == 13):
                    N_left.s_truelist=[three_addr_key]
                    three_addr_dict[three_addr_key]='if '+sign_stack[top - 2].s_addr+'<='+sign_stack[top].s_addr+' goto '
                    three_addr_key+=1
                    N_left.s_falselist=[three_addr_key]
                    three_addr_dict[three_addr_key]='goto '
                    three_addr_key+=1
                if (production_index == 14):
                    N_left.s_truelist=[three_addr_key]
                    three_addr_dict[three_addr_key]='if '+sign_stack[top - 2].s_addr+'=='+sign_stack[top].s_addr+' goto '
                    three_addr_key+=1
                    N_left.s_falselist=[three_addr_key]
                    three_addr_dict[three_addr_key]='goto '
                    three_addr_key+=1
                if (production_index == 15):
                    N_left.s_addr = 't' + str(temp_index)
                    temp_index += 1
                    N_left.s_value = sign_stack[top -
                                                2].s_value + sign_stack[top].s_value
                    three_addr_dict[three_addr_key]=N_left.s_addr+ '='+ sign_stack[top - 2].s_addr+ '+'+ sign_stack[top].s_addr
                    three_addr_key+=1
                if (production_index == 16):
                    N_left.s_addr = 't' + str(temp_index)
                    temp_index += 1
                    N_left.s_value = sign_stack[top -
                                                2].s_value - sign_stack[top].s_value
                    three_addr_dict[three_addr_key]=N_left.s_addr+ '='+ sign_stack[top - 2].s_addr+ '-'+ sign_stack[top].s_addr
                    three_addr_key+=1
                if (production_index == 17):
                    N_left.s_value = sign_stack[top].s_value
                    N_left.s_addr = sign_stack[top].s_addr
                if (production_index == 18):
                    N_left.s_value = sign_stack[top].s_value
                    N_left.s_addr = sign_stack[top].s_addr
                if (production_index == 19):
                    N_left.s_addr = 't' + str(temp_index)
                    temp_index += 1
                    N_left.s_value = sign_stack[top -
                                                2].s_value * sign_stack[top].s_value
                    three_addr_dict[three_addr_key]=N_left.s_addr+ '='+ sign_stack[top - 2].s_addr+ '*'+ sign_stack[top].s_addr
                    three_addr_key+=1
                if (production_index == 20):
                    N_left.s_addr = 't' + str(temp_index)
                    temp_index += 1
                    N_left.s_value = sign_stack[top -
                                                2].s_value / sign_stack[top].s_value
                    three_addr_dict[three_addr_key]=N_left.s_addr+ '='+ sign_stack[top - 2].s_addr+ '/'+ sign_stack[top].s_addr
                    three_addr_key+=1
                if (production_index == 21):
                    N_left.s_value = sign_stack[top-1].s_value
                    N_left.s_addr = sign_stack[top-1].s_addr
                if (production_index == 22):
                    N_left.s_value = self.symtable_list[sign_stack[top].token_symindex].lex_val
                    N_left.s_addr = sign_stack[top].token_name
                if (production_index == 23):
                    num = sign_stack[top].token_name
                    N_left.s_value = int(num)
                    N_left.s_addr = num
                if (production_index == 24):
                    num = sign_stack[top].token_name
                    N_left.s_value = float(num)
                    N_left.s_addr = num
                if (production_index == 25):
                    N_left.i_offset = 0#其实这个应该是综合属性（但不管了）
                if (production_index == 26):
                    N_left.i_offset = sign_stack[top -
                                                 3].i_offset+sign_stack[top-2].s_width
                    self.symtable_list[sign_stack[top -
                                                  1].token_symindex].lex_type = sign_stack[top-2].s_type
                    self.symtable_list[sign_stack[top -
                                                  1].token_symindex].lex_kind = "简单变量"
                    self.symtable_list[sign_stack[top -
                                                  1].token_symindex].lex_addr = sign_stack[top-3].i_offset
                if (production_index == 27):
                    N_left.s_instr = three_addr_key
                if (production_index == 28):
                    N_left.s_nextlist = [three_addr_key]
                    three_addr_dict[three_addr_key]='goto '
                    three_addr_key+=1
                # print(self.symtable_list[self.tag_list[string_index].token_symindex].lex_type)
                # 语义分析结束
                # pop(第i个产生式右部文法符号的个数)
                for i in range(len(right)):
                    # print(right)
                    if right != ['']:
                        sign_stack.pop()
                        status_stack.pop()
                status_stack.append(
                    self.analyse_table[status_stack[-1]][left][0])
                sign_stack.append(N_left)
                # if self.log_level >= 1:
                    # pprint(status_stack)
                    # for i in range(len(sign_stack)):
                        # if i != 0:
                            # print(sign_stack[i].token_name)
            # error，退出循环

            if self.tag_list[string_index].token_type not in self.analyse_table[status_stack[-1]].keys():
                error_line = self.tag_list[string_index].token_line
                if status_stack[-1] == 4:
                    self.__error.append(SyntaxError(
                        'int 后只能跟标识符 错误跟随'+self.tag_list[string_index].token_name, str(error_line)))

        for i in self.symtable_list:
            print(self.symtable_list[i].lex_type, self.symtable_list[i].lex_kind,
                  self.symtable_list[i].lex_val, self.symtable_list[i].lex_addr)
        pprint(three_addr_dict)
        return True

    def analyse(self, file):
        print('analysing: ' + file, end='\n\n')
        self.tag_list = []
        # 新建词法分析器
        lexical = Lexical()
        # 载入源代码
        lexical.load(open(file, encoding='UTF-8').read())
        # 执行词法分析
        lexical_success = lexical.analyze()
        # 打印结果
        print('词法分析是否成功:\t', lexical_success)
        if lexical_success:
            lexical_result1, lexical_result2, lexical_result3 = lexical.get_result()
            print()
            print('词法分析结果:')
            for i in lexical_result1:
                print(i.token_type, i.token_name, i.token_line,
                      i.token_code, i.token_symindex)
                self.tag_list.append(i)
            self.symtable_list = lexical_result2
            for i in lexical_result2:
                print(lexical_result2[i].lex_type, lexical_result2[i].lex_kind,
                      lexical_result2[i].lex_val, lexical_result2[i].lex_addr)
            pprint(lexical_result3)
            print()
            self.analyse_yufa()
            syntax_error = self.get_error()
            for i in syntax_error:
                print('错误原因:\t', i.info, '错误所在行:', i.line)
            return False
        else:
            lexical_error = lexical.get_error()
            for i in lexical_error:
                print('错误原因:\t', i.info, i.line)


compiler = Syntax()
compiler.analyse("new/test.c")
