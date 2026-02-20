from fastcrud import FastCRUD

from ..models.ingest import IngestCategory
from ..schemas.ingest import CategoryCreate, CategoryRead, CategoryUpdate

CRUDIngestCategory = FastCRUD[
    IngestCategory,
    CategoryCreate,
    CategoryUpdate,
    CategoryUpdate,
    CategoryUpdate,
    CategoryRead,
]
crud_ingest_category = CRUDIngestCategory(IngestCategory)
