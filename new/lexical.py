# -*- coding: utf-8 -*-
"""Lexical Analyzer ver.20190330
This program is used to analyze lexical which follows the MIT open source agreement.

@Author:YunMao

How to use it?
In main.py:
- Try to use "lexical.load(source)" to load the sourse;
- Try to use "lexical.analyze()" to execute the program 
  and the return values are TOKEN TABLE and SYMTABLE.
"""
#import error
from rule.lexical import *
import re
from error import LexicalError


class SymTable:
    """符号表
    """

    def __init__(self, lex_type, lex_kind, lex_val, lex_num):
        """构造符号表

        参数：
        --------
        lex_type: 标识符类型
        lex_kind: 标识符所属的种类
        lex_val: 常数标识符的值
        lex_num: 序号
        """
        self.lex_type = lex_type
        self.lex_kind = lex_kind
        self.lex_val = lex_val
        self.lex_num = lex_num


class Token:
    """Token类
    """

    def __init__(self, token_type, token_name, token_line, token_code, token_symindex):
        """构造Token

        参数：
        --------
        token_type: Token 的类型
        token_name: Token 的内容
        token_line: Token 所在行数
        token_code: Token码
        token_symindex: symtable中的位置
        """
        self.token_type = token_type
        self.token_name = token_name
        self.token_line = token_line
        self.token_code = token_code
        self.token_symindex = token_symindex


class Lexical:
    """
    词法分析器
    """

    def __init__(self):
        """
        构造
        """
        # 错误
        self.__error = list()

        # 源代码
        self.__source = ''

        # 行
        self.__lines = list()

        # Token
        self.__tokens = list()

        # 符号表
        self.__symtable = {}

        # 符号串
        self.__lexemes = "$"

    def load(self, source):
        """
        装载源代码
        :param source: 源代码
        """
        self.__source = source

    def analyze(self):
        """
        执行词法分析
        :return: 词法分析是否成功
        """
        self.__replace_useless_chars()
        if self.__del_notes():
            self.__split_lines()
            if self.__split_tokens():
                self.__del_spaces()
                return True
            else:
                return False
        else:
            return False

    def get_result(self):
        """
        获取结果
        :return: token 列表
        """
        return self.__tokens, self.__symtable

    def get_error(self):
        """
        获取错误
        :return: 错误原因
        """
        return self.__error

    def __replace_useless_chars(self):
        """
        预处理，替换无用的字符
        """
        # 将 \r 替换成 \n
        self.__source = self.__source.replace('\r', '\n')
        # 将 \t 替换成四个空格
        self.__source = self.__source.replace('\t', '    ')

    def __del_notes(self):
        """
        预处理，删除注释
        :return: 是否删除成功
        """
        # 缓冲区
        buffer = self.__source
        # 结果
        result = self.__source
        # 判断是否匹配到了末尾
        while True:
            # 匹配 /*
            match = re.compile(regex_dict[note_char_type[0]]).search(buffer)
            # 如果匹配到了
            if match:
                left_note_start = match.start()
                # 开始匹配 */
                match2 = re.compile(
                    regex_dict[note_char_type[1]]).search(buffer)
                # 如果匹配到了
                if match2:
                    right_note_end = match2.end()
                    # 判断匹配到的区间中有几行
                    line_count = result[left_note_start:right_note_end].count(
                        '\n')
                    # 执行删除
                    result = result.replace(
                        result[left_note_start:right_note_end], '\n' * line_count)
                    # 删除完毕之后进入下一次循环
                    buffer = result
                    continue
                else:
                    # 判断错误所在的行数
                    enter_location = list()
                    enter_location.append(0)
                    for i in range(0, len(result)):
                        if result[i] == '\n':
                            enter_location.append(i)
                    find = False

                    error_line = 0
                    for i in range(0, len(enter_location) - 1):
                        if enter_location[i] < left_note_start < enter_location[i + 1]:
                            error_line = i + 1
                            find = True
                            break
                    if not find:
                        error_line = len(enter_location)

                    # 报错
                    self.__error = LexicalError('/* 没有相匹配的 */', error_line)
                    return False
            # 如果没有匹配到
            else:
                # 尝试寻找有没有落单的 */
                match2 = re.compile(
                    regex_dict[note_char_type[1]]).search(buffer)
                # 如果找到了说明错误了
                if match2:
                    right_note_start = match2.start()
                    # 判断错误所在的行数
                    enter_location = list()
                    enter_location.append(0)
                    for i in range(0, len(result)):
                        if result[i] == '\n':
                            enter_location.append(i)
                    find = False

                    error_line = 0
                    for i in range(0, len(enter_location) - 1):
                        if enter_location[i] < right_note_start < enter_location[i + 1]:
                            error_line = i + 1
                            find = True
                            break
                    if not find:
                        error_line = len(enter_location)

                    # 报错
                    self.__error = LexicalError('多余的 */', error_line)
                    return False
                # 如果没有找到那就说明已经找完了，跳出
            # 匹配//
            match = re.compile(regex_dict[note_char_type[2]]).search(buffer)

            if match:
                note_start = match.start()
                match2 = re.compile('\n').search(
                    buffer[note_start:(len(buffer)-1)])
                # 如果匹配到了换行
                if match2:
                    note_end = match2.end()
                    result = result.replace(
                        result[note_start:(note_end+note_start-1)], '', 1)
                    buffer = result
                    continue
                else:
                    break
            else:
                break

        # 将 result 保存到 __source 中
        self.__source = result
        return True

    def __split_lines(self):
        """
        将完成源代码分割成行序列
        """
        # 清空
        self.__tokens.clear()
        self.__symtable.clear()
        self.__lexemes = "$"
        # 按行分割
        temp = self.__source.split('\n')
        # 将分割出来的行序列添加到 __lines 中
        for t in temp:
            self.__lines.append(' ' + t)
        # print(self.__lines)

    def __if_in_symtable(self, id):
        """
        是否在符号表中
        """
        findid = r"\$"+id+r"\$"
        match = re.compile(findid).search(self.__lexemes)

        # print(match)
        if match:
            return True, match.start()+1
        else:
            return False, len(self.__lexemes)

    def __if_behind_split(self, buffer):
        '''
        数字、标识符需要确保后面是空格、分隔符、操作符
        '''
        # 空格
        if buffer=='':
            return True
        for t in split_char_type:
            match_split1 = re.compile(t).match(buffer)
            if match_split1:
                return True
        # 分割符
        for t in type_specialchar:
            match_split2 = re.compile(t).match(buffer)
            if match_split2:
                return True
        # 操作符
        for t in type_op:
            match_split3 = re.compile(t).match(buffer)
            if match_split3:
                return True
        return False
    def __error_split(self, buffer):
        '''
        错误后需要截取空格、分隔符、操作符
        '''
        match = 0
        # 空格
        if buffer=='':
            return 0
        for t in split_char_type:
            match_split1 = re.compile(t).search(buffer)
            if match_split1:
                match1 = match_split1.start()+1
                #print(match1)
            else:
                match1 = len(buffer)
        # 分割符
        for t in type_specialchar:
            match_split2 = re.compile(t).search(buffer)
            if match_split2:
                match2 = match_split2.start()
            else:
                match2 = len(buffer)
        # 操作符
        for t in type_op:
            match_split3 = re.compile(t).search(buffer)
            if match_split3:
                match3 = match_split1.start()
            else:
                match3 = len(buffer)
        match = min(match1,match2,match3)
        #print(match1,match2,match3)
        return match
    def __split_tokens(self):
        """
        从行序列中分割出 token
        :return: 
        """
        # 先将 __lines 拷贝一份到临时变量中
        lines = list()
        for line in self.__lines:
            lines.append(line)
        # 缓冲区
        buffer = ''
        # 当前所在行数
        current_line_num = 0
        # 结果
        tokens = list()
        is_error = False
        temp_type = 'None'
        while len(lines) > 0 or buffer != '':
            # 当前循环中是否匹配成功
            match_split_char = False
            match_keywords = False
            match_id = False
            match_num = False
            match_op = False
            match_specialchar = False
            #print(buffer)
            #print(lines)
            # 如果缓冲区中没有数据了，就填充一行到缓冲区
            if buffer == '':
                buffer = lines[0]
                lines = lines[1:]
                # 行号自增
                current_line_num += 1

            # 处理空格
            for t in split_char_type:
                match = re.compile(t).match(buffer)
                if match:
                    buffer = buffer[match.end():]
                    match_split_char = True
                    break
            if match_split_char:
                continue

            # 开始匹配关键字（0~32）
            for i, t in enumerate(type_keywords):
                match = re.compile(t).match(buffer)
                # print(match)
                if match and self.__if_behind_split(buffer[match.end():]):
                    tokens.append(
                        Token(t, buffer[match.start():match.end()], current_line_num, i, 0))
                    if buffer[match.start():match.end()] == 'int':
                        temp_type='int'
                    if buffer[match.start():match.end()] == 'float':
                        temp_type='float'
                    if buffer[match.start():match.end()] == 'char':
                        temp_type='char'
                    if buffer[match.start():match.end()] == 'double':
                        temp_type='double'
                    buffer = buffer[match.end():]
                    match_keywords = True
                    break
            if match_keywords:
                continue

            # 匹配标识符(Code:33)
            for t in type_id:
                match = re.compile(t).match(buffer)
                if match and self.__if_behind_split(buffer[match.end():]):
                    # 将其添加到 tokens 中
                    isinsymtable, index = self.__if_in_symtable(
                        buffer[match.start():match.end()])
                    # print(isinsymtable)
                    if not isinsymtable:
                        self.__symtable[index] = SymTable(
                            temp_type, 'None', 'None', 'None')
                        # print(buffer[match.start():match.end()]+"$")
                        self.__lexemes = self.__lexemes + \
                            buffer[match.start():match.end()]+"$"
                        tokens.append(
                            Token('id', buffer[match.start():match.end()], current_line_num, 33, index))
                        buffer = buffer[match.end():]
                    else:
                        tokens.append(
                            Token('id', buffer[match.start():match.end()], current_line_num, 33, index))
                        buffer = buffer[match.end():]
                    match_id = True
                    break
            if match_id:
                temp_type = 'None'
                continue

            # 匹配数字,int:34,float:35,36-50预留位
            for i, t in enumerate(types_num):
                match = re.compile(t).match(buffer)
                # print(buffer)
                # 如果匹配到了
                if match and self.__if_behind_split(buffer[match.end():]):
                    isinsymtable, index = self.__if_in_symtable(
                        buffer[match.start():match.end()])
                    temp = 'num_int' if (i == 1) else 'num_float'
                    tokens.append(
                        Token(temp, buffer[match.start():match.end()], current_line_num, 34+i, 0))
                    buffer = buffer[match.end():]
                    match_num = True
                    break
            if match_num:
                continue

            # 匹配操作符（Code：51开始 到100为止）
            for i, t in enumerate(type_op):
                match = re.compile(t).match(buffer)
                # print(buffer)
                if match:
                    # 将其添加到 tokens 中
                    tokens.append(
                        Token(buffer[match.start():match.end()], buffer[match.start():match.end()], current_line_num, 51+i, 0))
                    # buffer 去除已经匹配的部分
                    buffer = buffer[match.end():]
                    match_op = True
                    break
            if match_op:
                continue

            # 匹配分割（Code：101开始）
            for i, t in enumerate(type_specialchar):
                match = re.compile(t).match(buffer)
                # print(buffer)
                if match:
                    # 将其添加到 tokens 中
                    tokens.append(
                        Token(buffer[match.start():match.end()], buffer[match.start():match.end()], current_line_num, 101+i, 0))
                    # buffer 去除已经匹配的部分
                    buffer = buffer[match.end():]
                    match_specialchar = True
                    break
            if match_specialchar:
                continue

            # 如果匹配完所有的正则表达式都不成功
            # 报错
            match = self.__error_split(buffer)
            #print(buffer)
            self.__error.append(LexicalError('词法错误'+buffer[0:(match-1)], current_line_num))
            buffer = buffer[match:]
            # lines = lines[1:]
            # 行号自增
            # current_line_num += 1
            is_error = True
            temp_type = 'None'
        # 循环正常结束则说明完全匹配成功，将结果保存到 __tokens 中，返回成功
        for token in tokens:
            self.__tokens.append(token)
        
        return not is_error

    def __del_spaces(self):
        """
        删除 __tokens 中的空格
        """
        # 新建临时变量
        tokens = list()
        # 将 __tokens 中的内容拷贝到 tokens 中
        for token in self.__tokens:
            tokens.append(token)
        # 清空 __tokens
        self.__tokens.clear()
        # 如果不是空格就添加进原来的 __tokens，相当于从原来的列表中去除了空格
        for token in tokens:
            if token.token_type != split_char_type[0]:
                self.__tokens.append(token)
# a=SymTable(1,2,3,1,)

# print(a.lex_num)
