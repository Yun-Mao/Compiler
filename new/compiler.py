import json
from pprint import pprint
from copy import deepcopy
from lexical import Lexical

class Compiler:
    overs = set()
    reserved = set()
    one_op_set = set()
    two_next = dict()

    def __init__(self, log_level=0, sharp='#', point='.', acc='acc', productions_file='productions.txt'):
        self.log_level = log_level
        with open(productions_file, 'r') as f:
            lines = f.readlines()
            self.start = json.loads(lines[0])
            self.productions = json.loads(lines[1])
        self.nonterminals = self.productions.keys()
        self.get_overs_reserved()

        self.sharp = sharp
        self.first = {nontermainal: {} for nontermainal in self.nonterminals}
        self.follow = {nontermainal: set() for nontermainal in self.nonterminals}
        self.get_first_follow()

        # 计算文法项目
        self.new_start = self.start + "'"
        self.point = point
        self.items = {key: list() for key in self.nonterminals}
        self.get_items()

        # 计算文法的状态和分析表
        self.status_list = [
            self.closure([(self.new_start, [self.point, self.start])]), ]
        self.analyse_table = dict()
        self.acc = acc
        self.get_analyse_table()

    def get_overs_reserved(self):
        for nonterminal in self.nonterminals:
            for right in self.productions[nonterminal]:
                for sign in right:
                    if sign not in self.nonterminals and len(sign) > 0:
                        self.overs.add(sign)
                        if len(sign) >= 2 and not sign[0].isalpha():
                            if sign[0] in self.two_next.keys():
                                self.two_next[sign[0]].add(sign[1:])
                            else:
                                self.two_next[sign[0]] = {sign[1:], }
                        elif sign[0].isalpha():
                            self.reserved.add(sign)
                        else:
                            self.one_op_set.add(sign)
        remove_set = set()
        for sign in self.one_op_set:
            if sign[0] in self.two_next.keys():
                self.two_next[sign[0]].add('')
                remove_set.add(sign)
        for sign in remove_set:
            self.one_op_set.remove(sign)
        if self.log_level >= 2:
            print('over sign set:')
            pprint(self.overs)
            print('reserved word set:')
            pprint(self.reserved)
            print('one_op_set:')
            pprint(self.one_op_set)
            print('two_next dict:')
            pprint(self.two_next)

    def get_first_follow(self):
        # 求first第一轮，产生式右部首字符为终结符号
        self.first_first = list()
        for nontermainal in self.nonterminals:
            for right in self.productions[nontermainal]:
                if right[0] in self.overs:
                    self.first[nontermainal][right[0]] = right
                    self.first_first.append((nontermainal, right))
        # 求first第二轮
        while True:
            old_first = deepcopy(self.first)
            for nontermainal in self.nonterminals:
                new_dict = {}
                for right in self.productions[nontermainal]:
                    if (nontermainal, right) in self.first_first:
                        new_dict = self.first[nontermainal]
                        continue
                    if right[0] != '':
                        if right[0] in self.overs:
                            new_dict.update({right[0]: right})
                        else:
                            for sign in right:
                                if sign in self.nonterminals:
                                    first_ = self.first[sign]
                                    new_dict.update({key: right for key in first_.keys()})
                                    if '' not in first_.keys():
                                        break
                    else:
                        new_dict.update({'': ''})
                self.first[nontermainal].update(new_dict)
            if old_first == self.first:
                break
        # 起始符号follow集
        self.follow[self.start].add(self.sharp)
        # 循环直到follow集不再变化
        while True:
            old_follow = deepcopy(self.follow)
            for nontermainal in self.nonterminals:
                for right in self.productions[nontermainal]:
                    if right[0] == '':
                        continue
                    for i, sign in enumerate(right):
                        if sign in self.overs:
                            continue
                        if i == len(right) - 1:
                            self.follow[sign] |= self.follow[nontermainal]
                        elif right[i + 1] in self.overs:
                            self.follow[sign].add(right[i + 1])
                        else:
                            next_set = {key for key in self.first[right[i + 1]].keys()}
                            next_set_without_null = {key for key in self.first[right[i + 1]].keys() if key != ''}
                            self.follow[sign] |= next_set_without_null
                            if '' in next_set:
                                self.follow[sign] |= self.follow[nontermainal]
            if old_follow == self.follow:
                break
        if self.log_level >= 2:
            print('follow:')
            pprint(self.follow)

    def get_items(self):
        self.items[self.new_start] = [[self.point, self.start], [self.start, self.point]]
        for nonterminal in self.nonterminals:
            for right in self.productions[nonterminal]:
                if right[0] == '':
                    self.items[nonterminal].append([self.point, ])
                    continue
                for i in range(len(right)):
                    self.items[nonterminal].append(
                        right[:i] + [self.point, ] + right[i:]
                    )
                self.items[nonterminal].append(right + [self.point, ])
        if self.log_level >= 2:
            print('items:')
            pprint(self.items)

    # 递归求解输入项目集合的闭包
    def closure(self, production_list):
        ret = production_list.copy()
        # 对于每一个项目，找到分隔符，如果后面有非终结符号，执行闭包操作
        for production in production_list:
            right = production[1]
            i = 0
            while i < len(right) and right[i] != self.point:
                i += 1
            if i + 1 < len(right) and right[i + 1] in self.nonterminals:
                for item in self.items[right[i + 1]]:
                    if self.point == item[0] and (right[i + 1], item) not in ret:
                        ret.append((right[i + 1], item))
        if ret == production_list:
            return ret
        else:
            return self.closure(ret)

    # 实现go函数
    def go(self, production_list, sign):
        new_production_list = list()
        # 找到接受sign的项目，将分隔符后移一位
        for production in production_list:
            right = production[1]
            i = 0
            while i < len(right) and right[i] != self.point:
                i += 1
            if i + 1 < len(right) and right[i + 1] == sign:
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
        # last_index指示现有状态集个数
        # index是正在分析的状态的索引
        last_index = 0
        index = 0
        while True:
            # 首先得到该状态接受的符号及其对应项目
            receive_sign_dict = {}
            # 遍历状态集中的每一个项目
            for (left, right) in self.status_list[index]:
                # 找到分隔符
                i = 0
                while i < len(right) and right[i] != self.point:
                    i += 1
                # 如果分隔符不在末尾，将则其后的符号为接受符号
                if i + 1 < len(right):
                    if right[i + 1] not in receive_sign_dict.keys():
                        receive_sign_dict[right[i + 1]] = [(left, right)]
                    elif (left, right) not in receive_sign_dict[right[i + 1]]:
                        receive_sign_dict[right[i + 1]].append((left, right))
                # 如果分隔符在末尾
                else:
                    # 如果左部为拓广文法起始符号，则记录acc
                    if left == self.new_start:
                        self.analyse_table[index] = {self.sharp: [self.acc, ]}
                    # 否则找到对应的产生式
                    else:
                        production_index = 0
                        for left_ in self.nonterminals:
                            for right_ in self.productions[left_]:
                                new_right = deepcopy(right)
                                new_right.remove(self.point)
                                if (left, new_right) == (left_, right_):
                                    # 根据左部的follow集将r填入分析表
                                    self.analyse_table[index] = {
                                        over: [production_index, 'r', (left_, right_)]
                                        for over in (self.follow[left_])
                                    }
                                production_index += 1
            # 遍历接受符号
            for sign, production_set in receive_sign_dict.items():
                # 用函数go求出新的状态
                new_status = self.go(production_set, sign)
                new_action = []
                # 如果新状态没有和已有的状态重复，讲起加入状态列表
                if new_status not in self.status_list:
                    self.status_list.append(new_status)
                    last_index += 1
                    new_action.append(last_index)
                else:
                    new_action.append(self.status_list.index(new_status))
                # 更新分析表
                for production in production_set:
                    new_action.append(production)
                if index not in self.analyse_table.keys():
                    self.analyse_table[index] = {sign: new_action}
                else:
                    self.analyse_table[index].update({sign: new_action})
            index += 1
            # 如果没有状态可以分析，结束循环
            if index > last_index:
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
        self.tag_list += self.sharp

        string_index = 0
        status_stack = [0, ]
        sign_stack = [self.sharp, ]
        # 初始化语义分析的四元式列表、分析栈
        siyuanshi_list = []
        # 不停分析直到接受
        while self.analyse_table[status_stack[-1]][self.tag_list[string_index]][0] != self.acc:
            # 如果不是r，则为s
            if 'r' != self.analyse_table[status_stack[-1]][self.tag_list[string_index]][1]:
                # push
                status_stack.append(self.analyse_table[status_stack[-1]][self.tag_list[string_index]][0])
                sign_stack.append(self.tag_list[string_index])
                # advance
                string_index += 1
                if self.log_level >= 1:
                    print(status_stack, sign_stack)
            else:
                # 为r，取出对应产生式的左部与右部
                left = self.analyse_table[status_stack[-1]][self.tag_list[string_index]][2][0]
                right = self.analyse_table[status_stack[-1]][self.tag_list[string_index]][2][1]
                # 语义分析，四元式
                # TO-DO
                # 语义分析结束
                # pop(第i个产生式右部文法符号的个数)
                for i in range(len(right)):
                    sign_stack.pop()
                    status_stack.pop()
                if self.log_level >= 1:
                    print(status_stack, sign_stack)
                # push(GOTO[新的栈顶状态][第i个产生式的左部])
                status_stack.append(self.analyse_table[status_stack[-1]][left][0])
                sign_stack.append(left)
                if self.log_level >= 1:
                    print(status_stack, sign_stack)
            # error，退出循环
            if self.tag_list[string_index] not in self.analyse_table[status_stack[-1]].keys():
                print('fail1', string_index, self.tag_list[string_index], status_stack[-1])
                return False
        if self.log_level >= 1:
            pprint(siyuanshi_list)
        with open(self.file_name + '.four', 'w') as f:
            for siyuanshi in siyuanshi_list:
                f.write('%s %s %s %s\n' % (siyuanshi[0], siyuanshi[1], siyuanshi[2], siyuanshi[3],))
        print('ok')
        return True

    def analyse(self, file):
        raw_string = open(file, 'r').read()
        self.raw_string = raw_string.replace('\t', '').replace('\n', '')
        self.file_name = file[ :file.rindex('.')]
        print('analysing: ' + file, end='\n\n')
        if self.log_level >= 1:
            print(raw_string, end='\n\n')
        self.tag_list = []
        # 新建词法分析器
        lexical = Lexical()
        # 载入源代码
        lexical.load(open('test.c',encoding='UTF-8').read())
        # 执行词法分析
        lexical_success = lexical.analyze()
        # 打印结果
        print('词法分析是否成功:\t', lexical_success)
        if lexical_success:
            lexical_result1,lexical_result2 = lexical.get_result()
            print()
            print('词法分析结果:')
            for i in lexical_result1:
                print(i.token_type, i.token_name, i.token_line,i.token_code,i.token_symindex)
                self.tag_list.append(i.token_type)
            print(self.tag_list)
            for i in lexical_result2:
                print(lexical_result2[i].lex_type)
            print()
            self.analyse_yufa()
        else:
            lexical_error= lexical.get_error()
            for i in lexical_error:
                print('错误原因:\t', i.info,i.line)
compiler=Compiler()
compiler.analyse("test.c")