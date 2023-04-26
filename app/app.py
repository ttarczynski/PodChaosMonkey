#!/usr/local/bin/python3

import logging
import sys
import random
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from kubernetes import client, config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Define logger
logger = logging.getLogger(__name__)

def load_kubernetes_config():
    try:
        config.load_incluster_config()
        logger.info('Successfully loaded in-cluster Kubernetes configuration.')
    except config.config_exception.ConfigException:
        try:
            config.load_kube_config()
            logger.info('Successfully loaded Kubernetes configuration from default location.')
        except Exception as e:
            logger.error("Error loading kube-config: %s", str(e))
            sys.exit(1)

def delete_random_pod(namespace, label_selector, num_pods, jitter):
    """
    Delete a specified number of pods at random from a given namespace and label selector.
    Deletion is delayed by a random number of seconds between 0 and `jitter`.

    Args:
    - namespace (str): The name of the namespace containing the pods to be deleted.
    - label_selector (str): The label selector used to select the pods to be deleted.
    - num_pods (int): The number of pods to be deleted at random.
    - jitter (int): Maximum number of seconds to delay deletion.

    Returns:
    None.
    """
    sleep_time=random.randint(0, jitter)
    logger.info(f"Sleeping {sleep_time} seconds.")
    time.sleep(sleep_time)

    api = client.CoreV1Api()
    pods = api.list_namespaced_pod(namespace, label_selector=label_selector).items
    if len(pods) == 0:
        logger.warning('No pods found with the given label selector in the specified namespace.')
        return

    selected_pods = random.sample(pods, num_pods)

    for pod in selected_pods:
        api.delete_namespaced_pod(pod.metadata.name, namespace)
        logger.info(f"Deleted pod {pod.metadata.name} in namespace {namespace} with label selector {label_selector}.")

def schedule_pod_deletions(namespace, label_selector, num_pods, jitter, schedule):
    logger.info(f'Starting pod deletion schedule with: schedule="{schedule}", namespace="{namespace}", num_pods="{num_pods}", label_selector="{label_selector}", jitter="{jitter}".')
    scheduler = BlockingScheduler()
    scheduler.add_job(delete_random_pod, args=[namespace, label_selector, num_pods, jitter], trigger=CronTrigger.from_crontab(schedule))
    scheduler.start()

if __name__ == '__main__':
    load_kubernetes_config()
    namespace = 'workloads'
    label_selector = 'app=nginx'
    num_pods = 2
    jitter = 10
    schedule = '* * * * *'
    schedule_pod_deletions(namespace, label_selector, num_pods, jitter, schedule)
