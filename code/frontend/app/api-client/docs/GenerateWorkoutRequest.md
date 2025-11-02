
# GenerateWorkoutRequest

Request model for AI-powered workout generation.

## Properties

Name | Type
------------ | -------------
`prompt` | string
`openaiApiKey` | string

## Example

```typescript
import type { GenerateWorkoutRequest } from ''

// TODO: Update the object below with actual values
const example = {
  "prompt": I want soft yoga mainly stretching mid efforts,
  "openaiApiKey": null,
} satisfies GenerateWorkoutRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as GenerateWorkoutRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


