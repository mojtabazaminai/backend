from fastcrud import FastCRUD

from ..models.ingest import IngestPointOfInterest
from ..schemas.ingest import PointOfInterestCreate, PointOfInterestRead, PointOfInterestUpdate

CRUDIngestPointOfInterest = FastCRUD[
    IngestPointOfInterest,
    PointOfInterestCreate,
    PointOfInterestUpdate,
    PointOfInterestUpdate,
    PointOfInterestUpdate,
    PointOfInterestRead,
]
crud_ingest_pointofinterest = CRUDIngestPointOfInterest(IngestPointOfInterest)
