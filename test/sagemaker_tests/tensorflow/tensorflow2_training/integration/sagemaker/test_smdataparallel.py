# Copyright 2017-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import os

import pytest
import sagemaker

from packaging.version import Version
from sagemaker.instance_group import InstanceGroup
from packaging.specifiers import SpecifierSet
from sagemaker.tensorflow import TensorFlow

from ..... import invoke_sm_helper_function
from ...integration.utils import processor, py_version, unique_name_from_base  # noqa: F401
from test.test_utils import get_framework_and_version_from_tag, get_cuda_version_from_tag

RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "resources")
MNIST_PATH = os.path.join(RESOURCE_PATH, "mnist")
THROUGHPUT_PATH = os.path.join(RESOURCE_PATH, "smdataparallel")


def validate_or_skip_smdataparallel(ecr_image):
    if not can_run_smdataparallel(ecr_image):
        pytest.skip("Data Parallelism is supported on CUDA 11 on TensorFlow 2.3.1 and above")


def can_run_smdataparallel(ecr_image):
    _, image_framework_version = get_framework_and_version_from_tag(ecr_image)
    image_cuda_version = get_cuda_version_from_tag(ecr_image)
    if Version(image_framework_version) == Version("2.12.0"):
        return False
    else:
        return Version(image_framework_version) in SpecifierSet(">=2.3.1") and Version(
            image_cuda_version.strip("cu")
        ) >= Version("110")


def validate_or_skip_smdataparallel_efa(ecr_image):
    if not can_run_smdataparallel_efa(ecr_image):
        pytest.skip(
            "EFA is only supported on CUDA 11, and on TensorFlow 2.4.1 or higher. SM Dataparallel support is not added in TF2.12 DLC"
        )


def can_run_smdataparallel_efa(ecr_image):
    _, image_framework_version = get_framework_and_version_from_tag(ecr_image)
    image_cuda_version = get_cuda_version_from_tag(ecr_image)
    if Version(image_framework_version) == Version("2.12.0"):
        return False
    else:
        return Version(image_framework_version) in SpecifierSet(">=2.4.1") and Version(
            image_cuda_version.strip("cu")
        ) >= Version("110")


@pytest.mark.integration("smdataparallel")
@pytest.mark.model("mnist")
@pytest.mark.processor("gpu")
@pytest.mark.skip_cpu
@pytest.mark.skip_py2_containers
@pytest.mark.team("smdataparallel")
def test_distributed_training_smdataparallel_script_mode(
    ecr_image, sagemaker_regions, instance_type, tmpdir, framework_version, sm_below_tf213_only
):
    invoke_sm_helper_function(
        ecr_image,
        sagemaker_regions,
        _test_distributed_training_smdataparallel_script_mode_function,
        instance_type,
        framework_version,
    )


def _test_distributed_training_smdataparallel_script_mode_function(
    ecr_image, sagemaker_session, instance_type, framework_version
):
    """
    Tests SMDataParallel single-node command via script mode
    """
    validate_or_skip_smdataparallel(ecr_image)
    instance_type = "ml.p4d.24xlarge"
    distribution = {"smdistributed": {"dataparallel": {"enabled": True}}}
    estimator = TensorFlow(
        entry_point="smdataparallel_mnist_script_mode.sh",
        source_dir=MNIST_PATH,
        role="SageMakerRole",
        instance_type=instance_type,
        instance_count=1,
        image_uri=ecr_image,
        framework_version=framework_version,
        py_version="py3",
        sagemaker_session=sagemaker_session,
        distribution=distribution,
    )

    estimator.fit(job_name=unique_name_from_base("test-tf-smdataparallel"))


@pytest.mark.usefixtures("feature_smddp_present")
@pytest.mark.processor("gpu")
@pytest.mark.skip_cpu
@pytest.mark.multinode(2)
@pytest.mark.integration("smdataparallel")
@pytest.mark.model("mnist")
@pytest.mark.skip_py2_containers
@pytest.mark.efa()
@pytest.mark.team("smdataparallel")
@pytest.mark.parametrize("instance_types", ["ml.p4d.24xlarge"])
def test_smdataparallel_mnist(
    ecr_image, sagemaker_regions, instance_types, py_version, tmpdir, sm_below_tf213_only
):
    invoke_sm_helper_function(
        ecr_image, sagemaker_regions, _test_smdataparallel_mnist_function, instance_types
    )


def _test_smdataparallel_mnist_function(ecr_image, sagemaker_session, instance_types):
    """
    Tests smddprun command via Estimator API distribution parameter
    """
    validate_or_skip_smdataparallel_efa(ecr_image)

    distribution = {"smdistributed": {"dataparallel": {"enabled": True}}}
    estimator = TensorFlow(
        entry_point="smdataparallel_mnist.py",
        role="SageMakerRole",
        image_uri=ecr_image,
        source_dir=MNIST_PATH,
        instance_count=2,
        instance_type=instance_types,
        sagemaker_session=sagemaker_session,
        distribution=distribution,
    )

    estimator.fit(job_name=unique_name_from_base("test-tf-smdataparallel-multi"))


@pytest.mark.usefixtures("feature_smddp_present")
@pytest.mark.processor("gpu")
@pytest.mark.skip_cpu
@pytest.mark.multinode(2)
@pytest.mark.integration("smdataparallel")
@pytest.mark.model("mnist")
@pytest.mark.skip_py2_containers
@pytest.mark.efa()
@pytest.mark.team("smdataparallel")
@pytest.mark.parametrize("instance_types", ["ml.p4d.24xlarge"])
def test_hc_smdataparallel_mnist(
    ecr_image, sagemaker_regions, instance_types, py_version, tmpdir, sm_below_tf213_only
):
    training_group = InstanceGroup("train_group", instance_types, 2)
    invoke_sm_helper_function(
        ecr_image, sagemaker_regions, _test_hc_smdataparallel_mnist_function, [training_group]
    )


def _test_hc_smdataparallel_mnist_function(ecr_image, sagemaker_session, instance_groups):
    """
    Tests smddprun command via Estimator API distribution parameter
    """
    validate_or_skip_smdataparallel_efa(ecr_image)

    distribution = {
        "smdistributed": {"dataparallel": {"enabled": True}},
        "instance_groups": instance_groups,
    }
    estimator = TensorFlow(
        entry_point="smdataparallel_mnist.py",
        role="SageMakerRole",
        image_uri=ecr_image,
        source_dir=MNIST_PATH,
        instance_groups=instance_groups,
        sagemaker_session=sagemaker_session,
        distribution=distribution,
    )

    estimator.fit(job_name=unique_name_from_base("test-tf-hc-smdataparallel-multi"))


@pytest.mark.usefixtures("feature_smddp_present")
@pytest.mark.processor("gpu")
@pytest.mark.skip_cpu
@pytest.mark.multinode(2)
@pytest.mark.integration("smdataparallel")
@pytest.mark.model("N/A")
@pytest.mark.skip_py2_containers
@pytest.mark.efa()
@pytest.mark.team("smdataparallel")
@pytest.mark.parametrize("instance_types", ["ml.p4d.24xlarge"])
def test_smdataparallel_throughput(
    ecr_image, sagemaker_regions, instance_types, py_version, tmpdir, sm_below_tf213_only
):
    invoke_sm_helper_function(
        ecr_image, sagemaker_regions, _test_smdataparallel_throughput_function, instance_types
    )


def _test_smdataparallel_throughput_function(ecr_image, sagemaker_session, instance_types):
    """
    Tests smddprun throughput
    """
    validate_or_skip_smdataparallel_efa(ecr_image)
    hyperparameters = {
        "size": 64,
        "num_tensors": 20,
        "iterations": 100,
        "warmup": 10,
        "bucket_size": 25,
        "info": "TF-{}-N{}".format(instance_types, 2),
    }

    distribution = {"smdistributed": {"dataparallel": {"enabled": True}}}
    estimator = TensorFlow(
        entry_point="smdataparallel_throughput.py",
        role="SageMakerRole",
        image_uri=ecr_image,
        source_dir=THROUGHPUT_PATH,
        instance_count=2,
        instance_type=instance_types,
        sagemaker_session=sagemaker_session,
        hyperparameters=hyperparameters,
        distribution=distribution,
    )
    estimator.fit()
