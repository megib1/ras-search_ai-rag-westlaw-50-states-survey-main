#!/usr/bin/env python3
# This script publishes images to Docker to the accounts and regions
# mentioned in the deploy spec.
# If you need to publish images to an ECR registry that is in an account outside those in your deployspec
# (ie the CICD account where you run your Cumulus pipeline), you can use the optional parameter account-id.
#
# It then sets the relevant published images to the stack parameters in the deployspec
# under the specified path.
#
# Usage:
# python3 cicd/publish-docker-images.py --image <IMAGE_NAME> --tag <TAG> --param-path <PARAM_PATH>
#
# Usage with the optional parameter account-id:
# python3 cicd/publish-docker-images.py --image <IMAGE_NAME> --tag <TAG> --param-path <PARAM_PATH> --account-id <AWS_Account_ID>
#
# Usage with the optional parameter deployspec which specifies where the deployspec is located.
# python3 cicd/publish-docker-images.py --image <IMAGE_NAME> --tag <TAG> --param-path <PARAM_PATH> --deployspec pipeline-examples/combined-pipeline-bluegreen-ecs/cumulus-deployspec.yaml

# Example:
# python3 cicd/publish-docker-images.py --image my-docker-image --tag 1444 --param-path DeployerParameters.StackParameters.ImageUri
#
# Requirements:
# boto3 docker pyyaml

import argparse
import base64
import pathlib

import boto3
import docker
import yaml
# Publish docker image to ECR
parser = argparse.ArgumentParser("Publish Docker images and update the deploy spec.")
parser.add_argument("--image", nargs=1, required=True)
parser.add_argument("--tag", nargs=1, required=True)
parser.add_argument("--param-path", nargs=1, required=True)
parser.add_argument("--account-id", nargs=1, required=False)
parser.add_argument("--asset-id", nargs=1, required=False)
parser.add_argument("--deployspec", nargs=1, required=False)
args = parser.parse_args()

docker_client = docker.from_env()
image_name = args.image[0]
tag = args.tag[0]
update_path = args.param_path[0].split(".")

# Function for setting values deep in a dict even if some parts are missing
def deepset(dict_, item, *path):
    for key in path[:-1]: dict_ = dict_.setdefault(key, {})
    dict_[path[-1]] = item

def assume_role(role_arn, region_name=None, session_name=None, time=900):
    """
    Create a new session based on the given role.
    """
    sts = boto3.client("sts")
    session_name = session_name or "CumulusAssumedRole"
    credentials = sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name, DurationSeconds=time,)
    credentials = credentials["Credentials"]
    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=region_name,
    )

def get_ecr_client(asset_id, account, region):
    """
    Return a client(Poweruser2) with which to enable ecr scanning.
    """
    power_user_arn = f"arn:aws:iam::{account}:role/human-role/a{asset_id}-PowerUser2"
    assumed_session = assume_role(
        role_arn=power_user_arn,
        region_name=region,
        session_name="EcrScanning",
        time=15 * 60,  # 15 minutes - Minimum time for session
    )
    return assumed_session.client("ecr")

# Load deployspec
deployspec_file = "cumulus-deployspec.yaml"
if args.deployspec is not None:
    deployspec_file = pathlib.Path.resolve(pathlib.Path(args.deployspec[0]))
deployspec_file = pathlib.Path.resolve(pathlib.Path(deployspec_file))
deployspec = yaml.safe_load(deployspec_file.read_text())

# Push image to all environments (regions & accounts)
defaults = deployspec["Defaults"]
for env, env_values in deployspec.items():
    if env == "Defaults":
        continue
    if args.account_id is not None:
        env_acc = args.account_id[0]
    else:
        env_acc = env_values.get("AccountId", defaults.get("AccountId"))

    if args.asset_id is not None:
        asset_id = args.asset_id[0]
    else:
        asset_id = env_values.get("AssetId", defaults.get("AssetId"))

    env_region = env_values.get("AccountRegion", defaults.get("AccountRegion"))

    # Log in to relevant ECR for account+region
    ecr = boto3.client("ecr", region_name=env_region)
    resp = ecr.get_authorization_token(registryIds=[env_acc])["authorizationData"][0]
    token = base64.decodebytes(resp["authorizationToken"].encode()).decode()
    [username, password] = token.split(":")
    registry = resp["proxyEndpoint"]
    docker_client.login(username, password, registry=registry)

    # Tag and push image
    registry = registry.replace("https://", "", 1)
    image_uri = f"{registry}/{image_name}"
    docker_client.images.get(image_name).tag(image_uri, tag=tag)
    image_uri = f"{image_uri}:{tag}"
    for line in docker_client.images.push(image_uri, stream=True, decode=True):
        print(line)
        if "error" in line.keys():
            raise ValueError("An error occurred when pushing the image.")

    deepset(env_values, image_uri, *update_path)

    # Manual start image scan
    ecr_client = get_ecr_client(asset_id, env_acc, env_region)
    ecr_client.start_image_scan(
        repositoryName=image_name,
        imageId={
            'imageTag': str(tag)
        }
    )

deployspec_file.write_text(yaml.dump(deployspec))