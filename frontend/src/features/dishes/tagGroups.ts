import type { Tag } from "../../api/catalog";

export type TagFamilyGroup = {
  family: string;
  tags: Tag[];
};

export function formatTagFamily(family: string): string {
  return family.replace(/_/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}

export function groupTagsByFamily(tags: Tag[]): TagFamilyGroup[] {
  const groups = new Map<string, Tag[]>();

  for (const tag of tags) {
    const familyTags = groups.get(tag.family) ?? [];
    familyTags.push(tag);
    groups.set(tag.family, familyTags);
  }

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([family, familyTags]) => ({
      family,
      tags: familyTags.sort((left, right) => left.name.localeCompare(right.name)),
    }));
}
