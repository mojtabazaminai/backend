from fastcrud import FastCRUD
from ..models.property import Property
from ..schemas.property import PropertyBase

CRUDProperty = FastCRUD[Property, PropertyBase, PropertyBase, PropertyBase, PropertyBase, PropertyBase]
crud_property = CRUDProperty(Property)
