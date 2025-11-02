# WorkoutsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createWorkoutWorkoutsPost**](WorkoutsApi.md#createworkoutworkoutspost) | **POST** /workouts/ | Create Workout |
| [**deleteWorkoutWorkoutsWorkoutIdDelete**](WorkoutsApi.md#deleteworkoutworkoutsworkoutiddelete) | **DELETE** /workouts/{workout_id} | Delete Workout |
| [**getWorkoutWorkoutsWorkoutIdGet**](WorkoutsApi.md#getworkoutworkoutsworkoutidget) | **GET** /workouts/{workout_id} | Get Workout |



## createWorkoutWorkoutsPost

> { [key: string]: any; } createWorkoutWorkoutsPost(createWorkoutRequest)

Create Workout

Create a new workout consisting of sets.  - **workout_plan**: Array of day plans, each containing:   - **day**: Day of the week (e.g., \&quot;Monday\&quot;, \&quot;Tuesday\&quot;)   - **exercises_ids**: Array of set IDs for that day  Returns the created workout with a generated ID.

### Example

```ts
import {
  Configuration,
  WorkoutsApi,
} from '';
import type { CreateWorkoutWorkoutsPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkoutsApi();

  const body = {
    // CreateWorkoutRequest
    createWorkoutRequest: ...,
  } satisfies CreateWorkoutWorkoutsPostRequest;

  try {
    const data = await api.createWorkoutWorkoutsPost(body);
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
| **createWorkoutRequest** | [CreateWorkoutRequest](CreateWorkoutRequest.md) |  | |

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


## deleteWorkoutWorkoutsWorkoutIdDelete

> { [key: string]: any; } deleteWorkoutWorkoutsWorkoutIdDelete(workoutId)

Delete Workout

Delete a workout by workout_id.  - **workout_id**: Unique identifier for the workout  Returns a confirmation message upon successful deletion.

### Example

```ts
import {
  Configuration,
  WorkoutsApi,
} from '';
import type { DeleteWorkoutWorkoutsWorkoutIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkoutsApi();

  const body = {
    // string
    workoutId: workoutId_example,
  } satisfies DeleteWorkoutWorkoutsWorkoutIdDeleteRequest;

  try {
    const data = await api.deleteWorkoutWorkoutsWorkoutIdDelete(body);
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
| **workoutId** | `string` |  | [Defaults to `undefined`] |

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


## getWorkoutWorkoutsWorkoutIdGet

> { [key: string]: any; } getWorkoutWorkoutsWorkoutIdGet(workoutId)

Get Workout

Get workout information by workout_id.  - **workout_id**: Unique identifier for the workout  Returns the workout data including workout_id and workout_plan.

### Example

```ts
import {
  Configuration,
  WorkoutsApi,
} from '';
import type { GetWorkoutWorkoutsWorkoutIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new WorkoutsApi();

  const body = {
    // string
    workoutId: workoutId_example,
  } satisfies GetWorkoutWorkoutsWorkoutIdGetRequest;

  try {
    const data = await api.getWorkoutWorkoutsWorkoutIdGet(body);
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
| **workoutId** | `string` |  | [Defaults to `undefined`] |

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

