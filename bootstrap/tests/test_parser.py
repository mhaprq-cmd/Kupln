from __future__ import annotations
from typing import Sequence
from bootstrap.lexer.token import Token,TokenKind
from bootstrap.parser.ast import (
ArrayExpression,AssignmentExpression,BinaryExpression,Block,CallExpression,
ClassDeclaration,CompilationUnit,ConditionalExpression,EmptyStatement,
ExportDeclaration,Expression,ExpressionStatement,FieldDeclaration,ForStatement,
FunctionDeclaration,Identifier,IdentifierExpression,IfStatement,ImportDeclaration,
IndexExpression,InterfaceDeclaration,LiteralExpression,MemberAccessExpression,
NewExpression,Parameter,ParenthesizedExpression,PostfixExpression,
RecordDeclaration,ReturnStatement,Statement,StructDeclaration,SuperExpression,
ThisExpression,TryStatement,TypeReference,UnaryExpression,VariableDeclaration,
WhileStatement
)

class ParserError(Exception): pass
class UnexpectedTokenError(ParserError): pass

class Parser:
    MODIFIERS=frozenset(("public","private","protected","static","abstract","final"))
    UNARY=frozenset(("+","-","!","++","--"))
    PREC={"??":0,"||":1,"&&":2,"==":3,"!=":3,"<":4,">":4,"<=":4,">=":4,
          "+":5,"-":5,"*":6,"/":6,"%":6}

    def __init__(self,tokens:Sequence[Token]):
        self.tokens=tuple(x for x in tokens if x.kind!=TokenKind.COMMENT)
        self.i=0

    def parse(self):
        a=[]
        while not self._check(TokenKind.EOF): a.append(self._top())
        return CompilationUnit(self._cur().position,tuple(a))

    def _top(self):
        if self._lex("import"): return self._import()
        if self._lex("export"): return self._export()
        return self._decl_stmt()

    def _decl_stmt(self):
        if self._starts_decl(): return self._decl()
        return self._stmt()

    def _starts_decl(self):
        return (self._lex("let") or self._lex("var") or self._lex("function") or
                self._lex("async") or self._lex("class") or self._lex("interface") or
                self._lex("struct") or self._lex("record") or self._modifier())

    def _modifier(self): return self._cur().lexeme in self.MODIFIERS

    def _mods(self):
        a=[]
        while self._modifier(): a.append(self._advance().lexeme)
        return tuple(a)

    def _decl(self):
        mods=self._mods()
        if self._lex("async"):
            self._advance()
            if not self._lex("function"): self._err("Expected 'function'.")
            return self._function(mods,True)
        if self._lex("let") or self._lex("var"): return self._variable(mods)
        if self._lex("function"): return self._function(mods,False)
        if self._lex("class"): return self._class(mods)
        if self._lex("interface"): return self._interface(mods)
        if self._lex("struct"): return self._struct(mods)
        if self._lex("record"): return self._record(mods)
        self._err("Expected declaration.")

    def _variable(self,mods=(),semi=True):
        p=self._cur().position
        k=self._any(("let","var")).lexeme
        n=self._id(); t=self._type()
        e=self._expr() if self._match("=") else None
        if semi: self._expect(";")
        return VariableDeclaration(p,mods,k,n,t,e)

    def _function(self,mods,async_):
        p=self._cur().position
        self._expect("function"); n=self._id(); self._expect("(")
        a=[]
        if not self._lex(")"):
            while True:
                a.append(self._param())
                if not self._match(","): break
        self._expect(")")
        r=self._type()
        return FunctionDeclaration(p,async_,mods,n,tuple(a),r,self._block())

    def _param(self):
        p=self._cur().position
        n=self._id()
        return Parameter(p,n,self._type())

    def _class(self,mods):
        p=self._cur().position
        self._expect("class"); n=self._id()
        ex=self._type() if self._match("extends") else None
        im=[]
        if self._match("implements"):
            while True:
                im.append(self._type_ref())
                if not self._match(","): break
        self._expect("{"); a=[]
        while not self._lex("}") and not self._check(TokenKind.EOF):
            a.append(self._member())
        self._expect("}")
        return ClassDeclaration(p,mods,n,ex,tuple(im),tuple(a))

    def _member(self):
        mods=self._mods()
        if self._lex("async"):
            self._advance()
            if not self._lex("function"): self._err("Expected 'function'.")
            return self._function(mods,True)
        if self._lex("function"): return self._function(mods,False)
        if self._lex("let") or self._lex("var"): return self._field(mods)
        self._err("Expected class member.")

    def _field(self,mods):
        p=self._cur().position
        n=self._any(("let","var"))
        name=self._id(); t=self._type()
        e=self._expr() if self._match("=") else None
        self._expect(";")
        return FieldDeclaration(p,mods,name,t,e)

    def _interface(self,mods):
        p=self._cur().position
        self._expect("interface"); n=self._id()
        ex=self._type() if self._match("extends") else None
        self._expect("{"); a=[]
        while not self._lex("}") and not self._check(TokenKind.EOF):
            mp=self._cur().position; mm=self._mods(); async_=self._match("async")
            self._expect("function"); mn=self._id(); self._expect("("); ps=[]
            if not self._lex(")"):
                while True:
                    ps.append(self._param())
                    if not self._match(","): break
            self._expect(")"); rt=self._type(); self._expect(";")
            a.append(FunctionDeclaration(mp,async_,mm,mn,tuple(ps),rt,Block(mp,())))
        self._expect("}")
        return InterfaceDeclaration(p,mods,n,ex,tuple(a))

    def _struct(self,mods):
        p=self._cur().position; self._expect("struct"); n=self._id()
        return StructDeclaration(p,mods,n,tuple(self._fields()))

    def _record(self,mods):
        p=self._cur().position; self._expect("record"); n=self._id()
        return RecordDeclaration(p,mods,n,tuple(self._fields()))

    def _fields(self):
        self._expect("{"); a=[]
        while not self._lex("}") and not self._check(TokenKind.EOF):
            a.append(self._field(self._mods()))
        self._expect("}"); return a

    def _import(self):
        p=self._cur().position; self._expect("import")
        path=self._expect_kind(TokenKind.STRING).lexeme
        self._expect(";"); return ImportDeclaration(p,path)

    def _export(self):
        p=self._cur().position; self._expect("export")
        return ExportDeclaration(p,self._decl())

    def _stmt(self):
        if self._lex("{"): return self._block()
        if self._lex("let") or self._lex("var"): return self._variable()
        if self._match(";"): return EmptyStatement(self._prev().position)
        if self._match("return"):
            p=self._prev().position
            e=None if self._lex(";") else self._expr()
            self._expect(";"); return ReturnStatement(p,e)
        if self._match("if"): return self._if(self._prev().position)
        if self._match("while"): return self._while(self._prev().position)
        if self._match("for"): return self._for(self._prev().position)
        if self._match("try"): return self._try(self._prev().position)
        e=self._expr(); self._expect(";")
        return ExpressionStatement(e.position,e)

    def _block(self):
        p=self._cur().position; self._expect("{"); a=[]
        while not self._lex("}") and not self._check(TokenKind.EOF):
            a.append(self._decl() if self._starts_decl() else self._stmt())
        self._expect("}"); return Block(p,tuple(a))

    def _if(self,p):
        self._expect("("); c=self._expr(); self._expect(")")
        a=self._stmt(); b=self._stmt() if self._match("else") else None
        return IfStatement(p,c,a,b)

    def _while(self,p):
        self._expect("("); c=self._expr(); self._expect(")")
        return WhileStatement(p,c,self._stmt())

    def _for(self,p):
        self._expect("("); init=None
        if not self._lex(";"):
            if self._lex("let") or self._lex("var"): init=self._variable(semi=False)
            else:
                e=self._expr(); init=ExpressionStatement(e.position,e)
        self._expect(";")
        cond=None if self._lex(";") else self._expr(); self._expect(";")
        upd=None if self._lex(")") else self._expr(); self._expect(")")
        return ForStatement(p,init,cond,upd,self._stmt())

    def _try(self,p):
        body=self._block(); self._expect("catch"); self._expect("(")
        n=self._id(); self._expect(")"); return TryStatement(p,body,n,self._block())

    def _type(self):
        return self._type_ref() if self._match(":") else None

    def _type_ref(self):
        p=self._cur().position; a=[self._id()]
        while self._match("."): a.append(self._id())
        return TypeReference(p,tuple(a))

    def _id(self):
        t=self._cur()
        if t.kind not in (TokenKind.IDENTIFIER,TokenKind.KEYWORD):
            self._err("Expected identifier.")
        self._advance(); return Identifier(t.position,t.lexeme)

    def _expr(self): return self._assign()

    def _assign(self):
        a=self._conditional()
        if self._match("="):
            return AssignmentExpression(self._prev().position,a,self._assign())
        return a

    def _conditional(self):
        a=self._binary(0)
        if self._match("?"):
            b=self._expr(); self._expect(":")
            return ConditionalExpression(a.position,a,b,self._conditional())
        return a

    def _binary(self,minp):
        a=self._unary()
        while True:
            op=self._cur().lexeme; p=self.PREC.get(op)
            if p is None or p<minp: break
            self._advance(); b=self._binary(p+1)
            a=BinaryExpression(a.position,a,op,b)
        return a

    def _unary(self):
        if self._lex("await"):
            t=self._advance()
            return UnaryExpression(t.position,"await",self._unary())
        if self._cur().lexeme in self.UNARY:
            t=self._advance()
            return UnaryExpression(t.position,t.lexeme,self._unary())
        return self._postfix()

    def _postfix(self):
        a=self._primary()
        while True:
            if self._match("("):
                args=[]
                if not self._lex(")"):
                    while True:
                        args.append(self._expr())
                        if not self._match(","): break
                self._expect(")")
                a=CallExpression(a.position,a,tuple(args)); continue
            if self._match("."):
                a=MemberAccessExpression(a.position,a,self._id()); continue
            if self._match("["):
                x=self._expr(); self._expect("]")
                a=IndexExpression(a.position,a,x); continue
            if self._cur().lexeme in ("++","--"):
                a=PostfixExpression(a.position,a,self._advance().lexeme); continue
            break
        return a

    def _primary(self):
        t=self._cur()
        if t.kind in (TokenKind.INTEGER,TokenKind.FLOAT,TokenKind.STRING,TokenKind.CHAR):
            self._advance(); return LiteralExpression(t.position,t.kind.name,t.lexeme)
        if t.lexeme in ("true","false","null"):
            self._advance(); return LiteralExpression(t.position,t.lexeme,t.lexeme)
        if t.lexeme=="this":
            self._advance(); return ThisExpression(t.position)
        if t.lexeme=="super":
            self._advance(); return SuperExpression(t.position)
        if t.lexeme=="new": return self._new()
        if t.kind in (TokenKind.IDENTIFIER,TokenKind.KEYWORD):
            self._advance()
            return IdentifierExpression(t.position,Identifier(t.position,t.lexeme))
        if self._match("("):
            p=self._prev().position; e=self._expr(); self._expect(")")
            return ParenthesizedExpression(p,e)
        if self._match("["):
            p=self._prev().position; a=[]
            if not self._lex("]"):
                while True:
                    a.append(self._expr())
                    if not self._match(","): break
            self._expect("]"); return ArrayExpression(p,tuple(a))
        self._err("Expected expression.")

    def _new(self):
        p=self._cur().position; self._expect("new"); t=self._type_ref()
        self._expect("("); a=[]
        if not self._lex(")"):
            while True:
                a.append(self._expr())
                if not self._match(","): break
        self._expect(")")
        return NewExpression(p,t,tuple(a))

    def _cur(self): return self.tokens[self.i]
    def _prev(self): return self.tokens[self.i-1]

    def _advance(self):
        t=self._cur()
        if t.kind!=TokenKind.EOF: self.i+=1
        return t

    def _check(self,k): return self._cur().kind==k
    def _lex(self,x): return self._cur().lexeme==x

    def _match(self,x):
        if self._lex(x):
            self._advance(); return True
        return False

    def _expect(self,x):
        if not self._lex(x): self._err(f"Expected '{x}'.")
        return self._advance()

    def _expect_kind(self,k):
        if not self._check(k): self._err(f"Expected {k.name}.")
        return self._advance()

    def _any(self,xs):
        if self._cur().lexeme not in xs:
            self._err("Unexpected token.")
        return self._advance()

    def _err(self,msg):
        t=self._cur()
        raise UnexpectedTokenError(
            f"{msg} At line {t.position.line}, column {t.position.column}, near {t.lexeme!r}."
    )
