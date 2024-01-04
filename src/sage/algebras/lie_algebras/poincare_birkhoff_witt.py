"""
The Poincare-Birkhoff-Witt Basis For A Universal Enveloping Algebra

AUTHORS:

- Travis Scrimshaw (2013-11-03): Initial version
- Travis Scrimshaw (2024-01-02): Adding the center
"""

#*****************************************************************************
#       Copyright (C) 2013-2024 Travis Scrimshaw <tcscrims at gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.misc.cachefunc import cached_method
from sage.structure.element import get_coercion_model
from operator import mul
from sage.categories.algebras import Algebras
from sage.monoids.indexed_free_monoid import IndexedFreeAbelianMonoid
from sage.combinat.free_module import CombinatorialFreeModule
from sage.sets.family import Family


class PoincareBirkhoffWittBasis(CombinatorialFreeModule):
    r"""
    The Poincare-Birkhoff-Witt (PBW) basis of the universal enveloping
    algebra of a Lie algebra.

    Consider a Lie algebra `\mathfrak{g}` with ordered basis
    `(b_1,\dots,b_n)`. Then the universal enveloping algebra `U(\mathfrak{g})`
    is generated by `b_1,\dots,b_n` and subject to the relations

    .. MATH::

        [b_i, b_j] = \sum_{k = 1}^n c_{ij}^k b_k

    where `c_{ij}^k` are the structure coefficients of `\mathfrak{g}`. The
    Poincare-Birkhoff-Witt (PBW) basis is given by the monomials
    `b_1^{e_1} b_2^{e_2} \cdots b_n^{e_n}`. Specifically, we can rewrite
    `b_j b_i = b_i b_j + [b_j, b_i]` where `j > i`, and we can repeat
    this to sort any monomial into

    .. MATH::

        b_{i_1} \cdots b_{i_k} = b_1^{e_1} \cdots b_n^{e_n} + LOT

    where `LOT` are lower order terms. Thus the PBW basis is a filtered basis
    for `U(\mathfrak{g})`.

    EXAMPLES:

    We construct the PBW basis of `\mathfrak{sl}_2`::

        sage: L = lie_algebras.three_dimensional_by_rank(QQ, 3, names=['E','F','H'])
        sage: PBW = L.pbw_basis()

    We then do some computations; in particular, we check that `[E, F] = H`::

        sage: E,F,H = PBW.algebra_generators()
        sage: E*F
        PBW['E']*PBW['F']
        sage: F*E
        PBW['E']*PBW['F'] - PBW['H']
        sage: E*F - F*E
        PBW['H']

    Next we construct another instance of the PBW basis, but sorted in the
    reverse order::

        sage: def neg_key(x):
        ....:     return -L.basis().keys().index(x)
        sage: PBW2 = L.pbw_basis(prefix='PBW2', basis_key=neg_key)

    We then check the multiplication is preserved::

        sage: PBW2(E) * PBW2(F)
        PBW2['F']*PBW2['E'] + PBW2['H']
        sage: PBW2(E*F)
        PBW2['F']*PBW2['E'] + PBW2['H']
        sage: F * E + H
        PBW['E']*PBW['F']

    We now construct the PBW basis for Lie algebra of regular
    vector fields on `\CC^{\times}`::

        sage: L = lie_algebras.regular_vector_fields(QQ)
        sage: PBW = L.pbw_basis()
        sage: G = PBW.algebra_generators()
        sage: G[2] * G[3]
        PBW[2]*PBW[3]
        sage: G[3] * G[2]
        PBW[2]*PBW[3] + PBW[5]
        sage: G[-2] * G[3] * G[2]
        PBW[-2]*PBW[2]*PBW[3] + PBW[-2]*PBW[5]

    .. TODO::

        When the Lie algebra is finite dimensional, set the ordering of the
        basis elements, translate the structure coefficients, and work with
        fixed-length lists as the exponent vectors. This way we only will
        run any nontrivial sorting only once and avoid other potentially
        expensive comparisons between keys.
    """
    @staticmethod
    def __classcall_private__(cls, g, basis_key=None, prefix='PBW', **kwds):
        """
        Normalize input to ensure a unique representation.

        TESTS::

            sage: from sage.algebras.lie_algebras.poincare_birkhoff_witt import PoincareBirkhoffWittBasis
            sage: L = lie_algebras.sl(QQ, 2)
            sage: P1 = PoincareBirkhoffWittBasis(L)
            sage: P2 = PoincareBirkhoffWittBasis(L, prefix='PBW')
            sage: P1 is P2
            True
        """
        return super().__classcall__(cls,
                                     g, basis_key, prefix, **kwds)

    def __init__(self, g, basis_key, prefix, **kwds):
        """
        Initialize ``self``.

        TESTS::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: PBW = L.pbw_basis()
            sage: E,F,H = PBW.algebra_generators()
            sage: TestSuite(PBW).run(elements=[E, F, H])
            sage: TestSuite(PBW).run(elements=[E, F, H, E*F + H]) # long time
        """
        if basis_key is not None:
            self._basis_key = basis_key
        else:
            self._basis_key_inverse = None

        R = g.base_ring()
        self._g = g
        monomials = IndexedFreeAbelianMonoid(g.basis().keys(), prefix,
                                             sorting_key=self._monoid_key, **kwds)
        CombinatorialFreeModule.__init__(self, R, monomials,
                                         prefix='', bracket=False, latex_bracket=False,
                                         sorting_key=self._monomial_key,
                                         category=Algebras(R).WithBasis().Filtered())

    def _basis_key(self, x):
        """
        Return a key for sorting for the index ``x``.

        TESTS::

            sage: L = lie_algebras.three_dimensional_by_rank(QQ, 3, names=['E','F','H'])
            sage: PBW = L.pbw_basis()
            sage: PBW._basis_key('E') < PBW._basis_key('H')
            True

        ::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: def neg_key(x):
            ....:     return -L.basis().keys().index(x)
            sage: PBW = L.pbw_basis(basis_key=neg_key)
            sage: prod(PBW.gens())  # indirect doctest
            PBW[-alpha[1]]*PBW[alphacheck[1]]*PBW[alpha[1]]
             - 4*PBW[-alpha[1]]*PBW[alpha[1]]
             + PBW[alphacheck[1]]^2
             - 2*PBW[alphacheck[1]]

        Check that :trac:`23266` is fixed::

            sage: sl2 = lie_algebras.sl(QQ, 2, 'matrix')
            sage: sl2.indices()
            {'e1', 'f1', 'h1'}
            sage: type(sl2.basis().keys())
            <... 'list'>
            sage: Usl2 = sl2.pbw_basis()
            sage: Usl2._basis_key(2)
            2
            sage: Usl2._basis_key(3)
            Traceback (most recent call last):
            ...
            KeyError: 3
        """
        if self._basis_key_inverse is None:
            K = self._g.basis().keys()
            if isinstance(K, (list, tuple)) or K.cardinality() < float('inf'):
                self._basis_key_inverse = {k: i for i,k in enumerate(K)}
            else:
                self._basis_key_inverse = False
        if self._basis_key_inverse is False:
            return x
        else:
            return self._basis_key_inverse[x]

    def _monoid_key(self, x):
        """
        Comparison key for the underlying monoid.

        EXAMPLES::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: def neg_key(x):
            ....:     return -L.basis().keys().index(x)
            sage: PBW = L.pbw_basis(basis_key=neg_key)
            sage: M = PBW.basis().keys()
            sage: prod(M.gens())  # indirect doctest
            PBW[-alpha[1]]*PBW[alphacheck[1]]*PBW[alpha[1]]
        """
        return self._basis_key(x[0])

    def _monomial_key(self, x):
        """
        Compute the key for ``x`` so that the comparison is done by
        reverse degree lexicographic order.

        EXAMPLES::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: PBW = L.pbw_basis()
            sage: E,H,F = PBW.algebra_generators()
            sage: F*H*H*E  # indirect doctest
            PBW[alpha[1]]*PBW[alphacheck[1]]^2*PBW[-alpha[1]]
             + 8*PBW[alpha[1]]*PBW[alphacheck[1]]*PBW[-alpha[1]]
             - PBW[alphacheck[1]]^3 + 16*PBW[alpha[1]]*PBW[-alpha[1]]
             - 4*PBW[alphacheck[1]]^2 - 4*PBW[alphacheck[1]]

            sage: def neg_key(x):
            ....:     return -L.basis().keys().index(x)
            sage: PBW = L.pbw_basis(basis_key=neg_key)
            sage: E,H,F = PBW.algebra_generators()
            sage: E*H*H*F  # indirect doctest
            PBW[-alpha[1]]*PBW[alphacheck[1]]^2*PBW[alpha[1]]
             - 8*PBW[-alpha[1]]*PBW[alphacheck[1]]*PBW[alpha[1]]
             + PBW[alphacheck[1]]^3 + 16*PBW[-alpha[1]]*PBW[alpha[1]]
             - 4*PBW[alphacheck[1]]^2 + 4*PBW[alphacheck[1]]
        """
        return (-len(x), [self._basis_key(l) for l in x.to_word_list()])

    def _repr_(self):
        """
        Return a string representation of ``self``.

        EXAMPLES::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: L.pbw_basis()
            Universal enveloping algebra of
             Lie algebra of ['A', 1] in the Chevalley basis
             in the Poincare-Birkhoff-Witt basis
        """
        return "Universal enveloping algebra of {} in the Poincare-Birkhoff-Witt basis".format(self._g)

    def _latex_(self):
        r"""
        Return a latex representation of ``self``.

        EXAMPLES::

            sage: g = lie_algebras.pwitt(GF(3), 6)
            sage: U = g.pbw_basis()
            sage: latex(U)
            PBW\left( \mathcal{W}(6)_{\Bold{F}_{3}} \right)
        """
        from sage.misc.latex import latex
        return r"PBW\left( {} \right)".format(latex(self._g))

    def _coerce_map_from_(self, R):
        """
        Return ``True`` if there is a coercion map from ``R`` to ``self``.

        EXAMPLES:

        We lift from the Lie algebra::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: PBW = L.pbw_basis()
            sage: PBW.has_coerce_map_from(L)
            True
            sage: [PBW(g) for g in L.basis()]
            [PBW[alpha[1]], PBW[alphacheck[1]], PBW[-alpha[1]]]

        We can go between PBW bases under different sorting orders::

            sage: def neg_key(x):
            ....:     return -L.basis().keys().index(x)
            sage: PBW2 = L.pbw_basis(basis_key=neg_key)
            sage: E,H,F = PBW.algebra_generators()
            sage: PBW2(E*H*F)
            PBW[-alpha[1]]*PBW[alphacheck[1]]*PBW[alpha[1]]
             - 4*PBW[-alpha[1]]*PBW[alpha[1]]
             + PBW[alphacheck[1]]^2
             - 2*PBW[alphacheck[1]]

        We can lift from another Lie algebra and its PBW basis that
        coerces into the defining Lie algebra::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: LZ = lie_algebras.sl(ZZ, 2)
            sage: L.has_coerce_map_from(LZ) and L != LZ
            True
            sage: PBW = L.pbw_basis()
            sage: PBWZ = LZ.pbw_basis()
            sage: PBW.coerce_map_from(LZ)
            Composite map:
              From: Lie algebra of ['A', 1] in the Chevalley basis
              To:   Universal enveloping algebra of Lie algebra of ['A', 1] in the Chevalley basis
               in the Poincare-Birkhoff-Witt basis
              Defn:   Coercion map:
                      From: Lie algebra of ['A', 1] in the Chevalley basis
                      To:   Lie algebra of ['A', 1] in the Chevalley basis
                    then
                      Generic morphism:
                      From: Lie algebra of ['A', 1] in the Chevalley basis
                      To:   Universal enveloping algebra of Lie algebra of ['A', 1] in the Chevalley basis
                       in the Poincare-Birkhoff-Witt basis
            sage: PBW.coerce_map_from(PBWZ)
            Generic morphism:
              From: Universal enveloping algebra of Lie algebra of ['A', 1] in the Chevalley basis
               in the Poincare-Birkhoff-Witt basis
              To:   Universal enveloping algebra of Lie algebra of ['A', 1] in the Chevalley basis
               in the Poincare-Birkhoff-Witt basis

        TESTS:

        Check that we can take the preimage (:trac:`23375`)::

            sage: L = lie_algebras.cross_product(QQ)
            sage: pbw = L.pbw_basis()
            sage: L(pbw(L.an_element()))
            X + Y + Z
            sage: L(pbw(L.an_element())) == L.an_element()
            True
            sage: L(prod(pbw.gens()))
            Traceback (most recent call last):
            ...
            ValueError: PBW['X']*PBW['Y']*PBW['Z'] is not in the image
            sage: L(pbw.one())
            Traceback (most recent call last):
            ...
            ValueError: 1 is not in the image
        """
        if R == self._g:
            # Make this into the lift map
            I = self._indices

            def basis_function(x):
                return self.monomial(I.gen(x))

            def inv_supp(m):
                return None if m.length() != 1 else m.leading_support()
            # TODO: this diagonal, but with a smaller indexing set...
            return self._g.module_morphism(basis_function, codomain=self,
                                           triangular='upper', unitriangular=True,
                                           inverse_on_support=inv_supp)

        coerce_map = self._g.coerce_map_from(R)
        if coerce_map:
            return self.coerce_map_from(self._g) * coerce_map

        if isinstance(R, PoincareBirkhoffWittBasis):
            if self._g == R._g:
                I = self._indices

                def basis_function(x):
                    return self.prod(self.monomial(I.gen(g)**e)
                                     for g, e in x._sorted_items())
                # TODO: this diagonal, but with a smaller indexing set...
                return R.module_morphism(basis_function, codomain=self)
            coerce_map = self._g.coerce_map_from(R._g)
            if coerce_map:
                I = self._indices
                lift = self.coerce_map_from(self._g)

                def basis_function(x):
                    return self.prod(lift(coerce_map(g))**e
                                     for g, e in x._sorted_items())
                # TODO: this diagonal, but with a smaller indexing set...
                return R.module_morphism(basis_function, codomain=self)

        return super()._coerce_map_from_(R)

    def lie_algebra(self):
        """
        Return the underlying Lie algebra of ``self``.

        EXAMPLES::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: PBW = L.pbw_basis()
            sage: PBW.lie_algebra() is L
            True
        """
        return self._g

    def algebra_generators(self):
        """
        Return the algebra generators of ``self``.

        EXAMPLES::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: PBW = L.pbw_basis()
            sage: PBW.algebra_generators()
            Finite family {alpha[1]: PBW[alpha[1]], alphacheck[1]: PBW[alphacheck[1]], -alpha[1]: PBW[-alpha[1]]}
        """
        G = self._indices.gens()
        return Family(self._indices._indices, lambda x: self.monomial(G[x]),
                      name="generator map")

    gens = algebra_generators

    @cached_method
    def one_basis(self):
        """
        Return the basis element indexing `1`.

        EXAMPLES::

            sage: L = lie_algebras.three_dimensional_by_rank(QQ, 3, names=['E','F','H'])
            sage: PBW = L.pbw_basis()
            sage: ob = PBW.one_basis(); ob
            1
            sage: ob.parent()
            Free abelian monoid indexed by {'E', 'F', 'H'}
        """
        return self._indices.one()

    @cached_method
    def product_on_basis(self, lhs, rhs):
        """
        Return the product of the two basis elements ``lhs`` and ``rhs``.

        EXAMPLES::

            sage: L = lie_algebras.three_dimensional_by_rank(QQ, 3, names=['E','F','H'])
            sage: PBW = L.pbw_basis()
            sage: I = PBW.indices()
            sage: PBW.product_on_basis(I.gen('E'), I.gen('F'))
            PBW['E']*PBW['F']
            sage: PBW.product_on_basis(I.gen('E'), I.gen('H'))
            PBW['E']*PBW['H']
            sage: PBW.product_on_basis(I.gen('H'), I.gen('E'))
            PBW['E']*PBW['H'] + 2*PBW['E']
            sage: PBW.product_on_basis(I.gen('F'), I.gen('E'))
            PBW['E']*PBW['F'] - PBW['H']
            sage: PBW.product_on_basis(I.gen('F'), I.gen('H'))
            PBW['F']*PBW['H']
            sage: PBW.product_on_basis(I.gen('H'), I.gen('F'))
            PBW['F']*PBW['H'] - 2*PBW['F']
            sage: PBW.product_on_basis(I.gen('H')**2, I.gen('F')**2)
            PBW['F']^2*PBW['H']^2 - 8*PBW['F']^2*PBW['H'] + 16*PBW['F']^2

            sage: E,F,H = PBW.algebra_generators()
            sage: E*F - F*E
            PBW['H']
            sage: H * F * E
            PBW['E']*PBW['F']*PBW['H'] - PBW['H']^2
            sage: E * F * H * E
            PBW['E']^2*PBW['F']*PBW['H'] + 2*PBW['E']^2*PBW['F']
             - PBW['E']*PBW['H']^2 - 2*PBW['E']*PBW['H']

        TESTS:

        Check that :trac:`23268` is fixed::

            sage: MS = MatrixSpace(QQ, 2,2)
            sage: gl = LieAlgebra(associative=MS)
            sage: Ugl = gl.pbw_basis()
            sage: prod(Ugl.gens())
            PBW[(0, 0)]*PBW[(0, 1)]*PBW[(1, 0)]*PBW[(1, 1)]
            sage: prod(reversed(list(Ugl.gens())))
            PBW[(0, 0)]*PBW[(0, 1)]*PBW[(1, 0)]*PBW[(1, 1)]
             - PBW[(0, 0)]^2*PBW[(1, 1)] + PBW[(0, 0)]*PBW[(1, 1)]^2
        """
        # Some trivial base cases
        if lhs == self.one_basis():
            return self.monomial(rhs)
        if rhs == self.one_basis():
            return self.monomial(lhs)

        I = self._indices
        trail = lhs.trailing_support()
        lead = rhs.leading_support()
        if self._basis_key(trail) <= self._basis_key(lead):
            return self.monomial(lhs * rhs)

        # Create the commutator
        # We have xy - yx = [x, y] -> xy = yx + [x, y] and we have x > y
        terms = self._g.monomial(trail).bracket(self._g.monomial(lead))
        lead = I.gen(lead)
        trail = I.gen(trail)
        mc = terms.monomial_coefficients(copy=False)
        terms = self.sum_of_terms((I.gen(t), c) for t,c in mc.items())
        terms += self.monomial(lead * trail)
        return self.monomial(lhs // trail) * terms * self.monomial(rhs // lead)

    def degree_on_basis(self, m):
        """
        Return the degree of the basis element indexed by ``m``.

        EXAMPLES::

            sage: L = lie_algebras.sl(QQ, 2)
            sage: PBW = L.pbw_basis()
            sage: E,H,F = PBW.algebra_generators()
            sage: PBW.degree_on_basis(E.leading_support())
            1
            sage: m = ((H*F)^10).trailing_support(key=PBW._monomial_key)  # long time
            sage: PBW.degree_on_basis(m)  # long time
            20
            sage: ((H*F*E)^4).maximal_degree()  # long time
            12
        """
        return m.length()

    def casimir_element(self, order=2, *args, **kwds):
        r"""
        Return the Casimir element of ``self``.

        .. SEEALSO::

            :meth:`~sage.categories.finite_dimensional_lie_algebras_with_basis.FiniteDimensionalLieAlgebrasWithBasis.ParentMethods.casimir_element`

        INPUT:

        - ``order`` -- (default: ``2``) the order of the Casimir element

        EXAMPLES::

            sage: L = LieAlgebra(QQ, cartan_type=['G', 2])
            sage: U = L.pbw_basis()
            sage: C = U.casimir_element(); C
            1/4*PBW[alpha[2]]*PBW[-alpha[2]] + 1/12*PBW[alpha[1]]*PBW[-alpha[1]]
             + 1/12*PBW[alpha[1] + alpha[2]]*PBW[-alpha[1] - alpha[2]] + 1/12*PBW[2*alpha[1] + alpha[2]]*PBW[-2*alpha[1] - alpha[2]]
             + 1/4*PBW[3*alpha[1] + alpha[2]]*PBW[-3*alpha[1] - alpha[2]]
             + 1/4*PBW[3*alpha[1] + 2*alpha[2]]*PBW[-3*alpha[1] - 2*alpha[2]]
             + 1/12*PBW[alphacheck[1]]^2 + 1/4*PBW[alphacheck[1]]*PBW[alphacheck[2]]
             + 1/4*PBW[alphacheck[2]]^2 - 5/12*PBW[alphacheck[1]] - 3/4*PBW[alphacheck[2]]
            sage: all(g * C == C * g for g in U.algebra_generators())
            True

        TESTS::

            sage: H = lie_algebras.Heisenberg(QQ, oo)
            sage: U = H.pbw_basis()
            sage: U.casimir_element()
            Traceback (most recent call last):
            ...
            ValueError: the Lie algebra must be finite dimensional
        """
        from sage.rings.infinity import Infinity
        if self._g.dimension() == Infinity:
            raise ValueError("the Lie algebra must be finite dimensional")
        return self._g.casimir_element(order=order, UEA=self, *args, **kwds)

    def center(self):
        r"""
        Return the center of ``self``.

        .. SEEALSO::

            :class:`~sage.algebras.lie_algebras.center_uea.CenterUEA`

        EXAMPLES::

            sage: g = LieAlgebra(QQ, cartan_type=['A', 2])
            sage: U = g.pbw_basis()
            sage: U.center()
            Center of Universal enveloping algebra of Lie algebra of ['A', 2]
             in the Chevalley basis in the Poincare-Birkhoff-Witt basis

            sage: g = lie_algebras.Heisenberg(GF(3), 4)
            sage: U = g.pbw_basis()
            sage: Z = U.center()
            Center of Universal enveloping algebra of Heisenberg algebra of rank 4
             over Finite Field of size 3 in the Poincare-Birkhoff-Witt basis
        """
        from sage.algebras.lie_algebras.center_uea import CenterUEA
        return CenterUEA(self._g, self)


    class Element(CombinatorialFreeModule.Element):
        def _act_on_(self, x, self_on_left):
            """
            Return the action of ``self`` on ``x`` by seeing if there is an
            action of the defining Lie algebra.

            EXAMPLES::

                sage: L = lie_algebras.VirasoroAlgebra(QQ)
                sage: d = L.basis()
                sage: x = d[-1]*d[-2]*d[-1] + 3*d[-3]
                sage: x
                PBW[-2]*PBW[-1]^2 + PBW[-3]*PBW[-1] + 3*PBW[-3]
                sage: M = L.verma_module(1/2,3/4)
                sage: v = M.highest_weight_vector()
                sage: x * v
                3*d[-3]*v + d[-3]*d[-1]*v + d[-2]*d[-1]*d[-1]*v
            """
            # Try the _acted_upon_ first as it might have a direct PBW action
            #   implemented that is faster
            ret = x._acted_upon_(self, not self_on_left)
            if ret is not None:
                return ret
            cm = get_coercion_model()
            L = self.parent()._g
            if self_on_left:
                if cm.discover_action(L, x.parent(), mul):
                    ret = x.parent().zero()
                    for mon, coeff in self._monomial_coefficients.items():
                        term = coeff * x
                        for k, exp in reversed(mon._sorted_items()):
                            for _ in range(exp):
                                term = L.monomial(k) * term
                        ret += term
                    return ret
            else:
                if cm.discover_action(x.parent(), L, mul):
                    ret = x.parent().zero()
                    for mon, coeff in self._monomial_coefficients.items():
                        term = coeff * x
                        for k, exp in reversed(mon._sorted_items()):
                            for _ in range(exp):
                                term = term * L.monomial(k)
                        ret += term
                    return ret
            return None
