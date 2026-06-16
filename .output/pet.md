# pet

> Everything about your Pets

**Endpoints:** 8

---

## GET /pet/findByStatus — Finds Pets by status.

**Description:** Multiple status values can be provided with comma separated strings.

**Operation ID:** `findPetsByStatus`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| status | query | string | Yes | available | Status values that need to be considered for filter |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | Pet |
| 400 | Invalid status value | — |
| default | Unexpected error | — |

#### 200 successful operation — Pet

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
| category | object | (无描述) |
| photoUrls | array<string> | (无描述) |
| tags | array<Tag> | (无描述) |
| status | string | pet status in the store |

#### Category

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |

#### Tag

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
---

## GET /pet/findByTags — Finds Pets by tags.

**Description:** Multiple tags can be provided with comma separated strings. Use tag1, tag2, tag3 for testing.

**Operation ID:** `findPetsByTags`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| tags | query | array | Yes | — | Tags to filter by |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | Pet |
| 400 | Invalid tag value | — |
| default | Unexpected error | — |

#### 200 successful operation — Pet

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
| category | object | (无描述) |
| photoUrls | array<string> | (无描述) |
| tags | array<Tag> | (无描述) |
| status | string | pet status in the store |

#### Category

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |

#### Tag

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
---

## GET /pet/{petId} — Find pet by ID.

**Description:** Returns a single pet.

**Operation ID:** `getPetById`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| petId | path | integer(int64) | Yes | — | ID of pet to return |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | Pet |
| 400 | Invalid ID supplied | — |
| 404 | Pet not found | — |
| default | Unexpected error | — |

#### 200 successful operation — Pet

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
| category | object | (无描述) |
| photoUrls | array<string> | (无描述) |
| tags | array<Tag> | (无描述) |
| status | string | pet status in the store |

#### Category

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |

#### Tag

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
---

## POST /pet — Add a new pet to the store.

**Description:** Add a new pet to the store.

**Operation ID:** `addPet`

### Request Parameters

无参数

### Request Body (application/json, required)

#### Pet

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer(int64) | No | (无描述) |
| name | string | Yes | (无描述) |
| category | object | No | (无描述) |
| photoUrls | array<string> | Yes | (无描述) |
| tags | array<Tag> | No | (无描述) |
| status | string | No | pet status in the store |

#### Category

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer(int64) | No | (无描述) |
| name | string | No | (无描述) |

#### Tag

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer(int64) | No | (无描述) |
| name | string | No | (无描述) |
### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | Successful operation | Pet |
| 400 | Invalid input | — |
| 422 | Validation exception | — |
| default | Unexpected error | — |

#### 200 Successful operation — Pet

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
| category | object | (无描述) |
| photoUrls | array<string> | (无描述) |
| tags | array<Tag> | (无描述) |
| status | string | pet status in the store |

#### Category

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |

#### Tag

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
---

## POST /pet/{petId} — Updates a pet in the store with form data.

**Description:** Updates a pet resource based on the form data.

**Operation ID:** `updatePetWithForm`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| petId | path | integer(int64) | Yes | — | ID of pet that needs to be updated |
| name | query | string | No | — | Name of pet that needs to be updated |
| status | query | string | No | — | Status of pet that needs to be updated |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | Pet |
| 400 | Invalid input | — |
| default | Unexpected error | — |

#### 200 successful operation — Pet

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
| category | object | (无描述) |
| photoUrls | array<string> | (无描述) |
| tags | array<Tag> | (无描述) |
| status | string | pet status in the store |

#### Category

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |

#### Tag

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
---

## POST /pet/{petId}/uploadImage — Uploads an image.

**Description:** Upload image of the pet.

**Operation ID:** `uploadFile`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| petId | path | integer(int64) | Yes | — | ID of pet to update |
| additionalMetadata | query | string | No | — | Additional Metadata |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | ApiResponse |
| 400 | No file uploaded | — |
| 404 | Pet not found | — |
| default | Unexpected error | — |

#### 200 successful operation — ApiResponse

| 字段 | 类型 | 描述 |
|------|------|------|
| code | integer(int32) | (无描述) |
| type | string | (无描述) |
| message | string | (无描述) |
---

## PUT /pet — Update an existing pet.

**Description:** Update an existing pet by Id.

**Operation ID:** `updatePet`

### Request Parameters

无参数

### Request Body (application/json, required)

#### Pet

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer(int64) | No | (无描述) |
| name | string | Yes | (无描述) |
| category | object | No | (无描述) |
| photoUrls | array<string> | Yes | (无描述) |
| tags | array<Tag> | No | (无描述) |
| status | string | No | pet status in the store |

#### Category

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer(int64) | No | (无描述) |
| name | string | No | (无描述) |

#### Tag

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer(int64) | No | (无描述) |
| name | string | No | (无描述) |
### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | Successful operation | Pet |
| 400 | Invalid ID supplied | — |
| 404 | Pet not found | — |
| 422 | Validation exception | — |
| default | Unexpected error | — |

#### 200 Successful operation — Pet

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
| category | object | (无描述) |
| photoUrls | array<string> | (无描述) |
| tags | array<Tag> | (无描述) |
| status | string | pet status in the store |

#### Category

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |

#### Tag

| 字段 | 类型 | 描述 |
|------|------|------|
| id | integer(int64) | (无描述) |
| name | string | (无描述) |
---

## DELETE /pet/{petId} — Deletes a pet.

**Description:** Delete a pet.

**Operation ID:** `deletePet`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| api_key | header | string | No | — | (无描述) |
| petId | path | integer(int64) | Yes | — | Pet id to delete |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | Pet deleted | — |
| 400 | Invalid pet value | — |
| default | Unexpected error | — |
