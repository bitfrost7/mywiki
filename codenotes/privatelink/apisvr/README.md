# apisvr — 代码知识图谱

> Graphify 自动分析 | 1220 节点 · 2215 边 · 83 社区

---

## 概览

| 指标 | 数值 |
|------|------|
| 节点数 | 1220 |
| 边数 | 2215 |
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
| 7 | CreateVPCEndpointServiceConfiguration.go, CreateVPCEndpointServiceConfigurationR | 57 |
| 8 | db.go, Config, Database | 56 |
| 9 | main.go, main(), runServer() | 53 |
| 10 | basic.go, IAllocateIpRequest, BaseRequest | 45 |
| 11 | base.go, InnerReqBase, ReqBase | 44 |
| 12 | basic.go, CreateResourceRequest, BaseRequest | 35 |
| 13 | gen.go, Use(), DB | 33 |
| 14 | DescribeVPCEndpointServices.go, DescribeVPCEndpointServicesReq, ReqBase | 29 |
| 15 | CreateVPCEndpoint.go, CreateVPCEndpointReq, ReqBase | 25 |

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


# Graph Report - /Users/user/Documents/Code/work/privatelink/apisvr  (2026-06-17)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1220 nodes · 2215 edges · 83 communities (69 shown, 14 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 115 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Service Data Objects|Service Data Objects]]
- [[_COMMUNITY_User Config Data Objects|User Config Data Objects]]
- [[_COMMUNITY_VPC Endpoint Data Objects|VPC Endpoint Data Objects]]
- [[_COMMUNITY_Connection Info Data Objects|Connection Info Data Objects]]
- [[_COMMUNITY_Service SNAT IP Objects|Service SNAT IP Objects]]
- [[_COMMUNITY_Service Whitelist Data Objects|Service Whitelist Data Objects]]
- [[_COMMUNITY_VPC Endpoint Service Creation|VPC Endpoint Service Creation]]
- [[_COMMUNITY_Database Connection Management|Database Connection Management]]
- [[_COMMUNITY_Application Configuration|Application Configuration]]
- [[_COMMUNITY_IPv6 Address Management|IPv6 Address Management]]
- [[_COMMUNITY_Common Response Utilities|Common Response Utilities]]
- [[_COMMUNITY_Resource Management Core|Resource Management Core]]
- [[_COMMUNITY_Database Query Layer|Database Query Layer]]
- [[_COMMUNITY_VPC Endpoint Description APIs|VPC Endpoint Description APIs]]
- [[_COMMUNITY_VPC Endpoint Creation Flow|VPC Endpoint Creation Flow]]
- [[_COMMUNITY_Billing Resource Operations|Billing Resource Operations]]
- [[_COMMUNITY_Load Balancer Description|Load Balancer Description]]
- [[_COMMUNITY_Service Configuration Update|Service Configuration Update]]
- [[_COMMUNITY_Resource Lifecycle Management|Resource Lifecycle Management]]
- [[_COMMUNITY_IP Validation Utilities|IP Validation Utilities]]
- [[_COMMUNITY_API Request Handling|API Request Handling]]
- [[_COMMUNITY_L4 Gateway Management|L4 Gateway Management]]
- [[_COMMUNITY_Database Metrics Collection|Database Metrics Collection]]
- [[_COMMUNITY_IP Address Allocation|IP Address Allocation]]
- [[_COMMUNITY_Company Info Management|Company Info Management]]
- [[_COMMUNITY_Endpoint Service User Addition|Endpoint Service User Addition]]
- [[_COMMUNITY_Postpaid Billing Operations|Postpaid Billing Operations]]
- [[_COMMUNITY_Endpoint Service User Update|Endpoint Service User Update]]
- [[_COMMUNITY_PrivateLink Pricing API|PrivateLink Pricing API]]
- [[_COMMUNITY_Base RequestResponse|Base Request/Response]]
- [[_COMMUNITY_Bandwidth Range API|Bandwidth Range API]]
- [[_COMMUNITY_Endpoint Service Users List|Endpoint Service Users List]]
- [[_COMMUNITY_Endpoint Connection Acceptance|Endpoint Connection Acceptance]]
- [[_COMMUNITY_Endpoint Deletion Internal|Endpoint Deletion Internal]]
- [[_COMMUNITY_Service Configuration Deletion Internal|Service Configuration Deletion Internal]]
- [[_COMMUNITY_Endpoint Deletion API|Endpoint Deletion API]]
- [[_COMMUNITY_Service Configuration Deletion API|Service Configuration Deletion API]]
- [[_COMMUNITY_Internal Endpoint Deletion|Internal Endpoint Deletion]]
- [[_COMMUNITY_Internal Service Configuration Deletion|Internal Service Configuration Deletion]]
- [[_COMMUNITY_Endpoint Connection Rejection|Endpoint Connection Rejection]]
- [[_COMMUNITY_Endpoint Service User Removal|Endpoint Service User Removal]]
- [[_COMMUNITY_Endpoint Service User Update|Endpoint Service User Update]]
- [[_COMMUNITY_Endpoint Attribute Update|Endpoint Attribute Update]]
- [[_COMMUNITY_Endpoint Connection Attribute Update|Endpoint Connection Attribute Update]]
- [[_COMMUNITY_L4 Gateway Operations|L4 Gateway Operations]]
- [[_COMMUNITY_Load Balancer Description|Load Balancer Description]]
- [[_COMMUNITY_Config Generation|Config Generation]]
- [[_COMMUNITY_Endpoint Connection Acceptance API|Endpoint Connection Acceptance API]]
- [[_COMMUNITY_Bandwidth API Handler|Bandwidth API Handler]]
- [[_COMMUNITY_Pricing API Handler|Pricing API Handler]]
- [[_COMMUNITY_Service Users List API|Service Users List API]]
- [[_COMMUNITY_Data Refresh API|Data Refresh API]]
- [[_COMMUNITY_Connection Rejection API|Connection Rejection API]]
- [[_COMMUNITY_User Removal API|User Removal API]]
- [[_COMMUNITY_Endpoint Attribute Update API|Endpoint Attribute Update API]]
- [[_COMMUNITY_Connection Attribute Update API|Connection Attribute Update API]]
- [[_COMMUNITY_Service Configuration Deletion Handler|Service Configuration Deletion Handler]]
- [[_COMMUNITY_Service Table Model|Service Table Model]]
- [[_COMMUNITY_User Config Table Model|User Config Table Model]]
- [[_COMMUNITY_VPC Endpoint Table Model|VPC Endpoint Table Model]]
- [[_COMMUNITY_Company Info Fetching|Company Info Fetching]]
- [[_COMMUNITY_Resource Implementation Factory|Resource Implementation Factory]]
- [[_COMMUNITY_VPC Implementation Factory|VPC Implementation Factory]]
- [[_COMMUNITY_Slice Utilities|Slice Utilities]]
- [[_COMMUNITY_Build Images|Build Images]]
- [[_COMMUNITY_Manual Build Images|Manual Build Images]]
- [[_COMMUNITY_Code Quality Templates|Code Quality Templates]]
- [[_COMMUNITY_Connection Info Table Model|Connection Info Table Model]]
- [[_COMMUNITY_Service SNAT IP Table Model|Service SNAT IP Table Model]]
- [[_COMMUNITY_Service Whitelist Table Model|Service Whitelist Table Model]]
- [[_COMMUNITY_Database Model Generation|Database Model Generation]]
- [[_COMMUNITY_Design Documentation|Design Documentation]]
- [[_COMMUNITY_Merge Request Template|Merge Request Template]]
- [[_COMMUNITY_Image Build Test|Image Build Test]]
- [[_COMMUNITY_Linting Tools|Linting Tools]]
- [[_COMMUNITY_Linter Settings|Linter Settings]]

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

## Communities (83 total, 14 thin omitted)
### Community 0 - "Service Data Objects"
Cohesion: 0.06
Nodes (20): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+12 more)
### Community 1 - "User Config Data Objects"
Cohesion: 0.06
Nodes (20): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+12 more)
### Community 2 - "VPC Endpoint Data Objects"
Cohesion: 0.06
Nodes (20): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+12 more)
### Community 3 - "Connection Info Data Objects"
Cohesion: 0.06
Nodes (19): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+11 more)
### Community 4 - "Service SNAT IP Objects"
Cohesion: 0.06
Nodes (19): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+11 more)
### Community 5 - "Service Whitelist Data Objects"
Cohesion: 0.06
Nodes (19): Asterisk, Context, Dao, DB, DO, Expr, OrderExpr, ResultInfo (+11 more)
### Community 6 - "VPC Endpoint Service Creation"
Cohesion: 0.05
Nodes (37): AutoAccept2ConnectStatus(), Bool2Int(), GetConnectStatusCode(), GetConnectStatusName(), GetIPVersionCode(), GetIPVersionName(), GetPayerCode(), GetResourceTypeCode() (+29 more)
### Community 7 - "Database Connection Management"
Cohesion: 0.07
Nodes (16): Config, Database, extract(), Context, Query, Time, TService, TServiceSnatip (+8 more)
### Community 8 - "Application Configuration"
Cohesion: 0.05
Nodes (40): AccountImpl, API, Config, Server, ApplicationConfig, dumpConfig(), loadConfig(), main() (+32 more)
### Community 9 - "IPv6 Address Management"
Cohesion: 0.10
Nodes (32): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, VPCImpl, IpAllocatedStatus, IPv6NetworkInfo (+24 more)
### Community 10 - "Common Response Utilities"
Cohesion: 0.12
Nodes (39): GenMessage(), GenResponse(), GenRetCode(), RandNewID(), RandNewIDWithPrefix(), CommonResponse, EndpointConnectionInfo, EndpointInfo (+31 more)
### Community 11 - "Resource Management Core"
Cohesion: 0.12
Nodes (26): CreateResourceInfo, ExtendInfo, BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, ResourceInfo (+18 more)
### Community 12 - "Database Query Layer"
Cohesion: 0.08
Nodes (20): Context, DB, Query, tConnectInfo, tService, tServiceSnatip, tServiceWhitelist, tUserConfig (+12 more)
### Community 13 - "VPC Endpoint Description APIs"
Cohesion: 0.08
Nodes (21): GetPayerName(), API, CommonResponse, Context, GetResourceListResponse, ReqBase, RespBase, filterWithWhiteList() (+13 more)
### Community 14 - "VPC Endpoint Creation Flow"
Cohesion: 0.15
Nodes (14): API, CommonResponse, Context, ReqBase, RespBase, CreateVPCEndpointReq, CreateVPCEndpointResp, CheckEndpointCanConnectOtherChannel() (+6 more)
### Community 15 - "Billing Resource Operations"
Cohesion: 0.17
Nodes (17): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, UBillImpl, ItemInfo, BuyResourceRequest (+9 more)
### Community 16 - "Load Balancer Description"
Cohesion: 0.17
Nodes (14): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, LBImpl, DescribeLoadBalancersRequest, DescribeLoadBalancersResponse (+6 more)
### Community 17 - "Service Configuration Update"
Cohesion: 0.16
Nodes (12): checkIPv4(), Addr, API, CommonResponse, Context, IpInfo, IPv6Info, ReqBase (+4 more)
### Community 18 - "Resource Lifecycle Management"
Cohesion: 0.21
Nodes (8): CreateResourceResponse, DeleteResourceResponse, Context, GetResourceListResponse, ResourceInfo, ResourceImpl, UpdateResourceExtendInfoResponse, UpdateResourceStatusResponse
### Community 19 - "IP Validation Utilities"
Cohesion: 0.24
Nodes (9): API, Context, ReqBase, SubnetworkInfo, TServiceSnatip, VPCInfo, Addr, NetworkContain() (+1 more)
### Community 20 - "API Request Handling"
Cohesion: 0.20
Nodes (12): extractContext(), Application, Context, Database, jsonKey(), NewAPI(), parseAPIMetadata(), Config (+4 more)
### Community 21 - "L4 Gateway Management"
Cohesion: 0.22
Nodes (12): BaseRequest, BaseResponse, Context, IBaseRequest, IBaseResponse, L4Impl, CreateL4GwRequest, CreateL4GwResponse (+4 more)
### Community 22 - "Database Metrics Collection"
Cohesion: 0.28
Nodes (8): DB, Duration, Config, CustomMetric, CustomMetricCollector, DBStatCollector, NewPrometheusMonitor(), PrometheusMonitor
### Community 23 - "IP Address Allocation"
Cohesion: 0.28
Nodes (6): Context, IpInfo, IPv6Info, SubnetworkInfo, VPCImpl, VPCInfo
### Community 24 - "Company Info Management"
Cohesion: 0.20
Nodes (10): BaseRequest, BaseResponse, ComopanyInfo, Context, IBaseRequest, IBaseResponse, AccountImpl, ComopanyInfo (+2 more)
### Community 25 - "Endpoint Service User Addition"
Cohesion: 0.22
Nodes (9): AddEndpointServiceUser, AddEndpointServiceUser, API, CommonResponse, Context, ReqBase, RespBase, AddUsersToVPCEndpointServiceReq (+1 more)
### Community 26 - "Postpaid Billing Operations"
Cohesion: 0.31
Nodes (5): Context, UBillImpl, getMultiple(), getProductIdByProductName(), getProductIdByProductTypeCode()
### Community 27 - "Endpoint Service User Update"
Cohesion: 0.21
Nodes (6): API, CommonResponse, Context, API, CommonResponse, Context
### Community 28 - "PrivateLink Pricing API"
Cohesion: 0.25
Nodes (6): ReqBase, RespBase, GetPrivateLinkPriceRequest, GetPrivateLinkPriceResponse, PriceSet, PriceSet
### Community 29 - "Base Request/Response"
Cohesion: 0.25
Nodes (4): BaseRequest, BaseResponse, IBaseRequest, IBaseResponse
### Community 30 - "Bandwidth Range API"
Cohesion: 0.40
Nodes (5): BandwidthRange, ReqBase, RespBase, GetPrivateLinkBandwidthRequest, GetPrivateLinkBandwidthResponse
### Community 31 - "Endpoint Service Users List"
Cohesion: 0.33
Nodes (5): ReqBase, RespBase, ListVPCEndpointServiceUsersReq, ListVPCEndpointServiceUsersResp, EndpointServiceUser
### Community 32 - "Endpoint Connection Acceptance"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, AcceptVPCEndpointConnectionReq, AcceptVPCEndpointConnectionResp
### Community 33 - "Endpoint Deletion Internal"
Cohesion: 0.60
Nodes (3): API, CommonResponse, Context
### Community 34 - "Service Configuration Deletion Internal"
Cohesion: 0.60
Nodes (3): API, CommonResponse, Context
### Community 35 - "Endpoint Deletion API"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, DeleteVPCEndpointReq, DeleteVPCEndpointResp
### Community 36 - "Service Configuration Deletion API"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, DeleteVPCEndpointServiceConfigurationReq, DeleteVPCEndpointServiceConfigurationResp
### Community 37 - "Internal Endpoint Deletion"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, IDeleteVPCEndpointReq, IDeleteVPCEndpointResp
### Community 38 - "Internal Service Configuration Deletion"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, IDeleteVPCEndpointServiceConfigurationReq, IDeleteVPCEndpointServiceConfigurationResp
### Community 39 - "Endpoint Connection Rejection"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, RejectVPCEndpointConnectionReq, RejectVPCEndpointConnectionResp
### Community 40 - "Endpoint Service User Removal"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, RemoveUsersToVPCEndpointServiceReq, RemoveUsersToVPCEndpointServiceResp
### Community 41 - "Endpoint Service User Update"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, UpdateUsersToVPCEndpointServiceRequest, UpdateUsersToVPCEndpointServiceResponse
### Community 42 - "Endpoint Attribute Update"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, UpdateVPCEndpointAttributeReq, UpdateVPCEndpointAttributeResp
### Community 43 - "Endpoint Connection Attribute Update"
Cohesion: 0.40
Nodes (4): ReqBase, RespBase, UpdateVPCEndpointConnectionAttributeReq, UpdateVPCEndpointConnectionAttributeResp
### Community 45 - "Load Balancer Description"
Cohesion: 0.60
Nodes (3): Context, LBImpl, LoadBalancer
### Community 46 - "Config Generation"
Cohesion: 0.80
Nodes (4): Config, genOut(), loadConfig(), main()
### Community 47 - "Endpoint Connection Acceptance API"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 48 - "Bandwidth API Handler"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 49 - "Pricing API Handler"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 50 - "Service Users List API"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 51 - "Data Refresh API"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 52 - "Connection Rejection API"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 53 - "User Removal API"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 54 - "Endpoint Attribute Update API"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 55 - "Connection Attribute Update API"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 56 - "Service Configuration Deletion Handler"
Cohesion: 0.50
Nodes (3): API, CommonResponse, Context
### Community 60 - "Company Info Fetching"
Cohesion: 0.50
Nodes (3): ComopanyInfo, Context, AccountImpl
### Community 61 - "Resource Implementation Factory"
Cohesion: 0.83
Nodes (3): HTTPClient, ResourceImpl, NewVPCImpl()
### Community 62 - "VPC Implementation Factory"
Cohesion: 0.83
Nodes (3): HTTPClient, VPCImpl, NewVPCImpl()
### Community 64 - "Build Images"
Cohesion: 0.67
Nodes (3): amd64-buildimage, arm64-buildimage, .buildimage
### Community 65 - "Manual Build Images"
Cohesion: 0.67
Nodes (3): amd64-buildimage-manual, arm64-buildimage-manual, .buildimage-manual
### Community 66 - "Code Quality Templates"
Cohesion: 0.67
Nodes (3): CodeLint, CodeTest, mr_only_template

## Knowledge Gaps
- **277 isolated node(s):** `ReqBase`, `RespBase`, `API`, `Context`, `CommonResponse` (+272 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_
- **Why does `Use()` connect `Database Query Layer` to `Service Data Objects`, `User Config Data Objects`, `VPC Endpoint Data Objects`, `Connection Info Data Objects`, `Service SNAT IP Objects`, `Service Whitelist Data Objects`, `Database Connection Management`?**
  _High betweenness centrality (0.353) - this node is a cross-community bridge._
- **Why does `NewDatabase()` connect `Database Connection Management` to `Application Configuration`, `IP Validation Utilities`, `Database Query Layer`, `Database Metrics Collection`?**
  _High betweenness centrality (0.275) - this node is a cross-community bridge._
- **Why does `Logger` connect `IP Validation Utilities` to `VPC Endpoint Service Creation`, `Database Connection Management`, `VPC Endpoint Description APIs`, `VPC Endpoint Creation Flow`, `Service Configuration Update`, `API Request Handling`, `L4 Gateway Management`, `IP Address Allocation`, `Endpoint Service User Addition`, `Endpoint Service User Update`, `Endpoint Deletion Internal`, `Service Configuration Deletion Internal`, `Endpoint Connection Acceptance API`, `Pricing API Handler`, `Service Users List API`, `Data Refresh API`, `Connection Rejection API`, `User Removal API`, `Endpoint Attribute Update API`, `Connection Attribute Update API`?**
  _High betweenness centrality (0.239) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `Logger` (e.g. with `.AcceptVPCEndpointConnection()` and `.AddUsersToVPCEndpointService()`) actually correct?**
  _`Logger` has 46 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ReqBase`, `RespBase`, `API` to the rest of the system?**
  _277 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Service Data Objects` be split into smaller, more focused modules?**
  _Cohesion score 0.06116700201207243 - nodes in this community are weakly interconnected._
- **Should `User Config Data Objects` be split into smaller, more focused modules?**
  _Cohesion score 0.06116700201207243 - nodes in this community are weakly interconnected._