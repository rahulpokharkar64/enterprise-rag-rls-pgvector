# Exercise E - negative tests and revocation

```text
Run: 2026-11-27 12:12:44  strategy=markdown  k=5
Question: What are recommended Kubernetes RBAC practices?

Target restricted document: sec-001 'Role Based Access Control Good Practices' (security)  https://kubernetes.io/docs/concepts/security/rbac-good-practices/

## T1 authorised user retrieves restricted doc
    meena: sec-001#0(security,0.161), sec-001#8(security,0.229), sec-001#2(security,0.239), shr-002#14(shared,0.248), sec-001#6(security,0.260)
[PASS] T1 authorised access - meena received 4 chunk(s) of sec-001

## T2 unauthorised user cannot retrieve it
    priya: shr-002#14(shared,0.248), shr-004#12(shared,0.261), app-004#24(application,0.283), shr-002#8(shared,0.286), shr-002#1(shared,0.301)
[PASS] T2 unauthorised denied - priya ranked hits on sec-001=0, direct SELECT count=0

## T3 revoke meena from 'security' (no re-embedding)
    SQL: revoke meena -> security  (1 row(s) changed, committed)
    meena: shr-002#14(shared,0.248), shr-004#12(shared,0.261), shr-002#8(shared,0.286), shr-002#1(shared,0.301), shr-003#16(shared,0.302)
    chunk fingerprint before=26 chunks ids 2582-2607 md5 df388b9c422f
    chunk fingerprint after =26 chunks ids 2582-2607 md5 df388b9c422f
[PASS] T3 revocation immediate - visible=0, embeddings unchanged=True

## T4 unknown / empty identity
[PASS] T4 identity 'mallory' - ranked hits=0, SELECT count(*) on all chunks=0
[PASS] T4 identity '<empty>' - ranked hits=0, SELECT count(*) on all chunks=0

## T5 restore meena -> 'security'
    SQL: restore meena -> security  (1 row(s) changed, committed)
    meena: sec-001#0(security,0.161), sec-001#8(security,0.229), sec-001#2(security,0.239), shr-002#14(shared,0.248), sec-001#6(security,0.260)
[PASS] T5 access restored - meena received 4 chunk(s) of sec-001

## T6 reader role cannot write or read memberships
[PASS] T6 UPDATE chunks - permission denied for table chunks
[PASS] T6 SELECT user_groups - permission denied for table user_groups
[PASS] T6 change own membership - permission denied for table user_groups

## Summary: 9/9 passed
```
