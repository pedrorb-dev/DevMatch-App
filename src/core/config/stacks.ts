import rawStacks from './stacks.json';

/** Categoría informativa: no condiciona el match. */
export type StackCategory = 'frontend' | 'mobile' | 'backend' | 'data' | 'cloud' | 'other';

/** Portales con slug explícito en el catálogo. */
export type StackPortal = 'occ' | 'computrabajo' | 'getonbrd';

export interface StackDefinition {
  name: string;
  category: StackCategory;
  selectable: boolean;
  aliases: string[];
  patterns: string[];
  slugs: Partial<Record<StackPortal, string>>;
}

export const STACK_CATALOG: readonly StackDefinition[] = rawStacks.map((stack) => ({
  name: stack.name,
  category: stack.category as StackCategory,
  selectable: stack.selectable,
  aliases: stack.aliases,
  patterns: stack.patterns,
  slugs: {
    occ: stack.slugs.occ,
    computrabajo: stack.slugs.computrabajo,
    getonbrd: stack.slugs.getonbrd,
  },
}));

export const TECH_OPTIONS: readonly string[] = STACK_CATALOG.filter(
  (stack) => stack.selectable,
).map((stack) => stack.name);
