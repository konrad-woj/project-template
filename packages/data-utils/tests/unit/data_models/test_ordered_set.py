import pytest

from data_utils.data_structures import OrderedSet


def test_init():
    s = OrderedSet()
    assert len(s) == 0
    assert not s

    s = OrderedSet([1, 2, 3])
    assert len(s) == 3
    assert list(s) == [1, 2, 3]

    s = OrderedSet([3, 1, 2, 3])  # Test with duplicates
    assert len(s) == 3
    assert list(s) == [3, 1, 2]

    s = OrderedSet("hello")  # Test with string
    assert list(s) == ["h", "e", "l", "o"]


def test_add():
    s = OrderedSet()
    s.add(1)
    assert len(s) == 1
    assert 1 in s
    assert list(s) == [1]

    s.add(2)
    assert len(s) == 2
    assert 2 in s
    assert list(s) == [1, 2]

    s.add(1)  # Adding existing item
    assert len(s) == 2
    assert list(s) == [1, 2]


def test_discard():
    s = OrderedSet([1, 2, 3])
    s.discard(2)
    assert len(s) == 2
    assert 2 not in s
    assert list(s) == [1, 3]

    s.discard(4)  # Discarding non-existent item
    assert len(s) == 2
    assert list(s) == [1, 3]

    s.discard(1)
    s.discard(3)
    assert len(s) == 0
    assert not s


def test_remove():
    s = OrderedSet([1, 2, 3])
    s.remove(2)
    assert len(s) == 2
    assert 2 not in s
    assert list(s) == [1, 3]

    with pytest.raises(KeyError, match="4 not found in OrderedSet"):
        s.remove(4)  # Removing non-existent item should raise KeyError

    s.remove(1)
    s.remove(3)
    assert len(s) == 0


def test_clear():
    s = OrderedSet([1, 2, 3])
    s.clear()
    assert len(s) == 0
    assert not s
    assert list(s) == []

    s_empty = OrderedSet()
    s_empty.clear()
    assert len(s_empty) == 0
    assert not s_empty


def test_contains():
    s = OrderedSet([1, 2, 3])
    assert 1 in s
    assert 2 in s
    assert 3 in s
    assert 4 not in s


def test_len():
    s = OrderedSet()
    assert len(s) == 0
    s.add(1)
    assert len(s) == 1
    s.add(2)
    assert len(s) == 2
    s.add(1)  # Duplicate
    assert len(s) == 2
    s.discard(1)
    assert len(s) == 1
    s.discard(3)  # Non-existent
    assert len(s) == 1


def test_iter():
    s = OrderedSet([10, 20, 30])
    iterator = iter(s)
    assert next(iterator) == 10
    assert next(iterator) == 20
    assert next(iterator) == 30
    with pytest.raises(StopIteration):
        next(iterator)

    s_empty = OrderedSet()
    assert list(s_empty) == []


def test_difference():
    s1 = OrderedSet([1, 2, 3, 4])
    s2 = OrderedSet([3, 4, 5, 6])
    result = s1.difference(s2)
    assert isinstance(result, OrderedSet)
    assert list(result) == [1, 2]
    assert list(s1) == [1, 2, 3, 4]  # Original should not be modified

    s3 = OrderedSet([1, 2])
    s4 = OrderedSet([1, 2, 3, 4])
    result = s3.difference(s4)
    assert list(result) == []

    result = s4.difference(s3)
    assert list(result) == [3, 4]


def test_difference_update():
    s = OrderedSet([1, 2, 3, 4, 5])
    s.difference_update([3, 5, 6])
    assert len(s) == 3
    assert list(s) == [1, 2, 4]

    s_empty = OrderedSet()
    s_empty.difference_update([1, 2])
    assert len(s_empty) == 0

    s_all_removed = OrderedSet([1, 2])
    s_all_removed.difference_update([1, 2])
    assert len(s_all_removed) == 0
    assert not s_all_removed


def test_intersection():
    s1 = OrderedSet([1, 2, 3, 4])
    s2 = OrderedSet([3, 1, 5, 2])  # Different order for s2
    result = s1.intersection(s2)
    assert isinstance(result, OrderedSet)
    assert list(result) == [1, 2, 3]  # Order from s1 for common elements
    assert list(s1) == [1, 2, 3, 4]  # Original should not be modified

    s3 = OrderedSet([1, 2])
    s4 = OrderedSet([3, 4])
    result = s3.intersection(s4)
    assert list(result) == []

    result = s1.intersection([])
    assert list(result) == []


def test_intersection_update():
    s = OrderedSet([1, 2, 3, 4])
    s.intersection_update([3, 1, 5, 2])
    assert list(s) == [1, 2, 3]  # Order preserved from original s for common elements

    s = OrderedSet([1, 2, 3, 4])
    s.intersection_update([5, 6])
    assert list(s) == []
    assert not s

    s = OrderedSet([1, 2])
    s.intersection_update([1, 2])
    assert list(s) == [1, 2]


def test_union():
    s1 = OrderedSet([1, 2, 3])
    s2 = OrderedSet([3, 4, 5])
    result = s1.union(s2)
    assert isinstance(result, OrderedSet)
    assert list(result) == [1, 2, 3, 4, 5]
    assert list(s1) == [1, 2, 3]  # Original should not be modified

    s3 = OrderedSet([1, 2])
    s4 = OrderedSet([1, 2])
    result = s3.union(s4)
    assert list(result) == [1, 2]

    result = s1.union([])
    assert list(result) == [1, 2, 3]


def test_update():
    s = OrderedSet([1, 2, 3])
    s.update([3, 4, 5])
    assert list(s) == [1, 2, 3, 4, 5]

    s_empty = OrderedSet()
    s_empty.update([1, 2])
    assert list(s_empty) == [1, 2]

    s_no_new_items = OrderedSet([1, 2])
    s_no_new_items.update([1, 2])
    assert list(s_no_new_items) == [1, 2]


def test_issubset():
    s1 = OrderedSet([1, 2])
    s2 = OrderedSet([1, 2, 3])
    s3 = OrderedSet([1, 3])
    s4 = OrderedSet([2, 1])  # Same elements, different order

    assert s1.issubset(s2)
    assert s1.issubset(s1)
    assert not s2.issubset(s1)
    assert not s1.issubset(s3)
    assert not s1.issubset([])  # Non-empty cannot be subset of empty
    assert OrderedSet().issubset(s1)  # Empty is subset of any set
    assert OrderedSet().issubset([])
    assert s1.issubset(s4)  # Order doesn't matter for subset logic


def test_issuperset():
    s1 = OrderedSet([1, 2, 3])
    s2 = OrderedSet([1, 2])
    s3 = OrderedSet([1, 4])
    s4 = OrderedSet([2, 1])  # Same elements, different order

    assert s1.issuperset(s2)
    assert s1.issuperset(s1)
    assert not s2.issuperset(s1)
    assert not s1.issuperset(s3)
    assert s1.issuperset([])  # Any set is superset of empty
    assert not OrderedSet().issuperset(s1)
    assert OrderedSet().issuperset([])
    assert s1.issuperset(s4)  # Order doesn't matter for superset logic


def test_pop():
    s = OrderedSet([1, 2, 3])
    assert s.pop() == 1
    assert list(s) == [2, 3]
    assert s.pop() == 2
    assert list(s) == [3]
    assert s.pop() == 3
    assert list(s) == []
    assert not s

    with pytest.raises(KeyError, match="pop from an empty OrderedSet"):
        s.pop()


def test_repr():
    s = OrderedSet()
    assert repr(s) == "OrderedSet([])"

    s.add("a")
    s.add("b")
    assert repr(s) == "OrderedSet(['a', 'b'])"


def test_bool():
    s = OrderedSet()
    assert not s
    s.add(1)
    assert bool(s)
    s.discard(1)
    assert not s


def test_eq_ne():
    s1 = OrderedSet([1, 2, 3])
    s2 = OrderedSet([1, 2, 3])
    s3 = OrderedSet([3, 2, 1])  # Different order
    s4 = OrderedSet([1, 2])

    assert s1 == s2
    assert s1 != s3
    assert s1 != s4
    assert s3 != s4

    assert s1 == OrderedSet(list(s1))  # Check with copy

    # Test with non-OrderedSet types (should return NotImplemented then False)
    assert (s1 == [1, 2, 3]) is False
    assert (s1 != [1, 2, 3]) is True


def test_sub_operator():
    s1 = OrderedSet([1, 2, 3, 4])
    s2 = OrderedSet([3, 4, 5])
    result = s1 - s2
    assert isinstance(result, OrderedSet)
    assert list(result) == [1, 2]
    assert list(s1) == [1, 2, 3, 4]  # Original unchanged


def test_and_operator():
    s1 = OrderedSet([1, 2, 3, 4])
    s2 = OrderedSet([3, 1, 5, 2])
    result = s1 & s2
    assert isinstance(result, OrderedSet)
    assert list(result) == [1, 2, 3]  # Order from s1
    assert list(s1) == [1, 2, 3, 4]  # Original unchanged


def test_or_operator():
    s1 = OrderedSet([1, 2, 3])
    s2 = OrderedSet([3, 4, 5])
    result = s1 | s2
    assert isinstance(result, OrderedSet)
    assert list(result) == [1, 2, 3, 4, 5]
    assert list(s1) == [1, 2, 3]  # Original unchanged


def test_isub_operator():
    s = OrderedSet([1, 2, 3, 4])
    s -= [3, 4, 5]
    assert list(s) == [1, 2]


def test_iand_operator():
    s = OrderedSet([1, 2, 3, 4])
    s &= [3, 1, 5, 2]
    assert list(s) == [1, 2, 3]


def test_ior_operator():
    s = OrderedSet([1, 2, 3])
    s |= [3, 4, 5]
    assert list(s) == [1, 2, 3, 4, 5]
