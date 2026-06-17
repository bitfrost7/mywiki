# apisvr — 代码知识图谱

> Graphify 自动分析 | 1211 节点 · 2228 边 · 83 社区

---

## 概览

| 指标 | 数值 |
|------|------|
| 节点数 | 1211 |
| 边数 | 2228 |
| 社区数 | 83 |
| 结构体/类型 | 0 |
| API Handler | 1 |

---

## 核心抽象（God Nodes）

连接数最多的节点，代表系统的核心抽象：

| 节点 | 连接数 | 类型 | 文件 |
|------|--------|------|------|
| `Logger` | 47 | code | `db/db.go` |
| `tConnectInfoDo` | 45 | code | `db/query/t_connect_info.gen.go` |
| `tServiceDo` | 45 | code | `db/query/t_service.gen.go` |
| `tServiceSnatipDo` | 45 | code | `db/query/t_service_snatips.gen.go` |
| `tServiceWhitelistDo` | 45 | code | `db/query/t_service_whitelist.gen.go` |
| `tUserConfigDo` | 45 | code | `db/query/t_user_config.gen.go` |
| `tVpcEndpointDo` | 45 | code | `db/query/t_vpc_endpoint.gen.go` |
| `Database` | 42 | code | `db/db.go` |
| `Context` | 40 | code | `db/db.go` |
| `ITConnectInfoDo` | 30 | code | `db/query/t_connect_info.gen.go` |
| `ITServiceDo` | 30 | code | `db/query/t_service.gen.go` |
| `ITServiceSnatipDo` | 30 | code | `db/query/t_service_snatips.gen.go` |
| `ITServiceWhitelistDo` | 30 | code | `db/query/t_service_whitelist.gen.go` |
| `ITUserConfigDo` | 30 | code | `db/query/t_user_config.gen.go` |
| `ITVpcEndpointDo` | 30 | code | `db/query/t_vpc_endpoint.gen.go` |

---

## 社区导航

按大小排序的代码社区（功能模块）：

| # | 社区 | 节点数 |
|---|------|--------|
| 1 | t_service.gen.go, newTService(), DB | 71 |
| 2 | t_user_config.gen.go, newTUserConfig(), DB | 71 |
| 3 | t_vpc_endpoint.gen.go, newTVpcEndpoint(), DB | 71 |
| 4 | t_connect_info.gen.go, newTConnectInfo(), DB | 70 |
| 5 | t_service_snatips.gen.go, newTServiceSnatip(), DB | 70 |
| 6 | t_service_whitelist.gen.go, newTServiceWhitelist(), DB | 70 |
| 7 | db.go, Config, Database | 56 |
| 8 | main.go, main(), runServer() | 53 |
| 9 | basic.go, IAllocateIpRequest, BaseRequest | 45 |
| 10 | base.go, InnerReqBase, ReqBase | 44 |
| 11 | basic.go, CreateResourceRequest, BaseRequest | 35 |
| 12 | gen.go, Use(), DB | 33 |
| 13 | user_config.go, API, .NewSyncUserConfigTask() | 25 |
| 14 | basic.go, OrderDetailInfo, BuyResourceRequest | 24 |
| 15 | API, .GetPrivateLinkBandwidth(), Context | 22 |

---

## API 接口

共 1 个 Handler：

- **.handleRequestUUID()** — `api/api.go`

---

## 交互式可视化


打开 `graph.html` 浏览完整的代码知识图谱。

---

## Graphify 分析报告

> 以下内容来自 graphify 的 GRAPH_REPORT.md


# Graph Report - apisvr  (2026-06-18)

## Corpus Check
- 72 files · ~34,702 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1211 nodes · 2228 edges · 83 communities (73 shown, 10 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 117 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fb1508be`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]

## God Nodes (most connected - your core abstractions)
1. `Logger` - 47 edges
2. `tConnectInfoDo` - 45 edges
3. `tServiceDo` - 45 edges
4. `tServiceSnatipDo` - 45 edges
5. `tServiceWhitelistDo` - 45 edges
6. `tUserConfigDo` - 45 edges
7. `tVpcEndpointDo` - 45 edges
8. `Database` - 42 edges
9. `Context` - 40 edges
10. `ITConnectInfoDo` - 30 edges

## Surprising Connections (you probably didn't know these)
- `NewServer()` --calls--> `NewAPI()`  [INFERRED]
  server.go → api/api.go
- `NewServer()` --calls--> `NewDatabase()`  [INFERRED]
  server.go → db/db.go
- `NewServer()` --calls--> `InitFactory()`  [INFERRED]
  server.go → factory/factory.go
- `NewServer()` --calls--> `CollectSysMetrics()`  [INFERRED]
  server.go → prometheus/prometheus.go
- `runServer()` --calls--> `NewServer()`  [INFERRED]
  cmd/main.go → server.go

## Import Cycles
- None detected.

## Communities (83 total, 10 thin omitted)
### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (20): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+12 more)
### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (20): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+12 more)
### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (20): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+12 more)
### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (19): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+11 more)
### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (19): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+11 more)
### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (19): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+11 more)
### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (16): Config, Database, extract(), Context, Query, Time, TService, TServiceSnatip (+8 more)
### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (41): AccountImpl, API, Config, Server, ApplicationConfig, dumpConfig(), loadConfig(), main() (+33 more)
### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (32): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, VPCImpl, IpAllocatedStatus, IPv6NetworkInfo (+24 more)
### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (39): GenMessage(), GenResponse(), GenRetCode(), RandNewID(), RandNewIDWithPrefix(), CommonResponse, EndpointConnectionInfo, EndpointInfo (+31 more)
### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (26): CreateResourceInfo, ExtendInfo, BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, ResourceInfo (+18 more)
### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (20): Context, DB, Query, tConnectInfo, tService, tServiceSnatip, tServiceWhitelist, tUserConfig (+12 more)
### Community 12 - "Community 12"
Cohesion: 0.15
Nodes (13): CheckEndpointCanConnectOtherChannel(), CheckEndpointCanConnectService(), CheckUserCanCreateIPService(), CheckUserConfig(), getKey(), API, Context, Context (+5 more)
### Community 13 - "Community 13"
Cohesion: 0.17
Nodes (17): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, UBillImpl, ItemInfo, BuyResourceRequest (+9 more)
### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (15): extractContext(), API, Application, Context, Database, jsonKey(), NewAPI(), Config (+7 more)
### Community 15 - "Community 15"
Cohesion: 0.17
Nodes (14): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, LBImpl, DescribeLoadBalancersRequest, DescribeLoadBalancersResponse (+6 more)
### Community 16 - "Community 16"
Cohesion: 0.21
Nodes (8): CreateResourceResponse, DeleteResourceResponse, Context, GetResourceListResponse, ResourceInfo, ResourceImpl, UpdateResourceExtendInfoResponse, UpdateResourceStatusResponse
### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (9): API, Context, ReqBase, SubnetworkInfo, TServiceSnatip, VPCInfo, Addr, NetworkContain() (+1 more)
### Community 18 - "Community 18"
Cohesion: 0.22
Nodes (9): API, CommonResponse, Context, IpInfo, IPv6Info, ReqBase, RespBase, CreateVPCEndpointServiceConfigurationReq (+1 more)
### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (12): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, L4Impl, CreateL4GwRequest, CreateL4GwResponse (+4 more)
### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (11): GetConnectStatusCode(), GetConnectStatusName(), API, CommonResponse, Context, ReqBase, RespBase, TVpcEndpoint (+3 more)
### Community 21 - "Community 21"
Cohesion: 0.17
Nodes (11): filterWithWhiteList(), API, CommonResponse, Context, ReqBase, RespBase, TService, TServiceWhitelist (+3 more)
### Community 22 - "Community 22"
Cohesion: 0.28
Nodes (7): API, CommonResponse, Context, ReqBase, RespBase, CreateVPCEndpointReq, CreateVPCEndpointResp
### Community 23 - "Community 23"
Cohesion: 0.28
Nodes (8): DB, Duration, Config, CustomMetric, CustomMetricCollector, DBStatCollector, NewPrometheusMonitor(), PrometheusMonitor
### Community 24 - "Community 24"
Cohesion: 0.26
Nodes (8): API, CommonResponse, Context, IpInfo, IPv6Info, ReqBase, TServiceSnatip, UpdateVPCEndpointServiceConfigurationReq
### Community 25 - "Community 25"
Cohesion: 0.20
Nodes (10): BaseRequest, BaseResponse, ComopanyInfo, Context, IBaseRequest, IBaseResponse, AccountImpl, ComopanyInfo (+2 more)
### Community 26 - "Community 26"
Cohesion: 0.22
Nodes (9): AddEndpointServiceUser, AddEndpointServiceUser, API, CommonResponse, Context, ReqBase, RespBase, AddUsersToVPCEndpointServiceReq (+1 more)
### Community 27 - "Community 27"
Cohesion: 0.31
Nodes (7): GetIPVersionName(), GetResourceTypeName(), API, CommonResponse, Context, GetResourceListResponse, ServiceInfo
### Community 28 - "Community 28"
Cohesion: 0.31
Nodes (5): Context, UBillImpl, getMultiple(), getProductIdByProductName(), getProductIdByProductTypeCode()
### Community 29 - "Community 29"
Cohesion: 0.38
Nodes (6): parseAPIMetadata(), GetPayerName(), API, CommonResponse, Context, GetResourceListResponse
### Community 30 - "Community 30"
Cohesion: 0.36
Nodes (5): AutoAccept2ConnectStatus(), Bool2Int(), GetIPVersionCode(), GetPayerCode(), GetResourceTypeCode()
### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (6): ReqBase, RespBase, GetPrivateLinkPriceRequest, GetPrivateLinkPriceResponse, PriceSet, PriceSet
### Community 32 - "Community 32"
Cohesion: 0.25
Nodes (4): BaseRequest, BaseResponse, IBaseRequest, IBaseResponse
### Community 33 - "Community 33"
Cohesion: 0.29
Nodes (5): ReqBase, RespBase, DescribeVPCEndpointsReq, DescribeVPCEndpointsResp, EndpointInfo
### Community 34 - "Community 34"
Cohesion: 0.29
Nodes (5): ReqBase, RespBase, DescribeVPCEndpointServiceConfigurationReq, DescribeVPCEndpointServiceConfigurationResp, EndpointServiceConfigurationInfo
### Community 35 - "Community 35"
Cohesion: 0.40
Nodes (5): BandwidthRange, ReqBase, RespBase, GetPrivateLinkBandwidthRequest, GetPrivateLinkBandwidthResponse
### Community 36 - "Community 36"
Cohesion: 0.33
Nodes (5): ReqBase, RespBase, ListVPCEndpointServiceUsersReq, ListVPCEndpointServiceUsersResp, EndpointServiceUser
### Community 37 - "Community 37"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, AcceptVPCEndpointConnectionReq, AcceptVPCEndpointConnectionResp
### Community 38 - "Community 38"
Cohesion: 0.60
Nodes (3): API, CommonResponse, Context
### Community 39 - "Community 39"
Cohesion: 0.60
Nodes (3): API, CommonResponse, Context
### Community 40 - "Community 40"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, DeleteVPCEndpointReq, DeleteVPCEndpointResp
### Community 41 - "Community 41"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, DeleteVPCEndpointServiceConfigurationReq, DeleteVPCEndpointServiceConfigurationResp
### Community 42 - "Community 42"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, IDeleteVPCEndpointReq, IDeleteVPCEndpointResp
### Community 43 - "Community 43"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, IDeleteVPCEndpointServiceConfigurationReq, IDeleteVPCEndpointServiceConfigurationResp
### Community 44 - "Community 44"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, RejectVPCEndpointConnectionReq, RejectVPCEndpointConnectionResp
### Community 45 - "Community 45"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, RemoveUsersToVPCEndpointServiceReq, RemoveUsersToVPCEndpointServiceResp
### Community 46 - "Community 46"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, UpdateUsersToVPCEndpointServiceRequest, UpdateUsersToVPCEndpointServiceResponse
### Community 47 - "Community 47"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, UpdateVPCEndpointAttributeReq, UpdateVPCEndpointAttributeResp
### Community 48 - "Community 48"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, UpdateVPCEndpointConnectionAttributeReq, UpdateVPCEndpointConnectionAttributeResp
### Community 50 - "Community 50"
Cohesion: 0.60
Nodes (3): Context, LBImpl, LoadBalancer
### Community 51 - "Community 51"
Cohesion: 0.80
Nodes (4): Config, genOut(), loadConfig(), main()
### Community 52 - "Community 52"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 53 - "Community 53"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 54 - "Community 54"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 55 - "Community 55"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 56 - "Community 56"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 57 - "Community 57"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 58 - "Community 58"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 59 - "Community 59"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 60 - "Community 60"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 61 - "Community 61"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 62 - "Community 62"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 66 - "Community 66"
Cohesion: 0.50
Nodes (3): ComopanyInfo, Context, AccountImpl
### Community 67 - "Community 67"
Cohesion: 0.83
Nodes (3): HTTPClient, ResourceImpl, NewVPCImpl()
### Community 68 - "Community 68"
Cohesion: 0.83
Nodes (3): HTTPClient, VPCImpl, NewVPCImpl()
### Community 69 - "Community 69"
Cohesion: 0.50
Nodes (3): db目录下model和query文件生成说明, 主题, 设计文档

## Knowledge Gaps
- **262 isolated node(s):** `ReqBase`, `RespBase`, `API`, `Context`, `CommonResponse` (+257 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_
- **Why does `Use()` connect `Community 11` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.380) - this node is a cross-community bridge._
- **Why does `NewDatabase()` connect `Community 6` to `Community 17`, `Community 11`, `Community 7`, `Community 23`?**
  _High betweenness centrality (0.319) - this node is a cross-community bridge._
- **Why does `Logger` connect `Community 17` to `Community 6`, `Community 12`, `Community 14`, `Community 18`, `Community 19`, `Community 20`, `Community 21`, `Community 22`, `Community 24`, `Community 26`, `Community 27`, `Community 29`, `Community 38`, `Community 39`, `Community 52`, `Community 53`, `Community 54`, `Community 55`, `Community 56`, `Community 57`, `Community 58`, `Community 59`, `Community 60`?**
  _High betweenness centrality (0.256) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `Logger` (e.g. with `.AcceptVPCEndpointConnection()` and `.AddUsersToVPCEndpointService()`) actually correct?**
  _`Logger` has 46 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ReqBase`, `RespBase`, `API` to the rest of the system?**
  _262 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06116700201207243 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06116700201207243 - nodes in this community are weakly interconnected._