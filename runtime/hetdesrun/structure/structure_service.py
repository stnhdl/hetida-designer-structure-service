import logging
from uuid import UUID

from sqlalchemy import select

from hetdesrun.persistence.db_engine_and_session import get_session
from hetdesrun.persistence.structure_service_dbmodels import (
    SinkOrm,
    SourceOrm,
    ThingNodeOrm,
)
from hetdesrun.structure.db.exceptions import DBNotFoundError
from hetdesrun.structure.db.orm_service import (
    orm_delete_structure,
    orm_get_children,
    orm_is_database_empty,
    orm_load_structure_from_json_file,
    orm_update_structure,
)
from hetdesrun.structure.models import CompleteStructure, Sink, Source, ThingNode

logger = logging.getLogger(__name__)


async def get_children(
    parent_id: UUID | None,
) -> tuple[list[ThingNode], list[Source], list[Sink]]:
    """Wrapper function to retrieve the child nodes, sources,
    and sinks associated with a given parent node from the database.
    """
    logger.debug("Calling wrapper function 'get_children' for parent_id: %s", parent_id)
    children = await orm_get_children(parent_id)
    logger.debug("Wrapper function 'get_children' completed for parent_id: %s", parent_id)
    return children


async def get_single_thingnode_from_db(tn_id: UUID) -> ThingNode:
    logger.debug("Fetching single ThingNode from database with ID: %s", tn_id)
    async with get_session()() as session:
        result = await session.execute(select(ThingNodeOrm).where(ThingNodeOrm.id == tn_id))
        thing_node = result.scalar_one_or_none()
        if thing_node:
            logger.debug("ThingNode with ID %s found.", tn_id)
            return ThingNode.from_orm_model(thing_node)

    logger.error("No ThingNode found for ID %s. Raising DBNotFoundError.", tn_id)
    raise DBNotFoundError(f"No ThingNode found for ID {tn_id}")


async def get_all_thing_nodes_from_db() -> list[ThingNode]:
    logger.debug("Fetching all ThingNodes from the database.")
    async with get_session()() as session:
        result = await session.execute(select(ThingNodeOrm))
        thing_nodes = result.scalars().all()

    logger.debug("Successfully fetched %d ThingNodes from the database.", len(thing_nodes))
    return [ThingNode.from_orm_model(thing_node) for thing_node in thing_nodes]


async def get_collection_of_thingnodes_from_db(tn_ids: list[UUID]) -> dict[UUID, ThingNode]:
    logger.debug("Fetching collection of ThingNodes with IDs: %s", tn_ids)
    thingnodes = {tn_id: await get_single_thingnode_from_db(tn_id) for tn_id in tn_ids}
    logger.debug("Successfully fetched collection of ThingNodes.")
    return thingnodes


async def get_single_source_from_db(src_id: UUID) -> Source:
    logger.debug("Fetching single Source from database with ID: %s", src_id)
    async with get_session()() as session:
        result = await session.execute(select(SourceOrm).filter(SourceOrm.id == src_id))
        source = result.scalar_one_or_none()
        if source:
            logger.debug("Source with ID %s found.", src_id)
            return Source.from_orm_model(source)

    logger.error("No Source found for ID %s. Raising DBNotFoundError.", src_id)
    raise DBNotFoundError(f"No Source found for ID {src_id}")


async def get_all_sources_from_db() -> list[Source]:
    logger.debug("Fetching all Sources from the database.")
    async with get_session()() as session:
        result = await session.execute(select(SourceOrm))
        sources = result.scalars().all()
    logger.debug("Successfully fetched %d sources from the database.", len(sources))
    return [Source.from_orm_model(source) for source in sources]


async def get_collection_of_sources_from_db(src_ids: list[UUID]) -> dict[UUID, Source]:
    logger.debug("Fetching collection of Sources with IDs: %s", src_ids)
    sources = {src_id: await get_single_source_from_db(src_id) for src_id in src_ids}

    logger.debug("Successfully fetched collection of Sources.")
    return sources


async def get_single_sink_from_db(sink_id: UUID) -> Sink:
    logger.debug("Fetching single Sink from database with ID: %s", sink_id)
    async with get_session()() as session:
        result = await session.execute(select(SinkOrm).filter(SinkOrm.id == sink_id))
        sink = result.scalar_one_or_none()
        if sink:
            logger.debug("Sink with ID %s found.", sink_id)
            return Sink.from_orm_model(sink)

    logger.error("No Sink found for ID %s. Raising DBNotFoundError.", sink_id)
    raise DBNotFoundError(f"No Sink found for ID {sink_id}")


async def get_all_sinks_from_db() -> list[Sink]:
    logger.debug("Fetching all Sinks from the database.")
    async with get_session()() as session:
        result = await session.execute(select(SinkOrm))
        sinks = result.scalars().all()

    logger.debug("Successfully fetched %d sinks from the database.", len(sinks))
    return [Sink.from_orm_model(sink) for sink in sinks]


async def get_collection_of_sinks_from_db(sink_ids: list[UUID]) -> dict[UUID, Sink]:
    logger.debug("Fetching collection of Sinks with IDs: %s", sink_ids)

    sinks = {sink_id: await get_single_sink_from_db(sink_id) for sink_id in sink_ids}
    logger.debug("Successfully fetched collection of Sinks.")
    return sinks


async def is_database_empty() -> bool:
    """Wrapper function to check if the database is empty."""
    logger.debug("Calling wrapper function 'is_database_empty'.")
    is_empty = await orm_is_database_empty()
    logger.debug(
        "Wrapper function 'is_database_empty' completed. Database is %s.",
        "empty" if is_empty else "not empty",
    )
    return is_empty


async def delete_structure() -> None:
    """Wrapper function to delete the entire structure in the database."""
    logger.debug("Calling wrapper function 'delete_structure'.")
    async with get_session()() as session:
        await orm_delete_structure(session)
    logger.debug(
        "Wrapper function 'delete_structure' completed. "
        "Successfully deleted the entire structure from the database."
    )


def update_structure(
    complete_structure: CompleteStructure,
) -> CompleteStructure:
    """Wrapper function to update or insert the given complete structure into the database."""
    logger.debug("Calling wrapper function 'update_structure'.")
    updated_structure = orm_update_structure(complete_structure)
    logger.debug(
        "Wrapper function 'update_structure' completed. "
        "Successfully updated or inserted the complete structure into the database."
    )
    return updated_structure


def load_structure_from_json_file(file_path: str) -> CompleteStructure:
    return orm_load_structure_from_json_file(file_path)
