import argparse
from collections import defaultdict

import boto3
import sagemaker

from sagemaker.tensorflow import TensorFlow

parser = argparse.ArgumentParser()
parser.add_argument(
    "--framework-version", type=str, help="framework version in image to be used", required=True
)
parser.add_argument("--image-uri", type=str, help="Image URI of image to benchmark", required=True)
parser.add_argument(
    "--instance-type", type=str, help="instance type to use for test", required=True
)
parser.add_argument("--node-count", type=int, help="number of nodes to train", default=4)
parser.add_argument("--python", help="python version", default="py3")
parser.add_argument("--region", help="region in which to run test", default="us-west-2")
parser.add_argument("--job-name", help="SageMaker Training Job Name", default=None)
parser.add_argument(
    "--xla-on", help="Enable XLA acceleration", action="store_true", dest="xla", default=True
)
parser.add_argument("--xla-off", help="Disable XLA acceleration", action="store_false", dest="xla")

args = parser.parse_args()

source_dir = "tensorflow1" if args.framework_version.startswith("1.") else "tensorflow2"
processor = "gpu" if "gpu" in args.image_uri else "cpu"
entrypoint_script = (
    f"singletrain_{processor}{'_without_xla' if processor == 'gpu' and not args.xla else ''}.sh"
)

processes_per_host = defaultdict(lambda: 1)
processes_per_host["ml.g5.48xlarge"] = 8
processes_per_host["ml.g5.12xlarge"] = 4
processes_per_host["ml.g5.8xlarge"] = 1

kwargs = {"train_volume_size": 200} if processor == "gpu" else {}

sagemaker_session = sagemaker.Session(boto_session=boto3.Session(region_name=args.region))

if str(sagemaker.__version__).startswith("2"):
    tf_estimator = TensorFlow(
        sagemaker_session=sagemaker_session,
        entry_point=entrypoint_script,
        source_dir=source_dir,
        role="SageMakerRole",
        instance_count=args.node_count,
        instance_type=args.instance_type,
        image_uri=args.image_uri,
        py_version=args.python,
        framework_version=args.framework_version,
        distribution={
            "mpi": {
                "enabled": True,
                "processes_per_host": processes_per_host[args.instance_type],
                "custom_mpi_options": (
                    "-x HOROVOD_HIERARCHICAL_ALLREDUCE=1 "
                    "-x HOROVOD_FUSION_THRESHOLD=16777216 "
                    "-x TF_CPP_MIN_LOG_LEVEL=3"
                ),
            }
        },
        output_path=f"s3://dlc-bai-results-sagemaker-{args.region}",
        **kwargs,
    )
else:
    tf_estimator = TensorFlow(
        sagemaker_session=sagemaker_session,
        script_mode=True,
        entry_point=entrypoint_script,
        source_dir=source_dir,
        role="SageMakerRole",
        train_instance_count=args.node_count,
        train_instance_type=args.instance_type,
        image_name=args.image_uri,
        py_version=args.python,
        framework_version=args.framework_version,
        distributions={
            "mpi": {
                "enabled": True,
                "processes_per_host": processes_per_host,
                "custom_mpi_options": (
                    "-x HOROVOD_HIERARCHICAL_ALLREDUCE=1 "
                    "-x HOROVOD_FUSION_THRESHOLD=16777216 "
                    "-x TF_CPP_MIN_LOG_LEVEL=3"
                ),
            }
        },
        output_path=f"s3://dlc-bai-results-sagemaker-{args.region}",
        **kwargs,
    )

data = (
    {
        "train": f"s3://dlc-data-sagemaker-{args.region}/imagenet/raw/train-480px",
        "validate": f"s3://dlc-data-sagemaker-{args.region}/imagenet/raw/validation-480px",
    }
    if processor == "gpu"
    else {
        # Just to make sm happy
        "s1": f"s3://dlc-data-sagemaker-{args.region}/small"
    }
)

tf_estimator.fit(data, job_name=args.job_name, logs=True, wait=True)
