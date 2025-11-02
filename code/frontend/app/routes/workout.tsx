import PageWrapper from "~/components/PageWrapper/PageWrapper";
import type { Route } from "./+types/workout";
import {
  Accordion,
  ActionIcon,
  Button,
  Group,
  NumberInput,
  Pill,
  rem,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { TbCheck, TbInfoCircle } from "react-icons/tb";
import { Configuration, HistoryApi, ResponseError } from "~/api-client";
import { getSession } from "~/sessions.server";
import { Form, redirect } from "react-router";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Current Workout" },
    { name: "description", content: "Your current workout" },
  ];
}

type ExerciseSet = {
  set_id: string;
  set_name: string;
  exercise_id: string;
  exercise_name: string;
  target_reps: number;
  completed_reps: number;
  target_weight: number | null;
  target_duration_sec: number | null;
  is_complete: boolean;
  completed_at: string | null;
  exercise_details: {
    category: string;
    equipment: string;
    primaryMuscles: string[];
    instructions: string[];
  };
};

// Shape of the data returned by the loader
type HistoryResponse = {
  history_id: string;
  user_id: string;
  workout_id: string;
  current_day_index: number;
  day_name: string;
  sets: ExerciseSet[];
  progress: {
    total_sets: number;
    completed_sets: number;
    remaining_sets: number;
    completion_percentage: number;
  };
  created_at: string;
  updated_at: string;
};

function groupSetsByExerciseId(
  historyData: HistoryResponse
): Map<string, { name: string; sets: ExerciseSet[] }> {
  const exerciseMap = new Map<string, { name: string; sets: ExerciseSet[] }>();

  historyData.sets.forEach((set) => {
    if (!exerciseMap.has(set.exercise_id)) {
      exerciseMap.set(set.exercise_id, {
        name: set.exercise_name,
        sets: [],
      });
    }
    exerciseMap.get(set.exercise_id)?.sets.push(set);
  });

  return exerciseMap;
}

export async function loader({
  request,
}: Route.LoaderArgs): Promise<HistoryResponse> {
  const session = await getSession(request.headers.get("Cookie"));
  const userId = session.get("userId");

  if (!userId) {
    throw redirect("/");
  }

  console.log("Requesting workout for user ID:", userId);
  if (!userId) {
    console.log("No user ID in session!");
    throw new Response("Unauthorized", { status: 401 });
  }

  const api = new HistoryApi(
    new Configuration({
      basePath: process.env.BACKEND_URL,
    })
  );

  try {
    const data = (await api.getLatestHistoryHistoryUserIdLatestGet({
      userId,
    })) as HistoryResponse;
    return data;
  } catch (error) {
    if (error instanceof ResponseError && error.response.status === 404) {
      // no workout found for user → redirect to onboarding
      console.log("No workout found for user, redirecting to onboarding");
      throw redirect("/onboarding");
    }
    throw new Response("Failed to load workout data", { status: 500 });
  }
}

async function handleSingleSetCompletion(formData: FormData, userId: string, api: HistoryApi) {
  console.log(`Will update set ${formData.get("setId")} with data: ${JSON.stringify(Object.fromEntries(formData.entries()))}`);

  try {
    const data = await api.updateSetProgressHistoryUserIdUpdatePost({
      userId,
      updateSetProgressRequest: {
        setId: formData.get("setId") as string,
        completedReps: formData.has("completedReps")
          ? Number(formData.get("completedReps"))
          : undefined,
        completedDurationSec: formData.has("completedDurationSec")
          ? Number(formData.get("completedDurationSec"))
          : undefined,
      },
    });
    console.log(JSON.stringify(data));
  } catch (error) {
    console.error(error);
  }
}

function handleExerciseSessionCompletion(formData: FormData, userId: string, api: HistoryApi) {
  console.log(`Will mark sets ${formData.get("setIds")} as completed`);

  const setIds = JSON.parse(formData.get("setIds") as string) as string[];
  const promises = setIds.map((setId) => {
    return api.completeSetHistoryUserIdCompletePost({
      userId,
      completeSetRequest: {
        setId,
      }
    })
    .then(() => console.log(`Set ${setId} marked as completed`))
  });
  return Promise.all(promises);
}

export async function action({ request }: Route.ActionArgs) {
  const session = await getSession(request.headers.get("Cookie"));
  const userId = session.get("userId");

  if (!userId) {
    throw redirect("/");
  }

  console.log("Logged in as: " + userId);
  const api = new HistoryApi(
    new Configuration({
      basePath: process.env.BACKEND_URL,
    })
  );
  const formData = await request.formData();

  if (formData.has("setId")) {
    await handleSingleSetCompletion(formData, userId, api);
  } else if (formData.has("setIds")) {
    await handleExerciseSessionCompletion(formData, userId, api);
  }
}

// Expects a list of sets for a single exercise
function ExerciseTracker({ sets }: { sets: ExerciseSet[] }) {
  if (sets.length === 0) {
    return null;
  }
  const exerciseName = sets[0].exercise_name;
  return (
    <Stack gap="sm" mb="md">
      <Title
        order={3}
        size={"md"}
        mb={0}
        style={{
          fontWeight: "bolder",
        }}
      >
        {exerciseName}
      </Title>
      <Accordion>
        <Accordion.Item key={"info"} value={"info"}>
          <Accordion.Control
            style={{ fontSize: rem(12) }}
            icon={<TbInfoCircle />}
          >
            How to
          </Accordion.Control>
          <Accordion.Panel>
            {sets[0].exercise_details.instructions}
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
      {sets.map((set, index) => (
        <SingleSetInput key={index} set={set} setIndex={index+1} />
      ))}
    </Stack>
  );
}

// A single-line form containing a single input (either for reps or for duration) and a submit button
function SingleSetInput({ set, setIndex }: { set: ExerciseSet, setIndex: number }) {
  const targetWeight = set.target_weight != null ? `${set.target_weight} kg` : "Bodyweight";
  return (
    <Form action="/workout" method="post">
      <Group gap="sm">
        <input
          type="hidden"
          style={{ display: "none" }}
          name="setId"
          value={set.set_id}
        />
        <Text size="md" style={{ flex: 1 }}>
          {setIndex}
        </Text>
        <Text size="md" style={{ flex: 1 }}>
          {targetWeight}
        </Text>
        <Text size="md" style={{ flex: 1, color: "gray" }}>
          x
        </Text>
        {set.target_reps !== null && (
          <NumberInput
            name="completedReps"
            min={0}
            variant="filled"
            flex={4}
            value={set.completed_reps > 0 ? set.completed_reps : undefined}
            readOnly={!!set.completed_reps}
            placeholder={`${set.target_reps} Reps`}
            style={{ flexBasis: "60px", flexShrink: 1, flexGrow: 1 }}
            required
          />
        )}
        {set.target_duration_sec !== null && (
          <NumberInput
            name="completedDurationSec"
            flex={4}
            min={0}
            style={{ flexBasis: "60px", flexShrink: 1, flexGrow: 1 }}
            variant="filled"
            value={set.completed_reps > 0 ? set.completed_reps : undefined}
            readOnly={!!set.completed_reps}
            placeholder={`${set.target_duration_sec} Sec`}
            required
          />
        )}
        {/* If the sets have already been submitted, they cannot be changed (is that right?) */}
        <ActionIcon type={set.completed_reps ? "button" : "submit"} size={"lg"} variant={set.completed_reps ? "filled" : "transparent"} color={set.completed_reps ? "green" : "gray"} radius={"50%"}>
          <TbCheck />
        </ActionIcon>
      </Group>
    </Form>
  );
}

export default function Workout({
  loaderData,
}: {
  loaderData: Route.LoaderData;
}) {
  console.log("Loader data:", loaderData);

  const allSetIds = JSON.stringify(loaderData.sets.map((set: ExerciseSet) => set.set_id));
  const setsByExercise = groupSetsByExerciseId(loaderData);
  return (
    <PageWrapper>
      <Title order={2} mb="xl" style={{ textAlign: "left" }}>
        {loaderData.day_name}
      </Title>


      <Stack align="stretch" style={{ textAlign: "left" }}>
        {Array.from(setsByExercise.values()).map((exercise, index) => (
          <ExerciseTracker
            key={exercise.name}
            sets={exercise.sets}
          />
        ))}
        <Form style={{ marginTop: "auto" }} method="post" action="/workout">
          <input type="hidden" name="setIds" value={allSetIds} />
          <Button type="submit" size="lg" mt="auto" fullWidth>
            Complete Workout
          </Button>
        </Form>
      </Stack>
    </PageWrapper>
  );
}
