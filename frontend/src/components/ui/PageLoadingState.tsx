import { Card } from "./Card";

type PageLoadingStateProps = {
  message: string;
};

export function PageLoadingState({ message }: PageLoadingStateProps) {
  return (
    <Card density="comfortable" aria-busy="true">
      <p className="muted page-loading-message">{message}</p>
    </Card>
  );
}
