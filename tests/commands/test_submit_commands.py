# tests/test_submit_commands.py

import logging
import uuid
from click.testing import CliRunner
from mockito import when
from terralab.commands import submit_commands


LOGGER = logging.getLogger(__name__)


def test_submit(caplog):
    runner = CliRunner()

    test_pipeline_name = "test_pipeline"
    test_inputs_dict = {}
    test_inputs_dict_str = str(test_inputs_dict)

    test_job_id = uuid.uuid4()

    when(submit_commands).process_json(test_inputs_dict_str).thenReturn(
        test_inputs_dict
    )
    when(submit_commands).validate_pipeline_inputs(
        test_pipeline_name, test_inputs_dict
    )  # do nothing

    when(submit_commands.submit_logic).prepare_upload_start_pipeline_run(
        test_pipeline_name, 0, test_inputs_dict, ""
    ).thenReturn(test_job_id)

    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(
            submit_commands.submit,
            [test_pipeline_name, "--inputs", test_inputs_dict_str],
        )

    assert result.exit_code == 0
    assert f"Successfully started {test_pipeline_name} job {test_job_id}" in caplog.text
