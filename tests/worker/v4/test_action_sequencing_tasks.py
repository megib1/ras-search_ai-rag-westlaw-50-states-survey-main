from unittest import mock


class TestFinishTask:
    @mock.patch("worker.v4.action_sequencing_tasks.add_to_span")
    @mock.patch("worker.v4.action_sequencing_tasks.send_metrics")
    def test_sends_metrics_and_updates_span(self, mock_send_metrics, mock_add_to_span):
        from worker.v4.action_sequencing_tasks import finish_task

        span = mock.MagicMock()

        finish_task(
            span=span,
            conversation_id="conv-1",
            conversation_entry_id="entry-1",
            answer_solution_profile="wl-rag-v054",
            total_queued_time=1.5,
            total_execution_time=3.0,
            response_status_code=500,
            user_classification="legal",
        )

        mock_send_metrics.assert_called_once_with(
            conversation_id="conv-1",
            conversation_entry_id="entry-1",
            answer_solution_profile="wl-rag-v054",
            total_queued_time=1.5,
            total_execution_time=3.0,
            success=False,
            user_classification="legal",
        )
        mock_add_to_span.assert_called_once_with("http.status_code", "500")
        span.set_exc_info.assert_called_once()

    @mock.patch("worker.v4.action_sequencing_tasks.add_to_span")
    @mock.patch("worker.v4.action_sequencing_tasks.send_metrics")
    def test_status_code_passed_as_string(self, mock_send_metrics, mock_add_to_span):
        from worker.v4.action_sequencing_tasks import finish_task

        span = mock.MagicMock()

        finish_task(
            span=span,
            conversation_id="c",
            conversation_entry_id="e",
            answer_solution_profile="p",
            total_queued_time=0.0,
            total_execution_time=0.0,
            response_status_code=417,
            user_classification="unknown",
        )

        mock_add_to_span.assert_called_once_with("http.status_code", "417")


class TestActionSequenceTaskImpl:
    def test_instantiation_uses_module_level_singletons(self):
        from worker.v4.action_sequencing_tasks import ActionSequenceTaskImpl

        impl = ActionSequenceTaskImpl()

        assert impl is not None

    def test_get_task_implementation_returns_action_sequencing_task(self):
        from worker.v4.action_sequencing_tasks import ActionSequenceTaskImpl, ActionSequencingTaskV4

        impl = ActionSequenceTaskImpl()
        task = impl.get_task_implementation()

        assert isinstance(task, ActionSequencingTaskV4)
