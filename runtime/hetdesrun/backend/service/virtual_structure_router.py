import logging

from fastapi import HTTPException, Query, status

from hetdesrun.structure.db.db_structure_service import orm_update_structure
from hetdesrun.structure.db.exceptions import (
    DBAssociationError,
    DBFetchError,
    DBIntegrityError,
    DBNotFoundError,
    DBUpdateError,
)
from hetdesrun.structure.models import CompleteStructure
from hetdesrun.structure.vst_structure_service import (
    delete_structure,
    is_database_empty,
)
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


virtual_structure_router = HandleTrailingSlashAPIRouter(
    prefix="/structure",
    tags=["structure"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@virtual_structure_router.put(
    "/update",
    summary="Updates a structure of the virtual structure adapter",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_204_NO_CONTENT: {"description": "Successfully updated the structure"}},
)
async def update_structure_endpoint(
    new_structure: CompleteStructure,
    delete_existing_structure: bool = Query(True, alias="delete_existing_structure"),
) -> None:
    logger.info("Starting to update the vst structure via the API endpoint")
    if delete_existing_structure and not is_database_empty():
        logger.info("Starting to delete existing structure")
        try:
            delete_structure()
        except DBIntegrityError as e:
            logger.error("Structure deletion during an update request failed: %s", e)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    try:
        orm_update_structure(new_structure)
        logger.info("The structure was successfully updated")
    except (DBIntegrityError, DBUpdateError, DBAssociationError, DBFetchError) as e:
        logger.error("Structure update request failed: %s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        logger.error("Structure update request failed: %s", e)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
