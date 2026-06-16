# clients

> (no description)

**Endpoints:** 7

---

## GET /clients — Deprecated, use '/{type}/{version}' instead. List generator languages of type 'client' or 'documentation' for given codegen version (defaults to V3)

**Description:** (no description)

**Operation ID:** `clientLanguages`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
|  |  | object | No | — | (无描述) |
| clientOnly | query | boolean | No | False | flag to only return languages of type `client` |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |

---

## GET /generate — Generates and download code. GenerationRequest input provided as JSON available at URL specified in parameter codegenOptionsURL.

**Description:** (no description)

**Operation ID:** `generateFromURL`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| codegenOptionsURL | query | string | Yes | — | (无描述) |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |

---

## GET /options — Returns options for a given language and version (defaults to V3)

**Description:** (no description)

**Operation ID:** `listOptions`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
| language | query | string | No | — | language |
|  |  | object | No | — | (无描述) |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |

---

## GET /types — List generator languages of version defined in 'version parameter (defaults to V3) and type included in 'types' parameter; all languages

**Description:** (no description)

**Operation ID:** `languagesMulti`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
|  |  | object | No | — | (无描述) |
|  |  | object | No | — | (无描述) |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |

---

## GET /{type}/{version} — List generator languages of the given type and version

**Description:** (no description)

**Operation ID:** `languages`

### Request Parameters

| Name | In | Type | Required | Default | Description |
|------|----|------|----------|---------|-------------|
|  |  | object | No | — | (无描述) |
| version | path | string | Yes | — | generator version used by codegen engine |

### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |

---

## POST /generate — Generates and download code. GenerationRequest input provided as request body.

**Description:** (no description)

**Operation ID:** `generate`

### Request Parameters

无参数

### Request Body (application/json, optional)

#### GenerationRequest

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| lang | string | Yes | language to generate (required) |
| spec | object | No | spec in json format. . Alternative to `specURL` |
| specURL | string | No | URL of the spec in json format. Alternative to `spec` |
| type | string | No | type of the spec |
| codegenVersion | string | No | codegen version to use |
| options | object | No | (无描述) |

#### Options

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| auth | string | No | adds authorization headers when fetching the open api definitions remotely. Pass in a URL-encoded string of name:header with a comma separating multiple values |
| authorizationValue | object | No | (无描述) |
| apiPackage | string | No | package for generated api classes |
| templateVersion | string | No | template version for generation |
| modelPackage | string | No | package for generated models |
| modelNamePrefix | string | No | Prefix that will be prepended to all model names. Default is the empty string. |
| modelNameSuffix | string | No | PrefixSuffix that will be appended to all model names. Default is the empty string. |
| systemProperties | object | No | sets specified system properties in key/value format |
| instantiationTypes | object | No | sets instantiation type mappings in key/value format. For example (in Java): array=ArrayList,map=HashMap. In other words array types will get instantiated as ArrayList in generated code. |
| typeMappings | object | No | sets mappings between swagger spec types and generated code types in key/value format. For example: array=List,map=Map,string=String. |
| additionalProperties | object | No | sets additional properties that can be referenced by the mustache templates in key/value format. |
| languageSpecificPrimitives | array<string> | No | specifies additional language specific primitive types in the format of type1,type2,type3,type3. For example: String,boolean,Boolean,Double. You can also have multiple occurrences of this option. |
| importMappings | object | No | specifies mappings between a given class and the import that should be used for that class in key/value format. |
| invokerPackage | string | No | root package for generated code |
| groupId | string | No | groupId in generated pom.xml |
| artifactId | string | No | artifactId in generated pom.xml |
| artifactVersion | string | No | artifact version generated in pom.xml |
| library | string | No | library template (sub-template) |
| gitUserId | string | No | Git user ID, e.g. swagger-api. |
| gitRepoId | string | No | Git repo ID, e.g. swagger-codegen. |
| releaseNote | string | No | Release note, default to 'Minor update'. |
| httpUserAgent | string | No | HTTP user agent, e.g. codegen_csharp_api_client, default to 'Swagger-Codegen/{packageVersion}}/{language}' |
| reservedWordsMappings | object | No | pecifies how a reserved name should be escaped to. Otherwise, the default _<name> is used. For example id=identifier. |
| ignoreFileOverride | string | No | Specifies an override location for the .swagger-codegen-ignore file. Most useful on initial generation. |
| removeOperationIdPrefix | boolean | No | Remove prefix of operationId, e.g. config_getId => getId |
| skipOverride | boolean | No | (无描述) |

#### AuthorizationValue

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| value | string | No | Authorization value |
| keyName | string | No | Authorization key |
| type | string | No | Authorization type |
### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |

---

## POST /model — Generates the intermediate model ("bundle") and returns it as a JSON. body.

**Description:** (no description)

**Operation ID:** `generateBundle`

### Request Parameters

无参数

### Request Body (application/json, optional)

#### GenerationRequest

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| lang | string | Yes | language to generate (required) |
| spec | object | No | spec in json format. . Alternative to `specURL` |
| specURL | string | No | URL of the spec in json format. Alternative to `spec` |
| type | string | No | type of the spec |
| codegenVersion | string | No | codegen version to use |
| options | object | No | (无描述) |

#### Options

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| auth | string | No | adds authorization headers when fetching the open api definitions remotely. Pass in a URL-encoded string of name:header with a comma separating multiple values |
| authorizationValue | object | No | (无描述) |
| apiPackage | string | No | package for generated api classes |
| templateVersion | string | No | template version for generation |
| modelPackage | string | No | package for generated models |
| modelNamePrefix | string | No | Prefix that will be prepended to all model names. Default is the empty string. |
| modelNameSuffix | string | No | PrefixSuffix that will be appended to all model names. Default is the empty string. |
| systemProperties | object | No | sets specified system properties in key/value format |
| instantiationTypes | object | No | sets instantiation type mappings in key/value format. For example (in Java): array=ArrayList,map=HashMap. In other words array types will get instantiated as ArrayList in generated code. |
| typeMappings | object | No | sets mappings between swagger spec types and generated code types in key/value format. For example: array=List,map=Map,string=String. |
| additionalProperties | object | No | sets additional properties that can be referenced by the mustache templates in key/value format. |
| languageSpecificPrimitives | array<string> | No | specifies additional language specific primitive types in the format of type1,type2,type3,type3. For example: String,boolean,Boolean,Double. You can also have multiple occurrences of this option. |
| importMappings | object | No | specifies mappings between a given class and the import that should be used for that class in key/value format. |
| invokerPackage | string | No | root package for generated code |
| groupId | string | No | groupId in generated pom.xml |
| artifactId | string | No | artifactId in generated pom.xml |
| artifactVersion | string | No | artifact version generated in pom.xml |
| library | string | No | library template (sub-template) |
| gitUserId | string | No | Git user ID, e.g. swagger-api. |
| gitRepoId | string | No | Git repo ID, e.g. swagger-codegen. |
| releaseNote | string | No | Release note, default to 'Minor update'. |
| httpUserAgent | string | No | HTTP user agent, e.g. codegen_csharp_api_client, default to 'Swagger-Codegen/{packageVersion}}/{language}' |
| reservedWordsMappings | object | No | pecifies how a reserved name should be escaped to. Otherwise, the default _<name> is used. For example id=identifier. |
| ignoreFileOverride | string | No | Specifies an override location for the .swagger-codegen-ignore file. Most useful on initial generation. |
| removeOperationIdPrefix | boolean | No | Remove prefix of operationId, e.g. config_getId => getId |
| skipOverride | boolean | No | (无描述) |

#### AuthorizationValue

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| value | string | No | Authorization value |
| keyName | string | No | Authorization key |
| type | string | No | Authorization type |
### Responses

| Status | Description | Schema |
|--------|-------------|--------|
| 200 | successful operation | — |
