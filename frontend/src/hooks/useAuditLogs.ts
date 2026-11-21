import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { Audit } from "@/client"

export function useAuditLogs(page: number, pageSize: number, action: string) {
  const query = useQuery({
    queryKey: ["audit-logs", { page, pageSize, action }],
    queryFn: () =>
      Audit.logs
        .readAuditLogs({
          query: {
            skip: page * pageSize,
            limit: pageSize,
            action: action || undefined,
          },
          throwOnError: true,
        })
        .then((response) => response.data),
    placeholderData: keepPreviousData,
  })
  return { query }
}
