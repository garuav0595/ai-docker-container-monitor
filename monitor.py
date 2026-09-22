#!/usr/bin/env python3
"""Simple Docker monitor - no AI, no AWS, just Docker commands.

This is the foundation layer described in "Built an AI Agent for Docker
Container Monitoring": a clean, minimal Docker monitor in pure Python.
Get this working first, understand it, then layer AI / Temporal on top.
"""

import sys
import os

import docker

try:
    client = docker.from_env()
except Exception:
    print("Docker not connected. Run: export DOCKER_HOST=unix://$HOME/.docker/run/docker.sock")
    sys.exit(1)


def format_bytes(bytes_val):
    """Convert bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}TB"


def get_cpu_percent(stats):
    """Calculate CPU percentage from stats."""
    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
    if system_delta > 0:
        num_cpus = len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1]))
        return (cpu_delta / system_delta) * num_cpus * 100
    return 0.0


def main():
    print("Simple Docker Monitor\n")
    print("Commands:")
    print("  list [all]           - List running (or all) containers")
    print("  health <name>        - Show container health stats")
    print("  logs <name> [lines]  - Show container logs (default 50 lines)")
    print("  restart <name>       - Restart container")
    print("  stop <name>          - Stop container")
    print("  start <name>         - Start container")
    print("  inspect <name>       - Show detailed container info")
    print("  stats                - Show live stats for all running containers")
    print("  images               - List Docker images")
    print("  prune                - Remove stopped containers")
    print("  exec <name>          - Interactive shell in container")
    print("  exec <name> <cmd>    - Execute command in container")
    print("  quit                 - Exit monitor\n")

    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue

            if cmd[0] == "quit":
                break

            elif cmd[0] == "list":
                show_all = len(cmd) > 1 and cmd[1] == "all"
                containers = client.containers.list(all=show_all)
                if not containers:
                    print("No containers found")
                else:
                    print(f"{'NAME':<20} {'STATUS':<15} {'IMAGE':<30} {'PORTS'}")
                    for c in containers:
                        ports = ", ".join(
                            f"{k}→{v[0]['HostPort']}" for k, v in (c.ports or {}).items() if v
                        ) or "-"
                        image = c.image.tags[0] if c.image.tags else "N/A"
                        print(f"{c.name:<20} {c.status:<15} {image:<30} {ports}")

            elif cmd[0] == "health" and len(cmd) > 1:
                c = client.containers.get(cmd[1])
                stats = c.stats(stream=False)
                mem_usage = stats["memory_stats"].get("usage", 0)
                mem_limit = stats["memory_stats"].get("limit", 1)
                mem_percent = (mem_usage / mem_limit) * 100 if mem_limit else 0
                cpu_percent = get_cpu_percent(stats)

                print(f"\n{c.name} Health:")
                print(f"  Status: {c.status}")
                print(f"  CPU: {cpu_percent:.1f}%")
                print(f"  Memory: {format_bytes(mem_usage)} / {format_bytes(mem_limit)} ({mem_percent:.1f}%)")
                print(f"  Restart Count: {c.attrs['RestartCount']}")
                print(f"  Created: {c.attrs['Created'][:19]}")

            elif cmd[0] == "logs" and len(cmd) > 1:
                lines = int(cmd[2]) if len(cmd) > 2 else 50
                c = client.containers.get(cmd[1])
                print(c.logs(tail=lines).decode("utf-8", errors="ignore"))

            elif cmd[0] == "restart" and len(cmd) > 1:
                c = client.containers.get(cmd[1])
                print(f"Restarting {cmd[1]}...")
                c.restart()
                c.reload()
                print(f"✓ Restarted {cmd[1]} - Status: {c.status}")

            elif cmd[0] == "stop" and len(cmd) > 1:
                c = client.containers.get(cmd[1])
                print(f"Stopping {cmd[1]}...")
                c.stop()
                print(f"✓ Stopped {cmd[1]}")

            elif cmd[0] == "start" and len(cmd) > 1:
                c = client.containers.get(cmd[1])
                print(f"Starting {cmd[1]}...")
                c.start()
                c.reload()
                print(f"✓ Started {cmd[1]} - Status: {c.status}")

            elif cmd[0] == "inspect" and len(cmd) > 1:
                c = client.containers.get(cmd[1])
                print(f"\n{c.name} Details:")
                print(f"  ID: {c.short_id}")
                print(f"  Image: {c.image.tags[0] if c.image.tags else c.image.short_id}")
                print(f"  Status: {c.status}")
                print(f"  Created: {c.attrs['Created'][:19]}")
                print(f"  Restart Policy: {c.attrs['HostConfig']['RestartPolicy']['Name']}")
                print(f"  Network Mode: {c.attrs['HostConfig']['NetworkMode']}")
                if c.attrs.get("Mounts"):
                    print("  Mounts:")
                    for m in c.attrs["Mounts"]:
                        print(f"    {m['Source']} → {m['Destination']}")

            elif cmd[0] == "stats":
                containers = client.containers.list()
                if not containers:
                    print("No running containers")
                else:
                    print(f"{'NAME':<20} {'CPU %':<10} {'MEMORY':<25} {'NET I/O'}")
                    for c in containers:
                        stats = c.stats(stream=False)
                        cpu = get_cpu_percent(stats)
                        mem_usage = stats["memory_stats"].get("usage", 0)
                        mem_limit = stats["memory_stats"].get("limit", 1)
                        mem_str = f"{format_bytes(mem_usage)} / {format_bytes(mem_limit)}"
                        net_rx = stats["networks"].get("eth0", {}).get("rx_bytes", 0)
                        net_tx = stats["networks"].get("eth0", {}).get("tx_bytes", 0)
                        net_str = f"{format_bytes(net_rx)} / {format_bytes(net_tx)}"
                        print(f"{c.name:<20} {cpu:<10.1f} {mem_str:<25} {net_str}")

            elif cmd[0] == "images":
                images = client.images.list()
                if not images:
                    print("No images found")
                else:
                    print(f"{'REPOSITORY':<30} {'TAG':<15} {'SIZE':<12} {'CREATED'}")
                    for img in images:
                        repo = img.tags[0].split(":")[0] if img.tags else "<none>"
                        tag = img.tags[0].split(":")[1] if img.tags and ":" in img.tags[0] else "<none>"
                        size = format_bytes(img.attrs["Size"])
                        created = img.attrs["Created"][:19]
                        print(f"{repo:<30} {tag:<15} {size:<12} {created}")

            elif cmd[0] == "prune":
                removed = client.containers.prune()
                print(f"✓ Removed {len(removed.get('ContainersDeleted', []))} stopped containers")
                print(f"  Reclaimed space: {format_bytes(removed.get('SpaceReclaimed', 0))}")

            elif cmd[0] == "exec" and len(cmd) > 1:
                container_name = cmd[1]
                client.containers.get(container_name)

                if len(cmd) == 2:
                    print(f"Opening interactive shell in {container_name}...")
                    print("(Type 'exit' to return to monitor)\n")
                    shell_result = os.system(f"docker exec -it {container_name} /bin/bash 2>/dev/null")
                    if shell_result != 0:
                        os.system(f"docker exec -it {container_name} /bin/sh")
                else:
                    exec_cmd = " ".join(cmd[2:])
                    c = client.containers.get(container_name)
                    result = c.exec_run(exec_cmd)
                    print(result.output.decode("utf-8", errors="ignore"))

            else:
                print("Invalid command. Type 'quit' to exit or see command list above.")

        except KeyboardInterrupt:
            break
        except docker.errors.NotFound:
            print("Error: Container not found")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
