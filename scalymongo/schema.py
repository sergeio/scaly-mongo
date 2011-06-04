"""The base document models.
"""

from scalymongo.errors import SchemaError

class UpdatingList(list):
    """Provide a list with an update method.

    Since dicts are used to describe some attributes they must use a data
    structure that does not rely on hashing.  This wrapper class just tacks the
    :meth:`update` method onto a list to make them interoperable with ``set``
    and ``dict`` instances.
    """
    update = list.extend


class SchemaMetaclass(type):
    """Metaclass for documents that have a schema."""

    mergeable_attrs = {
        'structure': dict,
        'indexes': UpdatingList,
        'required_fields': set,
    }
    "Map the merged base class attributes to their expected types."

    def __new__(cls, name, bases, attrs):
        for key, type_ in cls.mergeable_attrs.iteritems():
            if key in attrs:
                attrs[key] = type_(attrs[key])
            else:
                attrs[key] = type_()

        for base in bases:
            for field, type_ in cls.mergeable_attrs.iteritems():
                if hasattr(base, field):
                    attrs[field].update(getattr(base, field))

        attrs['shard_index'] = find_shard_index(attrs['indexes'])

        return type.__new__(cls, name, bases, attrs)


def find_shard_index(indexes):
    """Find the shard key and validate index properties.
    """
    shard_key_indexes = [index for index in indexes
                         if index.get('shard_key')]
    if not shard_key_indexes:
        return None

    if len(shard_key_indexes) > 1:
        raise SchemaError('There can only be one shard key per collection.')

    shard_index = shard_key_indexes[0]

    unique_indexes = [index for index in indexes if index.get('unique')]

    if len(unique_indexes) > 1:
        raise SchemaError(
            'A sharded collection may only have one unique index.')

    if unique_indexes and unique_indexes != shard_key_indexes:
        raise SchemaError(
            'Only the shard key may be used as a unique index on'
            ' a sharded collection.')

    return shard_index


class SchemaDocument(dict):
    """Base class for all documents with an enforced schema."""

    __metaclass__ = SchemaMetaclass

    def validate(self):
        validate_structure(self, self.structure)
        validate_required_fields(self, self.required_fields)


def validate_structure(fields, structure):
    """Recursively validate the structure of a :class:`dict`."""
    for field, value in fields.iteritems():
        if field not in structure:
            raise ValidationError(
                'Encountered unknown field {0}'.format(field))

        expected_type = structure[field]

        # Check the recursive case.
        if type(expected_type) is dict:
            validate_structure(value, expected_type)
        elif not isinstance(value, expected_type):
            raise ValidationError(
                'Field {0} was expected to be type {1}, but found {2}'
                .format(repr(field), expected_type, type(value)))


def validate_required_fields(fields, required):
    """Ensure that all :param required: fields are present in :param fields:.
    """
    missing = required.difference(fields.keys())
    if missing:
        raise ValidationError(
            'Missing required field(s) {0}'.format(
                ','.join([repr(name) for name in missing])))


class ValidationError(Exception):
    pass
