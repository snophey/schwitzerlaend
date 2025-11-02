# SetsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createSetSetsPost**](SetsApi.md#createsetsetspost) | **POST** /sets/ | Create Set |
| [**deleteSetSetsSetIdDelete**](SetsApi.md#deletesetsetssetiddelete) | **DELETE** /sets/{set_id} | Delete Set |
| [**getSetSetsSetIdGet**](SetsApi.md#getsetsetssetidget) | **GET** /sets/{set_id} | Get Set |



## createSetSetsPost

> { [key: string]: any; } createSetSetsPost(createSetRequest)

Create Set

Create a new set consisting of exercises.  - **name**: Name of the set - **exercise_id**: ID of the exercise this set references - **reps**: Number of repetitions (optional) - **weight**: Weight in kg (optional) - **duration_sec**: Duration in seconds (optional)  Returns the created set with a generated ID.

### Example

```ts
import {
  Configuration,
  SetsApi,
} from '';
import type { CreateSetSetsPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new SetsApi();

  const body = {
    // CreateSetRequest
    createSetRequest: ...,
  } satisfies CreateSetSetsPostRequest;

  try {
    const data = await api.createSetSetsPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **createSetRequest** | [CreateSetRequest](CreateSetRequest.md) |  | |

### Return type

**{ [key: string]: any; }**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## deleteSetSetsSetIdDelete

> { [key: string]: any; } deleteSetSetsSetIdDelete(setId)

Delete Set

Delete a set by set_id.  - **set_id**: Unique identifier for the set  Returns a confirmation message upon successful deletion.

### Example

```ts
import {
  Configuration,
  SetsApi,
} from '';
import type { DeleteSetSetsSetIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new SetsApi();

  const body = {
    // string
    setId: setId_example,
  } satisfies DeleteSetSetsSetIdDeleteRequest;

  try {
    const data = await api.deleteSetSetsSetIdDelete(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **setId** | `string` |  | [Defaults to `undefined`] |

### Return type

**{ [key: string]: any; }**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getSetSetsSetIdGet

> { [key: string]: any; } getSetSetsSetIdGet(setId)

Get Set

Get set information by set_id.  - **set_id**: Unique identifier for the set  Returns the set data including name, exercise_id, reps, weight, and duration_sec.

### Example

```ts
import {
  Configuration,
  SetsApi,
} from '';
import type { GetSetSetsSetIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new SetsApi();

  const body = {
    // string
    setId: setId_example,
  } satisfies GetSetSetsSetIdGetRequest;

  try {
    const data = await api.getSetSetsSetIdGet(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **setId** | `string` |  | [Defaults to `undefined`] |

### Return type

**{ [key: string]: any; }**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

