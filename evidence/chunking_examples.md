# Chunk boundary examples

Auto-selected. *Good* = starts at a heading, ends cleanly, code intact. *Poor* = cuts mid-word or splits a code block.

## fixed
_Good: none found_

**Poor** - `app-001` seq 1, 799 chars, heading: `Deployments > Use Case`

```text
ReplicaSet creates Pods in the background. Check the status of the rollout to see if it succeeds or not.
* [Declare the new state of the Pods](#updating-a-deployment) by updating the PodTemplateSpec of the Deployment. A 
...
 updates the revision of the Deployment.
* [Scale up the Deployment to facilitate more load](#scaling-a-deployment).
* [Pause the rollout of a Deployment](#pausing-and-resuming-a-deployment) to apply multiple fixes to it
```

**Poor** - `app-001` seq 2, 800 chars, heading: `Deployments > Use Case`

```text
Pause the rollout of a Deployment](#pausing-and-resuming-a-deployment) to apply multiple fixes to its PodTemplateSpec and then resume it to start a new rollout.
* [Use the status of the Deployment](#deployment-status) as
...
This name will become the basis for the ReplicaSets
  and Pods which are created later. See [Writing a Deployment Spec](#writing-a-deployment-spec)
  for more details.
* The Deployment creates a ReplicaSet that creates t
```

## recursive
**Good** - `app-001` seq 0, 555 chars, heading: `None`

```text
# Deployments

A _Deployment_ provides declarative updates for Pods and
ReplicaSets.

You describe a _desired state_ in a Deployment, and the Deployment {{< glossary_tooltip term_id="controller" >}} changes the actual st
...
xisting Deployments and adopt all their resources with new Deployments.

Do not manage ReplicaSets owned by a Deployment. Consider opening an issue in the main Kubernetes repository if your use case is not covered below.
```

**Poor** - `app-001` seq 50, 590 chars, heading: `Deployments > Rolling Back a Deployment > Rolling Back to a Previous Revision`

```text
Normal  ScalingReplicaSet   11m   deployment-controller  Scaled up replica set nginx-deployment-c4747d96c to 3
     Normal  ScalingReplicaSet   11m   deployment-controller  Scaled down replica set nginx-deployment-75675f
...
Rollback  15s   deployment-controller  Rolled back deployment "nginx-deployment" to revision 2
     Normal  ScalingReplicaSet   15s   deployment-controller  Scaled down replica set nginx-deployment-595696685f to 0
   ```
```

**Poor** - `app-005` seq 9, 799 chars, heading: `Jobs > Running an example Job`

```text
3.14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196442881097566593344
...
5238467481846766940513200056812714526356082778577134275778960917363717872146844090122495343014654958537105079227968925892354201995611212902196086403441815981362977477130996051870721134999999837297804995105973173281609631
```

## markdown
**Good** - `app-001` seq 0, 558 chars, heading: `Deployments`

```text
# Deployments  
A _Deployment_ provides declarative updates for Pods and
ReplicaSets.  
You describe a _desired state_ in a Deployment, and the Deployment {{< glossary_tooltip term_id="controller" >}} changes the actual 
...
isting Deployments and adopt all their resources with new Deployments.  
Do not manage ReplicaSets owned by a Deployment. Consider opening an issue in the main Kubernetes repository if your use case is not covered below.
```

**Poor** - `app-001` seq 5, 797 chars, heading: `Deployments > Creating a Deployment`

```text
* Create one container and name it `nginx` using the `.spec.containers[0].name` field.  
Before you begin, make sure your Kubernetes cluster is up and running.
Follow the steps given below to create the above Deployment:
...
AILABLE   AGE
nginx-deployment   0/3     0            0           1s
```
When you inspect the Deployments in your cluster, the following fields are displayed:
* `NAME` lists the names of the Deployments in the namespace.
```

**Poor** - `app-001` seq 6, 739 chars, heading: `Deployments > Creating a Deployment`

```text
* `READY` displays how many replicas of the application are available to your users. It follows the pattern ready/desired.
* `UP-TO-DATE` displays the number of replicas that have been updated to achieve the desired stat
...
 `kubectl rollout status deployment/nginx-deployment`.  
The output is similar to:
```
Waiting for rollout to finish: 2 out of 3 new replicas have been updated...
deployment "nginx-deployment" successfully rolled out
```
```

## semantic
**Good** - `app-001` seq 0, 404 chars, heading: `None`

```text
# Deployments
A _Deployment_ provides declarative updates for Pods and
ReplicaSets.
You describe a _desired state_ in a Deployment, and the Deployment {{< glossary_tooltip term_id="controller" >}} changes the actual state to the desired state at a controlled rate.
You can define Deployments to create new ReplicaSets, or to remove existing Deployments and adopt all their resources with new Deployments.
```

**Poor** - `app-001` seq 4, 494 chars, heading: `Deployments > Creating a Deployment`

```text
* The `.spec.template` field contains the following sub-fields:
  * The Pods are labeled `app: nginx`using the `.metadata.labels` field.
* The Pod template's specification, or `.spec` field, indicates that
    the Pods run one container, `nginx`, which runs the `nginx`
    [Docker Hub](https://hub.docker.com/) image at version 1.14.2.
* Create one container and name it `nginx` using the `.spec.containers[0].name` field.
Before you begin, make sure your Kubernetes cluster is up and running.
```

**Poor** - `app-001` seq 5, 738 chars, heading: `Deployments > Creating a Deployment`

```text
Follow the steps given below to create the above Deployment:
1.
Create the Deployment by running the following command:
```shell
   kubectl apply -f https://k8s.io/examples/controllers/nginx-deployment.yaml
   ```
2.
Run
...
t the Deployments in your cluster, the following fields are displayed:
   * `NAME` lists the names of the Deployments in the namespace.
* `READY` displays how many replicas of the application are available to your users.
```
