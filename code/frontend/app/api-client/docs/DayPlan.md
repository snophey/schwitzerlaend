
# DayPlan

Day plan model for workout schedules.

## Properties

Name | Type
------------ | -------------
`day` | string
`exercisesIds` | Array&lt;string&gt;

## Example

```typescript
import type { DayPlan } from ''

// TODO: Update the object below with actual values
const example = {
  "day": Monday,
  "exercisesIds": [set_1, set_2, set_3],
} satisfies DayPlan

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as DayPlan
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


