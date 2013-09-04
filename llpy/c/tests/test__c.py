#!/usr/bin/env python3
import unittest

from llpy.c import _c

class TestEnum(unittest.TestCase):

    def test_serial(self):
        Seq = _c.enum('Seq', FOO=1, BAR=2)
        ZERO = Seq(0)
        FOO = Seq(1)
        BAR = Seq(2)
        BAZ = Seq(3)
        assert Seq.FOO == FOO
        assert Seq.BAR == BAR
        assert Seq(3) == BAZ
        assert Seq.FOO is not FOO
        assert Seq.BAR is not BAR
        assert Seq(3) is not BAZ
        assert FOO != BAR
        assert not ZERO
        assert FOO
        assert BAR
        assert BAZ

        assert isinstance(FOO, Seq)
        assert isinstance(BAR, Seq)
        assert repr(ZERO) == 'Seq()'
        assert repr(FOO) == 'Seq.FOO'
        assert repr(BAR) == 'Seq.BAR'
        assert repr(BAZ) == 'Seq(3)'

    def test_bitwise(self):
        Bit = _c.bit_enum('Bit', FOO=1, BAR=2)
        ZERO = Bit(0)
        FOO = Bit(1)
        BAR = Bit(2)
        BAZ = Bit(3)
        assert Bit.FOO == FOO
        assert Bit.BAR == BAR
        assert Bit(3) == BAZ
        assert Bit.FOO is not FOO
        assert Bit.BAR is not BAR
        assert Bit(3) is not BAZ
        assert FOO != BAR
        assert not ZERO
        assert FOO
        assert BAR
        assert BAZ

        assert isinstance(FOO, Bit)
        assert isinstance(BAR, Bit)
        assert repr(ZERO) == 'Bit()'
        assert repr(FOO) == 'Bit.FOO'
        assert repr(BAR) == 'Bit.BAR'
        assert repr(BAZ) == 'Bit.FOO | Bit.BAR'
        assert repr(Bit(0x8)) == 'Bit(0x8)'
        assert repr(Bit(0xC)) == 'Bit(0xC)'
        assert repr(Bit(5)) == 'Bit.FOO | Bit(0x4)'
        assert repr(Bit(6)) == 'Bit.BAR | Bit(0x4)'
        assert repr(Bit(7)) == 'Bit.FOO | Bit.BAR | Bit(0x4)'


        assert FOO | ZERO == FOO
        assert FOO | FOO == FOO
        assert FOO | BAR == BAZ
        assert FOO | BAZ == BAZ

        assert FOO & ZERO == ZERO
        assert FOO & FOO == FOO
        assert FOO & BAR == ZERO
        assert FOO & BAZ == FOO

        assert FOO ^ ZERO == FOO
        assert FOO ^ FOO == ZERO
        assert FOO ^ BAR == BAZ
        assert FOO ^ BAZ == BAR

        assert FOO & ~ZERO == FOO
        assert FOO & ~FOO == ZERO
        assert FOO & ~BAR == FOO
        assert FOO & ~BAZ == ZERO

    def test_bitwise_max(self):
        Signed = _c.bit_enum('Signed', MAX=2**30)
        Unsigned = _c.bit_enum('Unsigned', MAX=2**31)
        assert Signed(2 ** 31).value < 0
        assert Unsigned(2 ** 31).value > 0


if __name__ == '__main__':
    unittest.main()
