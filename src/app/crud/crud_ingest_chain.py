from fastcrud import FastCRUD

from ..models.ingest import IngestChain
from ..schemas.ingest import ChainCreate, ChainRead, ChainUpdate

CRUDIngestChain = FastCRUD[
    IngestChain,
    ChainCreate,
    ChainUpdate,
    ChainUpdate,
    ChainUpdate,
    ChainRead,
]
crud_ingest_chain = CRUDIngestChain(IngestChain)
