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

from sqlalchemy.ext.declarative import declarative_base

from . import (
    template_elements,
    instance_elements,
    orchestrator_elements,
    elements,
    structure,
)

DB = declarative_base(cls=structure.ModelIDMixin)

# pylint: disable=abstract-method

# region elements


class Parameter(elements.ParameterBase, DB):
    pass

# endregion

# region template models


class MappingTemplate(DB, template_elements.MappingTemplateBase):
    pass


class SubstitutionTemplate(DB, template_elements.SubstitutionTemplateBase):
    pass


class InterfaceTemplate(DB, template_elements.InterfaceTemplateBase):
    pass


class OperationTemplate(DB, template_elements.OperationTemplateBase):
    pass


class ServiceTemplate(DB, template_elements.ServiceTemplateBase):
    pass


class NodeTemplate(DB, template_elements.NodeTemplateBase):
    pass


class GroupTemplate(DB, template_elements.GroupTemplateBase):
    pass


class ArtifactTemplate(DB, template_elements.ArtifactTemplateBase):
    pass


class PolicyTemplate(DB, template_elements.PolicyTemplateBase):
    pass


class GroupPolicyTemplate(DB, template_elements.GroupPolicyTemplateBase):
    pass


class GroupPolicyTriggerTemplate(DB, template_elements.GroupPolicyTriggerTemplateBase):
    pass


class RequirementTemplate(DB, template_elements.RequirementTemplateBase):
    pass


class CapabilityTemplate(DB, template_elements.CapabilityTemplateBase):
    pass


# endregion

# region instance models

class Mapping(DB, instance_elements.MappingBase):
    pass


class Substitution(DB, instance_elements.SubstitutionBase):
    pass


class ServiceInstance(DB, instance_elements.ServiceInstanceBase):
    pass


class Node(DB, instance_elements.NodeBase):
    pass


class Relationship(DB, instance_elements.RelationshipBase):
    pass


class Artifact(DB, instance_elements.ArtifactBase):
    pass


class Group(DB, instance_elements.GroupBase):
    pass


class Interface(DB, instance_elements.InterfaceBase):
    pass


class Operation(DB, instance_elements.OperationBase):
    pass


class Capability(DB, instance_elements.CapabilityBase):
    pass


class Policy(DB, instance_elements.PolicyBase):
    pass


class GroupPolicy(DB, instance_elements.GroupPolicyBase):
    pass


class GroupPolicyTrigger(DB, instance_elements.GroupPolicyTriggerBase):
    pass


# endregion

# region orchestrator models

class Execution(DB, orchestrator_elements.Execution):
    pass


class ServiceInstanceUpdate(DB, orchestrator_elements.ServiceInstanceUpdateBase):
    pass


class ServiceInstanceUpdateStep(DB, orchestrator_elements.ServiceInstanceUpdateStepBase):
    pass


class ServiceInstanceModification(DB, orchestrator_elements.ServiceInstanceModificationBase):
    pass


class Plugin(DB, orchestrator_elements.PluginBase):
    pass


class Task(DB, orchestrator_elements.TaskBase):
    pass
# endregion
