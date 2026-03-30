# `core/grpc_api` — Protobuf & gRPC Interface (Server Side)

Contains the protobuf schema and the auto-generated Python stubs used by the Core gRPC server. This is the **server-side mirror** of the identical `grpc_api/` folder in `collectors/`.

```
grpc_api/
├── proto/
│   └── core_ingest.proto        # ⚙️  Schema definition — edit to change the data contract
├── core_ingest_pb2.py           # Auto-generated message classes (DO NOT EDIT)
└── core_ingest_pb2_grpc.py      # Auto-generated service stubs (DO NOT EDIT)
```

> ⚠️ **Never hand-edit `*_pb2.py` or `*_pb2_grpc.py`**. Always edit the `.proto` file and regenerate.

---

## `proto/core_ingest.proto` — Schema

```proto
syntax = "proto3";
package core;

service CoreIngest {
  rpc SendMetric (Metric) returns (Ack);
}

message Metric {
  string device_hostname = 1;
  map<string, double> metric_values = 2;   // cpu, ram, disk, bytes, packets, latency…
  map<string, string>  tags         = 3;   // hostname, device_type, ip, mac, status
  int64 timestamp = 4;
}

message Ack {
  bool   success = 1;
  string message = 2;
}
```

This schema is **identical** to `collectors/grpc_api/proto/core_ingest.proto`. Any change must be applied **in both places** and stubs regenerated in both services.

---

## Regenerating Python Stubs

Run from inside the `core/` directory:

```bash
python -m grpc_tools.protoc \
  -I grpc_api/proto \
  --python_out=grpc_api \
  --grpc_python_out=grpc_api \
  grpc_api/proto/core_ingest.proto
```

> **Requires:** `grpcio-tools` (`pip install grpcio-tools==1.78.0`)

After regeneration, fix the import in `core_ingest_pb2_grpc.py` if needed:
```python
# Ensure relative import (not absolute):
from . import core_ingest_pb2 as core__ingest__pb2
```

---

## What to change

| What | How |
|---|---|
| Add a new metric | Add to `metric_values` map in `.proto` — no schema change needed (maps are flexible). Update `ingester/ingest_service.py` to read the new key. Regenerate stubs in **both** `core/` and `collectors/`. |
| Add a new field type | Add a new `message` or top-level field in `.proto`. Regenerate. Update `processer/normalizer.py` to validate the new field. |
| Add a second RPC method | Add another `rpc` line to the `service` block. Regenerate. Implement the handler in `CoreIngestService`. |
| Enable TLS | Change `server.add_insecure_port(...)` to `server.add_secure_port(...)` with `grpc.ssl_server_credentials(...)` in `ingester/ingest_service.py`. |
