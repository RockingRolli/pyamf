import pyamf
import pyamf.alias
from bson.dbref import (
    DBRef
)
from bson.objectid import (
    ObjectId
)
from mongoengine.base import (
    BaseDocument, BaseField
)
from mongoengine import (
    ObjectIdField
)


class MongoEngineDocumentAlias(pyamf.alias.ClassAlias):
    """
        Encode a mongoengine document into something appropriate for transport.
    """

    def __init__(self, klass, alias=None, **kwargs):
        default_excludes = ["_data", "pk", "_changed_fields", "_initialised", "_created", '_object_key']

        if not kwargs['exclude_attrs']:
            kwargs["exclude_attrs"] = default_excludes
        else:
            kwargs["exclude_attrs"] += default_excludes

        if klass._dynamic:
            kwargs["dynamic"] = True
        super(MongoEngineDocumentAlias, self).__init__(klass, alias, **kwargs)

    def getCustomProperties(self):
        try:
            props = [x for x in self.klass._fields.keys() if x is not None]
            self.encodable_properties.update(props)
            self.decodable_properties.update(props)
        except AttributeError as error:
            pass

    def getEncodableAttributes(self, obj, **kwargs):
        attrs = pyamf.ClassAlias.getEncodableAttributes(self, obj, **kwargs)

        if "_id" in attrs:
            attrs["id"] = str(attrs["_id"])
            del attrs["_id"]

        if not obj._dynamic:
            return attrs

        for name, field in obj._dynamic_fields.items():
            attrs[name] = obj.getattr(name, None)

        return attrs

    def getDecodableAttributes(self, obj, attrs, **kwargs):
        attrs = pyamf.ClassAlias.getDecodableAttributes(self, obj, attrs, **kwargs)
        fields = obj._fields
        for key, value in attrs.items():
            if key not in fields.keys():
                print "Got unknown key '%s' for %r" % (key, obj)
                del attrs[key]
        return attrs


def map_mongoengine_document(klass):
    if not isinstance(klass, type):
        klass = type(klass)
    if issubclass(klass, BaseDocument):
        return True
    return False


def objectIDHack(obj, encoder=None):
    """
    For some reason ObjectIDs fuck everything up. I dont know why and when I try to find
    out I end up smashing things. So here a little hack!

    @param obj:
    @param encoder:
    @return:
    """
    encoder.writeObject({})


pyamf.register_alias_type(MongoEngineDocumentAlias, map_mongoengine_document)
pyamf.add_type(ObjectId, objectIDHack)
