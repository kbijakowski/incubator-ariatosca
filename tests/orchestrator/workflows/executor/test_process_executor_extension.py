# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from aria import extension
from aria.orchestrator.workflows import api
from aria.orchestrator.workflows.core import engine
from aria.orchestrator.workflows.executor import process
from aria.orchestrator import workflow, operation

import tests
from tests import mock
from tests import storage


def test_decorate_extension(context, executor):
    inputs = {'input1': 1, 'input2': 2}

    def get_node_instance(ctx):
        return ctx.model.node_instance.get_by_name(mock.models.DEPENDENCY_NODE_INSTANCE_NAME)

    @workflow
    def mock_workflow(ctx, graph):
        node_instance = get_node_instance(ctx)
        op = 'test.op'
        op_dict = {'operation': '{0}.{1}'.format(__name__, _mock_operation.__name__)}
        node_instance.node.operations['test.op'] = op_dict
        task = api.task.OperationTask.node_instance(instance=node_instance, name=op, inputs=inputs)
        graph.add_tasks(task)
        return graph
    graph = mock_workflow(ctx=context)  # pylint: disable=no-value-for-parameter
    eng = engine.Engine(executor=executor, workflow_context=context, tasks_graph=graph)
    eng.execute()
    out = get_node_instance(context).runtime_properties['out']
    assert out['wrapper_inputs'] == inputs
    assert out['function_inputs'] == inputs


@extension.process_executor
class MockProcessExecutorExtension(object):

    def decorate(self):
        def decorator(function):
            def wrapper(ctx, **operation_inputs):
                ctx.node_instance.runtime_properties['out'] = {'wrapper_inputs': operation_inputs}
                function(ctx=ctx, **operation_inputs)
            return wrapper
        return decorator


@operation
def _mock_operation(ctx, **operation_inputs):
    ctx.node_instance.runtime_properties['out']['function_inputs'] = operation_inputs


@pytest.fixture
def executor():
    result = process.ProcessExecutor(python_path=[tests.ROOT_DIR])
    yield result
    result.close()


@pytest.fixture
def context(tmpdir):
    result = mock.context.simple(storage.get_sqlite_api_kwargs(str(tmpdir)))
    yield result
    storage.release_sqlite_storage(result.model)
