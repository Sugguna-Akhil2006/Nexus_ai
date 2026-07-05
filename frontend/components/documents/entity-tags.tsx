"use client";

interface EntityTagsProps {
  tags: string[];
}

export default function EntityTags({ tags }: EntityTagsProps) {
  if (tags.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 select-none">
      {tags.map((tag) => (
        <span
          key={tag}
          className="px-2.5 py-1 bg-surface-container-highest border border-outline-variant text-[10px] font-semibold rounded-md text-on-surface-variant hover:text-primary hover:border-primary/30 transition-all cursor-default"
        >
          {tag}
        </span>
      ))}
    </div>
  );
}
