class GlobalVar:
    _var_name = ''
    _var_type = ''
    _var_val = None
    _len_str = 0

    def __init__(self, var_name, var_type, var_val=None, len_str=None):
        self._var_name = var_name
        self._var_type = var_type

        if var_val is not None:
            self._var_val = var_val

        if len_str is not None:
            self._len_str = len_str

    def getVarName(self):
        return self._var_name

    def getVarType(self):
        return self._var_type

    def getVarVal(self):
        return self._var_val

    def getLenOfStr(self):
        return self._len_str