
# CreateExerciseRequest

Request model for creating an exercise.

## Properties

Name | Type
------------ | -------------
`exerciseId` | string
`name` | string
`force` | string
`level` | string
`mechanic` | string
`equipment` | string
`primaryMuscles` | Array&lt;string&gt;
`secondaryMuscles` | Array&lt;string&gt;
`instructions` | Array&lt;string&gt;
`category` | string

## Example

```typescript
import type { CreateExerciseRequest } from ''

// TODO: Update the object below with actual values
const example = {
  "exerciseId": 3_4_Sit-Up,
  "name": 3/4 Sit-Up,
  "force": null,
  "level": null,
  "mechanic": null,
  "equipment": null,
  "primaryMuscles": null,
  "secondaryMuscles": null,
  "instructions": null,
  "category": null,
} satisfies CreateExerciseRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CreateExerciseRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


