
import { useState } from 'react';
import { Checkbox, Group, Text } from '@mantine/core';
import classes from './WeekdaySelect.module.css';

export function WeekdayCheckbox({ label, name }: { label: string, name?: string }) {
  return (
    <Checkbox color='red' classNames={classes} p={0} size='lg' name={name || label} label={label} />
  );
}

export function WeekdaySelector({ prefix = "" }: { prefix: string }) {
  return (
    <Group style={{ alignSelf: "stretch" }} gap={"xs"} justify="space-between">
      <WeekdayCheckbox label="MON" name={prefix + "monday"} />
      <WeekdayCheckbox label="TUE" name={prefix + "tuesday"} />
      <WeekdayCheckbox label="WED" name={prefix + "wednesday"} />
      <WeekdayCheckbox label="THU" name={prefix + "thursday"} />
      <WeekdayCheckbox label="FRI" name={prefix + "friday"} />
      <WeekdayCheckbox label="SAT" name={prefix + "saturday"} />
      <WeekdayCheckbox label="SUN" name={prefix + "sunday"} />
    </Group>
  );
}
