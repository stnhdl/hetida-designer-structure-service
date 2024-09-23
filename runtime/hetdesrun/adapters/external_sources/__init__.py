from typing import Any

from hetdesrun.adapters.external_sources.sinks import sink_load_functions
from hetdesrun.adapters.external_sources.sources import source_load_functions
from hetdesrun.models.data_selection import FilteredSink, FilteredSource

try:
    with open("VERSION", encoding="utf8") as version_file:
        VERSION = version_file.read().strip()
except FileNotFoundError:
    VERSION = "dev snapshot"


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    return {
        # TODO: async parallelize tasks
        wf_input_name: await source_load_functions[
            relevant_id := str(
                filtered_source.ref_key
                if filtered_source.ref_key is not None
                else filtered_source.ref_id
            )
        ](
            relevant_id,
            filtered_source.filters,
        )
        for wf_input_name, filtered_source in wf_input_name_to_filtered_source_mapping_dict.items()
    }


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    for (
        wf_output_name,
        filtered_sink,
    ) in wf_output_name_to_filtered_sink_mapping_dict.items():
        data = wf_output_name_to_value_mapping_dict[wf_output_name]

        # for metadata(any) the complete path is expected to be encoded into the refKey while
        # the ref_id only contains the thing node 's path (a directory) where it is considered
        # to be attached to

        id_to_use = (
            filtered_sink.ref_key if filtered_sink.ref_key is not None else filtered_sink.ref_id
        )
        sink_load_functions[str(id_to_use)](data, str(id_to_use))
    return {}
