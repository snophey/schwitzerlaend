
# CreateSetRequest

Request model for creating an exercise set.

## Properties

Name | Type
------------ | -------------
`name` | string
`exerciseId` | string
`reps` | number
`weight` | number
`durationSec` | number

## Example

```typescript
import type { CreateSetRequest } from ''

// TODO: Update the object below with actual values
const example = {
  "name": Push-ups Set 1,
  "exerciseId": push_up_001,
  "reps": null,
  "weight": null,
  "durationSec": null,
} satisfies CreateSetRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CreateSetRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


