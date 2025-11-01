import { TbSkateboard } from "react-icons/tb";
import { LuWeight } from "react-icons/lu";
import { BiCheese } from "react-icons/bi";
import { Text } from "@mantine/core";
import { Tag } from "./Tag";

export function TrainingsPlanItem({
  title,
  day,
  day_number,
  exercises,
  type,
}: {
  title: string;
  day: string;
  day_number: number;
  exercises: any[];
  type: "Strength" | "Skate Session" | "Other";
}) {
  const exerciseNum = exercises.length;

  const Icon =
    type === "Skate Session"
      ? TbSkateboard
      : type === "Strength"
      ? LuWeight
      : BiCheese;

  return (
    <div className="flex flex-col gap-2 p-4 rounded-md bg-gray-100 border-2 border-gray-400 w-full max-w-[30em]">
      <div className="flex items-center justify-between gap-2 w-full">
        <Text size="lg" fw={600}>
          {title}
        </Text>
        <Icon size={24} />
      </div>

      <div className="flex items-start">
        <Text>{day}</Text>
      </div>

      <Tag color="bg-gray-200">{exerciseNum} Exercises</Tag>
    </div>
  );
}
