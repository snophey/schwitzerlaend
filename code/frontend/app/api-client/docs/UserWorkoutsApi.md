# UserWorkoutsApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**addWorkoutToUserUsersUserIdWorkoutsWorkoutIdPost**](UserWorkoutsApi.md#addworkouttouserusersuseridworkoutsworkoutidpost) | **POST** /users/{user_id}/workouts/{workout_id} | Add Workout To User |
| [**generateWorkoutForUserUsersUserIdGenerateWorkoutPost**](UserWorkoutsApi.md#generateworkoutforuserusersuseridgenerateworkoutpost) | **POST** /users/{user_id}/generate-workout | Generate Workout For User |
| [**getWeeklyOverviewUsersUserIdWeeklyOverviewGet**](UserWorkoutsApi.md#getweeklyoverviewusersuseridweeklyoverviewget) | **GET** /users/{user_id}/weekly-overview | Get Weekly Overview |
| [**removeWorkoutFromUserUsersUserIdWorkoutsWorkoutIdDelete**](UserWorkoutsApi.md#removeworkoutfromuserusersuseridworkoutsworkoutiddelete) | **DELETE** /users/{user_id}/workouts/{workout_id} | Remove Workout From User |



## addWorkoutToUserUsersUserIdWorkoutsWorkoutIdPost

> { [key: string]: any; } addWorkoutToUserUsersUserIdWorkoutsWorkoutIdPost(userId, workoutId)

Add Workout To User

Add a workout ID to the user\&#39;s associated_workout_ids list.  - **user_id**: ID of the user - **workout_id**: ID of the workout to associate with the user  Returns the updated user data.

### Example

```ts
import {
  Configuration,
  UserWorkoutsApi,
} from '';
import type { AddWorkoutToUserUsersUserIdWorkoutsWorkoutIdPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new UserWorkoutsApi();

  const body = {
    // string
    userId: userId_example,
    // string
    workoutId: workoutId_example,
  } satisfies AddWorkoutToUserUsersUserIdWorkoutsWorkoutIdPostRequest;

  try {
    const data = await api.addWorkoutToUserUsersUserIdWorkoutsWorkoutIdPost(body);
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


## generateWorkoutForUserUsersUserIdGenerateWorkoutPost

> { [key: string]: any; } generateWorkoutForUserUsersUserIdGenerateWorkoutPost(userId, generateWorkoutRequest)

Generate Workout For User

Generate an AI-powered workout plan for an existing user.  - **user_id**: ID of the user (must already exist) - **prompt**: Natural language description of the desired workout - **openai_api_key**: (Optional) OpenAI API key  Returns the created workout with workout_id and summary.

### Example

```ts
import {
  Configuration,
  UserWorkoutsApi,
} from '';
import type { GenerateWorkoutForUserUsersUserIdGenerateWorkoutPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new UserWorkoutsApi();

  const body = {
    // string
    userId: userId_example,
    // GenerateWorkoutRequest
    generateWorkoutRequest: ...,
  } satisfies GenerateWorkoutForUserUsersUserIdGenerateWorkoutPostRequest;

  try {
    const data = await api.generateWorkoutForUserUsersUserIdGenerateWorkoutPost(body);
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
| **generateWorkoutRequest** | [GenerateWorkoutRequest](GenerateWorkoutRequest.md) |  | |

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


## getWeeklyOverviewUsersUserIdWeeklyOverviewGet

> { [key: string]: any; } getWeeklyOverviewUsersUserIdWeeklyOverviewGet(userId)

Get Weekly Overview

Get weekly workout overview for a specific user.  - **user_id**: ID of the user  Returns a weekly overview showing all 7 days (Monday-Sunday) for each associated workout.

### Example

```ts
import {
  Configuration,
  UserWorkoutsApi,
} from '';
import type { GetWeeklyOverviewUsersUserIdWeeklyOverviewGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new UserWorkoutsApi();

  const body = {
    // string
    userId: userId_example,
  } satisfies GetWeeklyOverviewUsersUserIdWeeklyOverviewGetRequest;

  try {
    const data = await api.getWeeklyOverviewUsersUserIdWeeklyOverviewGet(body);
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


## removeWorkoutFromUserUsersUserIdWorkoutsWorkoutIdDelete

> { [key: string]: any; } removeWorkoutFromUserUsersUserIdWorkoutsWorkoutIdDelete(userId, workoutId)

Remove Workout From User

Remove a workout ID from the user\&#39;s associated_workout_ids list.  - **user_id**: ID of the user - **workout_id**: ID of the workout to remove from the user\&#39;s associated workouts  Returns the updated user data.

### Example

```ts
import {
  Configuration,
  UserWorkoutsApi,
} from '';
import type { RemoveWorkoutFromUserUsersUserIdWorkoutsWorkoutIdDeleteRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new UserWorkoutsApi();

  const body = {
    // string
    userId: userId_example,
    // string
    workoutId: workoutId_example,
  } satisfies RemoveWorkoutFromUserUsersUserIdWorkoutsWorkoutIdDeleteRequest;

  try {
    const data = await api.removeWorkoutFromUserUsersUserIdWorkoutsWorkoutIdDelete(body);
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

