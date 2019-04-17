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

class Syntax:
    terminator = set()
    def __init__(self, log_level=2, sharp='#', point='.', acc='acc', productions_file='productions.txt'):
        self.log_level = log_level # log显示等级（仅因为显示太多烦）
        with open(productions_file, 'r') as f:
            lines = f.readlines()
            self.start = json.loads(lines[0])
            self.productions = json.loads(lines[1])
        self.nonterminals = self.productions.keys()
        
        self.get_terminator() # 获取终结符集合
        self.sharp = sharp
        self.first = {nontermainal: {} for nontermainal in self.nonterminals}
        self.follow = {nontermainal: set() for nontermainal in self.nonterminals}
        self.get_first_follow() # 构建First和Follow集合
    def get_terminator(self):
        '''获取终结符集合
        '''
        for nonterminal in self.nonterminals:
            for right in self.productions[nonterminal]:
                for sign in right:                
                    if sign not in self.nonterminals and len(sign)>0:
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
            last_first = deepcopy(self.first)# 为保证所有的First集不再变化
            for nontermainal in self.nonterminals:
                new_dict = {}
                for right in self.productions[nontermainal]:# 取X->Y的产生式右部
                    if right[0] in self.terminator:
                        # it means the right[0] is already in nontermainal, which is termainal.
                        new_dict = self.first[nontermainal]                    
                        continue
                    if right[0] != '':
                        # 加入右侧不是空
                        for i,sign in enumerate(right):# 遍历右侧                           
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
        self.follow[self.start].add(self.sharp)#若S是开始符，则$ 属于FOLLOW(S)
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
                            #若A→αB，那么FOLLOW(A)中所有符号都在FOLLOW(B)中。
                            self.follow[sign] |= self.follow[nontermainal]
                        elif right[i + 1] in self.terminator:# 特殊处理终结符，等价于书上的FIRST级中包含终结符。
                            self.follow[sign].add(right[i + 1])
                        else:
                            next_first = {key for key in self.first[right[i + 1]].keys()}
                            next_first_without_null = {key for key in self.first[right[i + 1]].keys() if key != ''}
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
        
syntax = Syntax()
