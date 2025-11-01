import { TbSkateboard } from "react-icons/tb";
import { LuWeight } from "react-icons/lu";
import { Text } from '@mantine/core';
import { useMemo } from "react";
import { Tag } from "./Tag";


export function TrainingsPlanItem({ title, day, day_number, exercises }: { title: string, day: string, day_number: number, exercises: any[] }) {
    //evalute all exercises and determine the icon to use
    const type = useMemo(() => {
        let weightCount = 0;
        let skateCount = 0;

        if (exercises && Array.isArray(exercises)) {
            exercises.forEach((exercise) => {
                const exerciseType = exercise?.type;
                if (exerciseType === "repetition" || exerciseType === "weighted repetition") {
                    weightCount++;
                }
                else if (exerciseType === "time" || exerciseType === "skill") {
                    skateCount++;
                }
            });
        }

        return weightCount >= skateCount ? "weight" : "skateboard";
    }, [exercises]);

    let exerciseNum = exercises.length;

    return (
        <div className="flex flex-col gap-2 p-4 rounded-md bg-gray-100 border-2 border-gray-400 w-full max-w-[30em]">

            <div className="flex items-center justify-between gap-2 w-full max-w-[30em]">
                <Text size="lg" fw={600}>{title}: {day_number}</Text>
                {type === "skateboard" ? <TbSkateboard size={24} /> : <LuWeight size={24} />}
            </div>

            <div>
                <Text>{day}</Text>
            </div>

            <Tag color="red-200">{exerciseNum} Exercises</Tag>

        </div>
    );
}