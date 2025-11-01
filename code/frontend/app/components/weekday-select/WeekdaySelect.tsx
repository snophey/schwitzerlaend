
import { useState } from 'react';
import { Checkbox, Group, Text } from '@mantine/core';
import classes from './WeekdaySelect.module.css';

export function WeekdayCheckbox({ label }: { label: string }) {
  const [checked, setChecked] = useState(false);

  return (
    <Checkbox name={label} label={label} />
  );
}

export function WeekdaySelector() {
  return (
    <Group>
      <WeekdayCheckbox label="MON" />
      <WeekdayCheckbox label="TUE" />
      <WeekdayCheckbox label="WED" />
      <WeekdayCheckbox label="THU" />
      <WeekdayCheckbox label="FRI" />
      <WeekdayCheckbox label="SAT" />
      <WeekdayCheckbox label="SUN" />
    </Group> 
  )
}
