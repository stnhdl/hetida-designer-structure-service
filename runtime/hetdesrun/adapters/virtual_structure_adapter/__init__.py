from typing import Any

from hetdesrun.models.data_selection import FilteredSink, FilteredSource


# Empty functions just to register the adapter
async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    return {}


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,  # noqa: ARG001
) -> dict[str, Any]:
    return {}
