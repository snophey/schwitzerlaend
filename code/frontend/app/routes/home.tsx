import type { Route } from "./+types/home";
import { Welcome } from "../welcome/welcome";
import { TrainingsPlanItem } from "~/components/TrainingsPlanItem";

export function meta({ }: Route.MetaArgs) {
  return [
    { title: "New React Router App" },
    { name: "description", content: "Welcome to React Router!" },
  ];
}

export default function Home() {
  return (
    <div className="flex justify-center align-center">
      <TrainingsPlanItem
        title="Krafttraining"
        day_number={1}
        day="Monday"
        exercises={[{"name":"Push-ups","type":"repetition","reps":15,"description":"Perform 15 push-ups with proper form"},{"name":"Pull-ups","type":"repetition","reps":10,"description":"Complete 10 pull-ups or assisted pull-ups"},{"name":"Plank","type":"time","duration_sec":60,"description":"Hold plank position for 60 seconds"},{"name":"Bench Press","type":"weighted repetition","reps":8,"weight":75.0,"description":"Perform 8 reps of bench press with 75kg load"}]}
      />
    </div>
  );
}
