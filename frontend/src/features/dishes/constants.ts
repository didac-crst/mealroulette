export const DIFFICULTY_OPTIONS = [
  { value: "", label: "Not set" },
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
] as const;

export type DifficultyLevel = (typeof DIFFICULTY_OPTIONS)[number]["value"];

export function formatDifficulty(value: string | null | undefined): string {
  if (!value) {
    return "Not set";
  }
  return DIFFICULTY_OPTIONS.find((option) => option.value === value)?.label ?? value;
}
