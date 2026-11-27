# Exercise D - same question, different results

Run: 2026-11-27 12:12  |  strategy=`markdown`  |  k=5  |  model=`BAAI/bge-small-en-v1.5`

*authorised* = audit against expected group policy (enforcement is RLS). *Hidden by RLS* = chunks in the unfiltered top-k that this user did not receive.

## Q1: How does a Kubernetes Deployment manage application replicas?
Primary area: **application**

**Unfiltered top-k (owner view, audit only):** `app-002`(application, 0.157), `app-001`(application, 0.159), `app-001`(application, 0.180), `app-002`(application, 0.200), `shr-004`(shared, 0.200)

### priya  (groups: application, shared)
|   # | doc_id   | access      |   cos_dist | heading                                       | source                                                                | authorised   |
|-----|----------|-------------|------------|-----------------------------------------------|-----------------------------------------------------------------------|--------------|
|   1 | app-002  | application |     0.1569 | ReplicaSet > {{% heading "whatsnext" %}}      | https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/ | YES          |
|   2 | app-001  | application |     0.1595 | Deployments                                   | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | YES          |
|   3 | app-001  | application |     0.1799 | Deployments > Writing a Deployment Spec > Rep | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | YES          |
|   4 | app-002  | application |     0.1997 | ReplicaSet > Alternatives to ReplicaSet > Dep | https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/ | YES          |
|   5 | shr-004  | shared      |     0.2    | Objects In Kubernetes > Understanding Kuberne | https://kubernetes.io/docs/concepts/overview/working-with-objects/    | YES          |

Hidden by RLS from unfiltered top-k: none

### arjun  (groups: platform, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                             | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|--------------------------------------------------------------------|--------------|
|   1 | shr-004  | shared   |     0.2    | Objects In Kubernetes > Understanding Kuberne | https://kubernetes.io/docs/concepts/overview/working-with-objects/ | YES          |
|   2 | shr-002  | shared   |     0.218  | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   3 | plat-002 | platform |     0.2334 | Volumes > Out-of-tree volume plugins > csi    | https://kubernetes.io/docs/concepts/storage/volumes/               | YES          |
|   4 | shr-002  | shared   |     0.2373 | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   5 | shr-002  | shared   |     0.2441 | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                      | YES          |

Hidden by RLS from unfiltered top-k: `app-001`, `app-002`

### meena  (groups: security, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                             | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|--------------------------------------------------------------------|--------------|
|   1 | shr-004  | shared   |     0.2    | Objects In Kubernetes > Understanding Kuberne | https://kubernetes.io/docs/concepts/overview/working-with-objects/ | YES          |
|   2 | shr-002  | shared   |     0.218  | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   3 | sec-001  | security |     0.2305 | Role Based Access Control Good Practices > Ku | https://kubernetes.io/docs/concepts/security/rbac-good-practices/  | YES          |
|   4 | shr-002  | shared   |     0.2373 | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   5 | shr-002  | shared   |     0.2441 | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                      | YES          |

Hidden by RLS from unfiltered top-k: `app-001`, `app-002`

### divya  (groups: application, security, shared)
|   # | doc_id   | access      |   cos_dist | heading                                       | source                                                                | authorised   |
|-----|----------|-------------|------------|-----------------------------------------------|-----------------------------------------------------------------------|--------------|
|   1 | app-002  | application |     0.1569 | ReplicaSet > {{% heading "whatsnext" %}}      | https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/ | YES          |
|   2 | app-001  | application |     0.1595 | Deployments                                   | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | YES          |
|   3 | app-001  | application |     0.1799 | Deployments > Writing a Deployment Spec > Rep | https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ | YES          |
|   4 | app-002  | application |     0.1997 | ReplicaSet > Alternatives to ReplicaSet > Dep | https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/ | YES          |
|   5 | shr-004  | shared      |     0.2    | Objects In Kubernetes > Understanding Kuberne | https://kubernetes.io/docs/concepts/overview/working-with-objects/    | YES          |

Hidden by RLS from unfiltered top-k: none

### nobody  (groups: none - unknown identity)
_0 rows returned - RLS denied all chunks._

Hidden by RLS from unfiltered top-k: `app-001`, `app-002`, `shr-004`

## Q2: What are PersistentVolumes and PersistentVolumeClaims?
Primary area: **platform**

**Unfiltered top-k (owner view, audit only):** `sec-001`(security, 0.189), `app-003`(application, 0.205), `plat-001`(platform, 0.206), `plat-001`(platform, 0.214), `plat-002`(platform, 0.215)

### priya  (groups: application, shared)
|   # | doc_id   | access      |   cos_dist | heading                                       | source                                                                 | authorised   |
|-----|----------|-------------|------------|-----------------------------------------------|------------------------------------------------------------------------|--------------|
|   1 | app-003  | application |     0.2051 | StatefulSets > Pod Identity > Stable Storage  | https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ | YES          |
|   2 | app-003  | application |     0.2441 | StatefulSets > PersistentVolumeClaim retentio | https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ | YES          |
|   3 | app-003  | application |     0.2657 | StatefulSets > Components > Volume Claim Temp | https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ | YES          |
|   4 | shr-003  | shared      |     0.3285 | The Kubernetes API > Persistence              | https://kubernetes.io/docs/concepts/overview/kubernetes-api/           | YES          |
|   5 | app-003  | application |     0.3569 | StatefulSets > PersistentVolumeClaim retentio | https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ | YES          |

Hidden by RLS from unfiltered top-k: `plat-001`, `plat-002`, `sec-001`

### arjun  (groups: platform, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                          | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|-----------------------------------------------------------------|--------------|
|   1 | plat-001 | platform |     0.2064 | Persistent Volumes > Introduction             | https://kubernetes.io/docs/concepts/storage/persistent-volumes/ | YES          |
|   2 | plat-001 | platform |     0.2136 | Persistent Volumes > Introduction             | https://kubernetes.io/docs/concepts/storage/persistent-volumes/ | YES          |
|   3 | plat-002 | platform |     0.2148 | Volumes > Types of volumes {#volume-types} >  | https://kubernetes.io/docs/concepts/storage/volumes/            | YES          |
|   4 | plat-005 | platform |     0.2215 | Volume Snapshots > Lifecycle of a volume snap | https://kubernetes.io/docs/concepts/storage/volume-snapshots/   | YES          |
|   5 | plat-001 | platform |     0.2294 | Persistent Volumes > Claims As Volumes > A No | https://kubernetes.io/docs/concepts/storage/persistent-volumes/ | YES          |

Hidden by RLS from unfiltered top-k: `app-003`, `sec-001`

### meena  (groups: security, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                            | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|-------------------------------------------------------------------|--------------|
|   1 | sec-001  | security |     0.1893 | Role Based Access Control Good Practices > Ku | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   2 | sec-001  | security |     0.2913 | Role Based Access Control Good Practices > Ku | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   3 | shr-003  | shared   |     0.3285 | The Kubernetes API > Persistence              | https://kubernetes.io/docs/concepts/overview/kubernetes-api/      | YES          |
|   4 | shr-002  | shared   |     0.3964 | Overview > Historical context for Kubernetes  | https://kubernetes.io/docs/concepts/overview/                     | YES          |
|   5 | sec-004  | security |     0.403  | Security Checklist > Secrets                  | https://kubernetes.io/docs/concepts/security/security-checklist/  | YES          |

Hidden by RLS from unfiltered top-k: `app-003`, `plat-001`, `plat-002`

### divya  (groups: application, security, shared)
|   # | doc_id   | access      |   cos_dist | heading                                       | source                                                                 | authorised   |
|-----|----------|-------------|------------|-----------------------------------------------|------------------------------------------------------------------------|--------------|
|   1 | sec-001  | security    |     0.1893 | Role Based Access Control Good Practices > Ku | https://kubernetes.io/docs/concepts/security/rbac-good-practices/      | YES          |
|   2 | app-003  | application |     0.2051 | StatefulSets > Pod Identity > Stable Storage  | https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ | YES          |
|   3 | app-003  | application |     0.2441 | StatefulSets > PersistentVolumeClaim retentio | https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ | YES          |
|   4 | app-003  | application |     0.2657 | StatefulSets > Components > Volume Claim Temp | https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/ | YES          |
|   5 | sec-001  | security    |     0.2913 | Role Based Access Control Good Practices > Ku | https://kubernetes.io/docs/concepts/security/rbac-good-practices/      | YES          |

Hidden by RLS from unfiltered top-k: `plat-001`, `plat-002`

### nobody  (groups: none - unknown identity)
_0 rows returned - RLS denied all chunks._

Hidden by RLS from unfiltered top-k: `app-003`, `plat-001`, `plat-002`, `sec-001`

## Q3: What are recommended Kubernetes RBAC practices?
Primary area: **security**

**Unfiltered top-k (owner view, audit only):** `sec-001`(security, 0.161), `sec-001`(security, 0.229), `sec-001`(security, 0.239), `shr-002`(shared, 0.248), `sec-001`(security, 0.260)

### priya  (groups: application, shared)
|   # | doc_id   | access      |   cos_dist | heading                                       | source                                                               | authorised   |
|-----|----------|-------------|------------|-----------------------------------------------|----------------------------------------------------------------------|--------------|
|   1 | shr-002  | shared      |     0.2481 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                        | YES          |
|   2 | shr-004  | shared      |     0.261  | Objects In Kubernetes > {{% heading "whatsnex | https://kubernetes.io/docs/concepts/overview/working-with-objects/   | YES          |
|   3 | app-004  | application |     0.2829 | DaemonSet > {{% heading "whatsnext" %}}       | https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/ | YES          |
|   4 | shr-002  | shared      |     0.2857 | Overview > What Kubernetes is not             | https://kubernetes.io/docs/concepts/overview/                        | YES          |
|   5 | shr-002  | shared      |     0.3012 | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                        | YES          |

Hidden by RLS from unfiltered top-k: `sec-001`

### arjun  (groups: platform, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                             | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|--------------------------------------------------------------------|--------------|
|   1 | shr-002  | shared   |     0.2481 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   2 | shr-004  | shared   |     0.261  | Objects In Kubernetes > {{% heading "whatsnex | https://kubernetes.io/docs/concepts/overview/working-with-objects/ | YES          |
|   3 | shr-002  | shared   |     0.2857 | Overview > What Kubernetes is not             | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   4 | shr-002  | shared   |     0.3012 | Overview > Why you need Kubernetes and what i | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   5 | shr-003  | shared   |     0.3016 | The Kubernetes API > API groups and versionin | https://kubernetes.io/docs/concepts/overview/kubernetes-api/       | YES          |

Hidden by RLS from unfiltered top-k: `sec-001`

### meena  (groups: security, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                            | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|-------------------------------------------------------------------|--------------|
|   1 | sec-001  | security |     0.1612 | Role Based Access Control Good Practices      | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   2 | sec-001  | security |     0.2292 | Role Based Access Control Good Practices > Ge | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   3 | sec-001  | security |     0.2392 | Role Based Access Control Good Practices > Ge | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   4 | shr-002  | shared   |     0.2481 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                     | YES          |
|   5 | sec-001  | security |     0.2598 | Role Based Access Control Good Practices > Ge | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |

Hidden by RLS from unfiltered top-k: none

### divya  (groups: application, security, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                            | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|-------------------------------------------------------------------|--------------|
|   1 | sec-001  | security |     0.1612 | Role Based Access Control Good Practices      | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   2 | sec-001  | security |     0.2292 | Role Based Access Control Good Practices > Ge | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   3 | sec-001  | security |     0.2392 | Role Based Access Control Good Practices > Ge | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |
|   4 | shr-002  | shared   |     0.2481 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                     | YES          |
|   5 | sec-001  | security |     0.2598 | Role Based Access Control Good Practices > Ge | https://kubernetes.io/docs/concepts/security/rbac-good-practices/ | YES          |

Hidden by RLS from unfiltered top-k: none

### nobody  (groups: none - unknown identity)
_0 rows returned - RLS denied all chunks._

Hidden by RLS from unfiltered top-k: `sec-001`, `shr-002`

## Q4: What are the main Kubernetes components?
Primary area: **shared**

**Unfiltered top-k (owner view, audit only):** `shr-001`(shared, 0.130), `shr-001`(shared, 0.144), `shr-002`(shared, 0.154), `shr-004`(shared, 0.176), `shr-001`(shared, 0.204)

### priya  (groups: application, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                             | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|--------------------------------------------------------------------|--------------|
|   1 | shr-001  | shared   |     0.1299 | Kubernetes Components > Core Components       | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   2 | shr-001  | shared   |     0.1436 | Kubernetes Components                         | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   3 | shr-002  | shared   |     0.1537 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   4 | shr-004  | shared   |     0.1759 | Objects In Kubernetes > {{% heading "whatsnex | https://kubernetes.io/docs/concepts/overview/working-with-objects/ | YES          |
|   5 | shr-001  | shared   |     0.2042 | Kubernetes Components > Core Components > Con | https://kubernetes.io/docs/concepts/overview/components/           | YES          |

Hidden by RLS from unfiltered top-k: none

### arjun  (groups: platform, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                             | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|--------------------------------------------------------------------|--------------|
|   1 | shr-001  | shared   |     0.1299 | Kubernetes Components > Core Components       | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   2 | shr-001  | shared   |     0.1436 | Kubernetes Components                         | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   3 | shr-002  | shared   |     0.1537 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   4 | shr-004  | shared   |     0.1759 | Objects In Kubernetes > {{% heading "whatsnex | https://kubernetes.io/docs/concepts/overview/working-with-objects/ | YES          |
|   5 | shr-001  | shared   |     0.2042 | Kubernetes Components > Core Components > Con | https://kubernetes.io/docs/concepts/overview/components/           | YES          |

Hidden by RLS from unfiltered top-k: none

### meena  (groups: security, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                             | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|--------------------------------------------------------------------|--------------|
|   1 | shr-001  | shared   |     0.1299 | Kubernetes Components > Core Components       | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   2 | shr-001  | shared   |     0.1436 | Kubernetes Components                         | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   3 | shr-002  | shared   |     0.1537 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   4 | shr-004  | shared   |     0.1759 | Objects In Kubernetes > {{% heading "whatsnex | https://kubernetes.io/docs/concepts/overview/working-with-objects/ | YES          |
|   5 | shr-001  | shared   |     0.2042 | Kubernetes Components > Core Components > Con | https://kubernetes.io/docs/concepts/overview/components/           | YES          |

Hidden by RLS from unfiltered top-k: none

### divya  (groups: application, security, shared)
|   # | doc_id   | access   |   cos_dist | heading                                       | source                                                             | authorised   |
|-----|----------|----------|------------|-----------------------------------------------|--------------------------------------------------------------------|--------------|
|   1 | shr-001  | shared   |     0.1299 | Kubernetes Components > Core Components       | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   2 | shr-001  | shared   |     0.1436 | Kubernetes Components                         | https://kubernetes.io/docs/concepts/overview/components/           | YES          |
|   3 | shr-002  | shared   |     0.1537 | Overview > {{% heading "whatsnext" %}}        | https://kubernetes.io/docs/concepts/overview/                      | YES          |
|   4 | shr-004  | shared   |     0.1759 | Objects In Kubernetes > {{% heading "whatsnex | https://kubernetes.io/docs/concepts/overview/working-with-objects/ | YES          |
|   5 | shr-001  | shared   |     0.2042 | Kubernetes Components > Core Components > Con | https://kubernetes.io/docs/concepts/overview/components/           | YES          |

Hidden by RLS from unfiltered top-k: none

### nobody  (groups: none - unknown identity)
_0 rows returned - RLS denied all chunks._

Hidden by RLS from unfiltered top-k: `shr-001`, `shr-002`, `shr-004`

## Result
**PASS** - 0 unauthorised chunk(s) returned across 4 questions x 5 identities.
