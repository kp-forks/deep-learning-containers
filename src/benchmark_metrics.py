from packaging.specifiers import SpecifierSet
from packaging.version import Version


# TensorFlow
# Throughput, unit: images/second
TENSORFLOW_TRAINING_CPU_SYNTHETIC_THRESHOLD = {"<2.0": 50, ">=2.0": 50}
TENSORFLOW_TRAINING_GPU_SYNTHETIC_THRESHOLD = {"<2.0": 5000, ">=2.0": 7000}
TENSORFLOW_TRAINING_GPU_IMAGENET_THRESHOLD = {"<2.0": 5000, ">=2.0": 7000}

# p99 latency, unit: second
TENSORFLOW_INFERENCE_CPU_THRESHOLD = {
    "<2.0": {
        "INCEPTION": 0.06,
        "RCNN-Resnet101-kitti": 0.65,
        "Resnet50v2": 0.35,
        "MNIST": 0.00045,
        "SSDResnet50Coco": 0.4,
    },
    ">=2.0,<2.4": {
        "INCEPTION": 0.06,
        "RCNN-Resnet101-kitti": 0.65,
        "Resnet50v2": 0.35,
        "MNIST": 0.00045,
        "SSDResnet50Coco": 0.4,
    },
    # Updated thresholds for TF 2.4.1 CPU from Vanilla TF 2.4
    ">=2.4": {
        "INCEPTION": 0.11,
        "RCNN-Resnet101-kitti": 2.1,
        "Resnet50v2": 0.35,
        "MNIST": 0.001,
        "SSDResnet50Coco": 1.2,
    },
}
TENSORFLOW_INFERENCE_GPU_THRESHOLD = {
    "<2.0": {
        "INCEPTION": 0.04,
        "RCNN-Resnet101-kitti": 0.06,
        "Resnet50v2": 0.014,
        "MNIST": 0.0024,
        "SSDResnet50Coco": 0.1,
    },
    ">=2.0": {
        "INCEPTION": 0.04,
        "RCNN-Resnet101-kitti": 0.06,
        "Resnet50v2": 0.014,
        "MNIST": 0.0024,
        "SSDResnet50Coco": 0.1,
    },
}

# Throughput, unit: images/second
TENSORFLOW_SM_TRAINING_CPU_1NODE_THRESHOLD = {">=2.0": 30}
TENSORFLOW_SM_TRAINING_CPU_4NODE_THRESHOLD = {">=2.0": 20}
TENSORFLOW_SM_TRAINING_GPU_1NODE_THRESHOLD = {">=2.0": 2500}
TENSORFLOW_SM_TRAINING_GPU_4NODE_THRESHOLD = {">=2.0": 2500}

# MXNet
# Throughput, unit: images/second
MXNET_TRAINING_CPU_CIFAR_THRESHOLD = {">=1.0": 1000}
MXNET_TRAINING_GPU_IMAGENET_THRESHOLD = {">=1.0": 4500}
MXNET_INFERENCE_CPU_IMAGENET_THRESHOLD = {">=1.0": 100}
MXNET_INFERENCE_GPU_IMAGENET_THRESHOLD = {">=1.0": 4500}

# Accuracy, unit: NA
MXNET_TRAINING_GPU_IMAGENET_ACCURACY_THRESHOLD = {">=1.0": 0.9}

# Latency, unit: sec/epoch
MXNET_TRAINING_GPU_IMAGENET_LATENCY_THRESHOLD = {">=1.0": 120}

# PyTorch
# Throughput, unit: images/second
PYTORCH_TRAINING_GPU_SYNTHETIC_THRESHOLD = {">=1.0": 2400}

# Training Time Cost, unit: second/epoch
PYTORCH_TRAINING_GPU_IMAGENET_THRESHOLD = {">=1.0": 660}

# p99 latency, unit: millisecond
PYTORCH_INFERENCE_CPU_THRESHOLD = {
    ">=1.0": {
        "ResNet18": 80.0,
        "MobileNet_V2": 60.0,
        "GoogLeNet": 120.0,
        "DenseNet121": 200.0,
        "Inception_V3": 250.0,
        "DistilBert_128": 200.0,
        "Bert_128": 300.0,
        "Roberta_128": 300.0,
        "ASR": 300.0,
        "All-MPNet_128": 300.0,
    }
}
PYTORCH_INFERENCE_GPU_THRESHOLD = {
    ">=1.0": {
        "ResNet18": 7.5,
        "VGG13": 4.0,
        "MobileNet_V2": 13.0,
        "GoogLeNet": 18.0,
        "DenseNet121": 40.0,
        "Inception_V3": 30.0,
        "ResNet50": 15.0,
        "ViT_B_16": 20.0,
        "DistilBert_128": 10.0,
        "DistilBert_256": 11.0,
        "Bert_128": 20.0,
        "Bert_256": 20.0,
        "Roberta_128": 20.0,
        "Roberta_256": 20.0,
        "ASR": 20.0,
        "All-MPNet_128": 20.0,
        "All-MPNet_256": 30.0,
    }
}

# Threshold for TRCOMP benchmarks
# Metric: SM Billable secs
# Unit: secs
TRCOMP_THRESHOLD = {
    "tensorflow": {  # framework
        "2.9": {  # framework version
            "resnet101": {  # model name
                "ml.g5.8xlarge": {1: {224: 2500}}  # instance  # Num nodes  # batch size : threshold
            },
            "GPT-2": {  # model name
                "ml.g5.8xlarge": {1: {75: 2000}}  # instance  # Num nodes  # batch size : threshold
            },
        },
        "2.10": {  # framework version
            "resnet101": {  # model name
                "ml.g5.8xlarge": {1: {224: 2500}}  # instance  # Num nodes  # batch size : threshold
            },
            "GPT-2": {  # model name
                "ml.g5.8xlarge": {1: {75: 2000}}  # instance  # Num nodes  # batch size : threshold
            },
        },
        "2.11": {  # framework version
            "resnet101": {  # model name
                "ml.g5.8xlarge": {1: {224: 2500}}  # instance  # Num nodes  # batch size : threshold
            },
            "GPT-2": {  # model name
                "ml.g5.8xlarge": {1: {75: 2000}}  # instance  # Num nodes  # batch size : threshold
            },
        },
    }
}


def get_threshold_for_image(framework_version, lookup_table):
    """
    Find the correct threshold value(s) for a given framework version and a dict from which to lookup values.

    :param framework_version: Framework version of the image being tested
    :param lookup_table: The relevant dict from one of the dicts defined in this script
    :return: Threshold value as defined by one of the dicts in this script
    """
    for spec, threshold_val in lookup_table.items():
        if Version(framework_version) in SpecifierSet(spec):
            return threshold_val
    raise KeyError(
        f"{framework_version} does not satisfy any version constraint available in "
        f"{lookup_table.keys()}"
    )
