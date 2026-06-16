# store

> Access to Petstore orders

**Endpoints:** 4

---

## GET /store/inventory — Returns pet inventories by status.

**Description:** Returns a map of status codes to quantities.

**Operation ID:** `getInventory`

### Request Parameters

无参数

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |
| default | Unexpected error | — |

---

## GET /store/order/{orderId} — Find purchase order by ID.

**Description:** For valid response try integer IDs with value <= 5 or > 10. Other values will generate exceptions.

**Operation ID:** `getOrderById`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| orderId | path | integer(int64) | Yes | — | ID of order that needs to be fetched |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | Order |
| 400 | Invalid ID supplied | — |
| 404 | Order not found | — |
| default | Unexpected error | — |

#### 200 successful operation — Order

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| petId | integer(int64) | (无描述) |
| quantity | integer(int32) | (无描述) |
| shipDate | string(date-time) | (无描述) |
| status | string | Order Status |
| complete | boolean | (无描述) |
---

## POST /store/order — Place an order for a pet.

**Description:** Place a new order in the store.

**Operation ID:** `placeOrder`

### Request Parameters

无参数

### Request Body (application/json, optional)

#### Order

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer(int64) | No | (无描述) |
| petId | integer(int64) | No | (无描述) |
| quantity | integer(int32) | No | (无描述) |
| shipDate | string(date-time) | No | (无描述) |
| status | string | No | Order Status |
| complete | boolean | No | (无描述) |
### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | Order |
| 400 | Invalid input | — |
| 422 | Validation exception | — |
| default | Unexpected error | — |

#### 200 successful operation — Order

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| petId | integer(int64) | (无描述) |
| quantity | integer(int32) | (无描述) |
| shipDate | string(date-time) | (无描述) |
| status | string | Order Status |
| complete | boolean | (无描述) |
---

## DELETE /store/order/{orderId} — Delete purchase order by identifier.

**Description:** For valid response try integer IDs with value < 1000. Anything above 1000 or non-integers will generate API errors.

**Operation ID:** `deleteOrder`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| orderId | path | integer(int64) | Yes | — | ID of the order that needs to be deleted |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | order deleted | — |
| 400 | Invalid ID supplied | — |
| 404 | Order not found | — |
| default | Unexpected error | — |
