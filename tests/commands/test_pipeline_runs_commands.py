# tests/commands/test_pipeline_runs_commands.py

import logging
import pytest
import uuid
from click.testing import CliRunner
from mockito import when, verify
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


def test_download():
    runner = CliRunner()

    test_pipeline_name = "test_pipeline"
    test_job_id = uuid.uuid4()
    test_job_id_str = str(test_job_id)

    when(pipeline_runs_commands.pipeline_runs_logic).get_result_and_download_pipeline_run_outputs(
        test_pipeline_name, test_job_id, "."
    )  # do nothing, assume succeeded

    result = runner.invoke(
        pipeline_runs_commands.download,
        [test_pipeline_name, test_job_id_str]
    )

    assert result.exit_code == 0
    verify(pipeline_runs_commands.pipeline_runs_logic).get_result_and_download_pipeline_run_outputs(
        test_pipeline_name, test_job_id, "."
    )

def test_download_bad_job_id(capture_logs):
    runner = CliRunner()

    test_pipeline_name = "test_pipeline"
    test_job_id_str = "not a uuid"

    result = runner.invoke(
        pipeline_runs_commands.download,
        [test_pipeline_name, test_job_id_str]
    )

    assert result.exit_code == 1
    assert "Input error: JOB_ID must be a valid uuid." in capture_logs.text
