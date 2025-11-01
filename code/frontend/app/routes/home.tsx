import type { Route } from "./+types/home";
import { Welcome } from "../welcome/welcome";
import { TrainingsPlanItem } from "~/components/TrainingsPlanItem";
import { getSession } from "~/sessions.server";

export function meta({ }: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export async function loader({ request }: Route.LoaderArgs): Promise<any> {
  const session = await getSession(request.headers.get("Cookie"));
  const userId = 1;//session.get("userId");
  try {
    console.log(`${process.env.BACKEND_URL}/users/${userId}/weekly-overview`)
    const result = await fetch(`${process.env.BACKEND_URL}/users/${userId}/weekly-overview`);
    return result;
  } catch (e) {
    console.log("No workout for session" + e);
    return {};
  }
}

interface Exercise {
  name: string;
  type: string;
  reps?: number | null;
  weight?: number | null;
  duration_sec?: number | null;
  description: string;
}

interface WorkoutDay {
  day: string;
  day_number: number;
  sets: {
    name: string;
    reps: number | null;
    weight: number | null;
    duration_sec: number | null;
    exercise: {
      name: string;
      category: string; // 👈 added for "strength" or "stretching" type info
      instructions: string[];
    };
  }[];
  is_rest_day: boolean;
}

interface LoaderData {
  user_id: string;
  workouts: {
    weekly_plan: WorkoutDay[];
  }[];
}

export default function Home({ loaderData }: { loaderData: LoaderData }) {
  let strengthIndex = 0;
  let skateIndex = 0;
  return (
    <div className="flex flex-col gap-4 p-4">
      {loaderData.workouts[0].weekly_plan.map((day: WorkoutDay, index: number) => {
        if (day.is_rest_day) return null;

        const exercises: Exercise[] = day.sets.map((set) => ({
          name: set.exercise.name,
          type: set.weight
            ? "weighted repetition"
            : set.duration_sec
            ? "time"
            : "repetition",
          reps: set.reps,
          weight: set.weight,
          duration_sec: set.duration_sec,
          description: set.exercise.instructions.join(" "),
        }));

        let strengthCount = 0;
        let skateCount = 0;

        day.sets.forEach((set) => {
          const cat = set.exercise.category?.toLowerCase();
          if (cat === "strength") strengthCount++;
          else if (cat === "stretching" || cat === "skill") skateCount++;
        });

        const sessionType =
          strengthCount >= skateCount ? "Strength" : "Skate Session";

          const sessionNumber =
          sessionType === "Strength"
            ? ++strengthIndex
            : ++skateIndex;

        return (
          <div key={index} className="flex justify-center items-center">
            <TrainingsPlanItem
              title={sessionType}
              day_number={sessionNumber}
              day={day.day}
              exercises={exercises}
            />
          </div>
        );
      })}
    </div>
  );
}