# HistoryApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**completeSetHistoryUserIdCompletePost**](HistoryApi.md#completesethistoryuseridcompletepost) | **POST** /history/{user_id}/complete | Complete Set |
| [**getLatestHistoryHistoryUserIdLatestGet**](HistoryApi.md#getlatesthistoryhistoryuseridlatestget) | **GET** /history/{user_id}/latest | Get Latest History |
| [**healthCheckHistoryHealthGet**](HistoryApi.md#healthcheckhistoryhealthget) | **GET** /history/health | Health Check |
| [**updateSetProgressHistoryUserIdUpdatePost**](HistoryApi.md#updatesetprogresshistoryuseridupdatepost) | **POST** /history/{user_id}/update | Update Set Progress |



## completeSetHistoryUserIdCompletePost

> { [key: string]: any; } completeSetHistoryUserIdCompletePost(userId, completeSetRequest)

Complete Set

Mark a set as complete. When all sets in a day are complete, automatically creates a new history entry for the next day in the workout plan.  - **user_id**: ID of the user - **set_id**: ID of the set to mark as complete  Returns the updated history entry, and indicates if a new day was started.

### Example

```ts
import {
  Configuration,
  HistoryApi,
} from '';
import type { CompleteSetHistoryUserIdCompletePostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HistoryApi();

  const body = {
    // string
    userId: userId_example,
    // CompleteSetRequest
    completeSetRequest: ...,
  } satisfies CompleteSetHistoryUserIdCompletePostRequest;

  try {
    const data = await api.completeSetHistoryUserIdCompletePost(body);
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
| **userId** | `string` |  | [Defaults to `undefined`] |
| **completeSetRequest** | [CompleteSetRequest](CompleteSetRequest.md) |  | |

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


## getLatestHistoryHistoryUserIdLatestGet

> { [key: string]: any; } getLatestHistoryHistoryUserIdLatestGet(userId)

Get Latest History

Get the latest workout history for a user.  - **user_id**: ID of the user  Returns the current day\&#39;s workout progress including all sets and their completion status. If no history exists, creates an initial history entry from the user\&#39;s first workout.

### Example

```ts
import {
  Configuration,
  HistoryApi,
} from '';
import type { GetLatestHistoryHistoryUserIdLatestGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HistoryApi();

  const body = {
    // string
    userId: userId_example,
  } satisfies GetLatestHistoryHistoryUserIdLatestGetRequest;

  try {
    const data = await api.getLatestHistoryHistoryUserIdLatestGet(body);
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
| **userId** | `string` |  | [Defaults to `undefined`] |

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


## healthCheckHistoryHealthGet

> any healthCheckHistoryHealthGet()

Health Check

Health check endpoint to verify history router is loaded.

### Example

```ts
import {
  Configuration,
  HistoryApi,
} from '';
import type { HealthCheckHistoryHealthGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HistoryApi();

  try {
    const data = await api.healthCheckHistoryHealthGet();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

**any**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## updateSetProgressHistoryUserIdUpdatePost

> { [key: string]: any; } updateSetProgressHistoryUserIdUpdatePost(userId, updateSetProgressRequest)

Update Set Progress

Update progress on a specific set (e.g., number of reps completed).  - **user_id**: ID of the user - **set_id**: ID of the set to update - **completed_reps**: Number of reps completed (optional) - **completed_duration_sec**: Duration completed in seconds (optional)  Returns the updated history entry.

### Example

```ts
import {
  Configuration,
  HistoryApi,
} from '';
import type { UpdateSetProgressHistoryUserIdUpdatePostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new HistoryApi();

  const body = {
    // string
    userId: userId_example,
    // UpdateSetProgressRequest
    updateSetProgressRequest: ...,
  } satisfies UpdateSetProgressHistoryUserIdUpdatePostRequest;

  try {
    const data = await api.updateSetProgressHistoryUserIdUpdatePost(body);
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
| **userId** | `string` |  | [Defaults to `undefined`] |
| **updateSetProgressRequest** | [UpdateSetProgressRequest](UpdateSetProgressRequest.md) |  | |

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

