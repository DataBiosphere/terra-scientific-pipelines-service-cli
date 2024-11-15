# tests/test_pipeline_runs_commands.py

import logging
import uuid
from click.testing import CliRunner
from mockito import when
from terralab.commands import pipeline_runs_commands
from tests.utils_for_tests import capture_logs

LOGGER = logging.getLogger(__name__)


def test_submit(capture_logs):
    runner = CliRunner()

    test_pipeline_name = "test_pipeline"
    test_inputs_dict = {}
    test_inputs_dict_str = str(test_inputs_dict)

    test_job_id = uuid.uuid4()

    when(pipeline_runs_commands).process_json_to_dict(test_inputs_dict_str).thenReturn(
        test_inputs_dict
    )
    when(pipeline_runs_commands.pipelines_logic).validate_pipeline_inputs(
        test_pipeline_name, test_inputs_dict
    )  # do nothing

    when(pipeline_runs_commands.pipeline_runs_logic).prepare_upload_start_pipeline_run(
        test_pipeline_name, 0, test_inputs_dict, ""
    ).thenReturn(test_job_id)

    result = runner.invoke(
        pipeline_runs_commands.submit,
        [test_pipeline_name, "--inputs", test_inputs_dict_str],
    )

    assert result.exit_code == 0
    assert (
        f"Successfully started {test_pipeline_name} job {test_job_id}"
        in capture_logs.text
    )
