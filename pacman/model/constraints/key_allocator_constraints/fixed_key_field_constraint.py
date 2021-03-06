from .abstract_key_allocator_constraint import AbstractKeyAllocatorConstraint


class FixedKeyFieldConstraint(AbstractKeyAllocatorConstraint):
    """ Constraint that indicates fields in the mask of a key.
    """

    __slots__ = [
        # any fields that define regions in the mask with further limitations
        "_fields"
    ]

    def __init__(self, fields=None):
        """
        :param fields: \
            any fields that define regions in the mask with further limitations
        :type fields: iterable(:py:class:`pacman.utilities.utility_objs.Field`)
        :raise PacmanInvalidParameterException: if any of the fields are\
            outside of the mask i.e. mask & field.value != field.value or if\
            any of the field masks overlap i.e.,\
            field.value & other_field.value != 0
        """
        self._fields = sorted(fields, key=lambda field: field.value,
                              reverse=True)
        # TODO: Enforce the documented restrictions

    @property
    def fields(self):
        """ Any fields in the mask, i.e., ranges of the mask that have\
            further limitations

        :return: Iterable of fields, ordered by mask with the highest bit\
            range first
        :rtype: iterable(:py:class:`pacman.utilities.utility_objs.Field`)
        """
        return self._fields

    def __eq__(self, other):
        if not isinstance(other, FixedKeyFieldConstraint):
            return False
        if len(self._fields) != len(other.fields):
            return False
        return all(field in other.fields for field in self._fields)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        frozen_fields = frozenset(self._fields)
        return hash(frozen_fields)

    def __repr__(self):
        return "FixedKeyFieldConstraint(fields={})".format(
            self._fields)
