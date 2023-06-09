#!/usr/local/bin/python3

import logging
import sys
import random
import time
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Define logger
logger = logging.getLogger(__name__)

def load_kubernetes_config():
    """
    Load Kubernetes configuration either from in-cluster or local kube-config.
    Exit with an error if unsuccessful.
    """
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
    try:
        pods = api.list_namespaced_pod(namespace, label_selector=label_selector).items
    except ApiException as e:
        logger.error(f"Error listing pods in namespace {namespace} with label selector {label_selector}: {e}")
        return

    if len(pods) == 0:
        logger.warning('No pods found with the given label selector in the specified namespace.')
        return

    selected_pods = random.sample(pods, num_pods)

    for pod in selected_pods:
        try:
            api.delete_namespaced_pod(pod.metadata.name, namespace)
            logger.info(f"Deleted pod {pod.metadata.name} in namespace {namespace} with label selector {label_selector}.")
        except ApiException as e:
            logger.error(f"Error deleting pod {pod.metadata.name} in namespace {namespace}: {e}")

def schedule_pod_deletions(schedule, namespace, label_selector, num_pods, jitter):
    """
    Schedule pod deletions based on provided arguments using a blocking scheduler.

    Args:
    - schedule (str): Cron expression defining the deletion schedule.
    - namespace (str): Namespace containing the pods to be deleted.
    - label_selector (str): Label selector to filter the pods.
    - num_pods (int): Number of pods to delete at random.
    - jitter (int): Maximum number of seconds to delay deletion.
    """
    logger.info(f'Starting pod deletion schedule with: schedule="{schedule}", namespace="{namespace}", label_selector="{label_selector}", num_pods="{num_pods}", jitter="{jitter}".')
    scheduler = BlockingScheduler()
    scheduler.add_job(delete_random_pod, args=[namespace, label_selector, num_pods, jitter], trigger=CronTrigger.from_crontab(schedule))
    scheduler.start()

def load_configuration_from_environment():
    """
    Load configuration parameters from environment variables with default values.

    Returns:
    - schedule (str): Cron expression defining the deletion schedule.
    - namespace (str): Namespace containing the pods to be deleted.
    - label_selector (str): Label selector to filter the pods.
    - num_pods (int): Number of pods to delete at random.
    - jitter (int): Maximum number of seconds to delay deletion.
    """
    schedule = os.environ.get('SCHEDULE', '* * * * *')
    namespace = os.environ.get('NAMESPACE', 'workloads')
    label_selector = os.environ.get('LABEL_SELECTOR', 'app=nginx')
    num_pods = int(os.environ.get('NUM_PODS', 2))
    jitter = int(os.environ.get('JITTER', 10))

    return schedule, namespace, label_selector, num_pods, jitter

if __name__ == '__main__':
    load_kubernetes_config()
    schedule, namespace, label_selector, num_pods, jitter = load_configuration_from_environment()
    schedule_pod_deletions(schedule, namespace, label_selector, num_pods, jitter)
