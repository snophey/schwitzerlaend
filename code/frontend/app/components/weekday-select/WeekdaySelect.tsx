
import { useState } from 'react';
import { Checkbox, Group, Text } from '@mantine/core';
import classes from './WeekdaySelect.module.css';

export function WeekdayCheckbox({ label, name }: { label: string, name?: string }) {
  const [checked, setChecked] = useState(false);

  return (
    <Checkbox name={name || label} label={label} />
  );
}

export function WeekdaySelector({ prefix = "" }: { prefix: string }) {
  return (
    <Group>
      <WeekdayCheckbox label="MON" name={prefix + "mon"} />
      <WeekdayCheckbox label="TUE" name={prefix + "tue"} />
      <WeekdayCheckbox label="WED" name={prefix + "wed"} />
      <WeekdayCheckbox label="THU" name={prefix + "thu"} />
      <WeekdayCheckbox label="FRI" name={prefix + "fri"} />
      <WeekdayCheckbox label="SAT" name={prefix + "sat"} />
      <WeekdayCheckbox label="SUN" name={prefix + "sun"} />
    </Group> 
  )
}
