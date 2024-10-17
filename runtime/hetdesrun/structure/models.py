import uuid
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError, root_validator, validator

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.persistence.structure_service_dbmodels import (
    ElementTypeDBModel,
    SinkDBModel,
    SourceDBModel,
    ThingNodeDBModel,
)
from hetdesrun.structure.db.exceptions import DBIntegrityError


class ElementType(BaseModel):
    id: UUID = Field(
        default_factory=uuid.uuid4,
        description="The primary key for the ElementType table",
    )
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the ElementType")
    name: str = Field(..., description="Unique name of the ElementType")
    description: str | None = Field(None, description="Description of the ElementType")
    thing_nodes: list["ThingNode"] = Field(
        default_factory=list, description="List of associated ThingNodes"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ElementTypeDBModel:
        return ElementTypeDBModel(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            description=self.description,
            thing_nodes=[tn.to_orm_model() for tn in self.thing_nodes],
        )

    @classmethod
    def from_orm_model(cls, orm_model: ElementTypeDBModel) -> "ElementType":
        try:
            return cls(
                id=orm_model.id,
                external_id=orm_model.external_id,
                stakeholder_key=orm_model.stakeholder_key,
                name=orm_model.name,
                description=orm_model.description,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e


class ThingNode(BaseModel):
    id: UUID = Field(
        default_factory=uuid.uuid4,
        description="The primary key for the ThingNode table",
    )
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the Thing Node")
    name: str = Field(..., description="Unique name of the Thing Node")
    description: str = Field("", description="Description of the Thing Node")
    parent_node_id: UUID | None = Field(
        None, description="Parent node UUID if this is a child node"
    )
    parent_external_node_id: str | None = Field(
        None, description="Externally provided unique identifier for the parent node"
    )
    # This ID is filled with a dummy-value to enable object creation
    # from a json-file for CompleteStructure
    # It is necessary because at the time of json-creation the real UUID
    # corresponding to the element types external ID is unknown
    element_type_id: UUID = Field(
        default_factory=uuid.uuid4, description="Foreign key to the ElementType table"
    )
    element_type_external_id: str = Field(
        ..., description="Externally provided unique identifier for the element type"
    )
    meta_data: dict[str, Any] | None = Field(
        None, description="Optional metadata for the Thing Node"
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> ThingNodeDBModel:
        return ThingNodeDBModel(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            description=self.description,
            parent_node_id=self.parent_node_id,
            parent_external_node_id=self.parent_external_node_id,
            element_type_id=self.element_type_id,
            element_type_external_id=self.element_type_external_id,
            meta_data=self.meta_data,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ThingNodeDBModel) -> "ThingNode":
        try:
            return ThingNode(
                id=orm_model.id,
                external_id=orm_model.external_id,
                stakeholder_key=orm_model.stakeholder_key,
                name=orm_model.name,
                description=orm_model.description,
                parent_node_id=orm_model.parent_node_id,
                parent_external_node_id=orm_model.parent_external_node_id,
                element_type_id=orm_model.element_type_id,
                element_type_external_id=orm_model.element_type_external_id,
                meta_data=orm_model.meta_data,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e


class FilterType(str, Enum):
    free_text = "free_text"


class Filter(BaseModel):
    name: str = Field(..., description="Name of the filter")
    internal_name: str = Field(
        default="",
        description="Name used to identify the filter in the input or output wiring",
    )
    type: FilterType = Field(..., description="Type of the filter")  # noqa: A003
    required: bool = Field(..., description="Indicates if the filter is required")

    @root_validator(pre=True)
    def set_internal_name(cls, values: dict) -> dict:
        # Internally the designer requires an identifier for the filter
        # that has to be separated by underscores
        # Hence, an internal name is created for the wiring resoultion
        # performed by the virtual structure adapter
        values["internal_name"] = "_".join(values["name"].strip().lower().split())
        return values

    @validator("name")
    def no_empty_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The name of the filter must be set")
        return value


class Source(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the source")  # noqa: A003
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the Source")
    name: str = Field(..., description="Name of the source")
    type: ExternalType = Field(..., description="Type of the source")  # noqa: A003
    visible: bool = Field(True, description="Visibility of the source")
    display_path: str = Field(
        "", description="Displays all parent nodes in sequence in the designer frontend"
    )
    preset_filters: dict[str, Any] = Field(
        default_factory=dict, description="Preset filters for the source"
    )
    passthrough_filters: list[Filter] | None = Field(
        None, description="Passthrough filters for the source"
    )
    adapter_key: str = Field(..., description="Adapter key or identifier")
    source_id: str = Field(..., description="Referenced HD Source identifier")
    ref_key: str | None = Field(
        None,
        description="Key of the referenced metadatum, only used for sources of type metadata(any)",
    )
    ref_id: str = Field(
        "",
        description="ID of the thingnode in the mapped adapter hierarchy,"
        " which the mapped source references if source has type metadata(any)",
    )
    meta_data: dict[str, Any] | None = Field(None, description="Optional metadata for the Source")
    thing_node_external_ids: list[str] | None = Field(
        None,
        description="List of externally provided unique identifiers for the thing nodes",
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> SourceDBModel:
        return SourceDBModel(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            type=self.type,
            visible=self.visible,
            display_path=self.display_path,
            preset_filters=self.preset_filters,
            passthrough_filters=[f.dict() for f in self.passthrough_filters]
            if self.passthrough_filters
            else None,
            adapter_key=self.adapter_key,
            source_id=self.source_id,
            ref_key=self.ref_key,
            ref_id=self.ref_id,
            meta_data=self.meta_data,
            thing_node_external_ids=self.thing_node_external_ids
            if self.thing_node_external_ids is not None
            else [],
        )

    @classmethod
    def from_orm_model(cls, orm_model: SourceDBModel) -> "Source":
        return Source(
            id=orm_model.id,
            external_id=orm_model.external_id,
            stakeholder_key=orm_model.stakeholder_key,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            display_path=orm_model.display_path,
            preset_filters=orm_model.preset_filters,
            passthrough_filters=orm_model.passthrough_filters,
            adapter_key=orm_model.adapter_key,
            source_id=orm_model.source_id,
            ref_key=orm_model.ref_key,
            ref_id=orm_model.ref_id,
            meta_data=orm_model.meta_data,
            thing_node_external_ids=orm_model.thing_node_external_ids,
        )

    @validator("preset_filters", "passthrough_filters", pre=True, each_item=True)
    def validate_filters(cls, v: Any) -> Any:
        if not v:
            return {}
        return v


class Sink(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the sink")  # noqa: A003
    external_id: str = Field(..., description="Externally provided unique identifier")
    stakeholder_key: str = Field(..., description="Stakeholder key for the Sink")
    name: str = Field(..., description="Name of the sink")
    type: ExternalType = Field(..., description="Type of the sink")  # noqa: A003
    visible: bool = Field(True, description="Visibility of the sink")
    display_path: str = Field(
        "", description="Displays all parent nodes in sequence in the designer frontend"
    )
    preset_filters: dict[str, Any] = Field(
        default_factory=dict, description="Preset filters for the sink"
    )
    passthrough_filters: list[Filter] | None = Field(
        None, description="Passthrough filters for the sink"
    )
    adapter_key: str = Field(..., description="Adapter key or identifier")
    sink_id: str = Field(..., description="Referenced HD Sink identifier")
    ref_key: str | None = Field(
        None,
        description="Key of the referenced metadatum, only used for sinks of type metadata(any)",
    )
    ref_id: str = Field(
        "",
        description="ID of the thingnode in the mapped adapter hierarchy,"
        " which the mapped source references if sink has type metadata(any)",
    )
    meta_data: dict[str, Any] | None = Field(None, description="Optional metadata for the Sink")
    thing_node_external_ids: list[str] | None = Field(
        None,
        description="List of externally provided unique identifiers for the thing nodes",
    )

    class Config:
        orm_mode = True

    def to_orm_model(self) -> SinkDBModel:
        return SinkDBModel(
            id=self.id,
            external_id=self.external_id,
            stakeholder_key=self.stakeholder_key,
            name=self.name,
            type=self.type,
            visible=self.visible,
            display_path=self.display_path,
            preset_filters=self.preset_filters,
            passthrough_filters=[f.dict() for f in self.passthrough_filters]
            if self.passthrough_filters
            else None,
            adapter_key=self.adapter_key,
            sink_id=self.sink_id,
            ref_key=self.ref_key,
            ref_id=self.ref_id,
            meta_data=self.meta_data,
            thing_node_external_ids=self.thing_node_external_ids
            if self.thing_node_external_ids is not None
            else [],
        )

    @classmethod
    def from_orm_model(cls, orm_model: SinkDBModel) -> "Sink":
        return Sink(
            id=orm_model.id,
            external_id=orm_model.external_id,
            stakeholder_key=orm_model.stakeholder_key,
            name=orm_model.name,
            type=orm_model.type,
            visible=orm_model.visible,
            display_path=orm_model.display_path,
            preset_filters=orm_model.preset_filters,
            passthrough_filters=orm_model.passthrough_filters,
            adapter_key=orm_model.adapter_key,
            sink_id=orm_model.sink_id,
            ref_key=orm_model.ref_key,
            ref_id=orm_model.ref_id,
            meta_data=orm_model.meta_data,
            thing_node_external_ids=orm_model.thing_node_external_ids,
        )

    @validator("preset_filters", "passthrough_filters", pre=True, each_item=True)
    def validate_filters(cls, v: Any) -> Any:
        if not v:
            return {}
        return v


class CompleteStructure(BaseModel):
    element_types: list[ElementType] = Field(..., description="All element types of the structure")
    thing_nodes: list[ThingNode] = Field(
        default_factory=list, description="All thingnodes of the structure"
    )
    sources: list[Source] = Field(default_factory=list, description="All sources of the structure")
    sinks: list[Sink] = Field(default_factory=list, description="All sinks of the structure")

    @classmethod
    def agnostic_getattr(cls, obj: dict | Any, attr: str) -> Any:
        """Helper function to make the root validators work when instantiating
        from a json and from pydantic objects.
        """
        # Check if object is dict, if so use get
        if isinstance(obj, dict):
            return obj.get(attr)

        # Fallback to getattr
        return getattr(obj, attr)

    @validator("element_types")
    def check_element_types_not_empty(cls, v: list[ElementType]) -> list[ElementType]:
        if not v:
            raise ValueError(
                "The structure must include at least one ElementType object to be valid."
            )
        return v

    @root_validator(pre=True)
    def validate_root_nodes_parent_ids_are_none(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Check if each parent_external_node_id exists in at least one other node

        nodes = values.get("thing_nodes", [])
        # Create a set of all external_ids in the thing_nodes list
        external_ids = {cls.agnostic_getattr(node, "external_id") for node in nodes}

        for node in nodes:
            parent_ext_id = cls.agnostic_getattr(node, "parent_external_node_id")
            if parent_ext_id is not None and parent_ext_id not in external_ids:
                # Raise an error if the parent_external_node_id does not exist in the other nodes
                raise ValueError(
                    f"Root node '{cls.agnostic_getattr(node, "name")}' has an invalid "
                    f"parent_external_node_id '{parent_ext_id}' that does "
                    "not reference any existing ThingNode."
                )
        return values

    @root_validator(pre=True)
    def check_for_duplicate_key_and_id_pairs(cls, values: dict[str, Any]) -> dict[str, Any]:
        for element_name, element_list in values.items():
            seen = set()
            for element in element_list:
                stakeholder_key = cls.agnostic_getattr(element, "stakeholder_key")
                external_id = cls.agnostic_getattr(element, "external_id")

                key_id_pair = (stakeholder_key, external_id)
                if key_id_pair in seen:
                    raise ValueError(
                        f"The stakeholder key and external id pair: {key_id_pair} "
                        f"exists at least twice in the {element_name} list. "
                        "Each key-id pair must be unique within its list!"
                    )
                seen.add(key_id_pair)
        return values

    @root_validator(pre=True)
    def check_for_duplicate_ids_in_thing_node_external_ids(
        cls, values: dict[str, Any]
    ) -> dict[str, Any]:
        for element_name, element_list in values.items():
            if element_name in ("element_types", "thing_nodes"):
                continue

            for element in element_list:
                seen = set()
                thing_node_external_ids = cls.agnostic_getattr(element, "thing_node_external_ids")
                for parent_id in thing_node_external_ids:
                    if parent_id in seen:
                        raise ValueError(
                            f"The thing_node_external_ids attribute "
                            f"of the element with id: {element["external_id"]} "
                            f"in the {element_name} list, "
                            f"contains at least the duplicate id: {parent_id}. "
                            "Each id within thing_node_external_ids must be unique!"
                        )
                    seen.add(parent_id)
        return values

    @root_validator(pre=True)
    def check_stakeholder_key_consistency(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Retrieve the list of thing_nodes from the input values.
        # If 'thing_nodes' is not provided, default to an empty list.
        thing_nodes = values.get("thing_nodes", [])

        # Identify root nodes.
        # A root node is defined as a node without a parent (parent_external_node_id is None).
        root_nodes = [
            node
            for node in thing_nodes
            if cls.agnostic_getattr(node, "parent_external_node_id") is None
        ]

        # Iterate over each root node to validate the hierarchy starting from it.
        for root_node in root_nodes:
            # The expected stakeholder_key for this hierarchy is
            # the stakeholder_key of the root node.
            expected_stakeholder_key = cls.agnostic_getattr(root_node, "stakeholder_key")

            # Initialize a stack for depth-first traversal of the hierarchy.
            stack = [root_node]

            # Initialize a set to keep track of visited nodes to
            # prevent infinite loops in case of cycles.
            visited: set[str] = set()

            # Traverse the hierarchy using a stack (iterative Depth-First Search).
            while stack:
                # Pop the last node from the stack to process it.
                current_node = stack.pop()

                # Get the external_id of the current node for identification.
                current_external_id = cls.agnostic_getattr(current_node, "external_id")

                # Check if the current node has already been visited.
                if current_external_id in visited:
                    # If visited, skip processing this node to avoid
                    # revisiting and potential infinite loops.
                    continue  # Already visited

                # Mark the current node as visited by adding its external_id to the visited set.
                visited.add(current_external_id)

                # Validate the stakeholder_key of the current node.
                current_node_stakeholder_key = cls.agnostic_getattr(current_node, "stakeholder_key")
                if current_node_stakeholder_key != expected_stakeholder_key:
                    # If the stakeholder_key does not match the expected one, raise a ValueError.
                    raise ValueError(
                        f"Inconsistent stakeholder_key at node {current_external_id}. "
                        f"Expected: {expected_stakeholder_key}, "
                        f"found: {current_node_stakeholder_key}"
                    )

                # Find all child nodes of the current node.
                child_nodes = [
                    node
                    for node in thing_nodes
                    if cls.agnostic_getattr(node, "parent_external_node_id") == current_external_id
                ]

                # Add all child nodes to the stack to continue the traversal.
                stack.extend(child_nodes)
        # If all hierarchies have consistent stakeholder_keys, return the validated values.
        return values

    @root_validator(pre=True)
    def check_for_circular_reference(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Checks for circular references in the thing_nodes hierarchy
        # by recursively visiting parent nodes.

        # Create a dictionary mapping from external_id to the corresponding node for quick access.
        nodes_by_external_id = {
            cls.agnostic_getattr(node, "external_id"): node
            for node in values.get("thing_nodes", [])
        }

        # Set to keep track of nodes currently being visited to detect circular references.
        visited = set()

        # Define a nested function to recursively visit nodes and check for circular references.
        def visit(node: dict[str, Any]) -> None:
            node_external_id = cls.agnostic_getattr(node, "external_id")
            # If the current node is already in the visited set, a circular reference is detected.
            if node_external_id in visited:
                raise ValueError(f"Circular reference detected in node {node_external_id}")

            # Mark the current node as visited by adding its external_id to the visited set.
            visited.add(node_external_id)

            # Get the external_id of the parent node.
            parent_external_id = cls.agnostic_getattr(node, "parent_external_node_id")

            # If the parent_external_id exists and the parent node is in the
            # nodes_by_external_id dictionary, recursively visit the parent node.
            if parent_external_id and parent_external_id in nodes_by_external_id:
                visit(nodes_by_external_id[parent_external_id])

            # After visiting all parent nodes, remove the current node from the visited set.
            visited.remove(node_external_id)

        # Iterate over all thing_nodes in the input values.
        for node in values.get("thing_nodes", []):
            # If the node has not been visited yet, initiate a visit starting from this node.
            if cls.agnostic_getattr(node, "external_id") not in visited:
                visit(node)

        # If no circular references are detected, return the validated values.
        return values

    @root_validator(pre=True)
    def validate_source_sink_references(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Ensure that all sources and sinks reference valid thing_nodes by checking their
        # thing_node_external_ids against the set of known thing_node IDs.

        thing_node_ids = {
            cls.agnostic_getattr(node, "external_id") for node in values.get("thing_nodes", [])
        }
        for source in values.get("sources", []):
            # For each source, check all referenced ThingNode external IDs.
            for tn_id in cls.agnostic_getattr(source, "thing_node_external_ids"):
                # If a ThingNode external ID referenced by the source
                # does not exist in 'thing_node_ids', raise an error.
                if tn_id not in thing_node_ids:
                    raise ValueError(
                        f"Source '{cls.agnostic_getattr(source, "external_id")}' references "
                        f"non-existing ThingNode '{tn_id}'."
                    )

        for sink in values.get("sinks", []):
            # For each sink, check all referenced ThingNode external IDs.
            for tn_id in cls.agnostic_getattr(sink, "thing_node_external_ids"):
                # If a ThingNode external ID referenced by the sink
                # does not exist in 'thing_node_ids', raise an error.
                if tn_id not in thing_node_ids:
                    raise ValueError(
                        f"Sink '{cls.agnostic_getattr(source, "external_id")}' references "
                        f"non-existing ThingNode '{tn_id}'."
                    )
        # If all sources and sinks reference existing ThingNodes, return the validated values.
        return values
