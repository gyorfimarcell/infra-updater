from settings import settings
import requests
from requests.auth import HTTPBasicAuth
import yaml
import subprocess


def get_container_name(repo):
    return f"{repo['owner']['username']}_{repo['name']}"


def update_infra():
    # Read main config file
    with open(settings.config_path, "r", encoding="utf8") as file:
        print(f"Reading main config at {settings.config_path}")
        lines = [x.strip() for x in file.readlines()]

        base_domain = lines[0]
        root_username = lines[2]
        root_password = lines[3]
        competitors = [x.split(" ")[0] for x in lines[5:]]

    # Docker login
    print("Logging into docker")
    subprocess.run(
        [
            "docker",
            "login",
            "-u",
            root_username,
            "-p",
            root_password,
            f"git.{base_domain}",
        ]
    )

    # Fetch competitor repos
    repos = []
    for competitor in competitors:
        print(f"Getting repos for competitor {competitor}")

        r = requests.get(
            f"https://git.{base_domain}/api/v1/user/repos",
            headers={
                "Sudo": competitor,
            },
            auth=HTTPBasicAuth(root_username, root_password),
        )
        data = r.json()
        filtered = [x for x in data if x["owner"]["username"] == competitor]

        print(f"Found {len(data)} repos from {competitor}")
        repos = repos + filtered
    print(f"Found {len(repos)} repos in total")

    # Fetch packages
    packages = {}
    for competitor in competitors:
        print(f"Getting packages for competitor {competitor}")

        r = requests.get(
            f"https://git.{base_domain}/api/v1/packages/{competitor}",
            headers={
                "Sudo": competitor,
            },
            auth=HTTPBasicAuth(root_username, root_password),
        )
        data = r.json()

        print(f"Found {len(data)} packages from {competitor}")
        packages[competitor] = data

    # Write competitors.yml
    print("Writing competitors.yml")
    compose = {
        "services": {
            get_container_name(x): {
                "image": f"git.{base_domain}/{x['owner']['username']}/{x['name']}:latest",
                "container_name": get_container_name(x),
                "restart": "always",
                "networks": ["gitea"],
                "labels": [
                    "sablier.enable=true",
                    f"sablier.group={get_container_name(x)}",
                    "com.centurylinklabs.watchtower.enable=true",
                ],
            }
            for x in repos
        },
        "networks": {"gitea": {"external": True}},
    }
    with open(settings.competitors_compose_path, "w", encoding="utf8") as file:
        yaml.dump(compose, file, sort_keys=False)

    # Write Traefik dynamic config
    print("Writing traefik dynamic config")
    traefik_config = {
        "http": {
            "middlewares": {
                f"sablier-{get_container_name(x)}": {
                    "plugin": {
                        "sablier": {
                            "group": get_container_name(x),
                            "dynamic": {"displayName": get_container_name(x)},
                            "sablierUrl": "http://sablier:10000",
                        }
                    }
                }
                for x in repos
            },
            "routers": {
                get_container_name(x): {
                    "rule": f"Host(`{get_container_name(x)}.{base_domain}`)",
                    "entryPoints": ["websecure"],
                    "middlewares": [f"sablier-{get_container_name(x)}@file"],
                    "tls": True,
                    "service": get_container_name(x),
                }
                for x in repos
            },
            "services": {
                get_container_name(x): {
                    "loadBalancer": {
                        "servers": [{"url": f"http://{get_container_name(x)}:80"}]
                    }
                }
                for x in repos
            },
        }
    }
    with open(settings.traefik_config_path, "w", encoding="utf8") as file:
        yaml.dump(traefik_config, file, sort_keys=False)

    # Push empty containers
    print("Pushing initial containers")
    for repo in repos:
        container_name = f"git.{base_domain}/{repo['owner']['username']}/{repo['name']}"

        competitor_packages = packages[repo["owner"]["username"]]
        if any(x["name"] == repo["name"] for x in competitor_packages):
            print(f"Package {container_name} already exists")
            continue

        print(f"Pushing {container_name}")
        subprocess.run(
            [
                "docker",
                "tag",
                "nginx:latest",
                f"{container_name}:latest",
            ]
        )
        subprocess.run(["docker", "push", container_name])

    # Restart docker containers
    print("Restarting docker containers")
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            settings.competitors_compose_path,
            "-p",
            settings.docker_project_name,
            "create",
        ]
    )
