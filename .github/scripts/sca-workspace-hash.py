# Program takes in 3 parameters with flags from the command line - repo-name,
# num-workspaces, and key-prefix. Program performs modulus operation on
# repo-name using num-workspaces, and returns the result of the modulus
# appended to string-prefix.
#
# Example:
# python3 sca-workspace-hash.py --repo_name 'tr/myteams_example-project-repo' --num_workspaces 15 --key_prefix 'ISRM_VERACODE_SCA_WORKSPACE_'

import argparse


def mod_and_prefix(repo_name, num_workspaces, string_prefix):
    modulus_result = sum(ord(char) for char in repo_name) % num_workspaces + 1
    return string_prefix + str(modulus_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo_name", help="repository name", required=True)
    parser.add_argument(
        "--num_workspaces", type=int, help="number of workspaces", required=True
    )
    parser.add_argument("--key_prefix", help="string prefixed to output", required=True)
    args = parser.parse_args()

    result = mod_and_prefix(args.repo_name, args.num_workspaces, args.key_prefix)
    print(result)
