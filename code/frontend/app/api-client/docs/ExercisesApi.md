# ExercisesApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createExerciseExercisesPost**](ExercisesApi.md#createexerciseexercisespost) | **POST** /exercises/ | Create Exercise |
| [**deleteExerciseExercisesExerciseIdDelete**](ExercisesApi.md#deleteexerciseexercisesexerciseiddelete) | **DELETE** /exercises/{exercise_id} | Delete Exercise |
| [**getAllExercisesExercisesGet**](ExercisesApi.md#getallexercisesexercisesget) | **GET** /exercises/ | Get All Exercises |
| [**getExerciseExercisesExerciseIdGet**](ExercisesApi.md#getexerciseexercisesexerciseidget) | **GET** /exercises/{exercise_id} | Get Exercise |



## createExerciseExercisesPost

> { [key: string]: any; } createExerciseExercisesPost(createExerciseRequest)

Create Exercise

Create a new exercise.  - **exercise_id**: Unique identifier for the exercise - **name**: Name of the exercise - **force**: Force type (optional) - **level**: Difficulty level (optional) - **mechanic**: Mechanic type (optional) - **equipment**: Equipment required (optional) - **primaryMuscles**: Primary muscles targeted (optional) - **secondaryMuscles**: Secondary muscles targeted (optional) - **instructions**: Step-by-step instructions (optional) - **category**: Exercise category (optional)  Returns the created exercise with its ID.

### Example

```ts
import {
  Configuration,
  ExercisesApi,
} from '';
import type { CreateExerciseExercisesPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ExercisesApi();

  const body = {
    // CreateExerciseRequest
    createExerciseRequest: ...,
  } satisfies CreateExerciseExercisesPostRequest;

  try {
    const data = await api.createExerciseExercisesPost(body);
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
| **createExerciseRequest** | [CreateExerciseRequest](CreateExerciseRequest.md) |  | |

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


## deleteExerciseExercisesExerciseIdDelete

> { [key: string]: any; } deleteExerciseExercisesExerciseIdDelete(exerciseId)

Delete Exercise

Delete an exercise by exercise_id.  - **exercise_id**: Unique identifier for the exercise  Returns a confirmation message upon successful deletion.

### Example

```ts
import {
  Configuration,
  ExercisesApi,
} from '';
import type { DeleteExerciseExercisesExerciseIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ExercisesApi();

  const body = {
    // string
    exerciseId: exerciseId_example,
  } satisfies DeleteExerciseExercisesExerciseIdDeleteRequest;

  try {
    const data = await api.deleteExerciseExercisesExerciseIdDelete(body);
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
| **exerciseId** | `string` |  | [Defaults to `undefined`] |

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


## getAllExercisesExercisesGet

> Array&lt;{ [key: string]: any; }&gt; getAllExercisesExercisesGet(skip, limit)

Get All Exercises

Get all exercises with pagination support.  - **skip**: Number of exercises to skip (for pagination, default: 0) - **limit**: Maximum number of exercises to return (default: 100, max: 1000)  Returns a list of exercises.

### Example

```ts
import {
  Configuration,
  ExercisesApi,
} from '';
import type { GetAllExercisesExercisesGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ExercisesApi();

  const body = {
    // number (optional)
    skip: 56,
    // number (optional)
    limit: 56,
  } satisfies GetAllExercisesExercisesGetRequest;

  try {
    const data = await api.getAllExercisesExercisesGet(body);
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
| **skip** | `number` |  | [Optional] [Defaults to `0`] |
| **limit** | `number` |  | [Optional] [Defaults to `100`] |

### Return type

**Array<{ [key: string]: any; }>**

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


## getExerciseExercisesExerciseIdGet

> { [key: string]: any; } getExerciseExercisesExerciseIdGet(exerciseId)

Get Exercise

Get exercise information by exercise_id.  - **exercise_id**: Unique identifier for the exercise  Returns the exercise data including all fields.

### Example

```ts
import {
  Configuration,
  ExercisesApi,
} from '';
import type { GetExerciseExercisesExerciseIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ExercisesApi();

  const body = {
    // string
    exerciseId: exerciseId_example,
  } satisfies GetExerciseExercisesExerciseIdGetRequest;

  try {
    const data = await api.getExerciseExercisesExerciseIdGet(body);
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
| **exerciseId** | `string` |  | [Defaults to `undefined`] |

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

