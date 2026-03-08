# `collectors/grpc_api` — Protobuf & gRPC Interface

This folder contains the **protobuf schema** and the **auto-generated Python stubs** used by the collector to send metrics to the NEXORA Core service over gRPC.

```
grpc_api/
├── proto/
│   └── core_ingest.proto        # ⚙️  Schema definition — EDIT THIS to change the data model
├── core_ingest_pb2.py           # Auto-generated message classes (DO NOT EDIT)
└── core_ingest_pb2_grpc.py      # Auto-generated service stubs (DO NOT EDIT)
```

> ⚠️ **Never hand-edit `*_pb2.py` or `*_pb2_grpc.py`**. They are machine-generated. Always edit the `.proto` file and re-generate.

---

## `proto/core_ingest.proto` — Schema Definition

```proto
syntax = "proto3";
package core;

service CoreIngest {
  rpc SendMetric (Metric) returns (Ack);
}

message Metric {
  string device_hostname = 1;
  map<string, double> metric_values = 2;   // cpu, ram, disk, net counters, latency …
  map<string, string> tags = 3;            // hostname, device_type, ip, mac, status
  int64 timestamp = 4;
}

message Ack {
  bool success = 1;
  string message = 2;
}
```

### Fields explained

#### `Metric`
| Field | Type | Description |
|---|---|---|
| `device_hostname` | `string` | Primary device identifier |
| `metric_values` | `map<string, double>` | All numeric metrics (cpu, ram, disk, bytes, packets, latency…) |
| `tags` | `map<string, string>` | Non-numeric metadata (device_type, ip, mac, status) |
| `timestamp` | `int64` | Unix epoch seconds |

#### `Ack`
| Field | Type | Description |
|---|---|---|
| `success` | `bool` | `true` if Core accepted the metric |
| `message` | `string` | Optional status message from Core |

---

## Regenerating Python Stubs

**You MUST regenerate whenever you edit `core_ingest.proto`.**

Run this command from inside the `collectors/` directory:

```bash
python -m grpc_tools.protoc \
  -I grpc_api/proto \
  --python_out=grpc_api \
  --grpc_python_out=grpc_api \
  grpc_api/proto/core_ingest.proto
```

> **Requires:** `grpcio-tools` installed (`pip install grpcio-tools==1.78.0`).

This regenerates:
- `grpc_api/core_ingest_pb2.py` — message serialisation classes
- `grpc_api/core_ingest_pb2_grpc.py` — `CoreIngestStub` and `CoreIngestServicer`

> ⚠️ After regeneration, the import in `core_ingest_pb2_grpc.py` changes to an absolute import. You may need to fix it to a relative import:
> ```python
> # Fix this line in core_ingest_pb2_grpc.py if it breaks:
> from . import core_ingest_pb2 as core__ingest__pb2
> ```

---

## Generated Stubs

### `core_ingest_pb2_grpc.py`

| Class | Role |
|---|---|
| `CoreIngestStub` | **Client-side** — used by `transport/grpc_client.py` to call `SendMetric` |
| `CoreIngestServicer` | **Server-side** — base class for the Core service to implement |
| `add_CoreIngestServicer_to_server()` | Registers the servicer on a `grpc.Server` — used on the Core side |

The collectors service only uses `CoreIngestStub`.

---

## What to change

| Situation | What to do |
|---|---|
| Add a new metric field (e.g. `temperature`) | Add to `metric_values` map in `.proto` (no schema change needed, maps are flexible). Update `transport/grpc_client.py` to populate the new key. Regenerate stubs. |
| Add a structured field (e.g. nested `DeviceInfo`) | Add a new `message` block in `.proto`, add a field to `Metric`, regenerate, and update `grpc_client.py`. |
| Add a new RPC method | Add `rpc <MethodName> (<Input>) returns (<Output>);` to the `service` block. Regenerate. Implement on the Core side. |
| Change package name | Edit `package core;` in `.proto`. Update the stub import path in `grpc_client.py`. |
| Use TLS / authentication | Replace `grpc.insecure_channel(...)` in `transport/grpc_client.py` with `grpc.secure_channel(...)` using appropriate credentials. |
| Point to a different Core host/port | Update `self.host` and `self.port` in `scheduler/scheduler.py` (propagated to both `BufferManager` and `CoreClient`). |
