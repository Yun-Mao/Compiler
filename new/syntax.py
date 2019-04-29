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

class Syntax:
    terminator = set()

    def __init__(self, log_level=2, sharp='#', point='.', acc='acc', productions_file='C:\\Users\\YunMao\\Desktop\\Coding\\Compiler\\new\\productions1.txt'):
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
                        elif right[i + 1] in self.terminator:  # 特殊处理终结符，等价于书上的FIRST级中包含终结符。
                            self.follow[sign].add(right[i + 1])
                        else:
                            next_first = {
                                key for key in self.first[right[i + 1]].keys()}
                            next_first_without_null = {
                                key for key in self.first[right[i + 1]].keys() if key != ''}
                            # 若A→αBβ,那么将所有FIRST(β)中除了ε之外的所有符号都在FOLLOW(B)中。
                            self.follow[sign] |= next_first_without_null
                            # 若A→αBβ且FIRST(β)中包含ε，那么FOLLOW(A)中所有符号都在FOLLOW(B)中。
                            if '' in next_first:
                                self.follow[sign] |= self.follow[nontermainal]
            if last_follow == self.follow:
                break
        if self.log_level >= 2:
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
                                new_right = deepcopy(right)
                                if new_right == [self.point]:
                                    new_right = ['']
                                else:
                                    new_right.remove(self.point)
                                # print('_right')
                                # print(right_)
                                # print('new_right')
                                # print(new_right)
                                if (left, new_right) == (left_, right_):
                                    # print('new_right')
                                    # print(new_right)
                                    # 根据左部的follow集将r填入分析表
                                    self.analyse_table[index] = {
                                        over: [production_index,
                                               'r', (left_, right_)]
                                        for over in (self.follow[left_])
                                    }
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
            index += 1
            # 如果没有状态可以分析，结束循环
            if index > count_index:
                break
        if self.log_level >= 2:
            print('stauts list:')
            pprint(self.status_list)
            print('analyse table:')
            pprint(self.analyse_table)

    def analyse_yufa(self):
        if self.log_level >= 1:
            print('grammar analyse:')
        # 初始化输入串列表、状态栈、符号栈
        sharp=Token(self.sharp,0,0,0,0)

        self.tag_list.append(sharp)

        string_index = 0
        status_stack = [0, ]
        sign_stack = [self.sharp, ]
        # 初始化语义分析的四元式列表、分析栈
        siyuanshi_list = []
        # 不停分析直到接受
        while self.analyse_table[status_stack[-1]][self.tag_list[string_index].token_type][0] != self.acc:
            # 如果不是r，则为s
            if 'r' != self.analyse_table[status_stack[-1]][self.tag_list[string_index].token_type][1]:
                # push
                status_stack.append(
                    self.analyse_table[status_stack[-1]][self.tag_list[string_index].token_type][0])
                sign_stack.append(self.tag_list[string_index].token_type)
                # advance
                string_index += 1
                if self.log_level >= 1:
                    print(status_stack, sign_stack)
            else:
                # 为r，取出对应产生式的左部与右部
                left = self.analyse_table[status_stack[-1]
                                          ][self.tag_list[string_index].token_type][2][0]
                right = self.analyse_table[status_stack[-1]
                                           ][self.tag_list[string_index].token_type][2][1]
                # 语义分析，四元式
                # TO-DO
                # 语义分析结束
                # pop(第i个产生式右部文法符号的个数)
                for i in range(len(right)):
                    # print(right)
                    if right != ['']:
                        sign_stack.pop()
                        status_stack.pop()
                # if self.log_level >= 1:
                    #print(status_stack, sign_stack)
                # push(GOTO[新的栈顶状态][第i个产生式的左部])
                status_stack.append(
                    self.analyse_table[status_stack[-1]][left][0])
                sign_stack.append(left)
                if self.log_level >= 1:
                    print(status_stack, sign_stack)
            # error，退出循环
            if self.tag_list[string_index].token_type not in self.analyse_table[status_stack[-1]].keys():
                print(status_stack[-1])
                print('fail1', string_index,
                      self.tag_list[string_index].token_type, status_stack[-1])
                return False
        if self.log_level >= 1:
            pprint(siyuanshi_list)
        with open(self.file_name + '.four', 'w') as f:
            for siyuanshi in siyuanshi_list:
                f.write('%s %s %s %s\n' %
                        (siyuanshi[0], siyuanshi[1], siyuanshi[2], siyuanshi[3],))
        print('ok')
        return True

    def analyse(self, file):
        raw_string = open(file, 'r').read()
        self.raw_string = raw_string.replace('\t', '').replace('\n', '')
        self.file_name = file[:file.rindex('.')]
        print('analysing: ' + file, end='\n\n')
        if self.log_level >= 1:
            print(raw_string, end='\n\n')
        self.tag_list = []
        # 新建词法分析器
        lexical = Lexical()
        # 载入源代码
        lexical.load(open('test.c', encoding='UTF-8').read())
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
            for i in lexical_result2:
                print(lexical_result2[i].lex_type, lexical_result2[i].lex_kind,
                      lexical_result2[i].lex_val, lexical_result2[i].lex_num)
            pprint(lexical_result3)
            print()
            self.analyse_yufa()
        else:
            lexical_error = lexical.get_error()
            for i in lexical_error:
                print('错误原因:\t', i.info, i.line)


compiler = Syntax()
compiler.analyse("test.c")
