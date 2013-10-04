import itertools
import sys

class Token:
    def __init__(self, type, val):
        self.type = type
        self.val = val

    def __str__(self):
        return '{0.type}: {0.val}'.format(self)

class Reader:
    def __init__(self, filename):
        try:
            self.f = open(filename)
            self.file_iter = itertools.chain.from_iterable(self.f)
        except IOError:
            print('File {} does not exist'.format(filename))
        self.prev_char = None
        self.backtrack = False

    def get_char(self):
        if self.backtrack:
            self.backtrack = False
            return self.prev_char
        try:
            self.prev_char = next(self.file_iter)
            return self.prev_char
        except StopIteration:
            self.f.close()
            return None

    def unget_char(self):
        if not self.prev_char:
            print('WARNING: No character has been previously read')
        if self.backtrack:
            print('NOTE: Cannot unget_char more than once in succession')
        self.backtrack = True

    def finished(self):
        return self.f.closed

class Lexer:
    LOOKUP = {
        'else': 'ELSE',
        'if': 'IF',
        'int': 'INT',
        'return': 'RETURN',
        'void': 'VOID',
        'while': 'WHILE',
        '+': 'PLUS',
        '-': 'MINUS',
        '*': 'MULT',
        '/': 'DIV',
        '<': 'LT',
        '<=': 'LE',
        '>': 'GT',
        '>=': 'GE',
        '==': 'EQ',
        '!=': 'NE',
        '=': 'ASSIGN',
        ';': 'SEMICOLON',
        ',': 'COMMA',
        '(': 'LP',
        ')': 'RP',
        '[': 'LB',
        ']': 'RB',
        '{': 'LCURLY',
        '}': 'RCURLY',
    }
    (START, INNUM, INID, INDOP, INSLASH, INCOMMENT, OUTCOMMENT, DONE) = list(range(8))

    def __init__(self, filename):
        self.buf = []
        self.reader = Reader(filename)

    def _handle_start_state(self, c):
        state, save = self.START, True;
        if not c:
            state, save = self.DONE, False
        elif c.isdigit():
            state = self.INNUM
        elif c.isalpha():
            state = self.INID
        elif c == '<' or c == '>' or c == '=' or c == '!':
            state = self.INDOP
        elif c == '/':
            state = self.INSLASH
        elif c.isspace():
            save = False
        else:
            state = self.DONE
        return state, save

    def _handle_innum_state(self, c):
        state, save = self.INNUM, True
        if not c:
            state = self.DONE
            save = False
        elif not c.isdigit():
            state = self.DONE
            self.reader.unget_char()
            save = False
        return state, save

    def _handle_inid_state(self, c):
        state, save = self.INID, True
        if not c:
            state = self.DONE
            save = False
        elif not c.isalpha():
            state = self.DONE
            self.reader.unget_char()
            save = False
        return state, save

    def _handle_indop_state(self, c):
        save = True
        state = self.DONE
        if c != '=':
            self.reader.unget_char()
            save = False
        return state, save

    def _handle_inslash_state(self, c):
        state, save = self.INSLASH, True
        if c == '*':
            self.buf = []
            state = self.INCOMMENT
        else:
            self.reader.unget_char()
            state = self.DONE
        save = False
        return state, save

    def _handle_incomment_state(self, c):
        state, save = self.INCOMMENT, True
        if c == '*':
            state = self.OUTCOMMENT
        elif not c:
            state = self.DONE
        save = False
        return state, save

    def _handle_outcomment_state(self, c):
        state, save = self.OUTCOMMENT, True
        if c == '/':
            state = self.START
        elif not c:
            state = self.DONE
        else:
            state = self.INCOMMENT
        save = False
        return state, save

    def token(self):
        state = self.START
        token_type = None
        while state != self.DONE:
            c = self.reader.get_char()
            save = True
            if state == self.START:
                state, save = self._handle_start_state(c)
            elif state == self.INNUM:
                state, save = self._handle_innum_state(c)
                if state == self.DONE:
                    token_type = 'NUM'
            elif state == self.INID:
                state, save = self._handle_inid_state(c)
                if state == self.DONE:
                    token_type = 'ID'
            elif state == self.INDOP:
                state, save = self._handle_indop_state(c)
            elif state == self.INSLASH:
                state, save = self._handle_inslash_state(c)
            elif state == self.INCOMMENT:
                state, save = self._handle_incomment_state(c)
            elif state == self.OUTCOMMENT:
                state, save = self._handle_outcomment_state(c)
            else:
                print('Some weird bug occurred. State, char: {}, {}'
                        .format(state, c))

            if not c:
                state = self.DONE
            if save:
                self.buf.append(c)

        token_s = ''.join(self.buf)
        temp = self.LOOKUP.get(token_s)
        if temp:
            token_type = temp
        self.buf = []
        if token_type:
            return Token(token_type, token_s)
        else:
            error_msg = 'Token not recognized: {}'.format(token_s)
            return Token('ERROR', error_msg)

    def tokens(self):
        while True:
            tok = self.token()
            if not tok or self.reader.finished():
                break
            yield tok


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('Please supply a filename as argument')
        sys.exit()
    if len(sys.argv) > 2:
        print('Too many arguments, ignoring non-first argument(s)')
    lex = Lexer(sys.argv[1])
    for tok in lex.tokens():
        print(tok)
