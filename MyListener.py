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

    # element : list, element[0] : proc_name, element[1:] : string_of_stmts
    _list_of_proc = []

    ''' For prog '''

    def enterProg(self, ctx):
        pass

    def exitProg(self, ctx):
        pass

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

    def exitLib_decl(self, ctx):
        pass

    ''' For proc_decl '''

    def enterProc_decl(self, ctx):
        pass

    def exitProc_decl(self, ctx):
        pass

    ''' For compound_stmt '''

    def enterCompound_stmt(self, ctx):
        pass

    def exitCompound_stmt(self, ctx):
        if 'procedure' in ctx.parentCtx.getText():
            proc_name = ctx.parentCtx.ID().getText()
            proc_info = self.processInfoOfProcOrFunc(
                proc_name, ctx.stmt(), ctx)
            proc_var_decl_list = self.setVar_declText(ctx.var_decl())

            if proc_name == 'Main':
                self._list_of_global_var_decl = proc_var_decl_list
                # 전역변수로 텍스트 작성으로 인해 발생하는 예외상황에 대한 처리
                proc_info.append([])
            else:
                proc_info.append(proc_var_decl_list)
        else:
            pass

    ''' For expr_stmt '''

    def enterExpr_stmt(self, ctx):
        pass

    def exitExpr_stmt(self, ctx):

        pass

    ''' For expr '''
    def enterExpr(self, ctx):
        pass

    def exitExpr(self, ctx):
        pass

    ''' For var_decl '''

    def enterVar_decl(self, ctx):
        pass

    def exitVar_decl(self, ctx):
        pass

    ''' For var_type '''
    def enterVar_type(self, ctx):
        pass

    def exitVar_type(self, ctx):
        pass



    '''
    Main procedure에 담긴 변수 선언문들에 대한 처리
    C의 전역변수로 선언으로 변환한다.
    '''

    def setVar_declText(self, var_decl_list):
        if var_decl_list == None:
            pass

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
        translated_ctx_param = []
        translated_ctx_stmt = []
        check_string = False

        if proc_name == 'Main':
            proc_name = 'main'

        # parameter 정보 정리
        if 'procedure' in compound_stmt_ctx.parentCtx.getText():
            proc_ctx = compound_stmt_ctx.parentCtx  # proc_decl
            translated_param_info = []
            if proc_ctx.proc_param() is not None:
                translated_param_info = self.translateParamInfo(proc_ctx.proc_param())


        # 각 statement들을 상황에 맞도록 텍스트 변환
        for idx in range(num_of_stmt_ctx):

            cur_expr_stmt_text = list_of_stmt_ctx[idx].expr_stmt().getText()

            if '"' in cur_expr_stmt_text:
                check_string = True

            if not check_string:
                # divide left, right by assignment(':=')
                left_side_of_text, right_side_of_text = \
                    list(map(str, cur_expr_stmt_text.split(':=')))
                # string append after conversion

                replaced_right_side_of_text = \
                    self.exprTextReplace(right_side_of_text)

                # 매개변수 pointer 체크
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
                    # 순서 반드시 고려해야함
                    replaced_right_side_of_text = replaced_right_side_of_text.\
                        replace(param_var_name + ' ', '*' +
                                param_var_name + ' ')
                    replaced_right_side_of_text = replaced_right_side_of_text. \
                        replace(param_var_name + ';', '*' +
                                param_var_name + ';')
                    replaced_right_side_of_text = replaced_right_side_of_text. \
                        replace(' ' + param_var_name + ' ', ' *' +
                                param_var_name + ' ')
                    replaced_right_side_of_text = replaced_right_side_of_text. \
                        replace(' ' + param_var_name + ';', ' *' +
                                param_var_name + ';')

                    print(replaced_right_side_of_text)

                # 변환된 텍스트 합치기
                translated_text = left_side_of_text + ' = ' + replaced_right_side_of_text
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


    '''
    parameter 관련 정보를 C 코드에 맞게 변환
    '''
    def translateParamInfo(self, list_of_param_ctx):
        num_of_param = len(list_of_param_ctx)
        param_list = []
        # 모든 파라미터를 name, type,
        for idx in range(num_of_param):
            param_text = list_of_param_ctx[idx].getText()
            param_var_name = param_text.split(':')[0]
            param_type_text = param_text.split(':')[1]  # (in / out) + 매개변수 타입
            param_pointer_check = ''    # 매개변수가 out 인지 체크

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


    def exprTextReplace(self, target_text):
        replaced_text = target_text.replace('+', ' + ')
        replaced_text = replaced_text.replace('-', ' - ')
        replaced_text = replaced_text.replace('*', ' * ')
        replaced_text = replaced_text.replace('/', ' / ')
        replaced_text = replaced_text.replace('=', ' == ')

        return replaced_text



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
        num_of_proc = len(self._list_of_proc)   # number of procedure
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
            cur_proc_name = cur_proc_info[0]    # procedure 이름
            cur_proc_params = cur_proc_info[1]
            cur_proc_stmts = cur_proc_info[2]   # procedure statement의 리스트
            cur_proc_var_decls = cur_proc_info[3]   # procedure의 변수 선언 리스트
            num_of_stmt = len(cur_proc_stmts)
            num_of_var_decls = len(cur_proc_var_decls)
            num_of_params = len(cur_proc_params)
            cur_proc_return_type = 'void'   # 기본 return type -> void


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

            # statement 들에 대한 처리
            for stmt_idx in range(num_of_stmt):
                cur_proc_stmt_text += '\t' + cur_proc_stmts[stmt_idx] + '\n'

            # return 값 처리
            if cur_proc_name == 'Main':
                cur_proc_stmt_text += '\treturn 0;\n'

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
