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
from sqlalchemy import Column, Text, Integer

from aria import application_model_storage
from aria.storage import (
    ModelStorage,
    exceptions,
    sql_mapi,
    structure,
    modeling,
)
from aria.storage.modeling import type as aria_type
from ..mock import (
    context as mock_context,
    models
)
from ..storage import get_sqlite_api_kwargs, release_sqlite_storage


class MockModel(modeling.model.DB, structure.ModelMixin): #pylint: disable=abstract-method
    __tablename__ = 'mock_models'
    model_dict = Column(aria_type.Dict)
    model_list = Column(aria_type.List)
    value = Column(Integer)
    name = Column(Text)


@pytest.fixture
def storage():
    base_storage = ModelStorage(sql_mapi.SQLAlchemyModelAPI, api_kwargs=get_sqlite_api_kwargs())
    base_storage.register(MockModel)
    yield base_storage
    release_sqlite_storage(base_storage)


@pytest.fixture
def context():
    return mock_context.simple(get_sqlite_api_kwargs())


@pytest.fixture(scope='module', autouse=True)
def module_cleanup():
    modeling.model.DB.metadata.remove(MockModel.__table__)  #pylint: disable=no-member


def test_storage_base(storage):
    with pytest.raises(AttributeError):
        storage.non_existent_attribute()


def test_model_storage(storage):
    mock_model = MockModel(value=0, name='model_name')
    storage.mock_model.put(mock_model)

    assert storage.mock_model.get_by_name('model_name') == mock_model

    assert [mm_from_storage for mm_from_storage in storage.mock_model.iter()] == [mock_model]
    assert [mm_from_storage for mm_from_storage in storage.mock_model] == [mock_model]

    storage.mock_model.delete(mock_model)
    with pytest.raises(exceptions.StorageError):
        storage.mock_model.get(mock_model.id)


def test_inner_dict_update(storage):
    inner_dict = {'inner_value': 1}

    mock_model = MockModel(model_dict={'inner_dict': inner_dict, 'value': 0})
    storage.mock_model.put(mock_model)

    storage_mm = storage.mock_model.get(mock_model.id)
    assert storage_mm == mock_model

    storage_mm.model_dict['inner_dict']['inner_value'] = 2
    storage_mm.model_dict['value'] = -1
    storage.mock_model.update(storage_mm)
    storage_mm = storage.mock_model.get(storage_mm.id)

    assert storage_mm.model_dict['inner_dict']['inner_value'] == 2
    assert storage_mm.model_dict['value'] == -1


def test_inner_list_update(storage):
    mock_model = MockModel(model_list=[0, [1]])
    storage.mock_model.put(mock_model)

    storage_mm = storage.mock_model.get(mock_model.id)
    assert storage_mm == mock_model

    storage_mm.model_list[1][0] = 'new_inner_value'
    storage_mm.model_list[0] = 'new_value'
    storage.mock_model.update(storage_mm)
    storage_mm = storage.mock_model.get(storage_mm.id)

    assert storage_mm.model_list[1][0] == 'new_inner_value'
    assert storage_mm.model_list[0] == 'new_value'

# TODO: choose a new model to deployment
def test_model_to_dict(context):
    deployment = context.service_instance
    deployment_dict = deployment.to_dict()

    expected_keys = [
        'created_at',
        'description',
        'policy_triggers',
        'policy_types',
        'scaling_groups',
        'updated_at',
        'workflows',
        'service_template_name',
        'description'
    ]

    for expected_key in expected_keys:
        assert expected_key in deployment_dict

    assert 'blueprint_fk' not in deployment_dict

# TODO: change factory to create different models
def test_application_storage_factory():
    storage = application_model_storage(sql_mapi.SQLAlchemyModelAPI,
                                        api_kwargs=get_sqlite_api_kwargs())

    assert storage.parameter
    assert storage.mapping_template
    assert storage.substitution_template
    assert storage.service_template
    assert storage.node_template
    assert storage.group_template
    assert storage.interface_template
    assert storage.operation_template
    assert storage.artifact_template
    assert storage.policy_template
    assert storage.group_policy_template
    assert storage.group_policy_trigger_template
    assert storage.requirement_template
    assert storage.capability_template

    assert storage.mapping
    assert storage.substitution
    assert storage.service_instance
    assert storage.node
    assert storage.group
    assert storage.interface
    assert storage.operation
    assert storage.capability
    assert storage.artifact
    assert storage.policy
    assert storage.group_policy
    assert storage.group_policy_trigger
    assert storage.relationship

    assert storage.execution
    assert storage.service_instance_update
    assert storage.service_instance_update_step
    assert storage.service_instance_modification
    assert storage.plugin
    assert storage.task

    release_sqlite_storage(storage)


def test_relationship_model_ordering(context):
    deployment = context.model.service_instance.get_by_name(models.DEPLOYMENT_NAME)
    source_node = context.model.node_template.get_by_name(models.DEPENDENT_NODE_NAME)
    source_node_instance = context.model.node.get_by_name(
        models.DEPENDENT_NODE_INSTANCE_NAME)
    target_node = context.model.node_template.get_by_name(models.DEPENDENCY_NODE_NAME)
    target_node_instance = context.model.node.get_by_name(
        models.DEPENDENCY_NODE_INSTANCE_NAME)
    new_node = modeling.model.NodeTemplate(
        name='new_node',
        type_name='test_node_type',
        type_hierarchy=[],
        default_instances=1,
        min_instances=1,
        max_instances=1,
        service_template=deployment.service_template
    )
    req, cap = mock_context.models.get_relationship(new_node)
    context.model.requirement_template.put(req)
    context.model.capability_template.put(cap)

    source_node.requirement_templates = [req]
    source_node.capability_templates = [cap]
    context.model.node_template.update(source_node)

    new_node_instance = modeling.model.Node(
        name='new_node_instance',
        service_instance=deployment,
        runtime_properties={},
        version=None,
        node_template=new_node,
        state='',
        scaling_groups=[]
    )
    source_to_new_relationship_instance = mock_context.models.get_relationship_instance(
        target_instance=new_node_instance,
        source_instance=source_node_instance
    )
    context.model.relationship.put(source_to_new_relationship_instance)

    req, cap = mock_context.models.get_relationship(target_node)
    context.model.requirement_template.put(req)
    context.model.capability_template.put(cap)

    target_node.requirement_templates = [req]
    target_node.capability_templates = [cap]
    context.model.node_template.update(target_node)

    new_to_target_relationship_instance = modeling.model.Relationship(
        source_node=new_node_instance,
        target_node=target_node_instance,
    )
    context.model.relationship.put(new_to_target_relationship_instance)

    def flip_and_assert(node_instance, direction):
        """
        Reversed the order of relationships and assert effects took place.
        :param node_instance: the node instance to operatate on
        :param direction: the type of relationships to flip (inbound/outbount)
        :return:
        """
        assert direction in ('inbound', 'outbound')

        relationship_instances = getattr(node_instance, direction + '_relationships')
        assert len(relationship_instances) == 2

        first_rel_instance, second_rel_instance = relationship_instances
        assert getattr(first_rel_instance, relationship_instances.ordering_attr) == 0
        assert getattr(second_rel_instance, relationship_instances.ordering_attr) == 1

        reversed_relationship_instances = list(reversed(relationship_instances))

        assert relationship_instances != reversed_relationship_instances

        relationship_instances[:] = reversed_relationship_instances
        context.model.node.update(node_instance)

        assert relationship_instances == reversed_relationship_instances

        assert getattr(first_rel_instance, relationship_instances.ordering_attr) == 1
        assert getattr(second_rel_instance, relationship_instances.ordering_attr) == 0

    flip_and_assert(source_node_instance, 'outbound')
    flip_and_assert(target_node_instance, 'inbound')
