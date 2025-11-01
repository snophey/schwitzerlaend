import { Text } from "@mantine/core";
import animation from "assets/img/deadhang.gif";
import PageWrapper from "~/components/PageWrapper/PageWrapper";

export default function Done() {
    return (
        <PageWrapper>
            <div className="flex justify-center items-center">
                <div className="flex flex-col items-center gap-2">
                    <img src={animation} height={800} width={800} />
                    <Text size="lg" fw="bold">Done!</Text>
                    <Text>One step closer to greatness.</Text>
                </div>
            </div>
        </PageWrapper>
    );
}