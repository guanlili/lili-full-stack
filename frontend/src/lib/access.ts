export function canAccessPath(
  pages: readonly { path: string; allowed: boolean }[] | undefined,
  pathname: string,
): boolean {
  const path = pathname.replace(/\/$/, "") || "/"
  return pages?.some((page) => page.path === path && page.allowed) ?? false
}
