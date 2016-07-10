# -*- coding: utf-8 -*-
# TODO: create iso lens between sugar and non-sugar
# TODO: supress + given a + (-b). i.e. want a - b

from collections import namedtuple, deque
from itertools import repeat
from typing import Union
from enum import Enum
from sympy import Symbol
import funcy as fn

from lenses import lens

VarKind = Enum("VarKind", ["x", "u", "w"])
str_to_varkind = {"x": VarKind.x, "u": VarKind.u, "w": VarKind.w}
dt_sym = Symbol('dt', positive=True)
t_sym = Symbol('t', positive=True)

class LinEq(namedtuple("LinEquality", ["terms", "op", "const"])):
    def __repr__(self):
        rep = "{lhs} {op} {c}"
        return rep.format(lhs=self.terms, op=self.op, c=self.const)

    def children(self):
        return []


class Interval(namedtuple('I', ['lower', 'upper'])):
    def __repr__(self):
        return "[{},{}]".format(self.lower, self.upper)

    def children(self):
        return [self.lower, self.upper]


class NaryOpSTL(namedtuple('NaryOp', ['args'])):
    OP = "?"
    def __repr__(self):
        n = len(self.args)
        if n == 1:
            return "{}".format(self.args[0])
        elif self.args:
            rep = "({})" + " {op} ({})"*(len(self.args) - 1)
            return rep.format(*self.args, op=self.OP)
        else:
            return ""

    def children(self):
        return self.args


class Or(NaryOpSTL):
    OP = "∨"

class And(NaryOpSTL):
    OP = "∧"


class ModalOp(namedtuple('ModalOp', ['interval', 'arg'])):
    def children(self):
        return [self.arg]


class F(ModalOp):
    def __repr__(self):
        return "◇{}({})".format(self.interval, self.arg)


class G(ModalOp):
    def __repr__(self):
        return "□{}({})".format(self.interval, self.arg)


class Neg(namedtuple('Neg', ['arg'])):
    def __repr__(self):
        return "¬({})".format(self.arg)

    def children(self):
        return [self.arg]


def walk(stl, bfs=False):
    """Walks Ast. Defaults to DFS unless BFS flag is set."""
    pop = deque.popleft if bfs else deque.pop
    children = deque([stl])
    while len(children) != 0:
        node = pop(children)
        yield node
        children.extend(node.children())


def tree(stl):
    return {x:set(x.children()) for x in walk(stl) if x.children()}


def terms_lens(phi:"STL", bind=True) -> lens:
    tls = list(fn.flatten(_terms_lens(phi)))
    tl = lens().tuple_(*tls).each_()
    return tl.bind(phi) if bind else tl


def _child_lens(psi, focus):
    if isinstance(psi, NaryOpSTL):
        for j, _ in enumerate(psi.args):
            yield focus.args[j]
    else:
        yield focus.arg


def _terms_lens(phi, focus=lens()):
    psi = focus.get(state=phi)
    if isinstance(psi, LinEq):
        return [focus.terms]
    child_lenses = list(_child_lens(psi, focus=focus))
    return [_terms_lens(phi, focus=cl) for cl in child_lenses]
