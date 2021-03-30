__author__ = 'Jihun Bae'

import copy
from AdaToCListener import AdaToCListener
from AdaToCListenerHelper import GlobalVar


class MyListener(AdaToCListener):
    _check_stdio_lib = False
    _check_string_lib = False
    _indent_cnt = 0

    _lib_decl_text = ''
    _list_of_global_var_decl = []
    _list_of_proc_param = []    # 파라미터가 있는 프로시저만 저장하는 변수
    # element : list, element[0] : proc_name, element[1:] : string_of_stmts
    _list_of_proc = []

    ''' 
    For lib_decl
    라이브러리 선언문을 확인 후 C에 맞게 라이브러리 헤더 파일 설정
    '''

    def enterLib_decl(self, ctx):
        cur_text = ctx.getText()
        if 'with' in cur_text:
            if ('Text_IO' or 'Integer_Text_IO') in cur_text:
                self._check_stdio_package = True
        elif 'use' in cur_text:
            if ((('Text_IO' or 'Integer_Text_IO') in cur_text) and
                    self._check_stdio_package):
                self._lib_decl_text = '#include <stdio.h>\n'

    def enterProc_decl(self, ctx):
        '''

        매개변수가 있는 procedure만 info_of_param에 파라미터 순서대로 포인터 타입인지 아닌지 체크하여
        append 한다. 마지막으로는 [프로시져 이름, info_of_param] (리스트 타입) 을
        self._list_of_proc_param 에 append 한다.

        :param ctx:
        :return: None
        '''
        proc_name = ctx.ID().getText()
        params_of_proc = ctx.proc_param()
        info_of_param = []  # 매개변수가 out 타입이면 True 아니면 False
        if params_of_proc is not None:
            num_of_params = len(params_of_proc)
            for param_idx in range(num_of_params):
                if 'out' in params_of_proc[param_idx].getText():
                    info_of_param.append(True)
                else:
                    info_of_param.append(False)

            self._list_of_proc_param.append([proc_name, info_of_param])

    ''' For compound_stmt '''

    def enterCompound_stmt(self, ctx):
        pass

    def exitCompound_stmt(self, ctx):
        # compound_stmt 가 procedure 로부터 온 경우
        if 'procedure' in ctx.parentCtx.getText():
            proc_name = ctx.parentCtx.ID().getText()    # 프로시저 이름
            proc_info = self.processInfoOfProcOrFunc(
                proc_name, ctx.stmt(), ctx) # 프로시저 이름, 파라미터 정보, stmt 를 가져옴
            proc_var_decl_list = self.setVar_declText(ctx.var_decl())

            if proc_name == 'Main':
                self._list_of_global_var_decl = proc_var_decl_list
                # 전역변수로 텍스트 작성으로 인해 발생하는 예외상황에 대한 처리
                proc_info.append([])
            else:
                proc_info.append(proc_var_decl_list)
        else:
            pass

    '''
    Main procedure에 담긴 변수 선언문들에 대한 처리
    C의 전역변수로 선언으로 변환한다.
    '''

    def setVar_declText(self, var_decl_list):
        # 변수 선언부 텍스트 설정
        if var_decl_list is None:
            return []

        num_of_var_decl = len(var_decl_list)
        translated_var_decl_list = []

        for idx in range(num_of_var_decl):
            ctx = var_decl_list[idx]
            var_name = ctx.ID().getText()
            var_type = ctx.var_type().getText()
            var_val = None

            if ctx.expr() is not None:
                expr_text = ctx.expr().getText()
                var_val = expr_text.split(':=')[1]

            if var_type == 'INTEGER':
                var_type = 'int'

            elif 'STRING' in var_type:
                idx_text = expr_text.split('(')[1].split(')')[0]
                left_expr, right_expr = list(map(str, idx_text.split('..')))
                # consider '\n' at end of string
                len_of_char_arr = str('(' + right_expr + ') - (' +
                                      left_expr + ') + 2')
                var_type = 'char'
                self._check_string_lib = True

            if 'char' == var_type:
                if var_val is not None:
                    translated_var_decl_list.append(GlobalVar(
                        var_name, var_type, var_val=var_val,
                        len_str=len_of_char_arr))
                else:
                    translated_var_decl_list.append(GlobalVar(
                        var_name, var_type, len_str=len_of_char_arr))
            else:
                if var_val is not None:
                    translated_var_decl_list.append(GlobalVar(
                        var_name, var_type, var_val))
                else:
                    translated_var_decl_list.append(GlobalVar(
                        var_name, var_type))

        return translated_var_decl_list

    ''' 
    process of stmt_ctx that derived from proc_decl 
    
    proc_decl로 부터 유래된 stmt_ctx에 대한 처리
    각 stmt_ctx에 대하여 procedure 이름, parameter 정보, translated 된 param 정보를 
    전역변수 리스트에 append 하여 저장한다.
    '''

    def processInfoOfProcOrFunc(self, proc_name, list_of_stmt_ctx, compound_stmt_ctx):
        num_of_stmt_ctx = len(list_of_stmt_ctx)
        translated_info = []
        translated_ctx_stmt = []
        tab_cnt = 1  # 함수 또는 프로시저의 첫 부분 이후이므로 들여쓰기 필요!
        check_string = False

        if proc_name == 'Main':
            proc_name = 'main'

        # parameter 정보 정리 (procedure)
        if 'procedure' in compound_stmt_ctx.parentCtx.getText():
            proc_ctx = compound_stmt_ctx.parentCtx  # proc_decl
            translated_param_info = []
            if proc_ctx.proc_param() is not None:
                translated_param_info = self.translateParamInfo(proc_ctx.proc_param())

        # 각 statement들을 상황에 맞도록 텍스트 변환
        for idx in range(num_of_stmt_ctx):
            translated_text = ''
            # 줄바꿈 처리는 file writing 부분에서 처리하지만 특별한 경우는 추가한다.

            # if 시작과 끝 부분 처리
            if list_of_stmt_ctx[idx].if_start() is not None:
                cur_if_start = list_of_stmt_ctx[idx].if_start()
                if_expr_text = cur_if_start.expr().getText()
                translated_expr_text = self.exprTextReplace(if_expr_text)

                translated_text += self.getTabText(tab_cnt)
                translated_text += 'if (' + translated_expr_text + ') {'
                tab_cnt += 1

            elif list_of_stmt_ctx[idx].end_if() is not None:
                tab_cnt -= 1
                translated_text += self.getTabText(tab_cnt)
                translated_text += '}\n'

            elif list_of_stmt_ctx[idx].for_start() is not None:
                cur_for_start = list_of_stmt_ctx[idx].for_start()
                cur_for_id = cur_for_start.ID().getText()
                for_expr_text = cur_for_start.expr().getText()
                left_expr, right_expr = list(map(
                    str, for_expr_text.split('..')))  # index 시작과 끝 정보에 대한 분할
                translated_text += '\n'
                translated_text += self.getTabText(tab_cnt)
                translated_text += 'for (' + cur_for_id + ' = ' + \
                                   left_expr + '; '

                if 'reverse' in cur_for_start.getText():

                    translated_text += cur_for_id + ' >= ' + right_expr + \
                                       '; ' + cur_for_id + '--) {'
                else:
                    translated_text += cur_for_id + ' <= ' + right_expr + \
                                       '; ' + cur_for_id + '++) {'

                tab_cnt += 1

            elif list_of_stmt_ctx[idx].end_for() is not None:
                tab_cnt -= 1
                translated_text += self.getTabText(tab_cnt)
                translated_text += '}\n'

            elif list_of_stmt_ctx[idx].exit_stmt() is not None:
                exit_expr_text = list_of_stmt_ctx[idx].exit_stmt().expr(). \
                    getText()
                translated_expr_text = self.exprTextReplace(exit_expr_text)
                translated_expr_text = self.setVarAsPointer(
                    translated_expr_text, param_var_name)

                translated_text += self.getTabText(tab_cnt)
                translated_text += 'if (' + translated_expr_text + ') {\n'
                tab_cnt += 1
                translated_text += self.getTabText(tab_cnt)
                tab_cnt -= 1
                translated_text += 'break;\n'
                translated_text += self.getTabText(tab_cnt)
                translated_text += '}'
                # break문은 stmt가 아니고 임의로 추가하는 것이므로 여기서 ';'을 붙인다.


            # expr_stmt 처리
            elif list_of_stmt_ctx[idx].expr_stmt() is not None:
                cur_expr_stmt_text = list_of_stmt_ctx[idx].expr_stmt().getText()
                left_side_of_text = '' # expr_stmt에 ':='(assign)이 없는 경우

                if '"' in cur_expr_stmt_text:
                    check_string = True

                if not check_string:  # 문자열은 현재 구현 고려하지 않음
                    if ':=' in cur_expr_stmt_text:
                        # divide left, right by assignment(':=')
                        left_side_of_text, right_side_of_text = \
                            list(map(str, cur_expr_stmt_text.split(':=')))

                    else:
                        right_side_of_text = cur_expr_stmt_text
                    # string append after conversion
                    replaced_right_side_of_text = \
                        self.exprTextReplace(right_side_of_text)

                    # 매개변수 pointer 체크 (포인터 변수라면 '*'을 붙여준다.)
                    # 이 부분은 해당 함수의 작성부분에 한정한다.
                    num_of_params = len(translated_param_info)  # 파라미터 개수
                    for param_idx in range(num_of_params):
                        # param_info[0] -> pointer_check, [1] ->
                        param_info = translated_param_info[param_idx]
                        pointer_check, param_var_type, param_var_name = \
                            param_info
                        # 포인터인지 체크
                        if pointer_check != '*':
                            # 포인터 타입의 매개변수가 아니면 다음 파라미터 확인
                            continue

                        # 포인터 타입의 매개변수가 문장의 왼쪽에서 매칭되는 경우
                        if param_var_name == left_side_of_text:
                            left_side_of_text = '*' + param_var_name

                        # 포인터 타입의 매개변수가 문장의 오른쪽에 있는 경우 치환(4가지 경우 모두 고려)
                        replaced_right_side_of_text = self.setVarAsPointer(
                            replaced_right_side_of_text, param_var_name)

                    translated_text += self.getTabText(tab_cnt)
                    # 변환된 텍스트 합치기

                    translated_text += left_side_of_text
                    if ':=' in cur_expr_stmt_text:
                        translated_text += ' = '

                    if left_side_of_text == '':     # procedure 실행하는 경우
                        # 매개변수가 없는 경우
                        if ('(' and ')')not in replaced_right_side_of_text:
                            replaced_right_side_of_text = \
                                replaced_right_side_of_text.replace(';', '();')

                        else:   # 매개변수 있는 경우(포인터 체크)
                            replaced_right_side_of_text = self.checkProcParam(
                                replaced_right_side_of_text)


                    translated_text += replaced_right_side_of_text

            translated_ctx_stmt.append(translated_text)

        '''
        translated_ctx_info[0] -> procedure name (string)
        translated_ctx_info[1] -> params
        translated_ctx_info[2] -> statements of procedure 
        '''

        translated_info.append(proc_name)
        translated_info.append(translated_param_info)
        translated_info.append(translated_ctx_stmt)
        self._list_of_proc.append(translated_info)

        return translated_info

    def setVarAsPointer(self, text, var_name):
        text = text.replace(var_name + ' ', '*' + var_name + ' ')
        text = text.replace(var_name + ';', '*' + var_name + ';')
        text = text.replace('(' + var_name, '(*' + var_name)
        text = text.replace(var_name + ')', '*' + var_name + ')')
        text = text.replace(' ' + var_name + ' ', ' *' + var_name + ' ')
        text = text.replace(' ' + var_name + ';', ' *' + var_name + ';')

        return text

    '''
    parameter 관련 정보를 C 코드에 맞게 변환(함수 선언부)
    '''

    def translateParamInfo(self, list_of_param_ctx):
        num_of_param = len(list_of_param_ctx)
        param_list = []
        # 모든 파라미터를 name, type,
        for idx in range(num_of_param):
            param_text = list_of_param_ctx[idx].getText()
            param_var_name = param_text.split(':')[0]
            param_type_text = param_text.split(':')[1]  # (in / out) + 매개변수 타입
            param_pointer_check = ''  # 매개변수가 out 인지 체크

            if 'in' in param_type_text:
                if 'out' in param_type_text:
                    param_in_out_info = 'inout'
                else:
                    param_in_out_info = 'in'
            else:
                param_in_out_info = 'out'

            if param_in_out_info != 'in':
                param_pointer_check = '*'

            # 매개변수 타입 뽑아내기
            param_var_type = param_type_text.split(param_in_out_info)[1].split(';')[0]

            if param_var_type == 'INTEGER':
                param_var_type = 'int'
            elif param_var_type == 'STRING':
                param_var_type = 'char'

            param_list.append(
                [param_pointer_check, param_var_type, param_var_name])

        return param_list

    def checkProcParam(self, text):
        proc_name_from_text = text.split('(')[0]    # 호출된 프로시저 이름
        params_from_text = text.split('(')[1].split(')')[0]     # 프로시저 호출 시의 파라미터 텍스트
        param_info_list_to_check = self._list_of_proc_param
        num_of_proc_to_check = len(param_info_list_to_check)

        for idx in range(num_of_proc_to_check):
            proc_name = param_info_list_to_check[idx][0]
            param_check_list = param_info_list_to_check[idx][1]
            if proc_name_from_text != proc_name:    # 프로시저 이름이 일치하지 않는 경우
                continue
            else:   # 찾는 프로시저와 일치하는 경우
                num_of_params = len(param_check_list)
                replaced_params_from_text = ''
                for param_idx in range(num_of_params):
                    if param_check_list[param_idx] == False:
                        # 매개변수가 out 타입이 아닌 경우(다음 매개변수를 확인)
                        continue
                    else:
                        # 매개변수가 out 타입인 경우('&'를 해당 매개변수 위치에 맞게 붙인다.)
                        target_var_name = params_from_text.split(',')[param_idx]
                        if ' ' in target_var_name:
                            target_var_name = target_var_name.split(' ')[1]
                            replaced_params_from_text = \
                                params_from_text.replace(target_var_name,
                                                         '&' + target_var_name)

                break   # 매개변수의 수정이 끝났으므로 반복문을 종료한다.

        return proc_name + '(' + replaced_params_from_text + ');'






    def exprTextReplace(self, target_text):
        replaced_text = target_text.replace('+', ' + ')
        replaced_text = replaced_text.replace('-', ' - ')
        replaced_text = replaced_text.replace('*', ' * ')
        replaced_text = replaced_text.replace('/', ' / ')
        replaced_text = replaced_text.replace('/=', ' != ')
        replaced_text = replaced_text.replace('=', ' == ')
        replaced_text = replaced_text.replace(',', ', ')

        return replaced_text

    def getTabText(self, tab_cnt):
        text = ''
        for cnt in range(tab_cnt):
            text += '\t'

        return text

    def getLibTextForWriting(self):
        if self._check_string_lib:
            self._lib_decl_text += '#include <string.h>\n'

        self._lib_decl_text += '\n'
        return self._lib_decl_text

    # Write text that declare about global variable
    def getGlobalVarTextForWriting(self):
        list_of_global_var = copy.deepcopy(self._list_of_global_var_decl)
        num_of_global_vars = len(list_of_global_var)
        var_decl_text = ''

        for idx in range(num_of_global_vars):
            name_of_global_var = list_of_global_var[idx].getVarName()
            type_of_global_var = list_of_global_var[idx].getVarType()
            val_of_global_var = list_of_global_var[idx].getVarVal()

            if type_of_global_var == 'char':
                len_of_str = list_of_global_var[idx].getLenOfStr()
                var_decl_text += type_of_global_var + ' ' + name_of_global_var + \
                                 '[' + str(len_of_str) + ']'

                if val_of_global_var is not None:
                    var_decl_text += ' = ' + val_of_global_var

                var_decl_text += ';\n'
            else:
                var_decl_text += type_of_global_var + ' ' + name_of_global_var

                if val_of_global_var is not None:
                    var_decl_text += ' = ' + val_of_global_var

                var_decl_text += ';\n'

        var_decl_text += '\n'
        return var_decl_text

    '''
    지역변수 선언문 한 문장을 C의 변수 선언문 처럼 변환
    '''

    def getOneVar_declText(self, var_info):
        name_of_global_var = var_info.getVarName()
        type_of_global_var = var_info.getVarType()
        val_of_global_var = var_info.getVarVal()
        var_decl_text = ''

        if type_of_global_var == 'char':
            len_of_str = var_info.getLenOfStr()
            var_decl_text += type_of_global_var + ' ' + name_of_global_var + \
                             '[' + str(len_of_str) + ']'

            if val_of_global_var is not None:
                var_decl_text += ' = ' + val_of_global_var

            var_decl_text += ';\n'
        else:
            var_decl_text += type_of_global_var + ' ' + name_of_global_var

            if val_of_global_var is not None:
                var_decl_text += ' = ' + val_of_global_var

            var_decl_text += ';\n'

        return var_decl_text

    def getFuncTextForWriting(self):
        num_of_proc = len(self._list_of_proc)  # number of procedure
        func_text = ''

        # Get text of each procedure
        for proc_idx in range(num_of_proc):
            '''
            Get procedure information from list
            proc_info[0] -> Name of procedure
            proc_info[1] -> List that has parameter information of procedure
            proc_info[2] -> List that has statements of variable declare
            proc_info[3] -> List that has expr statements of procedure 
            '''
            cur_proc_info = self._list_of_proc[proc_idx]
            cur_proc_name = cur_proc_info[0]  # procedure 이름
            cur_proc_params = cur_proc_info[1]
            cur_proc_stmts = cur_proc_info[2]  # procedure statement의 리스트
            cur_proc_var_decls = cur_proc_info[3]  # procedure의 변수 선언 리스트
            num_of_stmt = len(cur_proc_stmts)
            num_of_var_decls = len(cur_proc_var_decls)
            num_of_params = len(cur_proc_params)
            cur_proc_return_type = 'void'  # 기본 return type -> void

            # Main procedure는 int type 반환타입 변환
            if cur_proc_name == 'main':
                cur_proc_return_type = 'int'

            # 파라미터 코드 작성
            if num_of_params != 0:
                cur_proc_stmt_text = cur_proc_return_type + ' ' + \
                                     cur_proc_name + '('

                for idx in range(num_of_params):
                    param_pointer_check, param_var_type, param_var_name \
                        = cur_proc_params[idx]
                    cur_proc_stmt_text += param_var_type + ' ' + \
                                          param_pointer_check + \
                                          param_var_name

                    if idx != num_of_params - 1:
                        cur_proc_stmt_text += ', '

                cur_proc_stmt_text += ') {\n'
            else:
                cur_proc_stmt_text = cur_proc_return_type + ' ' + \
                                     cur_proc_name + '() {\n'

            # 변수 선언부 처리 (지역변수)
            for var_decl_idx in range(num_of_var_decls):
                var_decl_text = self.getOneVar_declText(
                    cur_proc_var_decls[var_decl_idx])
                cur_proc_stmt_text += '\t' + var_decl_text + '\n'
                # 변수 선언은 함수나 프로시저의 윗단에서 이뤄지므로 탭을 한 번만 처리해도 되므로 여기서 처리함

            # statement 들에 대한 처리
            for stmt_idx in range(num_of_stmt):
                cur_proc_stmt_text += cur_proc_stmts[stmt_idx] + '\n'

            # return 값 처리
            if cur_proc_name == 'main':
                cur_proc_stmt_text += '\treturn 0;\n'
            else:
                pass

            # Store statements of each procedure
            cur_proc_stmt_text += '}\n\n'
            func_text += cur_proc_stmt_text

        return func_text

    def getTextForWriting(self):
        text_for_file_writing = ''
        text_for_file_writing += self.getLibTextForWriting()
        text_for_file_writing += self.getGlobalVarTextForWriting()
        text_for_file_writing += self.getFuncTextForWriting()
        return text_for_file_writing
