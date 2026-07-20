# enterprise_demo (synthetic)

Acme-JP style narrative only. Not a real company policy.

1. Agent tries `read_doc` → blocked on 稟議.
2. 稟議 approves → `read_doc` allowed.
3. Agent tries `send_external` → blocked on 法務 / 情シス.
4. 法務 then 情シス approve → `send_external` allowed.
5. Agent tries `change_prod` → blocked on 現場 (稟議/情シス already open).
6. 現場 approves → `change_prod` allowed.
