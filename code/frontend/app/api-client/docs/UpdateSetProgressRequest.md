
# UpdateSetProgressRequest

Request model for updating progress on sets.

## Properties

Name | Type
------------ | -------------
`setId` | string
`completedReps` | number
`completedDurationSec` | number

## Example

```typescript
import type { UpdateSetProgressRequest } from ''

// TODO: Update the object below with actual values
const example = {
  "setId": set_123,
  "completedReps": null,
  "completedDurationSec": null,
} satisfies UpdateSetProgressRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as UpdateSetProgressRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


