from fastcrud import FastCRUD

from ..models.ingest import IngestJob
from ..schemas.ingest import JobCreate, JobDelete, JobRead, JobUpdate

CRUDIngestJob = FastCRUD[
    IngestJob,
    JobCreate,
    JobUpdate,
    JobUpdate,
    JobDelete,
    JobRead,
]
crud_ingest_job = CRUDIngestJob(IngestJob)
